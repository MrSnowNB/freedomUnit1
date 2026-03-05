---
title: "Replication Notes — CyberMesh Codec POC"
version: 4.0.0
date: 2026-03-04
status: active
project: huffman-mesh-poc
---

# Replication Notes

Living document for reproducing this experiment. Updated after every run.

---

## Replicable Setup Checklist

### Experiments A & B (scripted messages)
- [ ] Python 3.10+ installed on both laptops
- [ ] `pip install meshtastic pyyaml` on both laptops
- [ ] Both Heltec V3 nodes flashed with same Meshtastic firmware version
- [ ] Both nodes on same LongFast channel (default channel 0)
- [ ] Both nodes can exchange DMs (verify manually before running script)
- [ ] Copy entire `huffman-mesh-poc/` directory to both laptops
- [ ] Verify `config.yaml` codec selection is the same on both laptops
- [ ] Plug one Heltec V3 into each laptop via USB
- [ ] Run `python huffman_mesh_poc.py` on both laptops
- [ ] Wait for "LISTENING" banner on both
- [ ] Send `Hi` as DM from one physical unit to the other
- [ ] Watch test execute and complete

### Experiment C (LLM conversation) — Additional Steps
- [ ] Ollama installed on both laptops
- [ ] `ollama pull gemma3:latest` on both laptops
- [ ] `pip install requests` on both laptops (for Ollama API)
- [ ] Verify `ollama run gemma3:latest` responds on both machines
- [ ] `config.yaml` has `model`, `conversation_seed`, `messages_per_node` fields
- [ ] Start Ollama service before running the script (`ollama serve`)
- [ ] Script will warm up the model automatically on startup
- [ ] One "Hi" trigger runs BOTH codec runs (MUX Grid then Huffman) sequentially

### Experiment D — Phase 1 (Pre-Tokenizer) — Additional Steps
- [ ] All Experiment C prerequisites above are met
- [ ] `config.yaml` set: `pretokenizer: true`, `llm_codec: false`
- [ ] Verify `pretokenizer.py` is in the repo directory on both laptops
- [ ] Run unit tests: `python test_codecs.py` — all 8 suites must pass
- [ ] One "Hi" trigger runs both codecs with pre-tokenizer normalization
- [ ] Check console output for hit% column — should be >80%

### Experiment D — Phase 2 (LLM Encode/Decode) — Additional Steps
- [ ] All Phase 1 prerequisites above are met
- [ ] `config.yaml` set: `llm_codec: true`, `fallback_threshold: 0.70`
- [ ] Verify `llm_codec.py` is in the repo directory on both laptops
- [ ] Verify Ollama is running — LLM codec makes 2 calls per TX (generate + encode)
- [ ] Expect ~5s per message turn (3 LLM calls: generate, encode, decode)
- [ ] One "Hi" trigger runs both codecs with full LLM encode/decode pipeline
- [ ] Check console output for FB (fallback) column — should be mostly "N"
- [ ] If >30% fallbacks, the encode prompt needs rework — document and stop

## Hardware

| Item | Spec |
|------|------|
| Node A | Heltec V3 — Liberty-Node-02 (!0408a160), USB-C, LoRa 915 MHz |
| Node B | Heltec V3 — Liberty-Node-04 (!07c01855), USB-C, LoRa 915 MHz |
| Laptop A | Windows, AMD Strix Halo workstation, COM6 (auto-detect works) |
| Laptop B | Windows, COM3 (auto-detect works) |
| Distance | Same room for first test (range test later) |

## Software Dependencies

```
meshtastic>=2.0.0
pyyaml>=6.0
requests>=2.28.0     # Experiments C & D: Ollama API
```

Additional for Experiments C & D:
- Ollama with `gemma3:latest` model pre-pulled on both machines

Codecs use only stdlib:
- `mesh_huffman.py`: `csv`, `heapq`, `re`, `os`, `dataclasses`
- `mux_codec.py`: `csv`, `os`
- `paginator.py`: `textwrap`, `re`
- `pretokenizer.py`: `re` (stdlib only)
- `llm_codec.py`: `requests`, `json`, `csv`, `os`, `time`

## Environment Notes

- Windows: CP210x USB driver required for Heltec V3 serial
- If `SerialInterface()` fails, install driver from Silicon Labs
- Both machines must have the full repo directory (includes both codebooks)
- `huffman_codebook_4k.csv` must be in the same directory as `mesh_huffman.py` (v4+)
- `mux_codebook.csv` must be in the same directory as `mux_codec.py`
- `english_unigram_freq.csv` is only needed as legacy fallback if `huffman_codebook_4k.csv` is missing
- Experiments C & D: Ollama must be running at `localhost:11434` before starting script
- Experiment D Phase 2: expect ~5 seconds per message turn (3 LLM inference calls)

## Phase Control (Experiment D)

Set in `config.yaml` before starting:

