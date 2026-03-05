---
title: "CyberMesh Codec POC — Experiment Design"
version: 4.0.0
date: 2026-03-04
status: approved
lifecycle_stage: build
owner: "Mark Snow, Jr. — Mindtech / CyberMesh"
project: huffman-mesh-poc
scope: "Prove dual-codec compress → LoRa transmit → decompress roundtrip, LLM conversation, and LLM-as-codec"
hardware:
  node_a: "Heltec V3 — Liberty-Node-02 (!0408a160)"
  node_b: "Heltec V3 — Liberty-Node-04 (!07c01855)"
  laptops: 2
software:
  python: ">=3.10"
  meshtastic: ">=2.0"
  ollama: "gemma3:latest (4B)"
  codecs:
    huffman: "mesh_huffman.py v4 (4,095-word shared codebook)"
    mux_grid: "mux_codec.py (4,096-entry 64×64 grid codebook)"
---

# CyberMesh Codec POC — Experiment Design

## Overview

Four-experiment POC proving text compression over LoRa mesh radio, progressing
from scripted messages (A/B) to live LLM conversation (C) to LLM-as-codec (D).
All experiments share the same hardware, trigger mechanism, and shared 4,096-word
codebook. Each experiment isolates a single variable.

| Experiment | Codec | Codebook | Status |
|-----------|-------|----------|--------|
| A | Huffman (word-level, variable-length) | 2,048 words | Validated over live LoRa |
| B | MUX Grid (tiered fixed-width index) | 4,002 entries | Validated over live LoRa (8/8, 2.34:1) |
| C | Both codecs, LLM conversation | 4,096 shared (64×64) | Validated: 40/40, Huffman 1.61:1 vs MUX 1.33:1 |
| D-Ph1 | Pre-tokenizer + both codecs, LLM conversation | 4,096 shared | Built, ready for live test |
| D-Ph2 | LLM encode/decode + both codecs | 4,096 shared | Built, ready for live test |

---

## Experiment A — Huffman Codec

### Objective

Prove that word-level Huffman compression works end-to-end over LoRa:

1. Compress a text message on Laptop A using `MeshHuffmanCodec`
2. Transmit the raw compressed bytes over Meshtastic serial → LoRa → serial
3. Decompress on Laptop B using the same static codebook
4. Verify roundtrip fidelity (decoded == original)
5. Log compression ratio, byte savings, RSSI, SNR, and latency

### Codec: `mesh_huffman.py` v3

- 2,048-word codebook from Kaggle Google Trillion Word Corpus + mesh domain vocabulary
- Variable-length Huffman codes — frequent words get shorter codes
- Implicit spaces between tokens (1-bit NOSPACE flag for exceptions)
- Case encoding: 1-bit lowercase, 2-bit capitalized/UPPER
- Number encoding: variable-width binary (8/16/32 bit)
- Unknown words: ESC + 5-bit length + 7-bit ASCII fallback
- 100% roundtrip on all 28 validation messages

### Experiment A Result

Validated over live LoRa on 2026-03-04. 6 of 8 messages roundtripped
perfectly; 2 missed from startup timing race (not codec failures).
Zero codec errors on any received packet. AI-constrained message:
56B → 17B (3.29:1). RSSI: -27 to -36 dBm, SNR: 5.25-6.75 dB.

---

## Experiment B — MUX Grid Codec

### Objective

Test a second codec method over the same hardware and message set.
Compare byte-for-byte against Huffman to determine which approach
performs better for mesh LoRa text compression.

1. Compress using `MuxGridCodec` (tiered fixed-width index encoding)
2. Transmit via same `sendData(portNum=256)` transport
3. Decompress using the same shared codebook
4. Verify roundtrip fidelity (case-insensitive — MUX Grid lowercases)
5. Compare compression ratios head-to-head against Experiment A

### Codec: `mux_codec.py`

- 4,002-entry frequency-sorted codebook (`mux_codebook.csv`)
  - 3,890 words from Kaggle frequency data
  - 101 numbers (0-100)
  - 10 mesh domain terms (sensor, battery, node, etc.)
  - Index 4095 = ESC sentinel for out-of-codebook words
