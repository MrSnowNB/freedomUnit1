#!/usr/bin/env python3
"""
build_mux_codebook.py — Generate mux_codebook.csv for CyberMesh
===================================================================
Builds a 4,096-entry (64×64 grid) frequency-sorted codebook from:
  1. Top words from Kaggle English Word Frequency dataset
  2. Integers 0-100 as string tokens ("0", "1", ..., "100") — 101 entries
  3. Mesh domain terms not already in the list
  4. Index 4095 reserved as ESC (escape for out-of-codebook words)

Target: exactly 4,095 word entries + 1 ESC = 4,096 total entries.
This fills a 64×64 MUX grid exactly.

Output: mux_codebook.csv with columns: index, word, frequency

Author: Mark Snow, Jr. — Mindtech / CyberMesh / Liberty Mesh
Date:   March 2026
"""

import csv
import os

# Mesh domain terms to ensure are in the codebook
MESH_DOMAIN_TERMS = [
    "node", "mesh", "sensor", "gateway", "reboot",
    "ping", "ack", "rssi", "snr", "lora",
    "sos", "humidity", "flood", "battery", "percent",
    "temperature", "degrees", "online", "alert",
    "dispatch", "responder", "ambulance", "rescue",
    "evacuation", "shelter", "hazard", "outage",
    "firmware", "uptime", "topology", "antenna",
    "latitude", "longitude", "altitude", "voltage",
]

# Synthetic frequency for injected tokens.
# Must be above the natural cutoff (~17M for a 4095-word codebook from Kaggle)
# to guarantee inclusion. These are synthetic — they don't affect Huffman tree
# quality because the Huffman builder uses actual Kaggle frequencies for words
# that have them, and these values only for words that don't.
NUMBER_FREQ_BASE = 50_000_000
# Mesh domain gap-fill terms get even higher to ensure they're never cut
DOMAIN_FREQ_BASE = 60_000_000

# Target: 64×64 = 4096 entries, minus 1 for ESC = 4095 word slots
TARGET_WORD_COUNT = 4095


def build_codebook(freq_csv_path: str, output_path: str) -> dict:
    """Build the 4,096-entry MUX Grid codebook (64×64)."""
    # Step 1: Load Kaggle frequency data
    words = {}
    with open(freq_csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            if len(row) < 2:
                continue
            w = row[0].strip().lower()
            try:
                freq = int(row[1])
            except ValueError:
                continue
            # Skip single chars that aren't useful words
            if len(w) == 1 and w not in {"a", "i"}:
                continue
            # Skip entries that are pure digits (we add numbers separately)
            if w.isdigit():
                continue
            if w not in words:
                words[w] = freq

    print(f"  Kaggle dataset: {len(words)} eligible words loaded")

    # Step 2: Merge mesh domain terms with high synthetic frequency
    domain_added = 0
    for term in MESH_DOMAIN_TERMS:
        t = term.lower()
        if t not in words:
            words[t] = DOMAIN_FREQ_BASE - domain_added * 10_000
            domain_added += 1
        else:
            # Boost existing mesh domain words to ensure they stay in top
            words[t] = max(words[t], DOMAIN_FREQ_BASE - domain_added * 10_000)
    print(f"  Mesh domain terms: {domain_added} new, {len(MESH_DOMAIN_TERMS) - domain_added} already present")

    # Step 3: Add integers 0-100 as string tokens
    num_added = 0
    for n in range(101):
        tok = str(n)
        if tok not in words:
            words[tok] = NUMBER_FREQ_BASE - n  # descending by value
            num_added += 1
    print(f"  Number tokens (0-100): {num_added} new")

    # Step 4: Sort by descending frequency and take exactly TARGET_WORD_COUNT entries
    sorted_words = sorted(words.items(), key=lambda x: x[1], reverse=True)

    if len(sorted_words) < TARGET_WORD_COUNT:
        print(f"  WARNING: Only {len(sorted_words)} entries available, need {TARGET_WORD_COUNT}")
        final = sorted_words
    else:
        final = sorted_words[:TARGET_WORD_COUNT]

    print(f"  Final word count: {len(final)} (target: {TARGET_WORD_COUNT})")

    # Step 5: Write CSV
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["index", "word", "frequency"])
        for idx, (word, freq) in enumerate(final):
            writer.writerow([idx, word, freq])
        # Index 4095 = ESC
        writer.writerow([4095, "<ESC>", 0])

    total = len(final) + 1  # +1 for ESC
    print(f"  Written {total} entries to {output_path}")
    print(f"  Grid: 64×64 = {total} slots ({total == 4096 and 'EXACT' or 'MISMATCH'})")
    print(f"  Index 0 = '{final[0][0]}' (freq={final[0][1]})")
    print(f"  Index {len(final)-1} = '{final[-1][0]}' (freq={final[-1][1]})")
    print(f"  Index 4095 = <ESC> (reserved)")

    return {w: idx for idx, (w, _) in enumerate(final)}


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    freq_csv = os.path.join(script_dir, "english_unigram_freq.csv")
    output = os.path.join(script_dir, "mux_codebook.csv")

    print("=" * 60)
    print("  MUX Grid Codebook Builder — 64×64 (4,096 entries)")
    print("=" * 60)

    if not os.path.exists(freq_csv):
        print(f"  ERROR: {freq_csv} not found")
        return

    lookup = build_codebook(freq_csv, output)

    # Verify coverage of test messages
    test_messages = [
        "ok",
        "sos",
        "battery at 89 percent",
        "node 12 temperature 72 humidity 45",
        "the sensor node is reporting temperature 94 degrees",
        "alert flood warning for the area",
        "what time is it",
        "the sensor is online battery at 89 percent signal strong",
    ]

    print(f"\n  Test message coverage check:")
    for msg in test_messages:
        words = msg.lower().split()
        missing = [w for w in words if w not in lookup]
        status = "✓" if not missing else f"✗ missing: {missing}"
        print(f"    {status}  '{msg[:50]}'")

    print("=" * 60)


if __name__ == "__main__":
    main()