```yaml
pretokenizer: true         # Always on for Experiment D
llm_codec: false           # Phase 1 only (pretokenizer + raw codec)
# llm_codec: true          # Phase 2 (pretokenizer + LLM encode/decode + codec)
fallback_threshold: 0.70   # Phase 2 only: skip encode if hit rate < 70%
```

**Phase 1 behavior:** LLM generates text → pre-tokenizer normalizes → codec encodes.
Same as Experiment C but with normalization fixing ESC-triggering patterns.

**Phase 2 behavior:** LLM generates text → LLM rewrites using codebook words →
pre-tokenizer normalizes → codec encodes. Receiver: codec decodes → LLM expands
compressed text to natural English → conversation history.

Both laptops must use the same `llm_codec` setting.

## Known Pitfalls to Avoid

1. **Don't filter by channel index** — use portnum filtering instead
   (see TROUBLESHOOTING.md Issue 004)
2. **Don't compare fromId string to myNodeNum int directly** — convert first
   (see TROUBLESHOOTING.md Issue 003)
3. **Don't run multiple serial-connected scripts** — one script per node per
   laptop. Two scripts fighting for the same serial port will crash.
4. **Don't send `Hi` before both scripts are in LISTENING state** — the trigger
   will be missed
5. **Don't use `sendText()` for compressed data** — UTF-8 encoding will corrupt
   raw bytes. Use `sendData()` with custom portnum.
6. **Always pass destinationId as hex string** — `"!07c01855"` not int.
   Int conversion silently fails routing (see TROUBLESHOOTING.md Issue 006).
7. **Portnum arrives as `"PRIVATE_APP"` not `"256"`** — check the enum name
   string, not the integer (see TROUBLESHOOTING.md Issue 007).
8. **Don't paste full 4,096-word list into LLM encode prompt** — Gemma3 4B has
   limited context. Use top 500 words as examples (see `llm_codec.py`).
9. **Don't increase timeout unless testing shows >30s round trips** — the 45s
   budget fits the 3-call LLM pipeline comfortably.
10. **Check fallback rate after Phase 2 run** — if >30% of messages trigger
    fallback, the encode prompt needs rework before continuing.

## Test Results Log

### Experiment A — Huffman Codec

| Run | Date | Node A | Node B | Messages | Roundtrip | Avg Ratio | Notes |
|-----|------|--------|--------|----------|-----------|-----------|-------|
| 1 | 2026-03-04 | !0408a160 | !07c01855 | 6/8 RX'd | 6/6 perfect | ~2.5:1 | 2 missed from timing race, 0 codec errors |

### Experiment B — MUX Grid Codec

| Run | Date | Node A | Node B | Messages | Roundtrip | Avg Ratio | Notes |
|-----|------|--------|--------|----------|-----------|-----------|-------|
| — | — | — | — | — | — | — | Unit tests pass, awaiting live LoRa test |
| 1 | 2026-03-04 | !07c01855 | !0408a160 | 8/8 | 8/8 perfect | 2.34:1 | v2.1 reactive sync, 0 timeouts, 0 codec errors |

### Experiment C — LLM Conversation (Both Codecs)

| Run | Date | Codec | Node A | Node B | Messages | Delivery | Avg Ratio | Hit% | Avg ESC | Notes |
|-----|------|-------|--------|--------|----------|----------|-----------|------|---------|-------|
| 1 | 2026-03-04 | MUX Grid | !07c01855 (Role A) | !0408a160 (Role B) | 20/20 | 20/20 | 1.33:1 | 61.3% | 4.4 | 0 timeouts, 0 errors |
| 1 | 2026-03-04 | Huffman (4K) | !07c01855 (Role A) | !0408a160 (Role B) | 20/20 | 20/20 | 1.61:1 | 80.9% | 2.4 | 0 timeouts, 0 errors |

Exp C winner: **Huffman (4K)** — 21% better compression, 20pp higher hit rate on LLM-generated text.
Exp B winner was MUX Grid (2.34:1 vs 1.51:1 on scripted text) — codecs have complementary strengths.

### Experiment D — Phase 1 (Pre-Tokenizer + Both Codecs)

| Run | Date | Codec | Node A | Node B | Messages | Delivery | Avg Ratio | Hit% | Avg ESC | Notes |
|-----|------|-------|--------|--------|----------|----------|-----------|------|---------|-------|
| — | — | — | — | — | — | — | — | — | — | Built, ready for live test |

### Experiment D — Phase 2 (LLM Encode/Decode + Both Codecs)

| Run | Date | Codec | Node A | Node B | Messages | Delivery | Avg Ratio | Hit% | Avg ESC | Fallback% | Notes |
|-----|------|-------|--------|--------|----------|----------|-----------|------|---------|-----------|-------|
| — | — | — | — | — | — | — | — | — | — | — | Built, ready for live test |

*Append results after each experiment run.*
