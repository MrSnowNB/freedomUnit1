#!/usr/bin/env python3
"""
bug12_utf8_fix_v2.py — Bug 12: Full Diagnosis + Fix (all 3 paths)
===================================================================
CyberMesh v7.1 — Mindtech / Liberty Mesh

v1 only patched _encode_raw/_decode_raw (the ESC path).
But most Unicode tokens go through PUNCT or NUMBER, not ESC.

THE REAL BUG — 3 broken code paths in huffman_codec.py:

  Path 1 — PUNCT (emoji, degree, em-dash):
    Tokenizer regex `([^\s])` matches emoji/symbols as single punct chars.
    encode(): `format(ord(tok_val) & 0x7F, "07b")` — 7-bit mask kills Unicode
    decode(): `chr(int(bits[pos:pos+7], 2))` — can't reconstruct > 127

  Path 2 — ESC/RAW (out-of-vocabulary words):
    encode(): `ord(c) & 0x7F` per char — same 7-bit mask
    decode(): reads 7-bit chars — can't do multi-byte UTF-8

  Path 3 — NUMBER (leading zeros like ZIP codes "08648"):
    encode(): `int("08648")` → 8648 — leading zero lost
    decode(): `str(8648)` → "8648" — never recovers

Fix strategy: route non-ASCII punct and leading-zero numbers through
a fixed ESC/raw path that uses proper UTF-8 byte encoding.

Drop into freedomUnit1/ root and run:
    python bug12_utf8_fix_v2.py

Author: Mark Snow, Jr. — Mindtech / CyberMesh / Liberty Mesh
Date:   March 2026
"""

import os
import re
import sys
import time
import types

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from huffman_codec import MeshHuffmanCodec

# Control token constants (must match huffman_codec.py)
_ESC     = "\x00ESC"
_NUM     = "\x00NUM"
_PUNCT   = "\x00PUN"
_NOSPACE = "\x00NSP"
_EOF     = "\x00EOF"


# ═══════════════════════════════════════════════════════════════════════════
# TEST VECTORS
# ═══════════════════════════════════════════════════════════════════════════

BUG12_VECTORS = [
    # Path 1: PUNCT — emoji/symbols routed through ord() & 0x7F
    ("emoji_siren",       "🚨",              "punct_path"),
    ("emoji_warning",     "⚠️",              "punct_path"),
    ("emoji_check",       "✅",              "punct_path"),
    ("emoji_chart",       "📊",              "punct_path"),
    ("emoji_green",       "🟢",              "punct_path"),
    ("degree_symbol",     "40.2171°N",       "punct_path"),
    ("em_dash",           "—",               "punct_path"),
    ("temp_reading",      "41°F",            "punct_path"),

    # Path 2: ESC/RAW — OOV words with Unicode
    ("esc_unicode_word",  "résumé",          "esc_path"),
    ("esc_accented",      "café",            "esc_path"),

    # Path 3: NUMBER — leading zeros
    ("zip_code",          "08648",           "number_path"),
    ("mil_time",          "0800",            "number_path"),
    ("node_id",           "08",              "number_path"),

    # ASCII baselines (should always pass)
    ("ascii_word",        "Trenton",         "ascii_ok"),
    ("ascii_punct",       "hello, world!",   "ascii_ok"),
    ("ascii_number",      "15",              "ascii_ok"),

    # Full Experiment H sentences
    ("sent_gps",
     "🚨 Flood warning active near Trenton NJ 40.2171°N 74.7429°W",
     "sentence"),
    ("sent_alert",
     "⚠️ ALERT ⚠️ Sensor grid sectors A3 B7 C12 showing CRITICAL",
     "sentence"),
    ("sent_status",
     "📊 MESHLEX SYNC — Trenton ✅ Lawrence Township ✅ codec stable 🟢",
     "sentence"),
    ("sent_weather",
     "temp 41°F barometric 29.12 inHg — tornado watch issued",
     "sentence"),
    ("sent_zip",
     "sensors at Lawrence Township 08648 are offline",
     "sentence"),
]


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 1: Diagnose which path each failure goes through
# ═══════════════════════════════════════════════════════════════════════════

