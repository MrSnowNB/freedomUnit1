#!/usr/bin/env python3
"""
experiment_h_meshlex.py — Experiment H: MeshLex Stress Test
============================================================
CyberMesh v7.1 — Mindtech / Liberty Mesh

Drop this file into the freedomUnit1/ project root and run:
    python experiment_h_meshlex.py

No radio, no LLM, no config.yaml needed. Uses scripted inputs
to eliminate randomness and isolate codec behavior.

Run Matrix (4 runs):
  1. huffman-333k-strict   — Baseline: best known compression
  2. mux-333k-strict       — MUX without MeshLex (current behavior)
  3. mux-333k-meshlex      — MUX + dynamic codebook, cold start
  4. mux-333k-meshlex-warm — Same script, MeshLex pre-warmed from Run 3

The crossover prediction: MUX+MeshLex should approach or beat Huffman
by message 5-7 as proper nouns settle into 2-byte grid slots.

Author: Mark Snow, Jr. — Mindtech / CyberMesh / Liberty Mesh
Date:   March 2026
"""

import copy
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Optional

# ── Ensure project root is on path ──
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from huffman_codec import MeshHuffmanCodec
from mux_codec import (
    MuxGridCodec,
    encode_grid_3byte,
    decode_grid_3byte,
    ESC_ROW_333K,
    ESC_COL_333K,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("experiment_h")


# ═══════════════════════════════════════════════════════════════════════════
# SCRIPTED MESSAGES — 10 messages, avg ~136 chars, 46+ edge-case categories
# ═══════════════════════════════════════════════════════════════════════════

SCRIPTED_MESSAGES = [
    # Msg 1: GPS coords, proper nouns, highway, emoji
    "🚨 Flood warning active near Trenton NJ 40.2171°N 74.7429°W — "
    "Route 1 bridge sensors show 15 feet and rising fast, dispatch EMS now",

    # Msg 2: Station IDs, phone numbers, ZIP codes, military time
    "Liberty-Node-04 reports sensors at Lawrence Township 08648 are offline — "
    "contact dispatch at 609-555-0147 by 1430 hours for backup",

    # Msg 3: Multiple proper nouns, abbreviations, numbers
    "Water levels at New Brunswick gauge NB-07 read 12.4 feet at 0800 — "
    "Raritan River overflow expected to hit Highland Park by 1200",

    # Msg 4: Emoji clusters, status codes, hashtags
    "⚠️ ALERT ⚠️ Sensor grid sectors A3 B7 C12 showing CRITICAL — "
    "humidity 98% temp 41°F barometric 29.12 inHg #FloodWatch #LibertyMesh",

    # Msg 5: Mixed languages hint, special chars, long proper nouns
    "Evacuate Trenton Water Works facility immediately — "
    "contamination detected at pump station PS-14 on Calhoun Street, "
    "notify NJDEP and Mercer County OEM",

    # Msg 6: Repeated proper nouns (MeshLex should cache these)
    "Trenton fire dept responding to Lawrence Township Route 1 bridge — "
    "New Brunswick units staging at Highland Park, Raritan River at 14 feet",

    # Msg 7: Coordinates, callsigns, technical measurements
    "Node KD2ZYX-7 at 40.4862°N 74.4518°W reports wind 45 mph gusting 62 — "
    "barometric pressure dropping 28.88 inHg, tornado watch issued",

    # Msg 8: Email-style, URLs, mixed punctuation
    "Forward to ops@libertymesh.net — sitrep: 7/10 nodes online, "
    "3 nodes dark since 0600, mesh coverage at 73%, "
    "see https://status.libertymesh.net/live for map",

    # Msg 9: Heavy proper noun reuse + new ones
    "Trenton police confirm Route 1 bridge CLOSED — "
    "detour via Route 206 through Lawrence Township to Princeton, "
    "ETA 45 min, notify New Brunswick and Highland Park staging areas",

    # Msg 10: Final status with max edge cases
    "📊 MESHLEX SYNC: 47 dynamic entries across 5 nodes — "
    "Trenton ✅ Lawrence Township ✅ New Brunswick ✅ Highland Park ✅ "
    "Princeton ✅ Raritan River ✅ Route 1 ✅ codec stable 🟢",
]

# Pre-defined proper nouns / edge tokens for MeshLex seeding analysis
EXPECTED_DYNAMIC_TOKENS = [
    # NJ Proper nouns
    "trenton", "lawrence", "township", "princeton", "highland",
    # Compound fragments
    "brunswick",
    # Infrastructure
    "raritan", "calhoun",
    # Station IDs / Callsigns
    "liberty-node-04", "nb-07", "ps-14", "kd2zyx-7",
    # Emoji (will be ESC'd)
    "🚨", "⚠️", "✅", "📊", "🟢",
    # GPS fragments
    "40.2171°n", "74.7429°w", "40.4862°n", "74.4518°w",
    # Special tokens
    "#floodwatch", "#libertymesh",
    "ops@libertymesh.net", "https://status.libertymesh.net/live",
    # Measurements with units
    "29.12", "28.88", "12.4",
    # ZIP, phone
    "08648", "609-555-0147",
]


# ═══════════════════════════════════════════════════════════════════════════
# MESHLEX ENGINE — Dynamic codebook extension for MUX Grid
# ═══════════════════════════════════════════════════════════════════════════

# Reserved grid region for dynamic entries: rows 690-699 (7,000 slots)
MESHLEX_ROW_START = 690
MESHLEX_ROW_END   = 699  # inclusive
MESHLEX_COL_MAX   = 699  # grid is 700x700 (0-699)

# Control packet type for codebook updates
CB_UPD_MARKER = 0xCB  # 1 byte marker


@dataclass
class MeshLexEntry:
    """A single dynamic codebook entry."""
    word: str
    row: int
    col: int
    added_at_msg: int       # which message index triggered the add
    hit_count: int = 0      # how many times retrieved after initial add


@dataclass
class MeshLexStats:
    """Per-message statistics for MeshLex activity."""
    msg_index: int
    dynamic_adds: int = 0
    dynamic_hits: int = 0
    esc_remaining: int = 0   # ESC tokens that couldn't be cached (emoji etc)
    cb_upd_packets: int = 0  # CB_UPD broadcasts that would be emitted
    cb_upd_bytes: int = 0    # total bytes of CB_UPD overhead


class MeshLexCodec:
    """
    Wraps MuxGridCodec with dynamic codebook (MeshLex) capability.

    On encode:
      - If word is in base codebook → normal 3-byte encode
      - If word is in dynamic lexicon → 3-byte encode from learned slot
      - If word is unknown → ESC encode + auto-add to dynamic lexicon
        + emit CB_UPD packet for mesh broadcast

    On decode:
      - If grid address is in base codebook → normal decode
      - If grid address is in dynamic lexicon → decode from learned slot
      - If ESC → raw decode + auto-add to dynamic lexicon at same slot
    """

    def __init__(self, base_codec: MuxGridCodec):
        self.base = base_codec
        self.dynamic_entries: dict[str, MeshLexEntry] = {}
        self.addr_to_dynamic: dict[tuple[int, int], MeshLexEntry] = {}
        self._next_row = MESHLEX_ROW_START
        self._next_col = 0
        self._msg_stats: list[MeshLexStats] = []
        self._current_msg = 0
        self._total_adds = 0
        self._total_hits = 0

    @property
    def dynamic_count(self) -> int:
        return len(self.dynamic_entries)

    @property
    def capacity_remaining(self) -> int:
        total = (MESHLEX_ROW_END - MESHLEX_ROW_START + 1) * (MESHLEX_COL_MAX + 1)
        return total - self.dynamic_count

    def _allocate_slot(self) -> tuple[int, int]:
        """Get the next available dynamic grid slot."""
        if self._next_row > MESHLEX_ROW_END:
            raise RuntimeError(
                f"MeshLex full: {self.dynamic_count} entries, "
                f"no more slots in rows {MESHLEX_ROW_START}-{MESHLEX_ROW_END}")
        row, col = self._next_row, self._next_col
        self._next_col += 1
        if self._next_col > MESHLEX_COL_MAX:
            self._next_col = 0
            self._next_row += 1
        return row, col

    def _add_dynamic(self, word: str) -> MeshLexEntry:
        """Add a word to the dynamic lexicon and return its entry."""
        row, col = self._allocate_slot()
        entry = MeshLexEntry(
            word=word, row=row, col=col,
            added_at_msg=self._current_msg,
        )
        self.dynamic_entries[word] = entry
        self.addr_to_dynamic[(row, col)] = entry
        self._total_adds += 1
        return entry

    def _cb_upd_packet(self, entry: MeshLexEntry) -> bytes:
        """
        Build a CB_UPD broadcast packet for mesh sync.

        Format: [CB_UPD_MARKER(1B)] [row(2B)] [col(2B)] [len(1B)] [word(nB)]
        Total: 6 + len(word) bytes
        """
        word_bytes = entry.word.encode("utf-8")
        pkt = bytearray()
        pkt.append(CB_UPD_MARKER)
        pkt.extend(entry.row.to_bytes(2, "big"))
        pkt.extend(entry.col.to_bytes(2, "big"))
        pkt.append(len(word_bytes) & 0xFF)
        pkt.extend(word_bytes)
        return bytes(pkt)

    def encode(self, text: str) -> tuple[bytes, int, MeshLexStats]:
        """
        Encode text using base MUX + MeshLex dynamic entries.

        Returns: (payload_bytes, padding_bits, stats)
        """
        stats = MeshLexStats(msg_index=self._current_msg)
        words = text.lower().split()
        result = bytearray()

        for word in words:
            # 1. Check base codebook
            if word in self.base.word_to_addr:
                row, col = self.base.word_to_addr[word]
                result.extend(encode_grid_3byte(row, col))

            # 2. Check dynamic lexicon
            elif word in self.dynamic_entries:
                entry = self.dynamic_entries[word]
                entry.hit_count += 1
                self._total_hits += 1
                stats.dynamic_hits += 1
                row, col = entry.row, entry.col
                result.extend(encode_grid_3byte(row, col))

            # 3. Unknown — ESC encode + add to MeshLex
            else:
                # ESC encode (same as base codec)
                result.extend(encode_grid_3byte(ESC_ROW_333K, ESC_COL_333K))
                raw = word.encode("utf-8")
                result.append(len(raw) & 0xFF)
                result.extend(raw)

                # Add to dynamic lexicon
                entry = self._add_dynamic(word)
                stats.dynamic_adds += 1
                cb_pkt = self._cb_upd_packet(entry)
                stats.cb_upd_packets += 1
                stats.cb_upd_bytes += len(cb_pkt)

                logger.debug("MeshLex ADD: '%s' → (%d,%d) [msg %d]",
                             word, entry.row, entry.col, self._current_msg)

        self._msg_stats.append(stats)
        return bytes(result), 0, stats

    def decode(self, payload: bytes) -> str:
        """Decode payload using base MUX + MeshLex dynamic entries."""
        if not payload:
            return ""
        words = []
        pos = 0
        while pos + 3 <= len(payload):
            row, col = decode_grid_3byte(payload, pos)
            pos += 3

            if row == ESC_ROW_333K and col == ESC_COL_333K:
                if pos >= len(payload):
                    break
                length = payload[pos]
                pos += 1
                if pos + length > len(payload):
                    break
                word = payload[pos:pos + length].decode("utf-8")
                pos += length
                words.append(word)
            elif (row, col) in self.addr_to_dynamic:
                words.append(self.addr_to_dynamic[(row, col)].word)
            else:
                word = self.base.addr_to_word.get((row, col))
                if word:
                    words.append(word)
                else:
                    words.append(f"<UNK:({row},{col})>")
        return " ".join(words)

    def set_message_index(self, idx: int):
        self._current_msg = idx

    def get_lexicon_snapshot(self) -> list[dict]:
        """Return current dynamic lexicon as a list of dicts."""
        return [
            {
                "word": e.word,
                "row": e.row,
                "col": e.col,
                "added_at_msg": e.added_at_msg,
                "hit_count": e.hit_count,
            }
            for e in sorted(self.dynamic_entries.values(),
                            key=lambda x: (x.added_at_msg, x.row, x.col))
        ]


# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT HARNESS
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class StepResult:
    """Result of encoding one message."""
    msg_index: int
    original: str
    original_bytes: int
    encoded_bytes: int
    decoded: str
    ratio: float
    roundtrip_ok: bool
    esc_words: list[str]
    # MeshLex-specific
    dynamic_adds: int = 0
    dynamic_hits: int = 0
    cb_upd_bytes: int = 0
    # Wire hex preview
    wire_hex: str = ""


@dataclass
class RunResult:
    """Aggregated result of one experiment run."""
    run_name: str
    codec_name: str
    steps: list[StepResult] = field(default_factory=list)
    total_original_bytes: int = 0
    total_encoded_bytes: int = 0
    total_cb_upd_bytes: int = 0
    aggregate_ratio: float = 0.0
    delivery: str = ""
    total_esc: int = 0
    total_dynamic_adds: int = 0
    total_dynamic_hits: int = 0
    runtime_ms: float = 0.0


def find_esc_words(text: str, codec) -> list[str]:
    """Find words in text that aren't in the codec's base codebook."""
    words = text.lower().split()
    missing = []
    if hasattr(codec, "word_to_addr") and codec.word_to_addr:
        for w in words:
            if w not in codec.word_to_addr:
                missing.append(w)
    elif hasattr(codec, "encode_table"):
        for w in words:
            if w.lower() not in codec.encode_table:
                missing.append(w)
    return missing


def run_huffman_strict(messages: list[str]) -> RunResult:
    """Run 1: Huffman 333K Strict — baseline."""
    codec = MeshHuffmanCodec(codebook_size="333k")
    run = RunResult(run_name="huffman-333k-strict", codec_name="Huffman 333K")
    t0 = time.perf_counter()

    for i, msg in enumerate(messages):
        raw_bytes = len(msg.encode("utf-8"))
        encoded = codec.encode(msg)
        enc_bytes = len(encoded)
        decoded = codec.decode(encoded)
        ratio = raw_bytes / enc_bytes if enc_bytes else 0
        esc = find_esc_words(msg, codec)

        step = StepResult(
            msg_index=i + 1,
            original=msg,
            original_bytes=raw_bytes,
            encoded_bytes=enc_bytes,
            decoded=decoded,
            ratio=ratio,
            roundtrip_ok=(decoded == msg),
            esc_words=esc,
            wire_hex=encoded[:24].hex(),
        )
        run.steps.append(step)
        run.total_original_bytes += raw_bytes
        run.total_encoded_bytes += enc_bytes
        run.total_esc += len(esc)

    run.runtime_ms = (time.perf_counter() - t0) * 1000
    run.aggregate_ratio = (run.total_original_bytes / run.total_encoded_bytes
                           if run.total_encoded_bytes else 0)
    ok = sum(1 for s in run.steps if s.roundtrip_ok)
    run.delivery = f"{ok}/{len(messages)}"
    return run


def run_mux_strict(messages: list[str]) -> RunResult:
    """Run 2: MUX Grid 333K Strict — no MeshLex."""
    codec = MuxGridCodec(codebook_size="333k")
    run = RunResult(run_name="mux-333k-strict", codec_name="MUX Grid 333K")
    t0 = time.perf_counter()

    for i, msg in enumerate(messages):
        raw_bytes = len(msg.encode("utf-8"))
        payload, padding = codec.encode(msg)
        enc_bytes = len(payload)
        decoded = codec.decode(payload, padding)
        ratio = raw_bytes / enc_bytes if enc_bytes else 0
        esc = find_esc_words(msg, codec)

        step = StepResult(
            msg_index=i + 1,
            original=msg,
            original_bytes=raw_bytes,
            encoded_bytes=enc_bytes,
            decoded=decoded,
            ratio=ratio,
            roundtrip_ok=(decoded == msg.lower()),
            esc_words=esc,
            wire_hex=payload[:24].hex(),
        )
        run.steps.append(step)
        run.total_original_bytes += raw_bytes
        run.total_encoded_bytes += enc_bytes
        run.total_esc += len(esc)

    run.runtime_ms = (time.perf_counter() - t0) * 1000
    run.aggregate_ratio = (run.total_original_bytes / run.total_encoded_bytes
                           if run.total_encoded_bytes else 0)
    run.delivery = f"{sum(1 for s in run.steps if s.roundtrip_ok)}/{len(messages)}"
    return run


def run_mux_meshlex(messages: list[str],
                    pre_warmed_codec: Optional[MeshLexCodec] = None,
                    run_label: str = "mux-333k-meshlex") -> tuple[RunResult, MeshLexCodec]:
    """Run 3/4: MUX Grid 333K + MeshLex dynamic codebook."""
    base_codec = MuxGridCodec(codebook_size="333k")

    if pre_warmed_codec is not None:
        # Run 4: reuse the MeshLex from Run 3 (pre-warmed)
        ml = pre_warmed_codec
        # Reset per-message stats but keep the lexicon
        ml._msg_stats = []
        ml._current_msg = 0
        # Reset hit counters for clean measurement
        for entry in ml.dynamic_entries.values():
            entry.hit_count = 0
        ml._total_hits = 0
    else:
        ml = MeshLexCodec(base_codec)

    run = RunResult(run_name=run_label, codec_name="MUX Grid 333K + MeshLex")
    t0 = time.perf_counter()

    for i, msg in enumerate(messages):
        ml.set_message_index(i + 1)
        raw_bytes = len(msg.encode("utf-8"))
        payload, padding, stats = ml.encode(msg)
        enc_bytes = len(payload)
        decoded = ml.decode(payload)
        ratio = raw_bytes / enc_bytes if enc_bytes else 0

        # Find ESC words (words not in base OR dynamic at encode time)
        # For cold start, this is the same as base ESC
        # For warm, dynamic hits won't ESC
        esc = [w for w in msg.lower().split()
               if w not in base_codec.word_to_addr
               and w not in ml.dynamic_entries]

        step = StepResult(
            msg_index=i + 1,
            original=msg,
            original_bytes=raw_bytes,
            encoded_bytes=enc_bytes,
            decoded=decoded,
            ratio=ratio,
            roundtrip_ok=(decoded == msg.lower()),
            esc_words=esc,
            dynamic_adds=stats.dynamic_adds,
            dynamic_hits=stats.dynamic_hits,
            cb_upd_bytes=stats.cb_upd_bytes,
            wire_hex=payload[:24].hex(),
        )
        run.steps.append(step)
        run.total_original_bytes += raw_bytes
        run.total_encoded_bytes += enc_bytes
        run.total_cb_upd_bytes += stats.cb_upd_bytes
        run.total_esc += len(esc)
        run.total_dynamic_adds += stats.dynamic_adds
        run.total_dynamic_hits += stats.dynamic_hits

    run.runtime_ms = (time.perf_counter() - t0) * 1000
    run.aggregate_ratio = (run.total_original_bytes / run.total_encoded_bytes
                           if run.total_encoded_bytes else 0)
    run.delivery = f"{sum(1 for s in run.steps if s.roundtrip_ok)}/{len(messages)}"
    return run, ml


# ═══════════════════════════════════════════════════════════════════════════
# OUTPUT FORMATTING
# ═══════════════════════════════════════════════════════════════════════════

def print_banner():
    print()
    print("=" * 90)
    print("  CyberMesh v7.1 — Experiment H: MeshLex Stress Test")
    print("  Mindtech / Liberty Mesh")
    print("─" * 90)
    print(f"  Messages:   {len(SCRIPTED_MESSAGES)} scripted  |  Avg length: "
          f"{sum(len(m) for m in SCRIPTED_MESSAGES) // len(SCRIPTED_MESSAGES)} chars")
    print(f"  Edge cases: proper nouns, emoji, GPS, phone, ZIP, URLs, callsigns,")
    print(f"              station IDs, hashtags, measurements, highway designations")
    print(f"  Runs:       4 (Huffman baseline → MUX → MeshLex cold → MeshLex warm)")
    print("=" * 90)


def print_run_header(run_name: str, run_num: int, total: int):
    print()
    print("─" * 90)
    print(f"  RUN {run_num}/{total}: {run_name.upper()}")
    print("─" * 90)


def print_step(step: StepResult, show_meshlex: bool = False):
    rt = "✓" if step.roundtrip_ok else "✗"
    trunc = step.original if len(step.original) <= 72 else step.original[:69] + "..."
    print(f"  [{step.msg_index:>2}/10] {step.original_bytes:>3}B → {step.encoded_bytes:>3}B "
          f"  ratio={step.ratio:.2f}:1  {rt}  ESC={len(step.esc_words)}", end="")
    if show_meshlex:
        print(f"  +adds={step.dynamic_adds} hits={step.dynamic_hits} "
              f"upd={step.cb_upd_bytes}B", end="")
    print()
    print(f"           {trunc}")
    if step.esc_words:
        esc_preview = ", ".join(step.esc_words[:8])
        if len(step.esc_words) > 8:
            esc_preview += f" ... (+{len(step.esc_words)-8} more)"
        print(f"           ESC tokens: {esc_preview}")
    if not step.roundtrip_ok:
        print(f"           ✗ ROUNDTRIP FAIL")
        print(f"             DECODED: {step.decoded[:80]}")


def print_run_summary(run: RunResult, show_meshlex: bool = False):
    print()
    print(f"  {'─' * 86}")
    ok = sum(1 for s in run.steps if s.roundtrip_ok)
    print(f"  {run.run_name.upper()} SUMMARY")
    print(f"    Aggregate ratio:  {run.aggregate_ratio:.3f}:1")
    print(f"    Total:            {run.total_original_bytes}B → {run.total_encoded_bytes}B")
    print(f"    Roundtrip:        {run.delivery}")
    print(f"    Total ESC:        {run.total_esc}")
    print(f"    Runtime:          {run.runtime_ms:.1f} ms")
    if show_meshlex:
        print(f"    Dynamic adds:     {run.total_dynamic_adds}")
        print(f"    Dynamic hits:     {run.total_dynamic_hits}")
        print(f"    CB_UPD overhead:  {run.total_cb_upd_bytes}B "
              f"({run.total_cb_upd_bytes / max(run.total_encoded_bytes, 1) * 100:.1f}% of payload)")


def print_comparison(runs: list[RunResult]):
    print()
    print("=" * 90)
    print("  EXPERIMENT H — COMPARISON TABLE")
    print("=" * 90)
    print(f"  {'Run':<28} {'Ratio':>8} {'Encoded':>9} {'ESC':>5} "
          f"{'Adds':>5} {'Hits':>5} {'CB_UPD':>7} {'RT':>6} {'ms':>8}")
    print(f"  {'─'*28} {'─'*8} {'─'*9} {'─'*5} {'─'*5} {'─'*5} {'─'*7} {'─'*6} {'─'*8}")
    for r in runs:
        print(f"  {r.run_name:<28} {r.aggregate_ratio:>7.3f}x "
              f"{r.total_encoded_bytes:>8}B {r.total_esc:>5} "
              f"{r.total_dynamic_adds:>5} {r.total_dynamic_hits:>5} "
              f"{r.total_cb_upd_bytes:>6}B "
              f"{r.delivery:>6} {r.runtime_ms:>7.1f}")
    print()

    # Per-message ratio progression
    print("  PER-MESSAGE RATIO PROGRESSION (higher = better compression)")
    print(f"  {'Msg':>4}", end="")
    for r in runs:
        label = r.run_name.split("-333k-")[1] if "-333k-" in r.run_name else r.run_name
        print(f"  {label:>14}", end="")
    print(f"  {'Winner':>16}")
    print(f"  {'─'*4}", end="")
    for _ in runs:
        print(f"  {'─'*14}", end="")
    print(f"  {'─'*16}")

    for i in range(len(SCRIPTED_MESSAGES)):
        print(f"  {i+1:>4}", end="")
        ratios = []
        for r in runs:
            ratio = r.steps[i].ratio
            ratios.append((ratio, r.run_name))
            print(f"  {ratio:>13.3f}", end="")
        best = max(ratios, key=lambda x: x[0])
        label = best[1].split("-333k-")[1] if "-333k-" in best[1] else best[1]
        marker = " ★" if "meshlex" in best[1] else ""
        print(f"  {label:>14}{marker}")

    # Crossover analysis
    print()
    huff_steps = runs[0].steps
    for ml_run in runs[2:]:
        crossover = None
        for i, (h, m) in enumerate(zip(huff_steps, ml_run.steps)):
            if m.ratio >= h.ratio:
                crossover = i + 1
                break
        label = ml_run.run_name
        if crossover:
            print(f"  ★ {label} crosses Huffman at message {crossover}")
        else:
            print(f"  ✗ {label} never crosses Huffman in 10 messages")


def print_meshlex_lexicon(ml: MeshLexCodec):
    print()
    print("=" * 90)
    print(f"  MESHLEX DYNAMIC LEXICON — {ml.dynamic_count} entries "
          f"({ml.capacity_remaining} slots remaining)")
    print("=" * 90)
    print(f"  {'Word':<35} {'Grid':>10} {'Added@':>7} {'Hits':>5}")
    print(f"  {'─'*35} {'─'*10} {'─'*7} {'─'*5}")
    for entry in sorted(ml.dynamic_entries.values(),
                        key=lambda x: (x.added_at_msg, x.row, x.col)):
        trunc = entry.word if len(entry.word) <= 33 else entry.word[:30] + "..."
        print(f"  {trunc:<35} ({entry.row:>3},{entry.col:>3}) "
              f"  msg {entry.added_at_msg:>2}  {entry.hit_count:>4}")


def write_log(runs: list[RunResult], ml: MeshLexCodec, log_dir: str = "./logs"):
    """Write Experiment H results to markdown log."""
    os.makedirs(log_dir, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = os.path.join(log_dir, f"experiment-H-meshlex-{ts}.md")

    with open(path, "w", encoding="utf-8") as f:
        f.write("# Experiment H — MeshLex Stress Test\n\n")
        f.write(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**CyberMesh:** v7.1\n")
        f.write(f"**Messages:** {len(SCRIPTED_MESSAGES)} scripted\n\n")

        # Comparison table
        f.write("## Comparison\n\n")
        f.write("| Run | Ratio | Encoded | ESC | Adds | Hits | CB_UPD | RT |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for r in runs:
            f.write(f"| {r.run_name} | {r.aggregate_ratio:.3f}:1 | "
                    f"{r.total_encoded_bytes}B | {r.total_esc} | "
                    f"{r.total_dynamic_adds} | {r.total_dynamic_hits} | "
                    f"{r.total_cb_upd_bytes}B | {r.delivery} |\n")

        # Per-message progression
        f.write("\n## Per-Message Ratio Progression\n\n")
        f.write("| Msg |")
        for r in runs:
            f.write(f" {r.run_name} |")
        f.write("\n|---|")
        for _ in runs:
            f.write("---|")
        f.write("\n")
        for i in range(len(SCRIPTED_MESSAGES)):
            f.write(f"| {i+1} |")
            for r in runs:
                f.write(f" {r.steps[i].ratio:.3f} |")
            f.write("\n")

        # MeshLex lexicon
        f.write("\n## MeshLex Dynamic Lexicon\n\n")
        f.write(f"**Entries:** {ml.dynamic_count} / "
                f"{ml.dynamic_count + ml.capacity_remaining}\n\n")
        f.write("| Word | Grid | Added | Hits |\n")
        f.write("|---|---|---|---|\n")
        for entry in sorted(ml.dynamic_entries.values(),
                            key=lambda x: (x.added_at_msg, x.row, x.col)):
            f.write(f"| `{entry.word}` | ({entry.row},{entry.col}) | "
                    f"msg {entry.added_at_msg} | {entry.hit_count} |\n")

        # Per-run detail
        for r in runs:
            f.write(f"\n## {r.run_name}\n\n")
            f.write("| Step | Raw | Enc | Ratio | ESC | RT |\n")
            f.write("|---|---|---|---|---|---|\n")
            for s in r.steps:
                rt = "✓" if s.roundtrip_ok else "✗"
                f.write(f"| {s.msg_index} | {s.original_bytes}B | "
                        f"{s.encoded_bytes}B | {s.ratio:.3f} | "
                        f"{len(s.esc_words)} | {rt} |\n")

    print(f"\n  📄 Log written: {path}")
    return path


def write_json_results(runs: list[RunResult], ml: MeshLexCodec,
                       log_dir: str = "./logs"):
    """Write machine-readable JSON results."""
    os.makedirs(log_dir, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = os.path.join(log_dir, f"experiment-H-meshlex-{ts}.json")

    data = {
        "experiment": "H",
        "version": "7.1",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "messages": len(SCRIPTED_MESSAGES),
        "runs": [],
        "meshlex_lexicon": ml.get_lexicon_snapshot(),
    }

    for r in runs:
        run_data = {
            "name": r.run_name,
            "codec": r.codec_name,
            "aggregate_ratio": round(r.aggregate_ratio, 4),
            "total_original_bytes": r.total_original_bytes,
            "total_encoded_bytes": r.total_encoded_bytes,
            "total_cb_upd_bytes": r.total_cb_upd_bytes,
            "total_esc": r.total_esc,
            "total_dynamic_adds": r.total_dynamic_adds,
            "total_dynamic_hits": r.total_dynamic_hits,
            "delivery": r.delivery,
            "runtime_ms": round(r.runtime_ms, 2),
            "steps": [
                {
                    "msg": s.msg_index,
                    "raw_bytes": s.original_bytes,
                    "enc_bytes": s.encoded_bytes,
                    "ratio": round(s.ratio, 4),
                    "roundtrip": s.roundtrip_ok,
                    "esc_count": len(s.esc_words),
                    "esc_words": s.esc_words,
                    "dynamic_adds": s.dynamic_adds,
                    "dynamic_hits": s.dynamic_hits,
                    "cb_upd_bytes": s.cb_upd_bytes,
                    "wire_hex": s.wire_hex,
                }
                for s in r.steps
            ],
        }
        data["runs"].append(run_data)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  📊 JSON written: {path}")
    return path


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print_banner()

    all_runs: list[RunResult] = []

    # ── Run 1: Huffman 333K Strict (baseline) ──
    print_run_header("huffman-333k-strict (baseline)", 1, 4)
    r1 = run_huffman_strict(SCRIPTED_MESSAGES)
    for s in r1.steps:
        print_step(s)
    print_run_summary(r1)
    all_runs.append(r1)

    # ── Run 2: MUX Grid 333K Strict (no MeshLex) ──
    print_run_header("mux-333k-strict (no meshlex)", 2, 4)
    r2 = run_mux_strict(SCRIPTED_MESSAGES)
    for s in r2.steps:
        print_step(s)
    print_run_summary(r2)
    all_runs.append(r2)

    # ── Run 3: MUX Grid 333K + MeshLex (cold start) ──
    print_run_header("mux-333k-meshlex (cold start)", 3, 4)
    r3, ml_codec = run_mux_meshlex(SCRIPTED_MESSAGES)
    for s in r3.steps:
        print_step(s, show_meshlex=True)
    print_run_summary(r3, show_meshlex=True)
    all_runs.append(r3)

    # Print lexicon state after cold run
    print_meshlex_lexicon(ml_codec)

    # ── Run 4: MUX Grid 333K + MeshLex (pre-warmed) ──
    print_run_header("mux-333k-meshlex-warm (pre-warmed lexicon)", 4, 4)
    r4, ml_warm = run_mux_meshlex(
        SCRIPTED_MESSAGES,
        pre_warmed_codec=ml_codec,
        run_label="mux-333k-meshlex-warm",
    )
    for s in r4.steps:
        print_step(s, show_meshlex=True)
    print_run_summary(r4, show_meshlex=True)
    all_runs.append(r4)

    # ── Comparison ──
    print_comparison(all_runs)

    # ── Write logs ──
    md_path = write_log(all_runs, ml_warm)
    json_path = write_json_results(all_runs, ml_warm)

    # ── Final verdict ──
    print()
    print("=" * 90)
    print("  VERDICT")
    print("=" * 90)

    huff_ratio = r1.aggregate_ratio
    mux_ratio = r2.aggregate_ratio
    ml_cold_ratio = r3.aggregate_ratio
    ml_warm_ratio = r4.aggregate_ratio

    print(f"  Huffman Strict:      {huff_ratio:.3f}:1  (baseline)")
    print(f"  MUX Strict:          {mux_ratio:.3f}:1  "
          f"({(mux_ratio/huff_ratio - 1)*100:+.1f}% vs Huffman)")
    print(f"  MeshLex Cold:        {ml_cold_ratio:.3f}:1  "
          f"({(ml_cold_ratio/huff_ratio - 1)*100:+.1f}% vs Huffman)")
    print(f"  MeshLex Warm:        {ml_warm_ratio:.3f}:1  "
          f"({(ml_warm_ratio/huff_ratio - 1)*100:+.1f}% vs Huffman)")
    print()

    if ml_warm_ratio > huff_ratio:
        print("  ★ MeshLex WARM beats Huffman — MUX earns a permanent role")
        print("    as the location-aware, operationally-secure codec.")
    elif ml_warm_ratio > mux_ratio * 1.15:
        improvement = (ml_warm_ratio / mux_ratio - 1) * 100
        print(f"  ◉ MeshLex improves MUX by {improvement:.1f}% but doesn't beat Huffman.")
        print("    MUX has a role for proper-noun-heavy traffic; Huffman stays general-purpose.")
    else:
        print("  ✗ MeshLex doesn't significantly improve MUX compression.")
        print("    Consider deprecating MUX Grid in favor of Huffman-only pipeline.")

    print()
    print(f"  Dynamic entries learned: {ml_warm.dynamic_count}")
    print(f"  CB_UPD overhead (cold):  {r3.total_cb_upd_bytes}B "
          f"(one-time mesh sync cost)")
    print(f"  CB_UPD overhead (warm):  {r4.total_cb_upd_bytes}B "
          f"(should be 0 if fully warmed)")
    print()
    print("=" * 90)
    print("  Experiment H complete.")
    print("=" * 90)


if __name__ == "__main__":
    main()
