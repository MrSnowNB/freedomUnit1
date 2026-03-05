#!/usr/bin/env python3
"""
llm_codec.py — LLM-based encode/decode for CyberMesh codec pipeline
=====================================================================
Phase 2 of Experiment D: Uses the LLM as an active encoder and decoder.

Sender pipeline:
  1. LLM generates natural response (Call 1 — same as Experiment C)
  2. LLM ENCODES: rewrites using only codebook words (Call 2 — NEW)
  3. Pre-tokenizer normalizes
  4. Codec encodes (MUX Grid or Huffman) — most/all words are codebook hits

Receiver pipeline:
  1. Codec decodes
  2. LLM DECODES: expands compressed text to natural English (Call 3 — NEW)
  3. Natural text enters conversation history

The encode prompt provides the top ~500 most common codebook words as
examples and instructs the LLM to prefer simple common synonyms for
anything not shown.

The decode prompt receives ONLY the codebook-constrained text — it never
sees the original natural text.

Author: Mark Snow, Jr. — Mindtech / CyberMesh / Liberty Mesh
Date:   March 2026
"""

import os
import csv
import time
import requests
from typing import Optional

OLLAMA_URL = "http://localhost:11434"


def _load_codebook_words(codebook_csv_path: Optional[str] = None) -> list[str]:
    """
    Load the word list from mux_codebook.csv, ordered by index (frequency rank).

    Returns list of words (lowercase), excluding the <ESC> sentinel.
    """
    if codebook_csv_path is None:
        codebook_csv_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "mux_codebook.csv",
        )

    words = []
    with open(codebook_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            word = row["word"]
            if word == "<ESC>":
                continue
            words.append(word.lower())
    return words


def _build_encode_prompt(codebook_words: list[str], top_n: int = 500) -> str:
    """
    Build the system prompt for the LLM encode step.

    Includes the top N most common words from the codebook as examples.
    The LLM is instructed to prefer simple common synonyms for anything
    not in the shown list.
    """
    # Take the first top_n words (they're already sorted by frequency)
    sample_words = codebook_words[:top_n]
    word_list = ", ".join(sample_words)

    return f"""You are a text compressor. Rewrite the following message using ONLY words from this approved word list. Do not add words that are not on the list. Keep the core meaning. Be as short as possible. Output ONLY the rewritten message, nothing else.

Approved words (most common shown, full list of 4096 available):
{word_list}

If you need a word not shown above, use the simplest common English synonym. Prefer short, common words over long, rare ones."""


def _build_decode_prompt() -> str:
    """
    Build the system prompt for the LLM decode step.
    """
    return """You are a message interpreter for an emergency mesh network. The following message was transmitted in compressed form using only common English words. Expand it into a clear, natural English sentence. Preserve all numbers, sensor IDs, and factual content exactly. Output ONLY the expanded message, nothing else."""


# ── Module-level cache ──
_codebook_words: Optional[list[str]] = None
_codebook_set: Optional[set] = None
_encode_prompt: Optional[str] = None
_decode_prompt: Optional[str] = None


def _ensure_loaded(codebook_csv_path: Optional[str] = None):
    """Lazy-load codebook and prompts on first use."""
    global _codebook_words, _codebook_set, _encode_prompt, _decode_prompt
    if _codebook_words is None:
        _codebook_words = _load_codebook_words(codebook_csv_path)
        _codebook_set = set(_codebook_words)
        _encode_prompt = _build_encode_prompt(_codebook_words)
        _decode_prompt = _build_decode_prompt()


def get_codebook_words(codebook_csv_path: Optional[str] = None) -> set:
    """Return the set of codebook words (lowercase). Loads on first call."""
    _ensure_loaded(codebook_csv_path)
    return _codebook_set


def llm_encode(
    natural_text: str,
    model: str = "gemma3:latest",
    codebook_csv_path: Optional[str] = None,
    timeout: int = 60,
) -> tuple[str, float]:
    """
    Use the LLM to rewrite natural text using only codebook words.

    Args:
        natural_text: The natural language message to compress.
        model: Ollama model name.
        codebook_csv_path: Path to mux_codebook.csv (optional).
        timeout: HTTP timeout in seconds.

    Returns:
        (encoded_text, inference_ms)
    """
    _ensure_loaded(codebook_csv_path)

    prompt = f'Message to rewrite:\n"{natural_text}"'

    start = time.time()
    resp = requests.post(f"{OLLAMA_URL}/api/generate", json={
        "model": model,
        "system": _encode_prompt,
        "prompt": prompt,
        "options": {"temperature": 0.3},  # Lower temp for more deterministic constraint
        "stream": False,
    }, timeout=timeout)
    elapsed_ms = (time.time() - start) * 1000

    data = resp.json()
    text = data.get("response", "").strip()

    # Clean up: remove quotes, markdown, multiline
    text = text.strip('"\'')
    if '\n' in text:
        text = text.split('\n')[0].strip()

    return text, elapsed_ms


def llm_decode(
    encoded_text: str,
    model: str = "gemma3:latest",
    timeout: int = 60,
) -> tuple[str, float]:
    """
    Use the LLM to expand codebook-constrained text into natural English.

    The LLM ONLY sees the encoded text — it never sees the original natural text.
    This tests true reconstruction fidelity.

    Args:
        encoded_text: The codebook-constrained compressed message.
        model: Ollama model name.
        timeout: HTTP timeout in seconds.

    Returns:
        (decoded_text, inference_ms)
    """
    _ensure_loaded()

    prompt = f'Compressed message:\n"{encoded_text}"'

    start = time.time()
    resp = requests.post(f"{OLLAMA_URL}/api/generate", json={
        "model": model,
        "system": _decode_prompt,
        "prompt": prompt,
        "options": {"temperature": 0.3},
        "stream": False,
    }, timeout=timeout)
    elapsed_ms = (time.time() - start) * 1000

    data = resp.json()
    text = data.get("response", "").strip()

    # Clean up: remove quotes, markdown, multiline
    text = text.strip('"\'')
    if '\n' in text:
        text = text.split('\n')[0].strip()

    return text, elapsed_ms


# ---------------------------------------------------------------------------
# CLI — standalone test (requires Ollama running)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  LLM CODEC — Standalone Test")
    print("  Requires Ollama running at localhost:11434")
    print("=" * 70)

    _ensure_loaded()
    print(f"  Codebook loaded: {len(_codebook_words)} words")
    print(f"  Encode prompt: {len(_encode_prompt)} chars (top 500 words)")

    test_messages = [
        "Turbidity at Sensor 7 is now at 95%, significantly above normal. We need to activate emergency.",
        "Sensor 10 is at 7.5 feet — all residents near the middle school should evacuate immediately.",
        "Don't worry, the backup power system is operational and battery levels are at 89 percent.",
    ]

    for i, msg in enumerate(test_messages, 1):
        print(f"\n  --- Message {i} ---")
        print(f"  Natural:  \"{msg}\"")

        try:
            encoded, enc_ms = llm_encode(msg)
            print(f"  Encoded:  \"{encoded}\" ({enc_ms:.0f}ms)")

            # Check hit rate
            words = encoded.lower().split()
            hits = sum(1 for w in words if w in _codebook_set)
            hit_rate = hits / len(words) * 100 if words else 0
            esc_count = len(words) - hits
            print(f"  Hit rate: {hit_rate:.0f}% ({hits}/{len(words)} words, {esc_count} ESC)")

            decoded, dec_ms = llm_decode(encoded)
            print(f"  Decoded:  \"{decoded}\" ({dec_ms:.0f}ms)")

        except requests.exceptions.ConnectionError:
            print(f"  SKIP: Cannot connect to Ollama at {OLLAMA_URL}")
            break
        except Exception as e:
            print(f"  ERROR: {e}")

    print("\n" + "=" * 70 + "\n")