def diagnose_token_path(codec, text):
    """Show which encode path each token takes."""
    tokens = codec._tokenize(text)
    paths = []
    for tok_type, tok_val, space_before in tokens:
        if tok_type == "word":
            wl = tok_val.lower()
            if wl in codec.encode_table:
                paths.append(("WORD", tok_val, "codebook hit"))
            else:
                paths.append(("ESC", tok_val, "OOV → _encode_raw"))
        elif tok_type == "number":
            if "." in tok_val:
                paths.append(("NUM", tok_val, f"float → ESC/raw"))
            else:
                paths.append(("NUM", tok_val, f"int({tok_val})={int(tok_val)}"))
        elif tok_type == "punct":
            cp = ord(tok_val)
            if cp > 127:
                paths.append(("PUNCT⚠", tok_val,
                              f"U+{cp:04X} → & 0x7F = {cp & 0x7F:#x} MANGLED"))
            else:
                paths.append(("PUNCT", tok_val, f"U+{cp:04X} ok"))
    return paths


def run_phase1():
    print()
    print("=" * 80)
    print("  PHASE 1: DIAGNOSE — Which code path mangles each token?")
    print("=" * 80)

    codec = MeshHuffmanCodec(codebook_size="333k")

    # Show path analysis for key failing tokens
    diag_samples = [
        "🚨", "⚠️", "°", "—", "08648",
        "🚨 Flood warning near Trenton NJ 40.2171°N",
    ]

    for sample in diag_samples:
        print(f"\n  Input: {sample!r}")
        paths = diagnose_token_path(codec, sample)
        for path_type, tok, detail in paths:
            marker = " ← BUG" if "MANGLED" in detail or "int(" in detail else ""
            print(f"    {path_type:<8} {tok!r:<16} {detail}{marker}")

    # Roundtrip test
    print(f"\n  {'─' * 76}")
    print(f"  Roundtrip failures by path:")
    path_fails = {"punct_path": 0, "esc_path": 0, "number_path": 0,
                  "ascii_ok": 0, "sentence": 0}
    total_fails = 0
    for label, test_str, category in BUG12_VECTORS:
        try:
            encoded = codec.encode(test_str)
            decoded = codec.decode(encoded)
            ok = (decoded == test_str)
        except:
            ok = False
        if not ok:
            path_fails[category] = path_fails.get(category, 0) + 1
            total_fails += 1

    for cat, count in path_fails.items():
        if count > 0:
            print(f"    {cat:<16} {count} failures")
    print(f"    {'TOTAL':<16} {total_fails} failures")


# ═══════════════════════════════════════════════════════════════════════════
# THE FIX — All 3 paths
# ═══════════════════════════════════════════════════════════════════════════

def _encode_raw_fixed(word: str) -> str:
    """FIX Path 2: UTF-8 bytes, 8-bit encoding, byte count."""
    raw = word.encode("utf-8")[:31]
    bits = format(len(raw), "05b")
    for byte in raw:
        bits += format(byte, "08b")
    return bits


def _decode_raw_fixed(bits: str, pos: int) -> tuple:
    """FIX Path 2: Read UTF-8 bytes, 8-bit, decode."""
    n = int(bits[pos:pos + 5], 2); pos += 5
    raw = bytearray()
    for _ in range(n):
        if pos + 8 > len(bits):
            break
        raw.append(int(bits[pos:pos + 8], 2)); pos += 8
    return raw.decode("utf-8", errors="replace"), pos