- Tiered bit packing (variable-width by frequency rank):
  - Tier 0: indices 0-127 → 7 bits (most frequent 128 words)
  - Tier 1: indices 128-1023 → 10 bits
  - Tier 2: indices 1024-4095 → 14 bits
- ESC fallback: 14-bit ESC marker + 5-bit length + 7-bit ASCII per char
- Case-insensitive: all text lowercased at encode time

### PPA Linkage

- Codec ID byte (Byte 0 of 3-byte header) = first implementation of
  Adaptive Multiplexer (PPA Claim 24)
- Shared codebook = initial state analogous to SVD basis matrix (PPA §2.3)
- Tiered bit packing = bandwidth-adaptive encoding per PPA §3.1

### Unit Test Results (Local, No Radio)

| Message | Raw | MUX | Huffman+Hdr | MUX Winner? |
|---------|-----|-----|-------------|-------------|
| ok | 2B | 4B | 5B | No (3B header > payload) |
| SOS | 3B | 4B | 6B | No (3B header > payload) |
| Battery at 89 percent | 22B | 10B | 15B | Yes |
| Node 12 temperature 72 humidity 45 | 37B | 14B | 22B | Yes |
| The sensor node is... | 51B | 17B | 30B | Yes |
| Alert flood warning for the area | 32B | 12B | 21B | Yes |
| What time is it? | 16B | 10B | 14B | Yes |
| the sensor is online... | 52B | 21B | 29B | Yes |
| **Aggregate** | **215B** | **92B (2.34:1)** | **142B (1.51:1)** | **MUX wins 6/8** |

---

## Shared Design Elements

### Architecture

```
┌─────────────┐    LoRa 915 MHz    ┌─────────────┐
│  Laptop A   │◄──────────────────►│  Laptop B   │
│  COM auto   │                    │  COM auto   │
│  Heltec V3  │                    │  Heltec V3  │
│             │                    │             │
│  huffman_   │   sendData()       │  huffman_   │
│  mesh_poc.py│   portnum=256      │  mesh_poc.py│
│  +codecs    │   3-byte header    │  +codecs    │
└─────────────┘                    └─────────────┘
```

- Same Python script on both laptops
- Both codecs available; receiver auto-detects from Byte 0 (Codec ID)
- Zero codebook negotiation — both sides hold identical copies
- Transport: `sendData()` with custom `portNum=256` (raw bytes, not text)
- 3-byte packet header: `[Codec ID][Sequence][Padding]`
  - Codec ID: `0x01` = Huffman, `0x02` = MUX Grid
  - Sequence: 0-255 message counter
  - Padding: reserved for future use

### Trigger Mechanism

1. Both laptops start `huffman_mesh_poc.py` → enter listening mode
2. Operator sends `Hi` as a **DM** from one physical Heltec unit to the other
   - Standard Meshtastic DM, sent manually from the unit itself
   - Arrives as `portnum=TEXT_MESSAGE_APP (1)` on the receiving script
3. Receiving script detects `Hi`, stores sender as `peer_id`, enters test mode
4. Receiving script sends the first compressed test message to peer
5. First compressed message arriving at the other node triggers that script into test mode
6. Both nodes now alternate through the scripted message list

### Test Messages (Same for Both Experiments)

| Step | Direction | Message | Tests |
|------|-----------|---------|-------|
| 1 | B→A | `ok` | Minimum payload, single codebook word |
| 2 | A→B | `SOS` | Single uppercase word, case encoding |
| 3 | B→A | `Battery at 89 percent` | Mixed case + number encoding |
| 4 | A→B | `Node 12 temperature 72 humidity 45` | Multi-number, mesh domain words |
| 5 | B→A | `The sensor node is reporting temperature 94 degrees` | Full conversational sentence |
| 6 | A→B | `Alert flood warning for the area` | Emergency domain message |
| 7 | B→A | `What time is it?` | Punctuation handling |
| 8 | A→B | `the sensor is online battery at 89 percent signal strong` | AI-constrained (all lowercase, codebook-only) |

### Timing

- 3-second delay between send and next receive window
- 15-second timeout per message (log timeout, continue to next)
- No retries — this is a first-pass POC

### Logging

