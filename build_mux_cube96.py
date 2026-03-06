#!/usr/bin/env python3
"""
build_mux_cube96.py — Build MUX Cube 96³ Codebook from Kaggle Unigram Frequency Data
======================================================================================
CyberMesh v7.1 — Mindtech / Liberty Mesh

Reads english_unigram_freq.csv, assigns each word an (x,y,z) coordinate in the
96³ cube via SHA-256 hash + collision probe (Z→Y→X), outputs:
  - codebooks/mux_cube96.bin  (pickle: word_to_xyz, xyz_to_word, metadata)
  - codebooks/mux_cube96.csv  (human-readable: word, x, y, z, frequency_rank)

Bit layout (FROZEN):
  Byte 0: [F0 | x6..x0]   F0 = namespace (0=static, 1=meshlex)
  Byte 1: [F1 | y6..y0]   F1 = hyperedge (reserved, always 0)
  Byte 2: [F2 | z6..z0]   F2 = capitalized (0=lower, 1=cap)

Coordinates 0-95 are valid word addresses.
Coordinates 96-127 are permanently reserved for control codes.
ESC sentinel: 0xFF 0xFF 0xFF (x=127, y=127, z=127, all flags=1)

Shared coordinate space: static and MeshLex words occupy the SAME cube.
Total capacity: 884,736 cells (96³). No coordinate reuse across namespaces.

Author: Mark Snow, Jr. — Mindtech / CyberMesh / Liberty Mesh
Date:   March 2026
"""

import csv
import hashlib
import logging
import os
import pickle
import sys
import time
from collections import Counter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("build_cube96")

# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

CUBE_SIZE = 96
MAX_COORD = CUBE_SIZE - 1  # 95
TOTAL_CAPACITY = CUBE_SIZE ** 3  # 884,736

# ESC sentinel — outside the 0-95 valid range on all axes
ESC_X = 127
ESC_Y = 127
ESC_Z = 127


# ═══════════════════════════════════════════════════════════════════════════
# PACK / UNPACK (FROZEN — copy verbatim from spec)
# ═══════════════════════════════════════════════════════════════════════════

def pack(x, y, z, f_namespace=0, f_hyperedge=0, f_capitalized=0):
    """Pack (x,y,z) + 3 flags into 3 bytes. One flag per byte high bit."""
    return bytes([(f_namespace << 7) | x,
                  (f_hyperedge << 7) | y,
                  (f_capitalized << 7) | z])


def unpack(data, offset=0):
    """Unpack 3 bytes into (x,y,z) + 3 flags. Zero cross-byte operations."""
    b0, b1, b2 = data[offset], data[offset + 1], data[offset + 2]
    return {
        'x': b0 & 0x7F, 'y': b1 & 0x7F, 'z': b2 & 0x7F,
        'f_namespace': b0 >> 7, 'f_hyperedge': b1 >> 7, 'f_capitalized': b2 >> 7
    }


# ═══════════════════════════════════════════════════════════════════════════
# HASH + PROBE
# ═══════════════════════════════════════════════════════════════════════════

def word_to_hash_coords(word):
    """Deterministic initial coordinates via SHA-256 hash."""
    h = hashlib.sha256(word.encode('utf-8')).digest()
    return (h[0] % CUBE_SIZE, h[1] % CUBE_SIZE, h[2] % CUBE_SIZE)


def place_word(word, occupied, stats):
    """
    Place word in cube via SHA-256 hash + linear probe Z→Y→X.

    Args:
        word: lowercased word string
        occupied: dict of (x,y,z) → word (shared coordinate space)
        stats: dict for tracking collision counts

    Returns:
        (x, y, z) tuple — the assigned coordinates
    """
    x0, y0, z0 = word_to_hash_coords(word)
    x, y, z = x0, y0, z0

    z_attempts = 0
    y_attempts = 0

    while (x, y, z) in occupied:
        stats['collisions'] += 1
        z = (z + 1) % CUBE_SIZE
        z_attempts += 1
        if z_attempts >= CUBE_SIZE:
            z_attempts = 0
            y = (y + 1) % CUBE_SIZE
            y_attempts += 1
            if y_attempts >= CUBE_SIZE:
                y_attempts = 0
                x = (x + 1) % CUBE_SIZE

    # Track max probe depth
    distance = 0
    if (x, y, z) != (x0, y0, z0):
        # Approximate linear distance
        dz = (z - z0) % CUBE_SIZE
        dy = (y - y0) % CUBE_SIZE
        dx = (x - x0) % CUBE_SIZE
        distance = dx * CUBE_SIZE * CUBE_SIZE + dy * CUBE_SIZE + dz
    stats['max_probe'] = max(stats.get('max_probe', 0), distance)

    return (x, y, z)


# ═══════════════════════════════════════════════════════════════════════════
# LOAD VOCABULARY
# ═══════════════════════════════════════════════════════════════════════════

