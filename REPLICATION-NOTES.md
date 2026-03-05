---
title: "Replication Notes — CyberMesh Codec POC"
version: 6.0.0
date: 2026-03-05
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

### Experiment C (LLM conversation — Ollama, legacy) — Additional Steps
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

### Experiment E — Lemonade Server + Liquid LFM2.5 1.2B Backend
- [ ] All Experiment D prerequisites above are met (except Ollama-specific steps)
- [ ] Lemonade Server installed and running on both laptops
- [ ] Liquid LFM2.5 1.2B model loaded in Lemonade, aliased as `test01`
- [ ] Verify: `curl http://localhost:8000/api/generate -d '{"model":"test01","prompt":"hello"}'` returns valid JSON
- [ ] `config.yaml` has `model_name: "test01"` and `llm_base_url: "http://localhost:8000"`
- [ ] Both laptops use identical `config.yaml` (same model_name and llm_base_url)
- [ ] `pip install requests` on both laptops (same dep as before)
- [ ] Run unit tests: `python test_codecs.py` — all 8 suites must pass
- [ ] One "Hi" trigger runs both codecs with Lemonade-backed LLM pipeline
- [ ] Verify console logs show `test01` as the model name (not `gemma3:latest`)
- [ ] **Hot-swap note**: To change models, edit only `model_name` in `config.yaml`. No code changes needed.

### Experiment F — Codec Harness Validation
- [ ] All Experiment E prerequisites above are met
- [ ] `experiment_f/` directory exists with 7 files (see TESTING-PROTOCOL.md)
- [ ] `mux_codebook.csv` accessible at `../mux_codebook.csv` from `experiment_f/`
- [ ] Lemonade Server running at `http://localhost:8000` with model `test01`
- [ ] Python 3.10+ with `requests` and `pyyaml` installed
- [ ] Sanity check: `cd experiment_f && python harness.py --mode sanity-check` passes
- [ ] Full run: `python harness.py --mode full` (runs 80 tests: 20 encode + 20 decode + 40 stress)
- [ ] Review `test_report.md` for issue gate pass/fail
- [ ] Run on BOTH nodes (Nvidia + Strix Halo) for cross-hardware comparison
- [ ] Compare results against Experiment E baselines (hit rate, latency)

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
requests>=2.28.0     # Experiments C–E: LLM API (Ollama or Lemonade)
```

Additional for Experiments C & D (Ollama backend — legacy):
- Ollama with `gemma3:latest` model pre-pulled on both machines

Additional for Experiment E (Lemonade backend — current):
- Lemonade Server running on both machines (default port 8000)
- Liquid LFM2.5 1.2B model loaded and aliased as `test01`
- Lemonade exposes Ollama-compatible `/api/generate` endpoint natively

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
- Experiments C & D (legacy): Ollama must be running at `localhost:11434` before starting script
- Experiment E (current): Lemonade Server must be running at URL specified in `config.yaml` → `llm_base_url` (default `http://localhost:8000`)
- Experiment D Phase 2: expect ~5 seconds per message turn (3 LLM inference calls)
- Experiment E: Liquid LFM2.5 1.2B on NPU may have different inference timing — log and compare

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

## Backend Control (Experiment E)

Set in `config.yaml` before starting:

```yaml
model_name: "test01"                        # Hot-swap: change this to switch models
llm_base_url: "http://localhost:8000"       # Lemonade default port
experiment: "E"                             # Experiment label for logs
```

**Hot-swap workflow**: To test a different model, edit only `model_name` in `config.yaml`
and restart the script. No code changes required. Both laptops must use the same
`model_name` value.

**Backend note**: Lemonade Server exposes an Ollama-compatible `/api/generate` endpoint.
The same API call pattern from Experiments C–D works unchanged. The `llm_base_url`
variable replaces the hardcoded Ollama URL.

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

### Experiment E — Lemonade Server + Liquid LFM2.5 1.2B (Both Codecs)

| Run | Date | Backend | Model | Codec | Node A | Node B | Messages | Delivery | Avg Ratio | Hit% | Avg ESC | FB | Notes |
|-----|------|---------|-------|-------|--------|--------|----------|----------|-----------|------|---------|-----|-------|
| 1 | 2026-03-05 | Lemonade | test01 | MUX Grid | !07c01855 (Role A) | !0408a160 (Role B) | 20/20 | 20/20 | 1.79:1 | 79.5% | 2.6 | 3/20 | Phase 2 (LLM Codec ON), 0 timeouts |
| 1 | 2026-03-05 | Lemonade | test01 | Huffman (4K) | !07c01855 (Role A) | !0408a160 (Role B) | 20/20 | 20/20 | 1.94:1 | 83.5% | 2.6 | 4/20 | Phase 2 (LLM Codec ON), 0 timeouts |

Exp E winner: **Huffman (4K)** — 8% better compression, 4pp higher hit rate. Consistent with Exp C.

Exp E vs Exp C (LLM codec effect): MUX ratio +35% (1.33→1.79), Huffman ratio +20% (1.61→1.94).
MUX hit rate +18pp (61.3%→79.5%), Huffman hit rate +2.5pp (80.9%→83.5%).

**Hardware inference comparison (Experiment E):**

