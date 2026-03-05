#!/usr/bin/env python3
"""
build_mux_codebook_333k.py — Build 700×700 MUX grid from full Kaggle 333K dataset
==================================================================================
Reads english_unigram_freq.csv (333,333 word-frequency pairs from Kaggle),
sorts by frequency, assigns sequential grid positions, and outputs:
  - codebooks/mux_333k.csv  (human-readable: word, row, col, frequency_rank)
  - codebooks/mux_333k.bin  (serialized lookup dicts for fast loading)

Grid encoding: 3 bytes per word (v7.0 — simple, debug-friendly).
  Byte 0: row high 8 bits
  Byte 1: (row low 2 bits << 6) | (col high 6 bits)
  Byte 2: (col low 4 bits << 4) | 0x00 (4 bits reserved)

700×700 = 490,000 cells. 333K words used, 156,667 spare slots for dynamic
allocation starting at position 333,333 (row 476, col 133).

Author: Mark Snow, Jr. — Mindtech / CyberMesh / Liberty Mesh
Date:   March 2026
"""

import csv
import os
import pickle
import sys
import time


def load_frequencies(csv_path: str) -> list[tuple[str, int]]:
    """Load word frequencies, return sorted (word, count) pairs descending."""
    words: list[tuple[str, int]] = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            word = row["word"].strip().lower()
            try:
                count = int(row["count"])
            except (ValueError, TypeError):
                continue
            if count > 0 and word:
                words.append((word, count))
    # Sort by count descending (most frequent first)
    words.sort(key=lambda x: x[1], reverse=True)
    return words


def index_to_grid(index: int, grid_width: int = 700) -> tuple[int, int]:
    """Convert linear index to (row, col) grid position."""
    return divmod(index, grid_width)


def encode_grid_3byte(row: int, col: int) -> bytes:
    """
    Encode (row, col) into 3 bytes per spec:
      Byte 0: row high 8 bits
      Byte 1: (row low 2 bits << 6) | (col high 6 bits)
      Byte 2: (col low 4 bits << 4)  [4 bits unused]
    """
    b0 = (row >> 2) & 0xFF
    b1 = ((row & 0x03) << 6) | ((col >> 4) & 0x3F)
    b2 = ((col & 0x0F) << 4) & 0xFF
    return bytes([b0, b1, b2])


def decode_grid_3byte(data: bytes) -> tuple[int, int]:
    """Decode 3 bytes back to (row, col)."""
    b0, b1, b2 = data[0], data[1], data[2]
    row = (b0 << 2) | ((b1 >> 6) & 0x03)
    col = ((b1 & 0x3F) << 4) | ((b2 >> 4) & 0x0F)
    return row, col


