#!/usr/bin/env python3
"""
hooks.py — Deterministic post-processing hooks for CyberMesh Codec Harness
===========================================================================
Pattern: claude-code-best-practice (hooks outside the agentic loop)
Architecture: OpenClaw policy-as-constraints (enforcement phase)

These hooks run OUTSIDE the LLM — they are pure Python regex/string
operations. No LLM calls, no network, no side effects beyond the
returned result dict.

Each hook takes raw LLM output and returns a dict with:
  - cleaned: str — the processed text
  - violations: list[str] — what was found and stripped
  - passed: bool — True if no violations detected

Hooks are composable: chain them in sequence. Each hook receives the
output of the previous hook's 'cleaned' field.

Author: Mark Snow, Jr. — Mindtech / CyberMesh / Liberty Mesh
Date:   March 2026
"""

import re
import logging
from typing import Optional

logger = logging.getLogger("harness.hooks")


# ─── Issue #2 Fix: Strip Encode Framing ───────────────────────────────────────

# Patterns the LLM prepends/appends when it "helps" instead of encoding.
# These are pedagogical framing artifacts from RLHF training.
ENCODE_FRAMING_PATTERNS = [
    # Prefix framing — model labels its output
    r"^(?:Translated(?:\s+to\s+\w+)?)\s*:\s*",
    r"^(?:Encoded|Encoding)\s*:\s*",
    r"^(?:Here'?s?\s+(?:the\s+)?(?:encoded|rewritten|compressed)(?:\s+\w+)?)\s*:\s*",
    r"^(?:Output|Result|Response)\s*:\s*",
    r"^(?:Rewritten|Compressed|Simplified)\s*:\s*",
    r"^(?:Or,?\s+(?:more\s+)?(?:naturally|simply))\s*:\s*",
    r"^(?:The\s+(?:encoded|rewritten|compressed)\s+(?:message|text|version))\s*(?:is)?\s*:\s*",
    # Suffix framing — model explains after output
    r"\s*\((?:using|with)\s+(?:only\s+)?(?:codebook|approved)\s+words?\)\.?\s*$",
    r"\s*\((?:simplified|rewritten|compressed)\)\.?\s*$",
]

ENCODE_FRAMING_RE = [re.compile(p, re.IGNORECASE) for p in ENCODE_FRAMING_PATTERNS]


def hook_strip_encode_framing(text: str) -> dict:
    """
    Strip pedagogical framing prefixes/suffixes from encode output.

    Issue #2: LLM adds "Translated to Spanish:", "Explanation:", etc.
    instead of outputting raw codebook tokens.

    Args:
        text: Raw LLM encode output.

    Returns:
        dict with 'cleaned', 'violations', 'passed' keys.
    """
    violations = []
    cleaned = text.strip()

    for pattern_re in ENCODE_FRAMING_RE:
        match = pattern_re.search(cleaned)
        if match:
            violations.append(f"encode_framing: '{match.group()}'")
            cleaned = pattern_re.sub("", cleaned).strip()

    # Also strip leading/trailing quotes the model sometimes adds
    if cleaned.startswith('"') and cleaned.endswith('"'):
        cleaned = cleaned[1:-1].strip()
        violations.append("encode_framing: wrapped in quotes")
    elif cleaned.startswith("'") and cleaned.endswith("'"):
        cleaned = cleaned[1:-1].strip()
        violations.append("encode_framing: wrapped in single quotes")

    # Strip multiline — take only first line if model rambles
    if "\n" in cleaned:
        lines = [ln.strip() for ln in cleaned.split("\n") if ln.strip()]
        if len(lines) > 1:
            violations.append(
                f"encode_framing: multiline output ({len(lines)} lines), kept first"
            )
            cleaned = lines[0]

    passed = len(violations) == 0
    if violations:
        logger.info("hook_strip_encode_framing: %d violations: %s", len(violations), violations)

    return {"cleaned": cleaned, "violations": violations, "passed": passed}


# ─── Issue #3 Fix: Strip Decode Noise ─────────────────────────────────────────

