#!/usr/bin/env python3
"""
keyword_codec.py — LLM-powered keyword extraction and sentence reconstruction
==============================================================================
v7.0 Smart Router module. Uses the LLM for TWO simple tasks:
  1. extract(): Text → keyword list (lossy compression of meaning)
  2. reconstruct(): Keyword list → natural sentence (receiver side)

CRITICAL: The extract() prompt does NOT reference any codebook.
Keywords are just important words — the codec layer handles encoding.
This is the KEY difference from v5.0's constrained rewrite approach.

Author: Mark Snow, Jr. — Mindtech / CyberMesh / Liberty Mesh
Date:   March 2026
"""

import logging
import re
import time

logger = logging.getLogger(__name__)


class KeywordCodec:
    """LLM-powered keyword extraction and sentence reconstruction."""

    def __init__(self, llm_client, config: dict):
        """
        Args:
            llm_client: LLMClient instance (or mock).
            config: Full config dict (needs 'keyword' section).
        """
        self.llm = llm_client
        kw_cfg = config.get("keyword", {})
        self.max_keywords = kw_cfg.get("max_keywords", 20)
        self.preserve_numbers = kw_cfg.get("preserve_numbers", True)
        self.preserve_negation = kw_cfg.get("preserve_negation", True)
        self.preserve_names = kw_cfg.get("preserve_names", True)

        # Exact prompts from v7.0 spec Section 4
        self._extract_system = (
            "You are a keyword extractor for emergency radio messages.\n"
            "Extract ONLY the important information-carrying words.\n"
            "Return keywords separated by spaces on a single line.\n"
            "Rules:\n"
            "- Remove articles (a, an, the), prepositions "
            "(in, on, at, for, to, of, from)\n"
            "- Remove filler (is, are, was, were, been, being, "
            "have, has, had)\n"
            "- KEEP all numbers exactly as written\n"
            "- KEEP negation words (not, no, never, none, dont, cant, wont)\n"
            "- KEEP proper nouns (names, places)\n"
            "- KEEP action verbs and status words\n"
            "- Maximum {max_kw} keywords\n"
            "- Output ONLY keywords separated by spaces, nothing else"
        )
        self._reconstruct_system = (
            "You are a message reconstructor for emergency radio.\n"
            "Given a list of keywords from a radio transmission, write a "
            "clear \nnatural sentence using ONLY the information in the "
            "keywords.\n"
            "Rules:\n"
            "- Use all provided keywords\n"
            "- Do NOT add information not present in the keywords\n"
            "- Do NOT ask questions or offer help\n"
            "- Write 1-2 sentences maximum\n"
            "- Be direct and clinical\n"
            "- Output ONLY the reconstructed sentence, nothing else"
        )

        logger.info("KeywordCodec init: max_keywords=%d, "
                     "preserve_numbers=%s, preserve_negation=%s, "
                     "preserve_names=%s",
                     self.max_keywords, self.preserve_numbers,
                     self.preserve_negation, self.preserve_names)

    def extract(self, text: str) -> tuple[list[str], float]:
        """
        Extract keywords from text using LLM.

        Returns:
            (keyword_list, elapsed_ms)

        The LLM is prompted with the exact system prompt from the v7.0 spec.
        Post-processing: split on whitespace, strip punctuation, lowercase,
        validate numerics, cap at max_keywords.
        """
        t0 = time.perf_counter()

        system = self._extract_system.format(max_kw=self.max_keywords)
        raw_text, llm_ms = self.llm.generate(
            system_prompt=system,
            user_prompt=text,
            max_tokens=100,  # keywords should be well under 100 tokens
            temperature=0.0,  # deterministic extraction
        )

        # Post-processing per spec
        keywords = self._postprocess_keywords(raw_text, text)

        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.info("KeywordCodec.extract: %d keywords in %.1f ms "
                     "(LLM: %.1f ms) from '%s'",
                     len(keywords), elapsed_ms, llm_ms,
                     text[:60])

        return keywords, elapsed_ms

    def _postprocess_keywords(self, raw_response: str,
                              original_text: str) -> list[str]:
        """
        Post-process LLM keyword extraction output.

        Steps per spec:
        1. Split result on whitespace
        2. Strip any punctuation from each keyword
        3. Lowercase all keywords
        4. If preserve_numbers: validate numeric tokens unchanged
        5. Cap at max_keywords
        """
        if not raw_response:
            logger.warning("KeywordCodec: empty LLM response, "
                           "falling back to simple extraction")
            return self._fallback_extract(original_text)

        # Step 1: Split on whitespace
        tokens = raw_response.split()

        # Step 2: Strip punctuation from each keyword
        cleaned = []
        for tok in tokens:
            # Remove leading/trailing punctuation but keep hyphens within words
            stripped = re.sub(r'^[^\w]+|[^\w]+$', '', tok)
            if stripped:
                cleaned.append(stripped)

        # Step 3: Lowercase all keywords
        keywords = [kw.lower() for kw in cleaned]

        # Step 4: Validate numeric tokens
        if self.preserve_numbers:
            # Extract numbers from original text for validation
            orig_numbers = set(re.findall(r'\b\d+(?:\.\d+)?\b',
                                           original_text))
            # Keep numeric keywords that appear in original
            validated = []
            for kw in keywords:
                if kw.isdigit() or re.match(r'^\d+\.\d+$', kw):
                    if kw in orig_numbers:
                        validated.append(kw)
                    else:
                        # LLM hallucinated a number — skip
                        logger.debug("Dropping hallucinated number: '%s'", kw)
                else:
                    validated.append(kw)
            keywords = validated

        # Step 5: Cap at max_keywords
        keywords = keywords[:self.max_keywords]

        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique.append(kw)

        return unique

    def _fallback_extract(self, text: str) -> list[str]:
        """
        Simple rule-based keyword extraction as fallback.

        Used when LLM returns empty or on error.
        """
        stop_words = {
            "a", "an", "the", "in", "on", "at", "for", "to", "of", "from",
            "is", "are", "was", "were", "been", "being", "have", "has", "had",
            "and", "or", "but", "with", "by", "up", "down", "out", "this",
            "that", "it", "its",
        }
        negation_words = {"not", "no", "never", "none", "dont", "cant", "wont"}

        words = text.lower().split()
        keywords = []
        for w in words:
            w_clean = re.sub(r'[^\w]', '', w)
            if not w_clean:
                continue
            if w_clean in negation_words:
                keywords.append(w_clean)
            elif w_clean not in stop_words:
                keywords.append(w_clean)

        return keywords[:self.max_keywords]

    def reconstruct(self, keywords: list[str]) -> tuple[str, float]:
        """
        Reconstruct a natural sentence from keywords using LLM.

        Returns:
            (reconstructed_sentence, elapsed_ms)

        The LLM is prompted with the exact system prompt from the v7.0 spec.
        Post-processing: strip whitespace, remove markdown formatting.
        """
        t0 = time.perf_counter()

        user_prompt = " ".join(keywords)
        raw_text, llm_ms = self.llm.generate(
            system_prompt=self._reconstruct_system,
            user_prompt=user_prompt,
            max_tokens=200,
            temperature=0.7,
        )

        # Post-processing per spec
        sentence = self._postprocess_reconstruction(raw_text)

        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.info("KeywordCodec.reconstruct: '%.60s' in %.1f ms "
                     "(LLM: %.1f ms)",
                     sentence, elapsed_ms, llm_ms)

        return sentence, elapsed_ms

    def _postprocess_reconstruction(self, raw_response: str) -> str:
        """
        Post-process LLM reconstruction output.

        Steps per spec:
        1. Strip whitespace
        2. Remove any markdown formatting
        """
        if not raw_response:
            return ""

        # Step 1: Strip whitespace
        text = raw_response.strip()

        # Step 2: Remove markdown formatting
        # Remove bold markers
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        # Remove italic markers
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'_(.+?)_', r'\1', text)
        # Remove code markers
        text = re.sub(r'`(.+?)`', r'\1', text)
        # Remove header markers
        text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
        # Remove bullet markers
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)

        return text.strip()