def main():
    t_start = time.perf_counter()

    GRID_WIDTH = 700
    GRID_HEIGHT = 700
    GRID_TOTAL = GRID_WIDTH * GRID_HEIGHT  # 490,000

    # Paths — match repo layout
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_csv = os.path.join(base_dir, "english_unigram_freq.csv")
    output_dir = os.path.join(base_dir, "codebooks")
    os.makedirs(output_dir, exist_ok=True)
    output_csv = os.path.join(output_dir, "mux_333k.csv")
    output_bin = os.path.join(output_dir, "mux_333k.bin")

    print("=" * 78)
    print("  BUILD MUX CODEBOOK 333K — CyberMesh v7.0")
    print("=" * 78)

    # Step 1: Load and sort frequencies
    print(f"\n  Loading frequencies from {os.path.basename(input_csv)}...")
    words = load_frequencies(input_csv)
    print(f"  Loaded: {len(words):,} words (sorted by frequency descending)")

    # Step 2: Assign grid positions
    print(f"  Assigning grid positions ({GRID_WIDTH}×{GRID_HEIGHT})...")
    word_to_addr: dict[str, tuple[int, int]] = {}
    addr_to_word: dict[tuple[int, int], str] = {}

    for i, (word, count) in enumerate(words):
        if i >= GRID_TOTAL:
            print(f"  WARNING: {len(words) - GRID_TOTAL:,} words exceed grid capacity")
            break
        row, col = index_to_grid(i, GRID_WIDTH)
        word_to_addr[word] = (row, col)
        addr_to_word[(row, col)] = word

    total_assigned = len(word_to_addr)
    spare_slots = GRID_TOTAL - total_assigned
    spare_start_row, spare_start_col = index_to_grid(total_assigned, GRID_WIDTH)

    # Step 3: Validate 3-byte encoding round-trip
    print("  Validating 3-byte grid encoding...")
    t_enc = time.perf_counter()
    enc_pass = 0
    enc_fail = 0
    for word, (row, col) in word_to_addr.items():
        encoded = encode_grid_3byte(row, col)
        dec_row, dec_col = decode_grid_3byte(encoded)
        if dec_row == row and dec_col == col:
            enc_pass += 1
        else:
            enc_fail += 1
            if enc_fail <= 5:
                print(f"    FAIL: '{word}' ({row},{col}) → "
                      f"encode → ({dec_row},{dec_col})")
    enc_ms = (time.perf_counter() - t_enc) * 1000
    print(f"  3-byte encoding: {enc_pass:,} pass, {enc_fail:,} fail "
          f"({enc_ms:.0f} ms)")

    # Step 4: Statistics
    print(f"\n  {'─' * 74}")
    print(f"  GRID STATISTICS")
    print(f"  {'─' * 74}")
    print(f"  Grid dimensions:   {GRID_WIDTH} × {GRID_HEIGHT} = {GRID_TOTAL:,} cells")
    print(f"  Words assigned:    {total_assigned:>10,}")
    print(f"  Grid utilization:  {total_assigned / GRID_TOTAL * 100:>10.1f}%")
    print(f"  Spare slots:       {spare_slots:>10,}")
    print(f"  Spare start:       row {spare_start_row}, col {spare_start_col}")
    print(f"  Bytes per word:    {3:>10} (fixed 3-byte encoding)")
    print(f"  {'─' * 74}")

    # Top words check
    print(f"\n  Top 10 words (highest frequency → lowest grid address):")
    for i in range(min(10, len(words))):
        word, count = words[i]
        row, col = word_to_addr[word]
        encoded = encode_grid_3byte(row, col)
        print(f"    {i+1:>3}. '{word}'  count={count:>15,}  "
              f"grid=({row},{col})  hex={encoded.hex().upper()}")

    # Boundary check: last word
    if words:
        last_word, last_count = words[min(len(words), GRID_TOTAL) - 1]
        last_row, last_col = word_to_addr[last_word]
        print(f"\n  Last assigned word: '{last_word}'  count={last_count:,}  "
              f"grid=({last_row},{last_col})")

    # Step 5: Write CSV
    print(f"\n  Writing {os.path.basename(output_csv)}...")
    with open(output_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["word", "row", "col", "frequency_rank"])
        for rank, (word, count) in enumerate(words):
            if word in word_to_addr:
                row, col = word_to_addr[word]
                writer.writerow([word, row, col, rank])
    csv_size = os.path.getsize(output_csv)
    print(f"  CSV: {csv_size:,} bytes ({csv_size / 1024 / 1024:.1f} MB)")

    # Step 6: Serialize to .bin
    print(f"  Writing {os.path.basename(output_bin)}...")
    bin_data = {
        "word_to_addr": word_to_addr,
        "addr_to_word": addr_to_word,
        "grid_width": GRID_WIDTH,
        "grid_height": GRID_HEIGHT,
        "total_words": total_assigned,
        "spare_slots": spare_slots,
    }
    with open(output_bin, "wb") as f:
        pickle.dump(bin_data, f, protocol=pickle.HIGHEST_PROTOCOL)
    bin_size = os.path.getsize(output_bin)
    print(f"  BIN: {bin_size:,} bytes ({bin_size / 1024 / 1024:.1f} MB)")

    # Step 7: Full round-trip validation (word → addr → encode → decode → addr → word)
    print(f"\n  Round-trip validation (all {total_assigned:,} words)...")
    t_rt = time.perf_counter()
    rt_pass = 0
    rt_fail = 0
    for word, (row, col) in word_to_addr.items():
        encoded = encode_grid_3byte(row, col)
        dec_row, dec_col = decode_grid_3byte(encoded)
        decoded_word = addr_to_word.get((dec_row, dec_col))
        if decoded_word == word:
            rt_pass += 1
        else:
            rt_fail += 1
            if rt_fail <= 5:
                print(f"    FAIL: '{word}' ({row},{col}) → "
                      f"3byte → ({dec_row},{dec_col}) → '{decoded_word}'")
    rt_ms = (time.perf_counter() - t_rt) * 1000
    print(f"  Round-trip: {rt_pass:,} pass, {rt_fail:,} fail ({rt_ms:.0f} ms)")
    print(f"  Result: {'100% PASS ✓' if rt_fail == 0 else 'FAILURES ✗'}")

    total_ms = (time.perf_counter() - t_start) * 1000
    print(f"\n  {'─' * 74}")
    print(f"  Total build time: {total_ms / 1000:.1f} s")
    print(f"  Files: {output_csv}")
    print(f"         {output_bin}")
    print(f"{'=' * 78}\n")

    if rt_fail > 0 or enc_fail > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