Each run produces `logs/experiment-log.md` with:
- YAML frontmatter: node IDs, codec used, codebook version, timestamp, pass/fail
- Per-message table: raw bytes, compressed bytes, ratio, roundtrip, RSSI, SNR, latency
- Aggregate stats: total compression, average ratio, overall pass/fail

### Success Criteria

- All 8 messages decompress to exact original text (100% roundtrip)
  - Experiment A: case-sensitive match
  - Experiment B: case-insensitive match (MUX Grid lowercases)
- Compressed bytes < raw bytes for messages with enough payload to justify header
- No serial or LoRa transport errors

### Failure Handling (POC Mode)

- On roundtrip failure: log the mismatch, continue the test
- On transport timeout: log the timeout, continue to next message
- After test: update TROUBLESHOOTING.md with any failures
- Full dataset always captured regardless of individual failures

## Future Iterations (Not This Test)

- Edge cases: out-of-codebook words, long messages, special characters
- Reliability: chunking protocol, CRC32 verification, retry logic
- Performance: latency benchmarks, throughput tests
- AI-constrained: LLM system prompt limiting output to codebook vocabulary
- Adaptive codec selection: auto-pick best codec per message at encode time
- SVD delta compression for AI state vectors (PPA §2 — separate experiment)

---

## Experiment C — LLM Conversation Over LoRa

### Objective

Run a 20-message live conversation (10 per node) between two Gemma3 4B instances
communicating over LoRa via Meshtastic. Messages generated by the LLM, compressed
by codec, transmitted over radio, decompressed, and fed back as conversation context.
Two sequential runs: MUX Grid first, then Huffman, both using the same 4,096-word
shared codebook. A genuine A/B comparison.

### Prerequisite: Shared 4,096-Word Codebook

Before Experiment C, both codecs were expanded to share identical vocabulary:
- `mux_codebook.csv` rebuilt to exactly 4,096 entries (64×64 grid)
- `huffman_codebook_4k.csv` built from same word list with Huffman tree
- `mesh_huffman.py` upgraded v3 → v4 to load 4K codebook
- All 8 original test messages pass roundtrip on both codecs (unit tested)

### Architecture

```
Node A/B:
  Gemma3 4B (Ollama) → generate response → paginate (max 200 chars)
  → encode (codec) → sendData(portNum=256) → LoRa
  → receive → decode → reassemble → conversation history → next LLM call
```

### Protocol

1. Both laptops start script, Ollama warms up Gemma3
2. One "Hi" DM triggers the full experiment
3. Run 1: MUX Grid — 20 messages with reactive sync
4. 5s pause
5. Run 2: Huffman — 20 messages with reactive sync
6. Comparison table generated

### Variables Under Test

- Codec performance under unpredictable LLM-generated vocabulary
- Codebook hit rate for natural Gemma3 output
- End-to-end pipeline: LLM → compress → transmit → decompress → LLM
- Paginator behavior with real LLM output lengths

### Controlled Variables

- Same 4,096-word codebook for both codecs
- Same model (gemma3:latest), same seed prompt, same hardware, same channel

### Logging

Per-message: step, direction, raw/compressed bytes, ratio, inference_ms, tokens,
pages, hit%, ESC count, RSSI, SNR, message preview.
Full conversation transcript with original and decoded text.
Comparison table: both codecs side by side.
JSON data dump for machine-readable analysis.

### Acceptance Criteria

- Pre-flight: unit tests pass on both codecs with shared codebook
- Live: at least 18/20 messages per run complete successfully (90%)
- Zero codec decode failures on received messages
- Full transcript + comparison table logged

### Unit Test Results (Local, 4K Shared Codebook)

| Message | Raw | Huffman 4K | MUX Grid | Huffman Winner? |
|---------|-----|-----------|----------|-----------------|
| ok | 2B | 4B | 5B | Yes |
| SOS | 3B | 4B | 5B | Yes |
| Battery at 89 percent | 21B | 10B | 10B | Tie |
| Node 12 temperature 72 humidity 45 | 34B | 16B | 14B | No |
| The sensor node is... | 51B | 16B | 16B | Tie |
| Alert flood warning for the area | 32B | 11B | 12B | Yes |
| What time is it? | 16B | 11B | 12B | Yes |
| the sensor is online... | 56B | 18B | 18B | Tie |
| **Aggregate** | **215B** | **90B (2.39:1)** | **92B (2.34:1)** | **Huffman 4K slightly ahead** |

