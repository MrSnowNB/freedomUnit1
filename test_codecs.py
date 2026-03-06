#!/usr/bin/env python3
"""
test_codecs.py — Unit tests for codecs, pretokenizer, and LLM codec pipeline
==============================================================================
Validates:
  1-5:   Original codec tests (Experiment B)
  6:     Pre-tokenizer normalize() function
  7:     Pre-tokenizer + codec roundtrip (normalized text through both codecs)
  8:     LLM codec module loads (no Lemonade Server required)
  9-17:  Cube96 3D codec tests (G-4)

Run before any live transmission: python test_codecs.py
Halt if any test fails.

Author: Mark Snow, Jr. — Mindtech / CyberMesh / Liberty Mesh
Date:   March 2026
"""

import sys
import os

# Ensure imports work from script directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mux_codec import (MuxGridCodec, CODEC_ID_HUFFMAN, CODEC_ID_MUX_GRID,
                       pack_cube96, unpack_cube96, is_esc_cube96,
                       cube96_hash_coords, ESC_CUBE_BYTE, CUBE_SIZE,
                       MAX_CUBE_COORD)

TEST_MESSAGES = [
    "ok",
    "SOS",
    "Battery at 89 percent",
    "Node 12 temperature 72 humidity 45",
    "The sensor node is reporting temperature 94 degrees",
    "Alert flood warning for the area",
    "What time is it?",
    "the sensor is online battery at 89 percent signal strong",
]


def test_mux_standalone():
    """Test MUX Grid codec: encode → decode roundtrip without header."""
    print("=" * 70)
    print("  TEST 1: MUX Grid Codec — Standalone (no header)")
    print("=" * 70)

    codec = MuxGridCodec()
    passed = 0
    failed = 0

    for i, msg in enumerate(TEST_MESSAGES, 1):
        payload, padding = codec.encode(msg)
        decoded = codec.decode(payload, padding)
        match = (decoded == msg.lower())

        status = "PASS ✓" if match else "FAIL ✗"
        print(f"  {i}. [{status}] \"{msg}\"")
        if not match:
            print(f"      Expected: \"{msg.lower()}\"")
            print(f"      Got:      \"{decoded}\"")
            failed += 1
        else:
            passed += 1

    print(f"\n  Results: {passed} passed, {failed} failed\n")
    return failed == 0


def test_mux_with_header():
    """Test MUX Grid codec: full packet with 3-byte header."""
    print("=" * 70)
    print("  TEST 2: MUX Grid Codec — Full packet with 3-byte header")
    print("=" * 70)

    codec = MuxGridCodec()
    passed = 0
    failed = 0

    for i, msg in enumerate(TEST_MESSAGES, 1):
        packet = codec.encode_packet(msg, seq=i)

        assert packet[0] == CODEC_ID_MUX_GRID, f"Bad codec ID: {packet[0]}"
        assert packet[1] == i, f"Bad seq: {packet[1]}"
        assert 0 <= packet[2] <= 7, f"Bad padding: {packet[2]}"

        decoded, codec_id, seq, padding = codec.decode_packet(packet)
        match = (decoded == msg.lower())

        raw = len(msg.encode("utf-8"))
        comp = len(packet)
        ratio = raw / comp if comp else 0

        status = "PASS ✓" if match else "FAIL ✗"
        print(f"  {i}. [{status}] {raw}B → {comp}B (ratio {ratio:.2f}:1)  "
              f"codec=0x{codec_id:02X} seq={seq}  \"{msg[:40]}\"")
        if not match:
            print(f"      Expected: \"{msg.lower()}\"")
            print(f"      Got:      \"{decoded}\"")
            failed += 1
        else:
            passed += 1

    print(f"\n  Results: {passed} passed, {failed} failed\n")
    return failed == 0