| Metric | Strix Halo (Role B) | Nvidia (Role A) | Ratio |
|--------|--------------------|-----------------|---------|
| MUX Generate | 2,114ms | 389ms | 5.4x |
| MUX Encode | 1,810ms | 354ms | 5.1x |
| Huff Generate | 1,476ms | 306ms | 4.8x |
| Huff Encode | 1,222ms | 245ms | 5.0x |

**Known issues from Run 1:**
1. Meta-loop collapse: model fell into "Would you like me to rewrite..." loop (MUX run)
2. LLM encode hallucination: model output meta-text ("Translated to Spanish:") instead of codebook rewrite
3. LLM decode noise: model added parenthetical notes instead of expanding text
4. System prompt and encode/decode prompts need hardening for LFM2.5 1.2B

#### Run 2 — Phase 1 (Pre-Tokenizer) + Phase 2 (LLM Codec)

| Run | Date | Phase | Codec | Node | Role | Msgs | Ratio | Hit% | ESC | Gen(ms) | Enc(ms) | Dec(ms) | FB | Notes |
|-----|------|-------|-------|------|------|------|-------|------|-----|---------|---------|---------|-----|-------|
| 2 | 2026-03-05 | P1 | MUX | Nvidia | A | 10/10 | 2.17:1 | 82.5% | 2.4 | 544 | — | — | — | Clean transport |
| 2 | 2026-03-05 | P1 | MUX | Strix | B | 10/10 | 2.42:1 | 92.5% | 1.8 | 1526 | — | — | — | Generate repetition (msgs 3-13 identical) |
| 2 | 2026-03-05 | P1 | Huff | Nvidia | A | 10/10 | 1.90:1 | 90.3% | 1.0 | 512 | — | — | — | 2 empty generates (0 tokens) |
| 2 | 2026-03-05 | P1 | Huff | Strix | B | 10/10 | 2.64:1 | 96.1% | 0.6 | 1350 | — | — | — | Generate convergence (msgs 7-19) |
| 2 | 2026-03-05 | P2 | MUX | Nvidia | A | 10/10 | 2.47:1 | 93.4% | 0.8 | 363 | 222 | 463 | 2/10 | 5 meta-loops, 3 framing, 5 decode noise |
| 2 | 2026-03-05 | P2 | MUX | Strix | B | 10/10 | 1.81:1 | 79.4% | 4.8 | 1345 | 1718 | 1437 | 0/10 | Received Nvidia meta-loop outputs |
| 2 | 2026-03-05 | P2 | Huff | Nvidia | A | 10/10 | 2.04:1 | 91.1% | 0.8 | 115 | 305 | 396 | 0/10 | SEVERE: 8/10 generates = "1 short response." |
| 2 | 2026-03-05 | P2 | Huff | Strix | B | 10/10 | 1.92:1 | 80.7% | 3.5 | 1448 | 1577 | 1256 | 0/10 | Encode repetition, 2 empty generates |

**Run 2 hardware comparison:**

| Pipeline Step | Nvidia (ms) | Strix (ms) | Nvidia Advantage |
|---------------|------------|------------|------------------|
| P1 MUX Generate | 544 | 1,526 | 2.8x |
| P1 Huff Generate | 512 | 1,350 | 2.6x |
| P2 MUX Generate | 363 | 1,345 | 3.7x |
| P2 MUX Encode | 222 | 1,718 | 7.7x |
| P2 Huff Generate | 115 | 1,448 | 12.6x |
| P2 Huff Encode | 305 | 1,577 | 5.2x |

**Run 2 issues (4 total, 1 NEW):**

1. **Issue #1 — Meta-loop collapse** (10 instances across both nodes):
   - Nvidia MUX P2: 5 instances ("Would you like...", "If you meant...", "But you want...")
   - Nvidia Huff P2: 4 instances ("I will provide...", "You're asking for...")
   - Strix Huff P2: 1 instance ("It seems like your message might be incomplete...")
   - Severity: CRITICAL — affects encoded output, propagates to peer node

2. **Issue #2 — Encode framing** (6 instances, Nvidia only):
   - Nvidia MUX P2: "Translation:", "Explanation:", "---"
   - Nvidia Huff P2: "Answer:", "I understand your request..."
   - Strix: 0 framing artifacts

3. **Issue #3 — Decode noise** (14 instances):
   - Nvidia MUX P2: 5x "(Word count: N)"
   - Nvidia Huff P2: 5x "(Word count: N)", 1x "Expanded: ..."
   - Strix MUX P2: 4x meta-commentary from decoding Nvidia's meta-loop outputs

4. **Issue #4 — Generate collapse** (NEW, pervasive):
   - Nvidia Huff P2: 8/10 generates = "1 short response." (complete model collapse)
   - Strix P1 MUX: msgs 3-13 near-identical text
   - Strix P2 MUX+Huff: msgs 3-17 all "The flood warning is active..." repeated
   - Both nodes: empty generates (0 tokens) on multiple occasions
   - Root cause: repetition_penalty=1.05 insufficient for conversation-level diversity
   - Impact: Experiment F soul prompts address encode/decode but not generate step

### Experiment F — Codec Harness Validation

| Run | Date | Backend | Model | Mode | Tests | Passed | Failed | Pass Rate | Avg Latency | Notes |
|-----|------|---------|-------|------|-------|--------|--------|-----------|-------------|-------|
| — | — | — | — | — | — | — | — | — | — | Built, ready for live test |

*Append results after each experiment run.*
