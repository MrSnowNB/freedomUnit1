#!/usr/bin/env python3
"""
paginator.py — Split text into LoRa-safe chunks for multi-page transmission
=============================================================================
Splits a message into pages of at most `max_chars` characters, breaking at
word boundaries. Each page gets a [1/N] header when N > 1.

Informed by the operator repo's textwrap.wrap + page-header pattern, but
written cleanly for the POC's binary codec pipeline (codec operates on
each page independently; receiver reassembles before feeding to LLM).

Author: Mark Snow, Jr. — Mindtech / CyberMesh / Liberty Mesh
Date:   March 2026
"""

import textwrap


def paginate(text: str, max_chars: int = 200) -> list[str]:
    """
    Split text into pages of at most max_chars characters.

    Args:
        text: The message to paginate.
        max_chars: Maximum characters per page (default 200).

    Returns:
        List of page strings. Single messages return a 1-element list.
        Multi-page messages get [1/N] headers prepended.
    """
    text = text.strip()
    if not text:
        return [""]

    # If it fits in one page, return as-is (no header needed)
    if len(text) <= max_chars:
        return [text]

    # Reserve space for page header "[XX/XX] " = max 8 chars
    header_reserve = 8
    usable = max_chars - header_reserve

    # Split at word boundaries using textwrap
    chunks = textwrap.wrap(text, width=usable, break_long_words=True, break_on_hyphens=True)

    if len(chunks) <= 1:
        return chunks if chunks else [text[:max_chars]]

    # Add page headers
    total = len(chunks)
    pages = []
    for i, chunk in enumerate(chunks):
        pages.append(f"[{i+1}/{total}] {chunk}")

    return pages


def reassemble(pages: list[str]) -> str:
    """
    Reassemble pages back into original text by stripping [X/N] headers.

    Args:
        pages: List of page strings, possibly with [X/N] headers.

    Returns:
        Reassembled text with headers stripped and pages joined by space.
    """
    import re
    cleaned = []
    for page in pages:
        # Strip [X/N] header if present
        stripped = re.sub(r'^\[\d+/\d+\]\s*', '', page)
        cleaned.append(stripped)
    return " ".join(cleaned)


# ---------------------------------------------------------------------------
# CLI — standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    test_cases = [
        "short message",
        "a " * 150,  # 300 chars, should paginate
        "The flood warning has been issued for Lawrence Township and all mesh nodes should report their current sensor readings including water level temperature and battery status immediately",
        "ok",
    ]

    for text in test_cases:
        pages = paginate(text.strip(), max_chars=200)
        print(f"\n  Input ({len(text.strip())} chars): \"{text.strip()[:60]}{'...' if len(text.strip()) > 60 else ''}\"")
        print(f"  Pages: {len(pages)}")
        for i, p in enumerate(pages):
            print(f"    [{i+1}] ({len(p)} chars) \"{p[:80]}{'...' if len(p) > 80 else ''}\"")

        # Test reassembly
        if len(pages) > 1:
            reassembled = reassemble(pages)
            print(f"  Reassembled ({len(reassembled)} chars): \"{reassembled[:80]}...\"")