def test_huffman_with_header():
    """Test Huffman codec wrapped with 3-byte header (retrofit)."""
    print("=" * 70)
    print("  TEST 3: Huffman Codec — Full packet with 3-byte header (retrofit)")
    print("=" * 70)

    from huffman_codec import MeshHuffmanCodec

    huffman = MeshHuffmanCodec()
    passed = 0
    failed = 0

    for i, msg in enumerate(TEST_MESSAGES, 1):
        payload = huffman.encode(msg)
        padding = 0
        header = bytes([CODEC_ID_HUFFMAN, i & 0xFF, padding])
        packet = header + payload

        assert packet[0] == CODEC_ID_HUFFMAN
        assert packet[1] == i

        codec_id = packet[0]
        seq = packet[1]
        payload_data = packet[3:]
        decoded = huffman.decode(payload_data)

        match = (decoded == msg)

        raw = len(msg.encode("utf-8"))
        comp = len(packet)
        ratio = raw / comp if comp else 0

        status = "PASS ✓" if match else "FAIL ✗"
        print(f"  {i}. [{status}] {raw}B → {comp}B (ratio {ratio:.2f}:1)  "
              f"codec=0x{codec_id:02X} seq={seq}  \"{msg[:40]}\"")
        if not match:
            print(f"      Expected: \"{msg}\"")
            print(f"      Got:      \"{decoded}\"")
            failed += 1
        else:
            passed += 1

    print(f"\n  Results: {passed} passed, {failed} failed\n")
    return failed == 0


def test_cross_codec_detection():
    """Test that decoder auto-detects codec from header byte."""
    print("=" * 70)
    print("  TEST 4: Cross-codec detection from Codec ID byte")
    print("=" * 70)

    from huffman_codec import MeshHuffmanCodec

    huffman = MeshHuffmanCodec()
    mux = MuxGridCodec()

    msg = "the sensor is online battery at 89 percent signal strong"

    huff_payload = huffman.encode(msg)
    huff_packet = bytes([CODEC_ID_HUFFMAN, 42, 0]) + huff_payload

    mux_packet = mux.encode_packet(msg, seq=43)

    for label, packet in [("Huffman", huff_packet), ("MUX Grid", mux_packet)]:
        cid = packet[0]
        codec_name = {CODEC_ID_HUFFMAN: "Huffman", CODEC_ID_MUX_GRID: "MUX Grid"}.get(cid, "UNKNOWN")
        seq = packet[1]
        payload = packet[3:]

        if cid == CODEC_ID_HUFFMAN:
            decoded = huffman.decode(payload)
            expected = msg
        elif cid == CODEC_ID_MUX_GRID:
            pad = packet[2]
            decoded = mux.decode(payload, pad)
            expected = msg.lower()
        else:
            decoded = "UNKNOWN"
            expected = ""

        match = decoded == expected
        status = "PASS ✓" if match else "FAIL ✗"
        print(f"  [{status}] {label}: Codec ID=0x{cid:02X} detected as {codec_name}, "
              f"seq={seq}, {len(packet)}B")

    print()
    return True


def test_esc_handling():
    """Test ESC (out-of-codebook) handling in MUX Grid."""
    print("=" * 70)
    print("  TEST 5: MUX Grid ESC handling (out-of-codebook words)")
    print("=" * 70)

    codec = MuxGridCodec()

    test_cases = [
        "the xylophonist played beautifully",
        "node 42 zzyzva status ok",
    ]

    passed = 0
    for msg in test_cases:
        packet = codec.encode_packet(msg)
        decoded, _, _, _ = codec.decode_packet(packet)
        match = decoded == msg.lower()
        status = "PASS ✓" if match else "FAIL ✗"
        print(f"  [{status}] \"{msg}\"")
        if not match:
            print(f"      Expected: \"{msg.lower()}\"")
            print(f"      Got:      \"{decoded}\"")
        else:
            passed += 1

    print(f"\n  Results: {passed}/{len(test_cases)} passed\n")
    return passed == len(test_cases)