# ---------------------------------------------------------------------------
# CLI — standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import os
    import sys
    import yaml

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Load config
    cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "config.yaml")
    with open(cfg_path, "r") as f:
        cfg = yaml.safe_load(f)

    # Force mock mode for CLI testing
    from llm_client import LLMClient
    lem = cfg.get("lemonade", {})
    mock_mode = cfg.get("testing", {}).get("mock_llm", False)
    if "--mock" in sys.argv:
        mock_mode = True

    client = LLMClient(
        base_url=lem.get("base_url", "http://localhost:8000"),
        model=lem.get("model", "test01"),
        timeout=lem.get("timeout_s", 45),
        mock=mock_mode,
    )

    codec = KeywordCodec(llm_client=client, config=cfg)

    print("=" * 78)
    print(f"  KEYWORD CODEC v7.0 — mock={mock_mode}")
    print("=" * 78)

    # 5 sample emergency messages from spec
    test_messages = [
        "The flood warning is active for Lawrence Township and sensors are "
        "operational but station 7 is offline",
        "Deploy rescue team to north sector immediately we have 3 casualties",
        "Water level at sensor 5 reads 2 point 1 feet and rising fast",
        "All nodes reporting normal battery at 89 percent signal strong",
        "Do not send additional units the situation is under control at "
        "main street bridge",
    ]

    all_pass = True
    for i, msg in enumerate(test_messages, 1):
        print(f"\n  [{i}] EXTRACT")
        print(f"      Input: \"{msg}\"")

        keywords, extract_ms = codec.extract(msg)
        print(f"      Keywords ({len(keywords)}): {keywords}")
        print(f"      Time: {extract_ms:.1f} ms")

        # Validate semantic content
        has_content = len(keywords) >= 3
        print(f"      Content check: "
              f"{'PASS' if has_content else 'FAIL — too few keywords'}")

        print(f"\n      RECONSTRUCT")
        sentence, recon_ms = codec.reconstruct(keywords)
        print(f"      Output: \"{sentence}\"")
        print(f"      Time: {recon_ms:.1f} ms")

        if not has_content:
            all_pass = False

    print(f"\n{'=' * 78}")
    print(f"  RESULT: {'ALL TESTS PASS ✓' if all_pass else 'FAILURES ✗'}")
    print(f"{'=' * 78}\n")
