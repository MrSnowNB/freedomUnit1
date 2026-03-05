#!/usr/bin/env python3
"""
mesh_huffman.py — Word-Level Huffman Codec for LoRa Mesh Messages
=================================================================
v4: 4,096-word shared codebook (loaded from huffman_codebook_4k.csv).

Upgraded from v3 (2,048-word codebook from english_unigram_freq.csv) to
use the same 4,095-word vocabulary as MUX Grid, enabling fair A/B
comparison in Experiment C.

Key features (unchanged from v3):
  - Spaces between words are IMPLICIT (no space bit needed for word→word)
  - Case bits: 0=lowercase (1 bit), 10=Capitalized, 11=UPPER (2 bit)
  - "No-space" flag is the rare case (only before punctuation), 1-bit penalty
  - Numbers after NUM token use tighter encoding
  - ESC fallback for out-of-codebook words

Author: Mark Snow, Jr. — CyberMesh / Liberty Mesh Project
Date:   March 2026
"""

import csv
import heapq
import re
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


# Control tokens — artificial entries in the Huffman tree
_ESC  = "\x00ESC"
_NUM  = "\x00NUM"
_PUNCT = "\x00PUN"
_NOSPACE = "\x00NSP"  # "next token has NO space before it"
_EOF     = "\x00EOF"  # end of stream marker