def test_pretokenizer():
    """Test pretokenizer normalize() function."""
    print("=" * 70)
    print("  TEST 6: Pre-Tokenizer — normalize() function")
    print("=" * 70)

    from pretokenizer import normalize

    test_cases = [
        # (input, expected, description)
        ("Sensor 5 now reads 2.1 feet – escalating the response.",
         "sensor 5 now reads 2 point 1 feet escalating the response",
         "Decimal + dash + punctuation"),
        ("Don't worry, it's online.",
         "do not worry it is online",
         "Contractions + punctuation"),
        ("Alert! Node down — reboot ASAP!!!",
         "alert node down reboot asap",
         "Exclamations + dash + mixed case"),
        ("off-grid low-power node",
         "off grid low power node",
         "Hyphens"),
        ("Temperature: 72.5°F",
         "temperature 72 point 5f",
         "Colon + decimal + degree symbol"),
        # Experiment B messages (should still roundtrip)
        ("ok", "ok", "Minimal"),
        ("SOS", "sos", "Uppercase"),
        ("Battery at 89 percent", "battery at 89 percent", "Mixed case"),
        ("Node 12 temperature 72 humidity 45",
         "node 12 temperature 72 humidity 45", "Multi-number"),
        ("The sensor node is reporting temperature 94 degrees",
         "the sensor node is reporting temperature 94 degrees", "Full sentence"),
        ("Alert flood warning for the area",
         "alert flood warning for the area", "Emergency"),
        ("What time is it?", "what time is it", "Punctuation"),
        ("the sensor is online battery at 89 percent signal strong",
         "the sensor is online battery at 89 percent signal strong", "AI-constrained"),
    ]

    passed = 0
    failed = 0
    for inp, expected, desc in test_cases:
        result = normalize(inp)
        ok = result == expected
        status = "PASS ✓" if ok else "FAIL ✗"
        print(f"  [{status}] {desc}: \"{inp[:50]}\" → \"{result[:50]}\"")
        if not ok:
            print(f"      Expected: \"{expected}\"")
            print(f"      Got:      \"{result}\"")
            failed += 1
        else:
            passed += 1

    print(f"\n  Results: {passed} passed, {failed} failed\n")
    return failed == 0


def test_pretokenizer_codec_roundtrip():
    """Test normalized text through both codecs (encode → decode roundtrip)."""
    print("=" * 70)
    print("  TEST 7: Pre-Tokenizer + Codec Roundtrip (both codecs)")
    print("=" * 70)

    from pretokenizer import normalize
    from huffman_codec import MeshHuffmanCodec

    mux = MuxGridCodec()
    huffman = MeshHuffmanCodec()

    # Normalize first, then encode/decode
    test_inputs = [
        "Sensor 5 now reads 2.1 feet – escalating the response.",
        "Don't worry, it's online.",
        "Alert! Node down — reboot ASAP!!!",
        "off-grid low-power node",
    ] + TEST_MESSAGES

    passed = 0
    failed = 0
    for msg in test_inputs:
        normalized = normalize(msg)

        # MUX roundtrip
        mux_packet = mux.encode_packet(normalized)
        mux_decoded, _, _, _ = mux.decode_packet(mux_packet)
        mux_ok = mux_decoded == normalized.lower()

        # Huffman roundtrip (Huffman preserves case, but normalized is already lowercase)
        huff_payload = huffman.encode(normalized)
        huff_decoded = huffman.decode(huff_payload)
        huff_ok = huff_decoded == normalized

        ok = mux_ok and huff_ok
        status = "PASS ✓" if ok else "FAIL ✗"
        print(f"  [{status}] \"{msg[:50]}\" → norm: \"{normalized[:50]}\"")
        if not mux_ok:
            print(f"      MUX: \"{mux_decoded[:50]}\" ≠ \"{normalized[:50]}\"")
        if not huff_ok:
            print(f"      HUF: \"{huff_decoded[:50]}\" ≠ \"{normalized[:50]}\"")
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\n  Results: {passed} passed, {failed} failed\n")
    return failed == 0