# Patterns the LLM appends after decoding — meta-commentary, word counts, notes.
DECODE_NOISE_PATTERNS = [
    # Parenthetical notes
    r"\s*\(Word\s+count\s*:\s*\d+\)\s*\.?\s*$",
    r"\s*\(Note\s*:.*?\)\s*\.?\s*$",
    r"\s*\(Total\s*:.*?\)\s*\.?\s*$",
    r"\s*\(Approximately\s*:?.*?\)\s*\.?\s*$",
    r"\s*\(The\s+(?:above|actual|original).*?\)\s*\.?\s*$",
    r"\s*\(This\s+(?:is|was|means).*?\)\s*\.?\s*$",
    # Separator lines
    r"\s*---+\s*$",
    r"\s*===+\s*$",
    r"\s*\*\*\*+\s*$",
    # Trailing meta-text after the actual decoded message
    r"\s*Note\s*:.*$",
    r"\s*\(In\s+(?:other|simple)\s+words.*?\)\s*\.?\s*$",
]

DECODE_NOISE_RE = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in DECODE_NOISE_PATTERNS]

# Prefix noise — same issue as encode but for decode
DECODE_PREFIX_PATTERNS = [
    r"^(?:Expanded|Decoded|Interpreted)\s*:\s*",
    r"^(?:The\s+(?:expanded|decoded|interpreted)\s+(?:message|text))\s*(?:is)?\s*:\s*",
    r"^(?:Here'?s?\s+(?:the\s+)?(?:expanded|decoded|interpreted)(?:\s+\w+)?)\s*:\s*",
]

DECODE_PREFIX_RE = [re.compile(p, re.IGNORECASE) for p in DECODE_PREFIX_PATTERNS]


def hook_strip_decode_noise(text: str) -> dict:
    """
    Strip meta-commentary noise from decode output.

    Issue #3: LLM adds "(Word count: 34)", "(Note: ...)", "---", etc.
    after the actual decoded text.

    Args:
        text: Raw LLM decode output.

    Returns:
        dict with 'cleaned', 'violations', 'passed' keys.
    """
    violations = []
    cleaned = text.strip()

    # Strip prefix framing first
    for pattern_re in DECODE_PREFIX_RE:
        match = pattern_re.search(cleaned)
        if match:
            violations.append(f"decode_prefix: '{match.group()}'")
            cleaned = pattern_re.sub("", cleaned).strip()

    # Strip suffix noise
    for pattern_re in DECODE_NOISE_RE:
        match = pattern_re.search(cleaned)
        if match:
            violations.append(f"decode_noise: '{match.group().strip()}'")
            cleaned = pattern_re.sub("", cleaned).strip()

    # Strip quotes
    if cleaned.startswith('"') and cleaned.endswith('"'):
        cleaned = cleaned[1:-1].strip()
        violations.append("decode_noise: wrapped in quotes")
    elif cleaned.startswith("'") and cleaned.endswith("'"):
        cleaned = cleaned[1:-1].strip()
        violations.append("decode_noise: wrapped in single quotes")

    # Multiline — take only first meaningful line
    if "\n" in cleaned:
        lines = [ln.strip() for ln in cleaned.split("\n") if ln.strip()]
        if len(lines) > 1:
            violations.append(
                f"decode_noise: multiline output ({len(lines)} lines), kept first"
            )
            cleaned = lines[0]

    passed = len(violations) == 0
    if violations:
        logger.info("hook_strip_decode_noise: %d violations: %s", len(violations), violations)

    return {"cleaned": cleaned, "violations": violations, "passed": passed}


# ─── Codebook Validation ─────────────────────────────────────────────────────

def hook_validate_codebook(text: str, codebook_set: Optional[set] = None) -> dict:
    """
    Validate that encode output tokens are in the codebook.

    Checks each space-separated word against the codebook set.
    Reports out-of-codebook words as violations.

    Args:
        text: Processed encode output (post framing-strip).
        codebook_set: Set of lowercase codebook words. If None, validation
                      is skipped with a warning.

    Returns:
        dict with 'cleaned' (unchanged), 'violations', 'passed',
        plus 'hit_rate', 'hits', 'total', 'oov_words' keys.
    """
    if codebook_set is None:
        logger.warning("hook_validate_codebook: no codebook_set provided, skipping")
        return {
            "cleaned": text,
            "violations": ["codebook_set not provided"],
            "passed": False,
            "hit_rate": 0.0,
            "hits": 0,
            "total": 0,
            "oov_words": [],
        }

    words = text.lower().split()
    total = len(words)
    if total == 0:
        return {
            "cleaned": text,
            "violations": ["empty output"],
            "passed": False,
            "hit_rate": 0.0,
            "hits": 0,
            "total": 0,
            "oov_words": [],
        }

    hits = 0
    oov_words = []
    for w in words:
        # Strip trailing punctuation for lookup (e.g., "level," → "level")
        w_clean = re.sub(r"[.,;:!?]+$", "", w)
        if w_clean in codebook_set:
            hits += 1
        else:
            oov_words.append(w)

    hit_rate = hits / total
    violations = []
    if oov_words:
        violations.append(f"oov_words: {oov_words}")

    passed = hit_rate >= 0.70  # matches fallback_threshold from config

    logger.info(
        "hook_validate_codebook: %d/%d hits (%.1f%%), oov=%s",
        hits, total, hit_rate * 100, oov_words,
    )

    return {
        "cleaned": text,  # don't modify — just report
        "violations": violations,
        "passed": passed,
        "hit_rate": hit_rate,
        "hits": hits,
        "total": total,
        "oov_words": oov_words,
    }


