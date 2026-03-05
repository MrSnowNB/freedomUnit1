#!/usr/bin/env python3
"""
pretokenizer.py — Text normalization for CyberMesh codec pipeline
==================================================================
Normalizes LLM output before codec encoding to maximize codebook hit rate.
Fixes known ESC-triggering patterns: contractions, punctuation, decimals,
hyphens, mixed case.

Applied BEFORE encoding (sender side). The decoded text on the receiver
side is already normalized because the sender normalized before encoding.

Pipeline: [LLM generates text] → normalize() → codec.encode() → TX
          RX → codec.decode() → [display / feed to LLM]

Author: Mark Snow, Jr. — Mindtech / CyberMesh / Liberty Mesh
Date:   March 2026
"""

import re


# ── Contractions map (lowercase) ──

CONTRACTIONS = {
    "don't": "do not", "can't": "cannot", "won't": "will not",
    "i'm": "i am", "it's": "it is", "we're": "we are",
    "they're": "they are", "you're": "you are", "he's": "he is",
    "she's": "she is", "that's": "that is", "there's": "there is",
    "i've": "i have", "we've": "we have", "they've": "they have",
    "i'll": "i will", "we'll": "we will", "they'll": "they will",
    "isn't": "is not", "aren't": "are not", "wasn't": "was not",
    "weren't": "were not", "hasn't": "has not", "haven't": "have not",
    "didn't": "did not", "doesn't": "does not", "couldn't": "could not",
    "shouldn't": "should not", "wouldn't": "would not",
    "let's": "let us", "who's": "who is", "what's": "what is",
}


def normalize(text: str) -> str:
    """
    Normalize text for maximum codebook hit rate.

    Steps (in order):
      1. Lowercase
      2. Expand contractions
      3. Split hyphenated words (hyphens, en-dash, em-dash)
      4. Strip punctuation (preserve spaces and decimal numbers)
      5. Collapse multiple spaces
      6. Convert decimal numbers to "N point M" form
      7. Final space cleanup

    Args:
        text: Raw text from LLM output.

    Returns:
        Normalized text with maximum codebook coverage.
    """
    # Step 1: Lowercase
    text = text.lower()

    # Step 2: Expand contractions
    for contraction, expansion in CONTRACTIONS.items():
        text = text.replace(contraction, expansion)

    # Step 3: Split hyphenated words BEFORE stripping punctuation
    # "off-grid" → "off grid", "low-power" → "low power"
    text = text.replace('-', ' ')
    # Also handle en-dash and em-dash (already lowercased)
    text = text.replace('\u2013', ' ')  # en-dash
    text = text.replace('\u2014', ' ')  # em-dash

    # Step 4: Strip punctuation (preserve spaces and decimal numbers)
    # Protect decimal numbers: "2.1" → "2_DOT_1"
    text = re.sub(r'(\d+)\.(\d+)', r'\1_DOT_\2', text)
    # Remove all remaining punctuation (keep alphanumeric, spaces, underscores)
    text = re.sub(r'[^\w\s]', '', text)
    # Restore decimals: "2_DOT_1" → "2.1"
    text = re.sub(r'(\d+)_DOT_(\d+)', r'\1.\2', text)

    # Step 5: Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()

    # Step 6: Convert decimal numbers to "N point M" form
    # "2.1" → "2 point 1"  (both "point" and digits 0-100 are in codebook)
    text = re.sub(r'(\d+)\.(\d+)', r'\1 point \2', text)

    # Step 7: Collapse multiple spaces again after all transforms
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def compute_hit_rate(text: str, codebook_words: set) -> float:
    """
    Compute what fraction of words in text are in the codebook.

    Args:
        text: Normalized text.
        codebook_words: Set of lowercase words in the codebook.

    Returns:
        Float 0.0-1.0 representing codebook hit rate.
    """
    words = text.lower().split()
    if not words:
        return 1.0
    hits = sum(1 for w in words if w in codebook_words)
    return hits / len(words)


# ---------------------------------------------------------------------------
# CLI — standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  PRETOKENIZER — Text Normalization Tests")
    print("=" * 70)

    test_cases = [
        # (input, expected_output, description)
        (
            "Sensor 5 now reads 2.1 feet – escalating the response.",
            "sensor 5 now reads 2 point 1 feet escalating the response",
            "Decimal + dash + punctuation"
        ),
        (
            "Don't worry, it's online.",
            "do not worry it is online",
            "Contractions + punctuation"
        ),
        (
            "Alert! Node down — reboot ASAP!!!",
            "alert node down reboot asap",
            "Exclamations + dash + mixed case"
        ),
        (
            "off-grid low-power node",
            "off grid low power node",
            "Hyphens (removed by punct step)"
        ),
        (
            "Temperature: 72.5°F",
            "temperature 72 point 5f",
            "Colon + decimal + degree symbol"
        ),
        # Experiment B test messages
        ("ok", "ok", "Minimal"),
        ("SOS", "sos", "Uppercase"),
        ("Battery at 89 percent", "battery at 89 percent", "Mixed case + number"),
        (
            "Node 12 temperature 72 humidity 45",
            "node 12 temperature 72 humidity 45",
            "Multi-number + domain words"
        ),
        (
            "The sensor node is reporting temperature 94 degrees",
            "the sensor node is reporting temperature 94 degrees",
            "Full sentence"
        ),
        (
            "Alert flood warning for the area",
            "alert flood warning for the area",
            "Emergency domain"
        ),
        ("What time is it?", "what time is it", "Punctuation"),
        (
            "the sensor is online battery at 89 percent signal strong",
            "the sensor is online battery at 89 percent signal strong",
            "AI-constrained (already clean)"
        ),
    ]

    passed = 0
    failed = 0
    for inp, expected, desc in test_cases:
        result = normalize(inp)
        ok = result == expected
        status = "PASS ✓" if ok else "FAIL ✗"
        print(f"\n  [{status}] {desc}")
        print(f"    Input:    \"{inp}\"")
        print(f"    Output:   \"{result}\"")
        if not ok:
            print(f"    Expected: \"{expected}\"")
            failed += 1
        else:
            passed += 1

    print(f"\n  Results: {passed} passed, {failed} failed")
    print("=" * 70 + "\n")