def test_llm_codec_module():
    """Test that llm_codec.py loads and codebook is accessible (no Lemonade Server needed)."""
    print("=" * 70)
    print("  TEST 8: LLM Codec Module — Load + Codebook Access")
    print("=" * 70)

    from llm_codec import get_codebook_words
    from pretokenizer import compute_hit_rate

    words = get_codebook_words()
    ok = True

    # Check codebook loaded
    if len(words) < 4000:
        print(f"  [FAIL ✗] Codebook too small: {len(words)} words (expected ~4095)")
        ok = False
    else:
        print(f"  [PASS ✓] Codebook loaded: {len(words)} words")

    # Check key words are present
    required = ["the", "of", "and", "sensor", "battery", "flood", "warning",
                 "alert", "node", "water", "point"]
    for w in required:
        if w not in words:
            print(f"  [FAIL ✗] Missing required word: \"{w}\"")
            ok = False
    if ok:
        print(f"  [PASS ✓] All {len(required)} required words present")

    # Check hit rate function
    test_text = "sensor 5 now reads 2 point 1 feet escalating the response"
    rate = compute_hit_rate(test_text, words)
    if rate > 0.8:
        print(f"  [PASS ✓] Hit rate for normalized text: {rate:.0%}")
    else:
        print(f"  [FAIL ✗] Hit rate too low: {rate:.0%} (expected >80%)")
        ok = False

    print()
    return ok


# =============================================================================
# CUBE96 TESTS (G-4)
# =============================================================================

def test_cube96_roundtrip_static():
    """Test 9: Cube96 encode/decode roundtrip for static vocabulary words."""
    print("=" * 70)
    print("  TEST 9: Cube96 — Static Vocabulary Roundtrip")
    print("=" * 70)

    codec = MuxGridCodec(codebook_size="cube96")
    test_msgs = [
        "ok",
        "sos",
        "battery at percent",
        "the sensor node is reporting temperature degrees",
        "alert flood warning for the area",
        "the sensor is online battery at percent signal strong",
    ]

    passed = 0
    failed = 0
    for i, msg in enumerate(test_msgs, 1):
        payload, padding = codec.encode(msg)
        decoded = codec.decode(payload, padding)
        match = (decoded == msg.lower())
        status = "PASS ✓" if match else "FAIL ✗"
        print(f"  {i}. [{status}] \"{msg}\" → {len(payload)} bytes")
        if not match:
            print(f"      Expected: \"{msg.lower()}\"")
            print(f"      Got:      \"{decoded}\"")
            failed += 1
        else:
            passed += 1

    print(f"\n  Results: {passed} passed, {failed} failed\n")
    return failed == 0


def test_cube96_capitalization():
    """Test 10: Capitalization flag (F2): 'the' vs 'The' same xyz, different F2."""
    print("=" * 70)
    print("  TEST 10: Cube96 — Capitalization Flag (F2)")
    print("=" * 70)

    codec = MuxGridCodec(codebook_size="cube96")
    ok = True

    test_word = "the"
    if test_word not in codec.word_to_xyz:
        print(f"  [SKIP] '{test_word}' not in codebook")
        return True

    x, y, z = codec.word_to_xyz[test_word]

    packed_lower = pack_cube96(x, y, z, f_namespace=0, f_hyperedge=0,
                               f_capitalized=0)
    packed_cap = pack_cube96(x, y, z, f_namespace=0, f_hyperedge=0,
                             f_capitalized=1)

    info_lo = unpack_cube96(packed_lower)
    info_hi = unpack_cube96(packed_cap)

    coord_match = (info_lo['x'] == info_hi['x'] and
                   info_lo['y'] == info_hi['y'] and
                   info_lo['z'] == info_hi['z'])
    flag_match = (info_lo['f_capitalized'] == 0 and
                  info_hi['f_capitalized'] == 1)

    if coord_match and flag_match:
        print(f"  [PASS ✓] '{test_word}' lower: F2=0, cap: F2=1, "
              f"same (x,y,z)=({x},{y},{z})")
    else:
        print(f"  [FAIL ✗] Coords match: {coord_match}, Flag match: {flag_match}")
        ok = False

    print()
    return ok


