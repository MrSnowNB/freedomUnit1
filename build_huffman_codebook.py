#!/usr/bin/env python3
"""
build_huffman_codebook.py — Generate huffman_codebook_4k.csv from mux_codebook.csv
====================================================================================
Reads the shared 4,096-word vocabulary from mux_codebook.csv, builds a Huffman tree
using each word's frequency as weight, and outputs huffman_codebook_4k.csv.

This ensures BOTH codecs use the identical vocabulary for a fair A/B comparison
in Experiment C. The Huffman tree structure is determined by frequency — high-
frequency words get shorter codes.

Output: huffman_codebook_4k.csv with columns: word, huffman_code, bits, frequency

Author: Mark Snow, Jr. — Mindtech / CyberMesh / Liberty Mesh
Date:   March 2026
"""

import csv
import heapq
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass(order=True)
class HuffmanNode:
    freq: int
    char: Optional[str] = field(default=None, compare=False)
    left: Optional["HuffmanNode"] = field(default=None, compare=False)
    right: Optional["HuffmanNode"] = field(default=None, compare=False)


def build_huffman_tree(freq_table: dict[str, int]) -> HuffmanNode:
    heap = [HuffmanNode(freq=f, char=w) for w, f in freq_table.items()]
    heapq.heapify(heap)
    while len(heap) > 1:
        lo = heapq.heappop(heap)
        hi = heapq.heappop(heap)
        heapq.heappush(heap, HuffmanNode(freq=lo.freq + hi.freq, left=lo, right=hi))
    return heap[0]


def build_codebook(root: HuffmanNode) -> dict[str, str]:
    codes: dict[str, str] = {}
    def walk(node, prefix=""):
        if node.char is not None:
            codes[node.char] = prefix or "0"
            return
        if node.left:  walk(node.left,  prefix + "0")
        if node.right: walk(node.right, prefix + "1")
    walk(root)
    return codes


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mux_csv = os.path.join(script_dir, "mux_codebook.csv")
    output = os.path.join(script_dir, "huffman_codebook_4k.csv")

    print("=" * 60)
    print("  Huffman 4K Codebook Builder")
    print("  Source: mux_codebook.csv (shared 4,096-word vocabulary)")
    print("=" * 60)

    if not os.path.exists(mux_csv):
        print(f"  ERROR: {mux_csv} not found")
        return

    # Step 1: Load words and frequencies from mux_codebook.csv
    freq_table = {}
    with open(mux_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            word = row["word"]
            if word == "<ESC>":
                continue  # ESC is handled separately in the codec
            freq = int(row["frequency"])
            freq_table[word] = freq

    print(f"  Loaded {len(freq_table)} words from mux_codebook.csv")

    # Step 2: Build Huffman tree
    tree = build_huffman_tree(freq_table)
    codes = build_codebook(tree)
    print(f"  Built Huffman tree: {len(codes)} codes")

    # Step 3: Sort by frequency (descending) for readability, same order as mux_codebook
    sorted_words = sorted(codes.items(), key=lambda x: freq_table.get(x[0], 0), reverse=True)

    # Step 4: Write CSV
    with open(output, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["word", "huffman_code", "bits", "frequency"])
        for word, code in sorted_words:
            writer.writerow([word, code, len(code), freq_table[word]])

    # Stats
    bit_lengths = [len(c) for _, c in sorted_words]
    min_bits = min(bit_lengths)
    max_bits = max(bit_lengths)
    avg_bits = sum(bit_lengths) / len(bit_lengths)

    print(f"\n  Output: {output}")
    print(f"  Entries: {len(sorted_words)}")
    print(f"  Code lengths: {min_bits}-{max_bits} bits (avg {avg_bits:.1f})")
    print(f"  Shortest code: '{sorted_words[0][0]}' = {sorted_words[0][1]} ({len(sorted_words[0][1])} bits)")
    print(f"  Longest code: bit_length={max_bits}")

    # Show top 10
    print(f"\n  Top 10 shortest codes:")
    by_length = sorted(sorted_words, key=lambda x: (len(x[1]), x[0]))
    for w, c in by_length[:10]:
        print(f"    {w:<16} {len(c):>2} bits  code={c}")

    print("=" * 60)


if __name__ == "__main__":
    main()
