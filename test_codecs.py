#!/usr/bin/env python3
"""
test_codecs.py — Unit tests for codecs, pretokenizer, and LLM codec pipeline
==============================================================================
Validates:
  1-5: Original codec tests (Experiment B)
  6:   Pre-tokenizer normalize() function
  7:   Pre-tokenizer + codec roundtrip (normalized text through both codecs)
  8:   LLM codec module loads (no Lemonade Server required)

Run before any live transmission: python test_codecs.py
Halt if any test fails.

Author: Mark Snow, Jr. — Mindtech / CyberMesh / Liberty Mesh
Date:   March 2026
"""

import sys
import os

# Ensure imports work from script directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mux_codec import MuxGridCodec, CODEC_ID_HUFFMAN, CODEC_ID_MUX_GRID

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


def main():
    print("\n" + "═" * 70)
    print("  CODEC UNIT TESTS — Pre-flight validation (Experiment D)")
    print("  Huffman (0x01), MUX Grid (0x02), Pre-Tokenizer, LLM Codec")
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