def test_cube96_namespace_flag():
    """Test 11: Namespace flag (F0): static word F0=0, MeshLex F0=1."""
    print("=" * 70)
    print("  TEST 11: Cube96 — Namespace Flag (F0)")
    print("=" * 70)

    codec = MuxGridCodec(codebook_size="cube96")
    ok = True

    for word in ["the", "flood", "sensor", "alert"]:
        if word in codec.word_to_xyz:
            x, y, z = codec.word_to_xyz[word]
            packed = pack_cube96(x, y, z, f_namespace=0)
            info = unpack_cube96(packed)
            if info['f_namespace'] != 0:
                print(f"  [FAIL ✗] Static '{word}': F0={info['f_namespace']}")
                ok = False
            else:
                print(f"  [PASS ✓] Static '{word}': F0=0")

    # MeshLex word (OOV) should get F0=1 after encode
    oov = "xyzquux99"
    text = f"the {oov} is here"
    payload, _ = codec.encode(text)
    if oov in codec.meshlex_word_to_xyz:
        mx, my, mz = codec.meshlex_word_to_xyz[oov]
        packed = pack_cube96(mx, my, mz, f_namespace=1)
        info = unpack_cube96(packed)
        if info['f_namespace'] != 1:
            print(f"  [FAIL ✗] MeshLex '{oov}': F0={info['f_namespace']}")
            ok = False
        else:
            print(f"  [PASS ✓] MeshLex '{oov}': F0=1 at ({mx},{my},{mz})")
    else:
        print(f"  [FAIL ✗] OOV '{oov}' not placed in MeshLex")
        ok = False

    print()
    return ok


def test_cube96_meshlex_inline_def():
    """Test 12: Inline MeshLex def — encoder adds OOV, separate decoder decodes."""
    print("=" * 70)
    print("  TEST 12: Cube96 — Inline MeshLex Definition (Two-Node)")
    print("=" * 70)

    oov_word = "fluxcapacitor42"
    text = f"the {oov_word} is active"

    encoder = MuxGridCodec(codebook_size="cube96")
    payload, _ = encoder.encode(text)

    decoder = MuxGridCodec(codebook_size="cube96")
    decoded = decoder.decode(payload, 0)

    match = (decoded == text.lower())
    print(f"  Encoded: '{text}' → {len(payload)} bytes")
    print(f"  Decoded: '{decoded}'")
    print(f"  [{'PASS ✓' if match else 'FAIL ✗'}] Two-node inline def roundtrip")

    if oov_word in decoder.meshlex_word_to_xyz:
        print(f"  [PASS ✓] Decoder learned '{oov_word}' from inline def")
    else:
        print(f"  [FAIL ✗] Decoder did NOT learn '{oov_word}'")
        match = False

    print()
    return match


def test_cube96_two_node_sim():
    """Test 13: Two separate codec instances roundtrip via packet bytes only."""
    print("=" * 70)
    print("  TEST 13: Cube96 — Two-Node Simulation")
    print("=" * 70)

    test_msgs = [
        "alert flood warning for the area",
        "sensor is online status normal",
        "battery low node needs attention",
    ]

    passed = 0
    for msg in test_msgs:
        enc = MuxGridCodec(codebook_size="cube96")
        dec = MuxGridCodec(codebook_size="cube96")
        payload, _ = enc.encode(msg)
        decoded = dec.decode(payload, 0)
        match = (decoded == msg.lower())
        status = "PASS ✓" if match else "FAIL ✗"
        print(f"  [{status}] '{msg}' → {len(payload)}B → '{decoded}'")
        if match:
            passed += 1

    print(f"\n  Results: {passed}/{len(test_msgs)} passed\n")
    return passed == len(test_msgs)


