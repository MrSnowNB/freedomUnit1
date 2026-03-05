#!/usr/bin/env python3
"""
build_huffman_codebook_333k.py — Build Huffman tree from full Kaggle 333K dataset
=================================================================================
Reads english_unigram_freq.csv (333,333 word-frequency pairs from Kaggle),
builds a standard Huffman tree, and outputs:
  - codebooks/huffman_333k.csv  (human-readable: word, code_hex, code_length_bits)
  - codebooks/huffman_333k.bin  (serialized tree for fast loading)

Validation: round-trip test on every word, prefix-free property check,
code length distribution analysis.

Author: Mark Snow, Jr. — Mindtech / CyberMesh / Liberty Mesh
Date:   March 2026
"""

import csv
import heapq
import os
import pickle
import sys
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass(order=True)
class HuffmanNode:
    freq: int
    word: Optional[str] = field(default=None, compare=False)
    left: Optional["HuffmanNode"] = field(default=None, compare=False)
    right: Optional["HuffmanNode"] = field(default=None, compare=False)


def load_frequencies(csv_path: str) -> dict[str, int]:
    """Load word frequencies from Kaggle unigram_freq.csv (columns: word, count)."""
    freq: dict[str, int] = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            word = row["word"].strip().lower()
            try:
                count = int(row["count"])
            except (ValueError, TypeError):
                continue
            if count > 0 and word:
                freq[word] = count
    return freq


# Control tokens — must match huffman_codec.py exactly
_ESC     = "\x00ESC"
_NUM     = "\x00NUM"
_PUNCT   = "\x00PUN"
_NOSPACE = "\x00NSP"
_EOF     = "\x00EOF"