Note: With the shared 4K codebook, Huffman now slightly outperforms MUX Grid on
the 8 scripted test messages. The real test is Experiment C with unpredictable
LLM-generated vocabulary.

### Experiment C Live Results

Validated over live LoRa on 2026-03-04. Both nodes: 40/40 messages per codec,
zero timeouts, zero errors. Cross-node byte verification confirmed.

| Metric | MUX Grid | Huffman 4K |
|--------|----------|------------|
| Messages (per codec, combined) | 40/40 | 40/40 |
| Aggregate ratio | 1.33:1 | 1.61:1 |
| Codebook hit rate | 61.3% | 80.9% |
| Avg ESC/msg | 4.4 | 2.4 |
| Total compressed bytes | 600B | 656B |
| Delivery | 100% | 100% |

Winner: **Huffman (4K)** — 21% better compression, 20pp higher hit rate on
LLM-generated text. Reversal from Experiment B (scripted text), where MUX Grid
won. Codecs have complementary strengths depending on vocabulary predictability.

---

## Experiment D — LLM Codec: Pre-Tokenizer + LLM Encode/Decode

### Risk Acknowledgment

This experiment introduces the LLM as an active participant in the codec pipeline —
not just generating conversation, but rewriting its own output to fit the codebook.
This is higher-risk than Experiments A–C.

**Known risks:**
- Gemma3 4B may not reliably constrain output to codebook vocabulary (mitigation: fallback to raw encoding if hit rate <70%)
- LLM rewriting adds inference latency — two LLM calls per TX instead of one (mitigation: measure, log, adjust timeout)
- Semantic drift during encode→decode — decoded message may not match original meaning (mitigation: log both, manual fidelity review)
- Overengineering pre-tokenizer before proving LLM codec concept (mitigation: Phase 1 and Phase 2 are independent)

**Failure is acceptable.** The experiment succeeds by producing data, not by producing good compression ratios.

### Phase 1 — Pre-Tokenizer

**Objective:** Add a text normalization layer between raw LLM output and the codec
encoder to fix ESC-triggering patterns identified in Experiment C.

**File:** `pretokenizer.py` — standalone importable module
**Function:** `normalize(text) → text`
**Pipeline:** `[LLM generates text] → normalize() → codec.encode() → TX`

Processing steps (in order):
1. Lowercase
2. Expand contractions (don't → do not, it's → it is, etc. — 26 mappings)
3. Split hyphens and dashes (en-dash, em-dash) to spaces
4. Strip punctuation (protecting decimal numbers via _DOT_ sentinel)
5. Collapse multiple spaces
6. Convert decimals to "N point M" form (both "point" and digits in codebook)
7. Final space collapse + strip

Also exports: `compute_hit_rate(text, codebook_set) → float` for fallback checking.

| Input | Output | Fixes |
|-------|--------|-------|
| "Sensor 5 now reads 2.1 feet – escalating the response." | "sensor 5 now reads 2 point 1 feet escalating the response" | 3 |
| "Don't worry, it's online." | "do not worry it is online" | 3 |
| "Alert! Node down — reboot ASAP!!!" | "alert node down reboot asap" | 5 |
| "off-grid low-power node" | "off grid low power node" | 2 |
| "Temperature: 72.5°F" | "temperature 72 point 5f" | 3 |

**Phase 1 Acceptance Criteria:**
1. All Experiment B messages still roundtrip after pre-tokenizer
2. Edge case inputs produce expected outputs (13 test cases)
3. Live run: codebook hit rate >80% (up from 65.5% MUX / 80.9% Huffman)
4. Live run: avg ESC <2.0 (down from 4.4 MUX / 2.4 Huffman)
5. Zero roundtrip failures introduced by pre-tokenizer

### Phase 2 — LLM Encode/Decode

**Objective:** Use the LLM as an active encoder and decoder. Sending LLM rewrites
its message using ONLY codebook words. Receiving LLM expands compressed text back
to natural English. Eliminates the ESC path entirely.