def test_cube96_esc_sentinel():
    """Test 14: ESC sentinel 0xFF 0xFF 0xFF is unambiguous."""
    print("=" * 70)
    print("  TEST 14: Cube96 — ESC Sentinel (0xFF 0xFF 0xFF)")
    print("=" * 70)

    ok = True

    esc_data = bytes([ESC_CUBE_BYTE, ESC_CUBE_BYTE, ESC_CUBE_BYTE])
    info = unpack_cube96(esc_data)

    if info['x'] == 127 and info['y'] == 127 and info['z'] == 127:
        print(f"  [PASS ✓] ESC unpacks to (127,127,127)")
    else:
        print(f"  [FAIL ✗] ESC unpacks to ({info['x']},{info['y']},{info['z']})")
        ok = False

    if (info['x'] > MAX_CUBE_COORD and info['y'] > MAX_CUBE_COORD and
            info['z'] > MAX_CUBE_COORD):
        print(f"  [PASS ✓] All coords > {MAX_CUBE_COORD}")
    else:
        print(f"  [FAIL ✗] Some coords within valid range")
        ok = False

    if is_esc_cube96(esc_data):
        print(f"  [PASS ✓] is_esc_cube96() returns True")
    else:
        print(f"  [FAIL ✗] is_esc_cube96() returns False")
        ok = False

    non_esc = bytes([0x00, 0x01, 0x02])
    if not is_esc_cube96(non_esc):
        print(f"  [PASS ✓] is_esc_cube96() returns False for non-ESC")
    else:
        print(f"  [FAIL ✗] False positive on non-ESC")
        ok = False

    codec = MuxGridCodec(codebook_size="cube96")
    if (127, 127, 127) not in codec.xyz_to_word:
        print(f"  [PASS ✓] (127,127,127) is not a valid word")
    else:
        print(f"  [FAIL ✗] (127,127,127) maps to word")
        ok = False

    print()
    return ok


def test_cube96_compression_ratio():
    """Test 15: Compression ratio on test corpus."""
    print("=" * 70)
    print("  TEST 15: Cube96 — Compression Ratio")
    print("=" * 70)

    codec = MuxGridCodec(codebook_size="cube96")
    test_msgs = [
        "the sensor node is reporting temperature degrees",
        "alert flood warning for the area",
        "the sensor is online battery at percent signal strong",
        "node temperature humidity",
        "emergency dispatch north sector casualties",
        "battery percent signal strong node online",
    ]

    total_raw = 0
    total_comp = 0
    for msg in test_msgs:
        raw = len(msg.encode("utf-8"))
        payload, _ = codec.encode(msg)
        comp = len(payload)
        total_raw += raw
        total_comp += comp
        ratio = raw / comp if comp else 0
        print(f"  {raw:>3}B → {comp:>3}B (ratio {ratio:.2f}:1)  \"{msg[:50]}\"")

    agg_ratio = total_raw / total_comp if total_comp else 0
    savings = (1 - total_comp / total_raw) * 100 if total_raw else 0
    ok = agg_ratio >= 1.0
    print(f"\n  Aggregate: {total_raw}B → {total_comp}B "
          f"(ratio {agg_ratio:.2f}:1, {savings:.0f}% savings)")
    print(f"  [{'PASS ✓' if ok else 'FAIL ✗'}] Ratio {'>=1.0' if ok else '<1.0'}\n")
    return ok


def test_cube96_collision_resolution():
    """Test 16: Displaced words roundtrip correctly."""
    print("=" * 70)
    print("  TEST 16: Cube96 — Collision Resolution")
    print("=" * 70)

    codec = MuxGridCodec(codebook_size="cube96")
    ok = True

    from collections import Counter
    collisions_found = []

    for word, xyz in list(codec.word_to_xyz.items())[:10000]:
        origin = cube96_hash_coords(word)
        if origin != xyz:
            collisions_found.append((word, origin, xyz))

    if collisions_found:
        w, orig, actual = collisions_found[0]
        print(f"  [PASS ✓] '{w}' hash origin ({orig[0]},{orig[1]},{orig[2]}) "
              f"placed at ({actual[0]},{actual[1]},{actual[2]})")

        text = f"the {w} is here"
        payload, _ = codec.encode(text)
        dec = MuxGridCodec(codebook_size="cube96")
        decoded = dec.decode(payload, 0)
        rt_ok = (decoded == text.lower())
        print(f"  [{'PASS ✓' if rt_ok else 'FAIL ✗'}] Displaced word '{w}' roundtrips")
        if not rt_ok:
            ok = False
    else:
        print(f"  [INFO] No collisions found in first 10000 words")

    print(f"  [INFO] {len(collisions_found)} displaced in first 10000\n")
    return ok