class MeshHuffmanCodec:
    """
    Static word-level Huffman codec for LoRa mesh messages.

    v4: Loads 4,095-word vocabulary from huffman_codebook_4k.csv (same
    word list as MUX Grid). Falls back to english_unigram_freq.csv if
    the 4K codebook is not found (backward compatibility).
    
    Encoding philosophy:
      - Spaces between tokens are IMPLICIT (most common case)
      - When a token should NOT have a preceding space, emit _NOSPACE first
      - Case: 1-bit flag after word code. 0=lowercase, 1=prefix for cap/upper
      - Numbers: _NUM + var-length binary
      - Unknown words: _ESC + 5-bit length + 7-bit ASCII chars  
      - Punctuation: _PUNCT + 7-bit ASCII
    """

    def __init__(self, codebook_csv_path: Optional[str] = None):
        self.codebook_source = "unknown"
        if codebook_csv_path is None:
            # Prefer huffman_codebook_4k.csv (shared vocabulary with MUX Grid)
            base = os.path.dirname(os.path.abspath(__file__))
            path_4k = os.path.join(base, "huffman_codebook_4k.csv")
            path_legacy = os.path.join(base, "english_unigram_freq.csv")
            if os.path.exists(path_4k):
                codebook_csv_path = path_4k
                self.codebook_source = "huffman_codebook_4k"
            else:
                codebook_csv_path = path_legacy
                self.codebook_source = "english_unigram_freq_legacy"

        self.freq_table = self._build_freq_table(codebook_csv_path)
        tree = build_huffman_tree(self.freq_table)
        self.encode_table = build_codebook(tree)
        self.decode_table = {v: k for k, v in self.encode_table.items()}
        self._tok_re = re.compile(
            r"([a-zA-Z]+(?:'[a-zA-Z]+)?)"
            r"|([0-9]+(?:\.[0-9]+)?)"
            r"|(\s+)"
            r"|([^\s])"
        )

    def _build_freq_table(self, csv_path: str) -> dict[str, int]:
        """
        Build frequency table from codebook CSV.
        
        Supports two formats:
          - huffman_codebook_4k.csv: columns word, huffman_code, bits, frequency
          - english_unigram_freq.csv: columns word, count (legacy fallback)
        """
        freq: dict[str, int] = {}
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Codebook not found: {csv_path}")

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fields = reader.fieldnames or []

            if "huffman_code" in fields:
                # 4K format: word, huffman_code, bits, frequency
                for row in reader:
                    w = row["word"].strip().lower()
                    if w == "<esc>":
                        continue
                    try:
                        c = int(row["frequency"])
                    except ValueError:
                        continue
                    freq[w] = c
            else:
                # Legacy format: word, count
                loaded = 0
                for row in reader:
                    vals = list(row.values())
                    if len(vals) < 2:
                        continue
                    w = vals[0].strip().lower()
                    try:
                        c = int(vals[1])
                    except ValueError:
                        continue
                    if len(w) == 1 and w not in {"a", "i"}:
                        continue
                    if w.isdigit():
                        continue
                    freq[w] = c
                    loaded += 1
                    if loaded >= 4000:
                        break
                # Legacy: also merge domain words
                from mesh_huffman import MESH_DOMAIN_WORDS_LEGACY
                for w, c in MESH_DOMAIN_WORDS_LEGACY.items():
                    freq[w.lower()] = max(freq.get(w.lower(), 0), c)
                sorted_w = sorted(freq.items(), key=lambda x: x[1], reverse=True)
                freq = dict(sorted_w[:2048])

        # Add control tokens with appropriate frequencies
        word_freqs = sorted(freq.values(), reverse=True)
        mid = word_freqs[len(word_freqs) // 2] if word_freqs else 1_000_000
        freq[_NOSPACE] = mid * 3
        freq[_NUM]     = mid * 2
        freq[_PUNCT]   = mid * 2
        freq[_ESC]     = mid
        freq[_EOF]     = 1  # rare = long code, but we only emit it once

        return freq

    def _tokenize(self, text: str) -> list[tuple[str, str, bool]]:
        """Returns (type, value, space_before) triples."""
        tokens = []
        space_pending = False
        for m in self._tok_re.finditer(text):
            word, number, ws, punct = m.groups()
            if ws is not None:
                space_pending = True
                continue
            if word:     tokens.append(("word", word, space_pending))
            elif number: tokens.append(("number", number, space_pending))
            elif punct:  tokens.append(("punct", punct, space_pending))
            space_pending = False
        return tokens

    # ---- sub-encoders ----

    @staticmethod
    def _encode_number(n: int) -> str:
        if n < 0:
            return "1" + MeshHuffmanCodec._encode_number(-n)[1:]  # flip sign
        if n <= 255:
            return "0" + "00" + format(n, "08b")       # 11 bits
        elif n <= 65535:
            return "0" + "01" + format(n, "016b")       # 19 bits
        else:
            return "0" + "10" + format(n & 0xFFFFFFFF, "032b")  # 35 bits

    @staticmethod
    def _decode_number(bits: str, pos: int) -> tuple[int, int]:
        neg = bits[pos] == "1"; pos += 1
        lc = bits[pos:pos+2]; pos += 2
        widths = {"00": 8, "01": 16, "10": 32}
        w = widths.get(lc)
        if w is None: raise ValueError(f"Bad num len: {lc}")
        v = int(bits[pos:pos+w], 2); pos += w
        return (-v if neg else v), pos

    @staticmethod
    def _encode_raw(word: str) -> str:
        w = word[:31]
        return format(len(w), "05b") + "".join(format(ord(c) & 0x7F, "07b") for c in w)

    @staticmethod
    def _decode_raw(bits: str, pos: int) -> tuple[str, int]:
        n = int(bits[pos:pos+5], 2); pos += 5
        chars = []
        for _ in range(n):
            chars.append(chr(int(bits[pos:pos+7], 2))); pos += 7
        return "".join(chars), pos

    @staticmethod
    def _encode_case(word: str) -> str:
        """0 = lowercase (1 bit), 10 = Capitalized (2 bits), 11 = UPPER (2 bits)"""
        if word.islower():
            return "0"
        if len(word) > 1 and word[0].isupper() and word[1:].islower():
            return "10"
        if word.isupper():
            return "11"
        return "10"  # fallback: treat as capitalized

    @staticmethod
    def _apply_case(word: str, bits: str, pos: int) -> tuple[str, int]:
        if bits[pos] == "0":
            return word.lower(), pos + 1
        pos += 1
        if bits[pos] == "0":
            return word.capitalize(), pos + 1
        else:
            return word.upper(), pos + 1

    # ---- encode ----

    def encode(self, text: str) -> bytes:
        """
        Encode text. Default assumption: space between every pair of tokens.
        When a token should NOT have a space, emit _NOSPACE before it.
        First token never has a space.
        """
        tokens = self._tokenize(text)
        bits = ""
        first = True

        for tok_type, tok_val, space_before in tokens:
            if not first:
                # Default is "space before". If no space, emit NOSPACE marker.
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
                    bits += self._encode_raw(tok_val)

            elif tok_type == "number":
                if '.' in tok_val:
                    bits += self.encode_table[_ESC]
                    bits += self._encode_raw(tok_val)
                else:
                    bits += self.encode_table[_NUM]
                    bits += self._encode_number(int(tok_val))

            elif tok_type == "punct":
                bits += self.encode_table[_PUNCT]
                bits += format(ord(tok_val) & 0x7F, "07b")

        # End-of-stream: emit EOF Huffman code
        bits += self.encode_table[_EOF]
        r = len(bits) % 8
        if r: bits += "0" * (8 - r)
        return int(bits, 2).to_bytes(len(bits) // 8, byteorder="big")

    # ---- decode ----

    def decode(self, data: bytes) -> str:
        bits = bin(int.from_bytes(data, byteorder="big"))[2:].zfill(len(data) * 8)
        pos = 0
        result = []
        first = True
        nospace_next = False

        while pos < len(bits):
            # Decode next Huffman code
            code = ""
            decoded = None
            while pos < len(bits):
                code += bits[pos]; pos += 1
                if code in self.decode_table:
                    decoded = self.decode_table[code]
                    break
            if decoded is None:
                break

            # Handle control tokens
            if decoded == _EOF:
                break
            if decoded == _NOSPACE:
                nospace_next = True
                continue

            # Insert space before this token (unless first or nospace)
            if not first and not nospace_next:
                result.append(" ")
            nospace_next = False
            first = False

            if decoded == _ESC:
                w, pos = self._decode_raw(bits, pos)
                result.append(w)
            elif decoded == _NUM:
                v, pos = self._decode_number(bits, pos)
                result.append(str(v))
            elif decoded == _PUNCT:
                ch = chr(int(bits[pos:pos+7], 2)); pos += 7
                result.append(ch)
            else:
                # Regular word + case
                w, pos = self._apply_case(decoded, bits, pos)
                result.append(w)

        return "".join(result)

    # ---- analysis ----

    def stats(self) -> dict:
        cl = [len(v) for k, v in self.encode_table.items() if not k.startswith("\x00")]
        ctrl = {t: len(self.encode_table.get(t, "")) for t in [_ESC, _NUM, _PUNCT, _NOSPACE, _EOF]}
        return {
            "codebook_size": len(self.encode_table) - 5,
            "codebook_source": self.codebook_source,
            "min_bits": min(cl), "max_bits": max(cl),
            "avg_bits": sum(cl) / len(cl),
            "controls": ctrl,
        }

    def analyze(self, text: str) -> dict:
        raw = len(text.encode("utf-8"))
        comp = self.encode(text)
        cb = len(comp)
        dec = self.decode(comp)
        return {
            "original": text, "decoded": dec,
            "raw_bytes": raw, "comp_bytes": cb,
            "ratio": raw / cb if cb else float("inf"),
            "savings_pct": (1 - cb / raw) * 100 if raw else 0,
            "roundtrip": dec == text,
            "headroom": 230 - cb,
        }

    def codebook_coverage(self, text: str) -> dict:
        toks = self._tokenize(text)
        words = [t[1] for t in toks if t[0] == "word"]
        inc = sum(1 for w in words if w.lower() in self.encode_table)
        return {
            "total": len(words), "in_cb": inc,
            "coverage": inc / len(words) * 100 if words else 100,
            "missing": [w for w in words if w.lower() not in self.encode_table],
        }


# Legacy domain words — only used if falling back to english_unigram_freq.csv
MESH_DOMAIN_WORDS_LEGACY = {
    "node": 50_000_000, "mesh": 50_000_000, "sensor": 45_000_000,
    "packet": 45_000_000, "signal": 40_000_000, "radio": 40_000_000,
    "frequency": 35_000_000, "antenna": 35_000_000, "channel": 35_000_000,
    "gateway": 30_000_000, "repeater": 30_000_000, "lora": 30_000_000,
    "rssi": 25_000_000, "snr": 25_000_000, "gps": 25_000_000,
    "latitude": 20_000_000, "longitude": 20_000_000, "altitude": 20_000_000,
    "battery": 25_000_000, "voltage": 20_000_000, "solar": 20_000_000,
    "firmware": 20_000_000, "reboot": 18_000_000, "uptime": 18_000_000,
    "hop": 20_000_000, "hops": 20_000_000, "route": 20_000_000,
    "neighbor": 18_000_000, "neighbors": 18_000_000, "topology": 15_000_000,
    "broadcast": 18_000_000, "ping": 18_000_000, "ack": 18_000_000,
    "timeout": 15_000_000, "retry": 15_000_000, "queue": 15_000_000,
    "payload": 15_000_000, "header": 15_000_000, "checksum": 15_000_000,
    "sos": 50_000_000, "emergency": 40_000_000, "dispatch": 35_000_000,
    "flood": 18_000_000, "storm": 18_000_000, "alert": 25_000_000,
    "humidity": 15_000_000, "temperature": 20_000_000,
}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    codec = MeshHuffmanCodec()
    s = codec.stats()

    print("=" * 78)
    print("  MESH HUFFMAN CODEC v4 — CyberMesh / Liberty Mesh")
    print(f"  {s['codebook_size']}-word codebook from {s['codebook_source']}")
    print("=" * 78)
    print(f"  Codebook:  {s['codebook_size']} words")
    print(f"  Codes:     {s['min_bits']}–{s['max_bits']} bits (avg {s['avg_bits']:.1f})")
    print(f"  Controls:  ESC={s['controls'][_ESC]}b  NUM={s['controls'][_NUM]}b  "
          f"PUNCT={s['controls'][_PUNCT]}b  NOSPACE={s['controls'][_NOSPACE]}b")

    msgs = [
        "ok",
        "SOS",
        "Battery at 89 percent",
        "Node 12 temperature 72 humidity 45",
        "The sensor node is reporting temperature 94 degrees",
        "Alert flood warning for the area",
        "What time is it?",
        "the sensor is online battery at 89 percent signal strong",
    ]

    print(f"\n{'=' * 78}")
    print(f"  COMPRESSION BENCHMARKS — 8 Test Messages")
    print(f"{'=' * 78}")
    hdr = f"  {'#':<3} {'Raw':>4} {'Cmp':>4} {'Ratio':>6} {'Sav%':>5} {'Head':>5} {'RT'} Message"
    print(hdr)
    print(f"  {'-'*3} {'-'*4} {'-'*4} {'-'*6} {'-'*5} {'-'*5} {'-'*2} {'-'*50}")

    tr = tc = 0
    ok = True
    for i, m in enumerate(msgs, 1):
        r = codec.analyze(m)
        tr += r["raw_bytes"]; tc += r["comp_bytes"]
        rt = "✓" if r["roundtrip"] else "✗"
        if not r["roundtrip"]: ok = False
        dm = m if len(m) <= 55 else m[:52] + "..."
        print(f"  {i:<3} {r['raw_bytes']:>4} {r['comp_bytes']:>4} "
              f"{r['ratio']:>6.2f} {r['savings_pct']:>4.0f}% {r['headroom']:>5} "
              f"{rt}  {dm}")
        if not r["roundtrip"]:
            print(f"      FAIL: '{r['decoded']}'")

    ar = tr / tc if tc else 0
    ap = (1 - tc / tr) * 100 if tr else 0
    am = tc / len(msgs)

    print(f"\n  {'─' * 76}")
    print(f"  AGGREGATE  {tr:>4} {tc:>4} {ar:>6.2f} {ap:>4.0f}%")
    print(f"  Avg compressed:  {am:.0f} bytes  |  Avg headroom: {230 - am:.0f} bytes")
    print(f"  Roundtrip:       {'100% PASS ✓' if ok else 'FAILURES ✗'}")
    print(f"{'=' * 78}")


if __name__ == "__main__":
    main()