def make_fixed_encode(codec):
    """Build a fixed encode() that handles all 3 paths."""
    original_encode_table = codec.encode_table

    def encode_fixed(self, text: str) -> bytes:
        tokens = self._tokenize(text)
        bits = ""
        first = True

        for tok_type, tok_val, space_before in tokens:
            if not first:
                if not space_before:
                    bits += self.encode_table[_NOSPACE]
            first = False

            if tok_type == "word":
                wl = tok_val.lower()
                if wl in self.encode_table:
                    bits += self.encode_table[wl]
                    bits += self._encode_case(tok_val)
                else:
                    bits += self.encode_table[_ESC]
                    bits += self._encode_raw(tok_val)  # uses fixed version

            elif tok_type == "number":
                # FIX Path 3: leading-zero numbers go through ESC/raw
                if tok_val.startswith("0") and len(tok_val) > 1 and "." not in tok_val:
                    bits += self.encode_table[_ESC]
                    bits += self._encode_raw(tok_val)
                elif "." in tok_val:
                    bits += self.encode_table[_ESC]
                    bits += self._encode_raw(tok_val)
                else:
                    bits += self.encode_table[_NUM]
                    bits += self._encode_number(int(tok_val))

            elif tok_type == "punct":
                cp = ord(tok_val)
                if cp > 127:
                    # FIX Path 1: non-ASCII punct → ESC/raw (UTF-8 safe)
                    bits += self.encode_table[_ESC]
                    bits += self._encode_raw(tok_val)
                else:
                    # ASCII punct: original 7-bit path (still works fine)
                    bits += self.encode_table[_PUNCT]
                    bits += format(cp, "07b")

        bits += self.encode_table[_EOF]
        r = len(bits) % 8
        if r:
            bits += "0" * (8 - r)
        return int(bits, 2).to_bytes(len(bits) // 8, byteorder="big")

    return encode_fixed


def apply_fix(codec):
    """Apply all 3 fixes to a codec instance via monkey-patch."""
    # Fix Path 2: ESC/raw encoding
    MeshHuffmanCodec._encode_raw = staticmethod(_encode_raw_fixed)
    MeshHuffmanCodec._decode_raw = staticmethod(_decode_raw_fixed)

    # Fix Paths 1 & 3: replace encode() to reroute non-ASCII punct and
    # leading-zero numbers through the (now fixed) ESC/raw path
    fixed_encode = make_fixed_encode(codec)
    codec.encode = types.MethodType(fixed_encode, codec)

    # decode() needs no change — ESC tokens are decoded by _decode_raw
    # (now fixed), and we no longer emit non-ASCII PUNCT codes.


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 2: Apply fix, test individual tokens
# ═══════════════════════════════════════════════════════════════════════════

def run_phase2():
    print()
    print("=" * 80)
    print("  PHASE 2: FIX APPLIED — Test all vectors")
    print("=" * 80)
    print("  Path 1 fix: non-ASCII punct → ESC/raw (UTF-8)")
    print("  Path 2 fix: _encode_raw/_decode_raw → 8-bit UTF-8 bytes")
    print("  Path 3 fix: leading-zero numbers → ESC/raw (preserves zeros)")
    print()

    codec = MeshHuffmanCodec(codebook_size="333k")
    apply_fix(codec)

    results = []
    for label, test_str, category in BUG12_VECTORS:
        try:
            encoded = codec.encode(test_str)
            decoded = codec.decode(encoded)
            ok = (decoded == test_str)
            enc_bytes = len(encoded)
            raw_bytes = len(test_str.encode("utf-8"))
        except Exception as e:
            decoded = f"ERROR: {e}"
            ok = False
            enc_bytes = 0
            raw_bytes = len(test_str.encode("utf-8"))

        results.append({
            "label": label, "input": test_str, "output": decoded,
            "category": category, "ok": ok,
            "enc_bytes": enc_bytes, "raw_bytes": raw_bytes,
        })

        status = "✓ PASS" if ok else "✗ FAIL"
        print(f"  [{status}] {label:<20} {category:<14}", end="")
        if ok:
            ratio = raw_bytes / enc_bytes if enc_bytes else 0
            print(f"  {raw_bytes}B → {enc_bytes}B  ratio={ratio:.2f}:1")
        else:
            print(f"  IN: {test_str[:35]!r}")
            print(f"  {'':>45}OUT: {decoded[:35]!r}")

    passed = sum(1 for r in results if r["ok"])
    failed = sum(1 for r in results if not r["ok"])
    print(f"\n  {'─' * 76}")
    print(f"  PHASE 2 RESULT: {passed} passed, {failed} failed out of {len(results)}")

    by_cat = {}
    for r in results:
        cat = r["category"]
        if cat not in by_cat:
            by_cat[cat] = {"pass": 0, "fail": 0}
        by_cat[cat]["pass" if r["ok"] else "fail"] += 1
    for cat, counts in by_cat.items():
        status = "✓ ALL PASS" if counts["fail"] == 0 else f"✗ {counts['fail']} FAIL"
        print(f"    {cat:<16} {status}")

    return results


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 3: Full Experiment H re-run with fix
# ═══════════════════════════════════════════════════════════════════════════

EXPERIMENT_H_MESSAGES = [
    "\U0001f6a8 Flood warning active near Trenton NJ 40.2171\u00b0N 74.7429\u00b0W \u2014 "
    "Route 1 bridge sensors show 15 feet and rising fast, dispatch EMS now",

    "Liberty-Node-04 reports sensors at Lawrence Township 08648 are offline \u2014 "
    "contact dispatch at 609-555-0147 by 1430 hours for backup",

    "Water levels at New Brunswick gauge NB-07 read 12.4 feet at 0800 \u2014 "
    "Raritan River overflow expected to hit Highland Park by 1200",

    "\u26a0\ufe0f ALERT \u26a0\ufe0f Sensor grid sectors A3 B7 C12 showing CRITICAL \u2014 "
    "humidity 98% temp 41\u00b0F barometric 29.12 inHg #FloodWatch #LibertyMesh",

    "Evacuate Trenton Water Works facility immediately \u2014 contamination detected "
    "at pump station PS-14 on Calhoun Street, notify NJDEP and Mercer County OEM",

    "Trenton fire dept responding to Lawrence Township Route 1 bridge \u2014 "
    "New Brunswick units staging at Highland Park, Raritan River at 14 feet",

    "Node KD2ZYX-7 at 40.4862\u00b0N 74.4518\u00b0W reports wind 45 mph gusting 62 \u2014 "
    "barometric pressure dropping 28.88 inHg, tornado watch issued",

    "Forward to ops@libertymesh.net \u2014 sitrep: 7/10 nodes online, "
    "3 nodes dark since 0600, mesh coverage at 73%, "
    "see https://status.libertymesh.net/live for map",

    "Trenton police confirm Route 1 bridge CLOSED \u2014 detour via Route 206 "
    "through Lawrence Township to Princeton, ETA 45 min, "
    "notify New Brunswick and Highland Park staging areas",

    "\U0001f4ca MESHLEX SYNC: 47 dynamic entries across 5 nodes \u2014 Trenton \u2705 "
    "Lawrence Township \u2705 New Brunswick \u2705 Highland Park \u2705 "
    "Princeton \u2705 Raritan River \u2705 Route 1 \u2705 codec stable \U0001f7e2",
]


def run_phase3():
    print()
    print("=" * 80)
    print("  PHASE 3: EXPERIMENT H RE-RUN — Fixed Huffman on all 10 messages")
    print("=" * 80)
    print()

    codec = MeshHuffmanCodec(codebook_size="333k")
    apply_fix(codec)

    total_raw = 0
    total_enc = 0
    rt_ok = 0

    # Also track original (broken) results for comparison
    orig_enc_totals = [99, 101, 72, 148, 69, 60, 128, 201, 80, 108]  # from Exp H

    for i, msg in enumerate(EXPERIMENT_H_MESSAGES):
        raw_bytes = len(msg.encode("utf-8"))
        try:
            encoded = codec.encode(msg)
            decoded = codec.decode(encoded)
            enc_bytes = len(encoded)
            ok = (decoded == msg)
        except Exception as e:
            decoded = f"ERROR: {e}"
            enc_bytes = 0
            ok = False

        total_raw += raw_bytes
        total_enc += enc_bytes
        if ok:
            rt_ok += 1

        ratio = raw_bytes / enc_bytes if enc_bytes else 0
        status = "\u2713" if ok else "\u2717"
        trunc = msg if len(msg) <= 65 else msg[:62] + "..."
        orig = orig_enc_totals[i] if i < len(orig_enc_totals) else 0
        delta = enc_bytes - orig
        delta_str = f"({delta:+d}B vs broken)" if orig else ""

        print(f"  [{status}] Msg {i+1:>2}  {raw_bytes:>3}B \u2192 {enc_bytes:>3}B  "
              f"ratio={ratio:.2f}:1  {delta_str}")
        print(f"           {trunc}")
        if not ok:
            print(f"           \u2717 ROUNDTRIP FAIL")
            print(f"           GOT: {decoded[:72]}")

    agg_ratio = total_raw / total_enc if total_enc else 0
    HR = "\u2500" * 76
    print(f"\n  {HR}")
    print(f"  PHASE 3 RESULT: {rt_ok}/10 roundtrip")
    print(f"  Aggregate ratio: {agg_ratio:.3f}:1")
    print(f"  Total: {total_raw}B \u2192 {total_enc}B")

    print(f"\n  BEFORE vs AFTER (Huffman 333K Strict on Experiment H messages)")
    print(f"  {'Metric':<30} {'BEFORE (Bug 12)':>16} {'AFTER (Fixed)':>16}")
    HR30 = "\u2500" * 30; HR16 = "\u2500" * 16
    print(f"  {HR30} {HR16} {HR16}")
    print(f"  {'Roundtrip':<30} {'0/10':>16} {f'{rt_ok}/10':>16}")
    print(f"  {'Aggregate ratio':<30} {'1.391:1':>16} {f'{agg_ratio:.3f}:1':>16}")
    print(f"  {'Total encoded':<30} {'1066B':>16} {f'{total_enc}B':>16}")

    return rt_ok, agg_ratio, total_enc


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 4: Code diff for huffman_codec.py
# ═══════════════════════════════════════════════════════════════════════════

def print_diff():
    print()
    print("=" * 80)
    print("  PHASE 4: PATCH — 3 changes to huffman_codec.py")
    print("=" * 80)
    print("""
  ── CHANGE 1: _encode_raw (staticmethod) ────────────────────────────────

    @staticmethod
    def _encode_raw(word: str) -> str:
        raw = word.encode("utf-8")[:31]       # ← bytes not chars
        bits = format(len(raw), "05b")         # ← byte count
        for byte in raw:
            bits += format(byte, "08b")         # ← 8-bit not 7-bit
        return bits

  ── CHANGE 2: _decode_raw (staticmethod) ────────────────────────────────

    @staticmethod
    def _decode_raw(bits: str, pos: int) -> tuple[str, int]:
        n = int(bits[pos:pos + 5], 2); pos += 5
        raw = bytearray()
        for _ in range(n):
            if pos + 8 > len(bits):
                break
            raw.append(int(bits[pos:pos + 8], 2))  # ← 8-bit
            pos += 8
        return raw.decode("utf-8", errors="replace"), pos

  ── CHANGE 3: encode() method — two blocks inside the token loop ───────

    In the `elif tok_type == "number":` block, REPLACE:

        elif tok_type == "number":
            if '.' in tok_val:
                bits += self.encode_table[_ESC]
                bits += self._encode_raw(tok_val)
            else:
                bits += self.encode_table[_NUM]
                bits += self._encode_number(int(tok_val))

    WITH:

        elif tok_type == "number":
            if '.' in tok_val:
                bits += self.encode_table[_ESC]
                bits += self._encode_raw(tok_val)
            elif tok_val.startswith("0") and len(tok_val) > 1:
                # Leading-zero numbers (ZIP, mil time) → raw to preserve
                bits += self.encode_table[_ESC]
                bits += self._encode_raw(tok_val)
            else:
                bits += self.encode_table[_NUM]
                bits += self._encode_number(int(tok_val))

    In the `elif tok_type == "punct":` block, REPLACE:

        elif tok_type == "punct":
            bits += self.encode_table[_PUNCT]
            bits += format(ord(tok_val) & 0x7F, "07b")

    WITH:

        elif tok_type == "punct":
            if ord(tok_val) > 127:
                # Non-ASCII punct (emoji, °, —) → ESC/raw for UTF-8 safety
                bits += self.encode_table[_ESC]
                bits += self._encode_raw(tok_val)
            else:
                bits += self.encode_table[_PUNCT]
                bits += format(ord(tok_val), "07b")
  """)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print()
    print("=" * 80)
    print("  Bug 12 v2 — Full 3-Path Fix: PUNCT + ESC/RAW + NUMBER")
    print("  CyberMesh v7.1 — Single-machine codec test")
    print("=" * 80)

    run_phase1()
    results = run_phase2()
    rt_ok, ratio, total_enc = run_phase3()
    print_diff()

    # Verdict
    p2_fail = sum(1 for r in results if not r["ok"])
    print("=" * 80)
    print("  VERDICT")
    print("=" * 80)
    print(f"  Phase 1 (diagnose):     3 broken paths identified")
    print(f"  Phase 2 (token fix):    {p2_fail} failures remaining")
    print(f"  Phase 3 (Exp H msgs):   {rt_ok}/10 roundtrip, {ratio:.3f}:1")
    if p2_fail == 0 and rt_ok == 10:
        print(f"\n  \u2605 Bug 12 FULLY FIXED — all 3 paths verified")
        print(f"    Apply the 3 changes from Phase 4 to huffman_codec.py")
    elif p2_fail == 0:
        print(f"\n  \u25c9 Token fix works, {10-rt_ok} sentence(s) have secondary issues")
    else:
        print(f"\n  \u2717 {p2_fail} token failures remain — investigate")
    print("=" * 80)


if __name__ == "__main__":
    main()