# ─── Issue #1 Detection: Meta-Loop Collapse ──────────────────────────────────

# Phrases that indicate the model broke character and entered the
# RLHF "helpful assistant" persona instead of staying in codec role.
META_LOOP_PHRASES = [
    "would you like",
    "i can also",
    "let me",
    "here's",
    "here is",
    "do you want",
    "shall i",
    "i'd be happy to",
    "i can help",
    "if you'd like",
    "alternatively",
    "would you prefer",
    "i've",
    "i have",
    "sure,",
    "sure!",
    "of course",
    "certainly",
    "absolutely",
    "great question",
    "good question",
]


def hook_detect_meta_loop(text: str) -> dict:
    """
    Detect meta-loop collapse — model broke out of codec persona.

    Issue #1: LFM2.5-1.2B falls into "Would you like me to rewrite..."
    loop. This is the RLHF helpfulness bias activating despite system
    prompt constraints.

    This hook is DETECTION ONLY — it does not modify the text.
    The harness logs the violation and marks the test case as FAIL.

    Args:
        text: Raw or processed LLM output (works on either).

    Returns:
        dict with 'cleaned' (unchanged), 'violations', 'passed',
        plus 'meta_phrases_found' key.
    """
    text_lower = text.lower()
    found = []

    for phrase in META_LOOP_PHRASES:
        if phrase in text_lower:
            found.append(phrase)

    violations = []
    if found:
        violations.append(f"meta_loop: {found}")

    passed = len(found) == 0

    if not passed:
        logger.warning("hook_detect_meta_loop: DETECTED %d phrases: %s", len(found), found)

    return {
        "cleaned": text,  # detection only — don't modify
        "violations": violations,
        "passed": passed,
        "meta_phrases_found": found,
    }


# ─── Hook Runner ──────────────────────────────────────────────────────────────

def run_hooks(
    text: str,
    hook_names: list[str],
    codebook_set: Optional[set] = None,
) -> dict:
    """
    Run a sequence of hooks on LLM output.

    Each hook receives the 'cleaned' output of the previous hook.
    Violations accumulate across all hooks.

    Args:
        text: Raw LLM output.
        hook_names: List of hook function names from config.
        codebook_set: Codebook word set (for validate_codebook hook).

    Returns:
        dict with:
          - cleaned: final processed text
          - all_violations: list of all violations from all hooks
          - all_passed: True only if ALL hooks passed
          - hook_results: dict of hook_name → individual result
    """
    hook_map = {
        "strip_encode_framing": hook_strip_encode_framing,
        "strip_decode_noise": hook_strip_decode_noise,
        "validate_codebook": hook_validate_codebook,
        "detect_meta_loop": hook_detect_meta_loop,
    }

    current_text = text
    all_violations = []
    all_passed = True
    hook_results = {}

    for name in hook_names:
        fn = hook_map.get(name)
        if fn is None:
            logger.error("Unknown hook: %s", name)
            hook_results[name] = {"error": f"Unknown hook: {name}"}
            all_passed = False
            continue

        # validate_codebook needs codebook_set
        if name == "validate_codebook":
            result = fn(current_text, codebook_set=codebook_set)
        else:
            result = fn(current_text)

        hook_results[name] = result
        current_text = result["cleaned"]
        all_violations.extend(result.get("violations", []))
        if not result.get("passed", True):
            all_passed = False

    logger.info(
        "run_hooks: %d hooks, %d total violations, all_passed=%s",
        len(hook_names), len(all_violations), all_passed,
    )

    return {
        "cleaned": current_text,
        "all_violations": all_violations,
        "all_passed": all_passed,
        "hook_results": hook_results,
    }