def add_control_tokens(freq: dict[str, int]) -> dict[str, int]:
    """
    Add control tokens to frequency table BEFORE building the Huffman tree.

    This ensures the .bin file contains codes for all control tokens,
    eliminating the need to rebuild the tree at load time.
    """
    word_freqs = sorted(freq.values(), reverse=True)
    mid = word_freqs[len(word_freqs) // 2] if word_freqs else 1_000_000
    freq[_NOSPACE] = mid * 3
    freq[_NUM]     = mid * 2
    freq[_PUNCT]   = mid * 2
    freq[_ESC]     = mid
    freq[_EOF]     = 1
    return freq


def build_tree(freq: dict[str, int]) -> HuffmanNode:
    """Build standard Huffman tree using heapq priority queue."""
    # Use a tie-breaker counter to ensure stable ordering for equal frequencies
    counter = 0
    heap: list[tuple[int, int, HuffmanNode]] = []
    for word, f in freq.items():
        heapq.heappush(heap, (f, counter, HuffmanNode(freq=f, word=word)))
        counter += 1

    while len(heap) > 1:
        f1, _, lo = heapq.heappop(heap)
        f2, _, hi = heapq.heappop(heap)
        merged = HuffmanNode(freq=f1 + f2, left=lo, right=hi)
        heapq.heappush(heap, (merged.freq, counter, merged))
        counter += 1

    return heap[0][2]


def generate_codes(root: HuffmanNode) -> dict[str, str]:
    """Generate binary codes via tree traversal. Returns word → binary_string."""
    codes: dict[str, str] = {}

    def walk(node: HuffmanNode, prefix: str = ""):
        if node.word is not None:
            codes[node.word] = prefix or "0"  # single-node tree edge case
            return
        if node.left:
            walk(node.left, prefix + "0")
        if node.right:
            walk(node.right, prefix + "1")

    walk(root)
    return codes


def bits_to_hex(bits: str) -> str:
    """Convert a binary string to hex representation."""
    # Pad to nibble boundary for clean hex
    padded = bits + "0" * ((4 - len(bits) % 4) % 4)
    return hex(int(padded, 2))[2:].upper()


def verify_prefix_free(codes: dict[str, str]) -> bool:
    """Verify no code is a prefix of another code."""
    sorted_codes = sorted(codes.values())
    for i in range(len(sorted_codes) - 1):
        if sorted_codes[i + 1].startswith(sorted_codes[i]):
            return False
    return True


def main():
    t_start = time.perf_counter()

    # Paths — match repo layout, NOT spec's kaggle/ path
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_csv = os.path.join(base_dir, "english_unigram_freq.csv")
    output_dir = os.path.join(base_dir, "codebooks")
    os.makedirs(output_dir, exist_ok=True)
    output_csv = os.path.join(output_dir, "huffman_333k.csv")
    output_bin = os.path.join(output_dir, "huffman_333k.bin")

    print("=" * 78)
    print("  BUILD HUFFMAN CODEBOOK 333K — CyberMesh v7.0")
    print("=" * 78)

    # Step 1: Load frequencies
    print(f"\n  Loading frequencies from {os.path.basename(input_csv)}...")
    freq = load_frequencies(input_csv)
    print(f"  Loaded: {len(freq):,} words with count > 0")

    # Step 1b: Add control tokens BEFORE building tree
    freq = add_control_tokens(freq)
    print(f"  Added 5 control tokens (ESC, NUM, PUNCT, NOSPACE, EOF)")
    print(f"  Total symbols: {len(freq):,}")

    # Step 2: Build Huffman tree
    print("  Building Huffman tree...")
    t_tree = time.perf_counter()
    root = build_tree(freq)
    tree_ms = (time.perf_counter() - t_tree) * 1000
    print(f"  Tree built in {tree_ms:.0f} ms")

    # Step 3: Generate binary codes
    print("  Generating binary codes...")
    codes = generate_codes(root)
    print(f"  Generated: {len(codes):,} codes")

    # Step 4: Verify prefix-free property
    print("  Verifying prefix-free property...")
    t_pfx = time.perf_counter()
    is_prefix_free = verify_prefix_free(codes)
    pfx_ms = (time.perf_counter() - t_pfx) * 1000
    print(f"  Prefix-free: {'PASS ✓' if is_prefix_free else 'FAIL ✗'} "
          f"({pfx_ms:.0f} ms)")

    # Step 5: Compute statistics
    lengths = [len(c) for c in codes.values()]
    min_len = min(lengths)
    max_len = max(lengths)
    avg_len = sum(lengths) / len(lengths)

    # Code length distribution by frequency rank
    sorted_by_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    top_100_lens = [len(codes[w]) for w, _ in sorted_by_freq[:100] if w in codes]
    top_10k_lens = [len(codes[w]) for w, _ in sorted_by_freq[:10000] if w in codes]
    tail_lens = [len(codes[w]) for w, _ in sorted_by_freq[10000:] if w in codes]

    print(f"\n  {'─' * 74}")
    print(f"  CODEBOOK STATISTICS")
    print(f"  {'─' * 74}")
    print(f"  Total words:       {len(codes):>10,}")
    print(f"  Min code length:   {min_len:>10} bits")
    print(f"  Max code length:   {max_len:>10} bits")
    print(f"  Avg code length:   {avg_len:>10.1f} bits")
    print(f"  Tree depth:        {max_len:>10}")
    print(f"  {'─' * 74}")
    print(f"  Top 100 words:     {min(top_100_lens):>3}–{max(top_100_lens):<3} bits "
          f"(avg {sum(top_100_lens)/len(top_100_lens):.1f})")
    print(f"  Top 10K words:     {min(top_10k_lens):>3}–{max(top_10k_lens):<3} bits "
          f"(avg {sum(top_10k_lens)/len(top_10k_lens):.1f})")
    if tail_lens:
        print(f"  Tail (10K+):       {min(tail_lens):>3}–{max(tail_lens):<3} bits "
              f"(avg {sum(tail_lens)/len(tail_lens):.1f})")

    # Distribution buckets
    buckets = {}
    for l in lengths:
        bucket = f"{(l // 5) * 5 + 1}–{(l // 5) * 5 + 5}"
        buckets[bucket] = buckets.get(bucket, 0) + 1
    print(f"\n  Code length distribution:")
    for bucket in sorted(buckets.keys()):
        count = buckets[bucket]
        bar = "█" * max(1, count // 2000)
        print(f"    {bucket:>8}: {count:>7,}  {bar}")

    # Step 6: Write CSV
    print(f"\n  Writing {os.path.basename(output_csv)}...")
    with open(output_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["word", "code_hex", "code_length_bits"])
        for word, _ in sorted_by_freq:
            if word in codes:
                code = codes[word]
                writer.writerow([word, bits_to_hex(code), len(code)])
    csv_size = os.path.getsize(output_csv)
    print(f"  CSV: {csv_size:,} bytes ({csv_size / 1024 / 1024:.1f} MB)")

    # Step 7: Serialize tree and lookup tables to .bin
    # Separate word-only codes from control codes for the .bin
    word_codes = {k: v for k, v in codes.items() if not k.startswith("\x00")}
    control_codes = {k: v for k, v in codes.items() if k.startswith("\x00")}
    print(f"  Writing {os.path.basename(output_bin)}...")
    print(f"  Word codes: {len(word_codes):,}, Control codes: {len(control_codes)}")
    bin_data = {
        "word_to_code": word_codes,
        "code_to_word": {v: k for k, v in word_codes.items()},
        "control_codes": control_codes,  # ESC, NUM, PUNCT, NOSPACE, EOF
        "all_codes": codes,              # word + control codes combined
        "total_words": len(word_codes),
        "max_code_length": max_len,
    }
    with open(output_bin, "wb") as f:
        pickle.dump(bin_data, f, protocol=pickle.HIGHEST_PROTOCOL)
    bin_size = os.path.getsize(output_bin)
    print(f"  BIN: {bin_size:,} bytes ({bin_size / 1024 / 1024:.1f} MB)")

    # Step 8: Round-trip validation (every word)
    print(f"\n  Round-trip validation (all {len(codes):,} words)...")
    t_rt = time.perf_counter()
    rt_pass = 0
    rt_fail = 0
    # Use all_codes reverse map for complete round-trip (words + controls)
    all_code_to_word = {v: k for k, v in codes.items()}
    for word, code in codes.items():
        decoded = all_code_to_word.get(code)
        if decoded == word:
            rt_pass += 1
        else:
            rt_fail += 1
            if rt_fail <= 5:
                print(f"    FAIL: '{word}' → code → '{decoded}'")
    rt_ms = (time.perf_counter() - t_rt) * 1000
    print(f"  Round-trip: {rt_pass:,} pass, {rt_fail:,} fail ({rt_ms:.0f} ms)")
    print(f"  Result: {'100% PASS ✓' if rt_fail == 0 else 'FAILURES ✗'}")

    total_ms = (time.perf_counter() - t_start) * 1000
    print(f"\n  {'─' * 74}")
    print(f"  Total build time: {total_ms / 1000:.1f} s")
    print(f"  Files: {output_csv}")
    print(f"         {output_bin}")
    print(f"{'=' * 78}\n")

    if rt_fail > 0 or not is_prefix_free:
        sys.exit(1)


if __name__ == "__main__":
    main()