def load_vocab(csv_path, max_words=None):
    """
    Load vocabulary from english_unigram_freq.csv, sorted by frequency descending.

    Returns:
        List of (word, count) tuples, sorted by count descending.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Vocabulary file not found: {csv_path}")

    words = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            word = row["word"].strip().lower()
            try:
                count = int(row["count"])
            except (ValueError, TypeError):
                continue
            if count > 0 and word and len(word) <= 31:
                words.append((word, count))

    # Sort by frequency descending
    words.sort(key=lambda x: x[1], reverse=True)

    if max_words:
        words = words[:max_words]

    logger.info("Loaded %d words from %s", len(words), csv_path)
    return words


# ═══════════════════════════════════════════════════════════════════════════
# BUILD CODEBOOK
# ═══════════════════════════════════════════════════════════════════════════

def build_codebook(vocab):
    """
    Build the cube96 codebook by placing all words via hash + probe.

    Args:
        vocab: list of (word, count) tuples, frequency-sorted

    Returns:
        (word_to_xyz, xyz_to_word, stats)
    """
    word_to_xyz = {}
    xyz_to_word = {}
    stats = {
        'collisions': 0,
        'max_probe': 0,
        'words_with_collision': 0,
    }

    t0 = time.perf_counter()

    for rank, (word, count) in enumerate(vocab):
        if word in word_to_xyz:
            continue  # skip duplicates

        origin = word_to_hash_coords(word)
        xyz = place_word(word, xyz_to_word, stats)

        if xyz != origin:
            stats['words_with_collision'] += 1

        word_to_xyz[word] = xyz
        xyz_to_word[xyz] = word

        # Progress logging
        if (rank + 1) % 50000 == 0:
            elapsed = time.perf_counter() - t0
            logger.info("  Placed %d/%d words (%.1f s, %d collisions so far)",
                        rank + 1, len(vocab), elapsed, stats['collisions'])

    build_time = time.perf_counter() - t0
    stats['build_time_s'] = round(build_time, 2)
    stats['total_words'] = len(word_to_xyz)

    return word_to_xyz, xyz_to_word, stats


# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

def validate_roundtrip(word_to_xyz, xyz_to_word):
    """Validate every word roundtrips through pack → unpack → lookup."""
    errors = 0
    tested = 0

    for word, (x, y, z) in word_to_xyz.items():
        # Pack with F0=0 (static), F1=0 (reserved), F2=0 (lowercase)
        packed = pack(x, y, z, f_namespace=0, f_hyperedge=0, f_capitalized=0)
        info = unpack(packed)

        # Verify coordinates survive pack/unpack
        if info['x'] != x or info['y'] != y or info['z'] != z:
            logger.error("ROUNDTRIP FAIL (coords): %s (%d,%d,%d) → (%d,%d,%d)",
                         word, x, y, z, info['x'], info['y'], info['z'])
            errors += 1
            continue

        # Verify flags
        if info['f_namespace'] != 0 or info['f_hyperedge'] != 0 or info['f_capitalized'] != 0:
            logger.error("ROUNDTRIP FAIL (flags): %s — flags should be 0,0,0 got %d,%d,%d",
                         word, info['f_namespace'], info['f_hyperedge'], info['f_capitalized'])
            errors += 1
            continue

        # Verify reverse lookup
        recovered = xyz_to_word.get((info['x'], info['y'], info['z']))
        if recovered != word:
            logger.error("ROUNDTRIP FAIL (lookup): %s → (%d,%d,%d) → %s",
                         word, x, y, z, recovered)
            errors += 1
            continue

        tested += 1

    # Also test capitalization flag
    sample_word = list(word_to_xyz.keys())[0]
    sx, sy, sz = word_to_xyz[sample_word]
    packed_cap = pack(sx, sy, sz, f_namespace=0, f_hyperedge=0, f_capitalized=1)
    info_cap = unpack(packed_cap)
    if info_cap['f_capitalized'] != 1 or info_cap['x'] != sx:
        logger.error("CAPITALIZATION FLAG FAIL: %s", sample_word)
        errors += 1

    # Test ESC sentinel is outside valid range
    esc_packed = bytes([0xFF, 0xFF, 0xFF])
    esc_info = unpack(esc_packed)
    if esc_info['x'] <= MAX_COORD or esc_info['y'] <= MAX_COORD or esc_info['z'] <= MAX_COORD:
        logger.error("ESC SENTINEL FAIL: coords (%d,%d,%d) should all be > %d",
                     esc_info['x'], esc_info['y'], esc_info['z'], MAX_COORD)
        errors += 1

    # Verify ESC is not a valid word
    esc_xyz = (esc_info['x'], esc_info['y'], esc_info['z'])
    if esc_xyz in xyz_to_word:
        logger.error("ESC SENTINEL COLLISION: (127,127,127) maps to word '%s'",
                     xyz_to_word[esc_xyz])
        errors += 1

    return tested, errors


def compute_spatial_stats(word_to_xyz):
    """Compute spatial distribution across the cube."""
    x_dist = Counter()
    y_dist = Counter()
    z_dist = Counter()

    for x, y, z in word_to_xyz.values():
        x_dist[x] += 1
        y_dist[y] += 1
        z_dist[z] += 1

    def axis_summary(dist, name):
        vals = list(dist.values())
        if not vals:
            return f"  {name}: empty"
        avg = sum(vals) / len(vals)
        mn = min(vals)
        mx = max(vals)
        return f"  {name}: min={mn} max={mx} avg={avg:.1f} spread={mx-mn}"

    return (axis_summary(x_dist, "X-axis"),
            axis_summary(y_dist, "Y-axis"),
            axis_summary(z_dist, "Z-axis"))


# ═══════════════════════════════════════════════════════════════════════════
# OUTPUT
# ═══════════════════════════════════════════════════════════════════════════

def save_bin(word_to_xyz, xyz_to_word, stats, out_path):
    """Save binary codebook (.bin) via pickle."""
    data = {
        'word_to_xyz': word_to_xyz,
        'xyz_to_word': xyz_to_word,
        'cube_size': CUBE_SIZE,
        'total_words': len(word_to_xyz),
        'spare_slots': TOTAL_CAPACITY - len(word_to_xyz),
        'build_stats': stats,
    }
    with open(out_path, 'wb') as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    logger.info("Saved %s (%.1f MB)", out_path, size_mb)


def save_csv(word_to_xyz, vocab_order, out_path):
    """Save human-readable CSV codebook."""
    with open(out_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['word', 'x', 'y', 'z', 'frequency_rank'])
        for rank, word in enumerate(vocab_order):
            if word in word_to_xyz:
                x, y, z = word_to_xyz[word]
                writer.writerow([word, x, y, z, rank + 1])
    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    logger.info("Saved %s (%.1f MB)", out_path, size_mb)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print()
    print("=" * 78)
    print("  BUILD MUX CUBE 96³ — CyberMesh / Liberty Mesh")
    print("  3D Content-Addressable Memory Codebook Builder")
    print("=" * 78)

    base = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base, "english_unigram_freq.csv")
    out_dir = os.path.join(base, "codebooks")
    os.makedirs(out_dir, exist_ok=True)

    bin_path = os.path.join(out_dir, "mux_cube96.bin")
    csv_out_path = os.path.join(out_dir, "mux_cube96.csv")

    # ── Load vocabulary ──
    print()
    vocab = load_vocab(csv_path)
    print(f"  Vocabulary: {len(vocab):,} words")
    print(f"  Cube: {CUBE_SIZE}³ = {TOTAL_CAPACITY:,} cells")
    print(f"  Load factor: {len(vocab) / TOTAL_CAPACITY:.1%}")
    print()

    # ── Build codebook ──
    print("  Building codebook (SHA-256 hash + Z→Y→X linear probe)...")
    word_to_xyz, xyz_to_word, stats = build_codebook(vocab)

    print()
    print(f"  ── Build Results ──")
    print(f"  Words placed:        {stats['total_words']:,}")
    print(f"  Total collisions:    {stats['collisions']:,}")
    print(f"  Words with collision:{stats['words_with_collision']:,} "
          f"({stats['words_with_collision'] / stats['total_words'] * 100:.1f}%)")
    print(f"  Max probe distance:  {stats['max_probe']:,}")
    print(f"  Build time:          {stats['build_time_s']:.2f} s")
    print(f"  Utilization:         {stats['total_words'] / TOTAL_CAPACITY:.1%}")
    print(f"  Spare slots:         {TOTAL_CAPACITY - stats['total_words']:,}")

    # ── Spatial distribution ──
    print()
    print(f"  ── Spatial Distribution ──")
    for line in compute_spatial_stats(word_to_xyz):
        print(f"  {line}")

    # ── Validation ──
    print()
    print("  ── Roundtrip Validation ──")
    tested, errors = validate_roundtrip(word_to_xyz, xyz_to_word)
    print(f"  Tested: {tested:,}  Errors: {errors}")
    if errors == 0:
        print(f"  ✓ ALL {tested:,} WORDS ROUNDTRIP CORRECTLY")
    else:
        print(f"  ✗ {errors} ROUNDTRIP FAILURES — DO NOT USE THIS CODEBOOK")
        sys.exit(1)

    # ── Save outputs ──
    print()
    vocab_order = [w for w, _ in vocab]
    save_bin(word_to_xyz, xyz_to_word, stats, bin_path)
    save_csv(word_to_xyz, vocab_order, csv_out_path)

    # ── Summary ──
    print()
    print("=" * 78)
    print(f"  ✓ MUX CUBE 96³ CODEBOOK BUILT SUCCESSFULLY")
    print(f"  Words:    {stats['total_words']:,} / {TOTAL_CAPACITY:,} ({stats['total_words'] / TOTAL_CAPACITY:.1%})")
    print(f"  Files:    {bin_path}")
    print(f"            {csv_out_path}")
    print(f"  Collisions: {stats['collisions']:,} total, {stats['words_with_collision']:,} words affected")
    print("=" * 78)
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