**File:** `llm_codec.py` — standalone module wrapping Ollama REST API
**Functions:** `llm_encode(text, model) → (encoded_text, ms)`,
`llm_decode(text, model) → (decoded_text, ms)`, `get_codebook_words() → set`

**Architecture (sender):**
```
LLM Call 1: Generate natural response (same as Exp C)  ~2000ms
LLM Call 2: Encode to codebook words (NEW)              ~1500ms
normalize() → codec.encode() → TX over LoRa
```

**Architecture (receiver):**
```
RX → codec.decode()
LLM Call 3: Decode to natural English (NEW)             ~1500ms
Append to conversation history
```

**Encode prompt strategy:**
- Top 500 words from codebook provided as examples (not full 4,096 — Gemma3 4B context limit)
- Temperature 0.3 for deterministic constraint (vs 0.7 for generation)
- System prompt: "Rewrite using ONLY approved words. Be as short as possible."
- Instruction: prefer simple common synonyms for unlisted words

**Fallback path:**
```python
if compute_hit_rate(normalized_encoded, codebook) < 0.70:
    log("WARN: fallback to raw")
    use normalize(natural_text) instead
```
If >30% of messages trigger fallback, the encode prompt needs rework — document and stop.

**Phase 2 Acceptance Criteria:**
1. `llm_codec.py` passes standalone tests (no Ollama required for unit tests)
2. LLM encode produces >90% codebook hit rate on at least 7/10 messages
3. Fallback triggers on <30% of messages
4. At least 18/20 messages complete successful roundtrip
5. Full 3-stage transcript logged for manual fidelity review
6. Comparison table populated across all 5 conditions (Exp C MUX, Exp C Huf, D-Ph1 MUX, D-Ph2 MUX, D-Ph2 Huf)

### Logging Format (Extended for Phase 2)

```
| # | Dir | Natural | Encoded | Decoded | Raw | Cmp | Ratio | Hit% | ESC | Gen(ms) | Enc(ms) | Dec(ms) | FB | RSSI | SNR |
```

Full transcript per message:
```
## Message N — B→A
**Natural:** "[original LLM output]"
**Encoded:** "[codebook-constrained rewrite]"
**Transmitted:** N codebook indices, M ESC, K bytes compressed
**Decoded:** "[receiver LLM expansion]"
**Fidelity:** [manual review — same meaning? Y/N]
```

### End-of-Experiment Comparison Table

```
| Metric              | Exp C MUX | Exp C Huf | D-Ph1 MUX | D-Ph2 MUX | D-Ph2 Huf |
|---------------------|-----------|-----------|-----------|-----------|----------|
| Codebook hit rate   | 61.3%     | 80.9%     |           |           |          |
| Avg ESC/msg         | 4.4       | 2.4       |           |           |          |
| Aggregate ratio     | 1.33:1    | 1.61:1    |           |           |          |
| Roundtrip success   | 40/40     | 40/40     |           |           |          |
```

### Config-Driven Phase Control

```yaml
pretokenizer: true        # Always on for Experiment D
llm_codec: false           # Phase 1 only (pretokenizer + raw codec)
llm_codec: true            # Phase 2 (pretokenizer + LLM encode/decode + codec)
fallback_threshold: 0.70   # Phase 2 only: skip LLM encode if hit rate below this
```

Backward compatibility: `llm_codec: false` runs Experiment C behavior with pretokenizer added.

### PPA Linkage

- **LLM as lossy codec** — sending LLM compresses meaning by substituting rare vocabulary
  with common codebook synonyms, analogous to PPA's lossy SVD delta compression (§2.3)
- **Receiver LLM reconstruction** — analogous to PPA's Zombie Protocol reconstruction
  from compressed deltas and neighborhood aggregates
- **Static codebook = shared initial state** — both LLMs agree on vocabulary, as both
  nodes agree on SVD basis in PPA
- **Fallback path** — analogous to PPA's checkpoint restoration when reconstruction
  error exceeds threshold

### What This Experiment Does NOT Include

- No coordinate-only transmission (grid locations without text) — Experiment E
- No SVD embedding retrieval — Experiment E
- No toroidal grid organization
- No multi-node (3+) testing
- No changes to the codebook — the 4,096 words are FROZEN