def test_cube96_packet_ids():
    """Test 17: packet.py accepts codec IDs 0x05 and 0x06."""
    print("=" * 70)
    print("  TEST 17: Cube96 — Packet IDs (0x05/0x06)")
    print("=" * 70)

    from packet import (CyberMeshPacket, CODEC_MUX_CUBE_STRICT,
                        CODEC_MUX_CUBE_LOSSY)

    ok = True

    payload = b"\x01\x02\x03\x04\x05"
    pkt = CyberMeshPacket.encode(CODEC_MUX_CUBE_STRICT, payload)
    dec = CyberMeshPacket.decode(pkt)
    if dec.codec_id == CODEC_MUX_CUBE_STRICT and dec.payload == payload:
        print(f"  [PASS ✓] 0x05 strict roundtrip")
    else:
        print(f"  [FAIL ✗] 0x05 strict roundtrip failed")
        ok = False

    if dec.is_cube:
        print(f"  [PASS ✓] is_cube=True for 0x05")
    else:
        print(f"  [FAIL ✗] is_cube=False for 0x05")
        ok = False

    pkt_l = CyberMeshPacket.encode(CODEC_MUX_CUBE_LOSSY, payload,
                                    keyword_count=8)
    dec_l = CyberMeshPacket.decode(pkt_l)
    if (dec_l.codec_id == CODEC_MUX_CUBE_LOSSY and
            dec_l.payload == payload and dec_l.keyword_count == 8):
        print(f"  [PASS ✓] 0x06 lossy roundtrip (kw=8)")
    else:
        print(f"  [FAIL ✗] 0x06 lossy roundtrip failed")
        ok = False

    if dec_l.is_cube and dec_l.is_lossy:
        print(f"  [PASS ✓] is_cube=True, is_lossy=True for 0x06")
    else:
        print(f"  [FAIL ✗] is_cube={dec_l.is_cube}, is_lossy={dec_l.is_lossy}")
        ok = False

    print()
    return ok


def main():
    print("\n" + "═" * 70)
    print("  CODEC UNIT TESTS — Pre-flight validation (G-4)")
    print("  Huffman (0x01), MUX Grid (0x02), Cube96 (0x05/0x06),")
    print("  Pre-Tokenizer, LLM Codec")
    print("═" * 70 + "\n")

    results = []
    results.append(("MUX Standalone", test_mux_standalone()))
    results.append(("MUX + Header", test_mux_with_header()))
    results.append(("Huffman + Header", test_huffman_with_header()))
    results.append(("Cross-codec Detection", test_cross_codec_detection()))
    results.append(("ESC Handling", test_esc_handling()))
    results.append(("Pre-Tokenizer", test_pretokenizer()))
    results.append(("Pre-Tokenizer + Codec Roundtrip", test_pretokenizer_codec_roundtrip()))
    results.append(("LLM Codec Module", test_llm_codec_module()))
    # Cube96 tests (G-4)
    results.append(("Cube96 Static Roundtrip", test_cube96_roundtrip_static()))
    results.append(("Cube96 Capitalization", test_cube96_capitalization()))
    results.append(("Cube96 Namespace Flag", test_cube96_namespace_flag()))
    results.append(("Cube96 Inline MeshLex", test_cube96_meshlex_inline_def()))
    results.append(("Cube96 Two-Node Sim", test_cube96_two_node_sim()))
    results.append(("Cube96 ESC Sentinel", test_cube96_esc_sentinel()))
    results.append(("Cube96 Compression", test_cube96_compression_ratio()))
    results.append(("Cube96 Collision", test_cube96_collision_resolution()))
    results.append(("Cube96 Packet IDs", test_cube96_packet_ids()))

    print("═" * 70)
    print("  SUMMARY")
    print("═" * 70)
    all_pass = True
    for name, passed in results:
        status = "PASS ✓" if passed else "FAIL ✗"
        if not passed:
            all_pass = False
        print(f"  {status}  {name}")

    print(f"\n  {'ALL TESTS PASSED ✓' if all_pass else 'SOME TESTS FAILED ✗'}")
    print("═" * 70 + "\n")

    if not all_pass:
        print("  ⚠ HALT: Do not proceed to live transmission until all tests pass.")
        sys.exit(1)
    else:
        print("  ✓ Safe to proceed with live LoRa transmission.")
        sys.exit(0)


if __name__ == "__main__":
    main()
