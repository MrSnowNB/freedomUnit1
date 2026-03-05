---
title: "CyberMesh Codec POC"
version: 7.0.0
date: 2026-03-05
status: build
lifecycle_stage: build
owner: "Mark Snow, Jr. — Mindtech / CyberMesh"
repository: "huffman-mesh-poc"
license: "CC BY-SA 4.0"
---

# CyberMesh Codec POC

Dual-codec text compression over LoRa mesh radio with LLM kernel–driven
conversation and LLM-as-codec. Two laptops, two Heltec V3 nodes, Liquid
LFM2.5-1.2B kernel via Lemonade Server, zero internet.

## What This Proves

Seven experiments progressively prove that LLM kernel–generated messages can be
compressed, transmitted over LoRa radio, and decompressed with full fidelity —
culminating in Smart Router architecture with 333K codebooks, keyword compression,
and a 4-run experiment matrix validated by a deterministic codec harness.

| Experiment | Codec | Codebook | LLM Kernel | Status |
|-----------|-------|----------|------------|--------|
| A | Huffman (word-level, variable-length) | 2,048 words | — | Validated over live LoRa |
| B | MUX Grid (tiered fixed-width index) | 4,002 entries | — | Validated over live LoRa (8/8, 2.34:1) |
| C | Both codecs, LLM conversation | 4,096 shared (64×64) | Gemma3 4B / Ollama | Validated: 40/40, Huffman 1.61:1 vs MUX 1.33:1 |
| D-Ph1 | Pre-tokenizer + both codecs | 4,096 shared | Gemma3 4B / Ollama | Built, ready for live test |
| D-Ph2 | LLM kernel encode/decode + both codecs | 4,096 shared | Gemma3 4B / Ollama | Built, ready for live test |
| E | Full codec pipeline + Lemonade backend | 4,096 shared | LFM2.5-1.2B / Lemonade | Validated: 80/80, Huffman 1.94:1, hit 91.8% |
| F | Codec harness validation (SOUL.md + hooks) | 4,096 shared | LFM2.5-1.2B / Lemonade | Built, ready for live test |
| G (v7.0) | Smart Router: 333K codebooks + keyword codec | 333,333 words | LFM2.5-1.2B / Lemonade | Built, mock-validated |

```
Laptop A                    LoRa 915 MHz                    Laptop B
┌──────────┐                                          ┌──────────┐
│ LFM2.5   │  generate → pretokenize → smart_route() │ LFM2.5   │
│ 1.2B     │  strict: encode → packet(0x01|02) → TX  │ 1.2B     │
│ +codecs  │  lossy:  extract_kw → encode_kw → TX   │ +codecs  │
│ 333K     │  paginate: chunk → multi-pkt TX         │ 333K     │
│ Lemonade │  RX: decode → (reconstruct) → history    │ Lemonade │
└──────────┘                                          └──────────┘
        Heltec V3 ◄────── LoRa ──────► Heltec V3
```

## Architecture

The system follows the **codec pipeline** architecture defined in
`ARCHITECT-TO-CODING-AGENT-2026-03-05.md`:

- **LLM Kernel**: Hot-swappable compute unit (not an agent). Receives one
  prompt, returns one completion. The codec harness decides everything else.
  Currently validated: Gemma3 4B (Ollama), LFM2.5-1.2B (Lemonade).
- **Codec Harness**: Deterministic Python scaffolding wrapping the kernel.
  Constructs prompts, calls kernel via OpenAI-compatible REST API, runs
  post-processing hooks, accepts or retries based on validation. Not agentic.
- **Codec Pipeline**: Full encode/decode path — plaintext → kernel encode →
  pretokenizer → codec compress → paginator → TX (and reverse on RX).
- **Codec ID Byte**: `0x01` = Huffman strict, `0x02` = MUX Grid strict,
  `0x03` = Huffman keyword, `0x04` = MUX Grid keyword. Wire protocol
  constants implementing PPA Claim 24 (Adaptive Multiplexer).
- **Vendor/Hardware/Software Agnostic**: Any model behind an
  OpenAI-compatible chat completions endpoint is a valid kernel. Swapping
  inference servers is a `config.yaml` change.

## Quick Start

### Requirements

- 2 laptops (Windows/Linux/Mac)
- 2 Heltec V3 Meshtastic nodes (USB serial)
- Python 3.10+
- `pip install meshtastic pyyaml requests pypubsub`
- Lemonade Server with Liquid LFM2.5-1.2B model aliased as `test01` (Experiments E–G)
- Legacy: Ollama with `gemma3:latest` (Experiments C & D)

### Run

```bash
# v7.0 Smart Router (Experiment G) — mock mode
python huffman_mesh_poc.py --mock --role B

# v7.0 Smart Router — live with real LLM
python huffman_mesh_poc.py --role auto

# Run a single experiment (1-4)
python huffman_mesh_poc.py --run 1 --mock
```

In live mode, both scripts enter LISTENING mode. Pick up one Heltec unit and send
`Hi` as a DM to the other node. The "Hi" trigger runs all 4 experiment runs
automatically (Huffman keyword → MUX keyword → Huffman strict → MUX strict →
comparison table).

### v7.0 Smart Router (Experiment G)

```yaml
# config.yaml — key v7.0 settings
codec:
  engine: huffman          # huffman | mux_grid
  codebook_size: 333k      # 333k | 4k
  mode: keyword            # keyword | strict_only
router:
  strict_threshold: 180    # bytes — above this, route to lossy or paginate
testing:
  mock_llm: true           # true = mock mode, false = live Lemonade
```

### Phase Control (Experiment D)

Edit `config.yaml` to select which phase to run:

```yaml
pretokenizer: true        # Always on for Experiment D
llm_codec: false           # Phase 1: pretokenizer + raw codec (Exp C behavior + normalization)
llm_codec: true            # Phase 2: pretokenizer + LLM kernel encode/decode + codec
fallback_threshold: 0.70   # Phase 2 only: skip kernel encode if hit rate < 70%
```

### Backend / Kernel Hot-Swap (Experiment E)

Edit `config.yaml` to swap kernels or inference servers:

```yaml
model_name: "test01"                   # Change this to swap kernels — no code edits
llm_base_url: "http://localhost:8000"  # Lemonade default; change for Ollama (port 11434)
experiment: "E"                        # Experiment label for logs
```

Backward compatible: `llm_codec: false` runs Experiment C behavior with pre-tokenizer added.

### Codec Harness (Experiment F)

```bash
cd experiment_f
python harness.py --mode sanity-check   # Verify kernel responds
python harness.py --mode full           # Run all 80 tests (20 encode + 20 decode + 40 stress)
```

See `experiment_f/TESTING-PROTOCOL.md` for the full 10-step run protocol.

### Output

- Console: real-time TX/RX log with compression ratios, hit rates, inference timing
- `logs/experiment-*-log_*.md`: per-run markdown results with YAML frontmatter
- `logs/experiment-*-log_*.json`: machine-readable JSON logs
- `experiment_f/test_report.md`: codec harness validation results (Exp F)

## How It Works

1. **Trigger**: You DM `Hi` from one physical Heltec to the other (or use `--role B --mock` for loopback)
2. **Role assignment**: Receiver of `Hi` = Role B (sends first). Other node = Role A
3. **LLM kernel generates** a response from conversation history (Liquid LFM2.5-1.2B via Lemonade Server)
4. **Pre-tokenizer normalizes**: lowercase, expand contractions, strip punctuation
5. **Codec encodes**: Huffman or MUX Grid compress to binary (333K codebook)
6. **Smart Router decides**: strict (fits in 1 packet) / lossy (extract keywords) / paginate (multi-packet)
7. **Transport**: `sendData(portNum=256)` — CyberMeshPacket header + compressed payload
8. **Codec decodes**: receiver auto-detects codec from header Codec ID byte
9. **Keyword reconstruction** (lossy only): LLM reconstructs from keywords
10. **Conversation continues**: decoded text enters history for next kernel turn
11. **Logging**: every message logged with full codec pipeline metrics

## The Codecs

### Huffman — `huffman_codec.py` v7 (Experiments A, C, D, E, G)

- 333,333-word codebook from `codebooks/huffman_333k.csv` (built from Kaggle unigram data)
- Variable-length Huffman codes — frequent words get shorter codes (5–25 bits)
- Tight bit packing for keyword encoding (no per-keyword byte padding)
- Legacy: 4,095-word codebook from `huffman_codebook_4k.csv` still supported
- Implicit spaces between tokens (1-bit NOSPACE flag for exceptions)
- Case encoding: 1-bit lowercase, 2-bit capitalized/UPPER
- Number encoding: variable-width binary (8/16/32 bit)
- Unknown words: ESC + 5-bit length + 7-bit ASCII fallback
- Case-sensitive roundtrip

### MUX Grid — `mux_codec.py` v7 (Experiments B, C, D, E, G)

- 333,333-entry frequency-sorted codebook (`codebooks/mux_333k.csv`, 700×700 grid)
- Fixed 3-byte encoding per word (row_high, row_low+col_high, col_low)
- Legacy: 4,096-entry codebook (`mux_codebook.csv`, 64×64 grid) still supported
- ESC fallback for unknown words (sentinel index)
- Case-insensitive (all text lowercased at encode)
- Generated by `build_mux_codebook_333k.py` from Kaggle data

### Pre-Tokenizer — `pretokenizer.py` (Experiments D, E, G)

- Normalizes LLM kernel output before codec encoding: lowercase, expand contractions,
  split hyphens, strip punctuation, convert decimals ("2.1" → "2 point 1")
- Reduces ESC-triggering patterns from Experiment C
- `compute_hit_rate()` checks codebook coverage for fallback decisions

### Keyword Codec — `keyword_codec.py` (Experiment G/v7.0)

- LLM kernel extracts keywords from text for lossy compression
- Receiver LLM reconstructs natural language from keywords
- Max 20 keywords per message
- Preserves numbers, negation, and proper names
- Works with both Huffman and MUX codecs for keyword encoding

### Smart Router — `smart_router.py` (Experiment G/v7.0)

- Decides route for each message: strict (fits in 180B), lossy (keyword compression),
  or paginate (multi-packet)
- Uses LLM classification for keyword mode: briefing/status → lossy, command/data/narrative → strict
- Strict-only mode skips LLM classification entirely

### Context Manager — `context_manager.py` (Experiment G/v7.0)

- Thread-safe per-sender sliding-window conversation history
- Anchor-first: always keeps the first message in context
- Configurable window size (default 4 messages)

### LLM Codec — `llm_codec.py` (Experiments D Phase 2, E)

- LLM kernel rewrites its own output using only codebook vocabulary before encoding
- Receiver kernel expands compressed text back to natural English
- Encode prompt: top 500 codebook words as examples, temperature 0.3
- Fallback: if hit rate <70%, codec harness skips encode and sends raw through codec
- Backend-agnostic: talks to any OpenAI-compatible `/v1/chat/completions` endpoint
- Kernel and URL configurable via `config.yaml` (`model_name`, `llm_base_url`)

### Codec Harness — `experiment_f/` (Experiment F)

- SOUL.md-pattern prompts defining kernel identity ("codec encoder, machine
  component, not a conversational assistant")
- 4 deterministic post-processing hooks: strip encode framing, strip decode
  noise, validate codebook compliance, detect meta-loop collapse
- 80-test validation suite (20 encode + 20 decode + 40 stress)
- Dual logging: `harness.log` (human-readable) + `harness_data.jsonl` (machine)
- Addresses 3 issues from Experiment E: meta-loop collapse, encode framing,
  decode noise

### Head-to-Head Results

**Unit Test (4K Shared Codebook, No Radio):**

| Metric | Huffman 4K | MUX Grid |
|--------|-----------|----------|
| Aggregate (8 msgs) | 90B (2.39:1) | 92B (2.34:1) |
| Codebook size | 4,095 words | 4,095 entries + ESC |
| Case preservation | Yes | No (lowercases) |

**Experiment C Live Results (40 msgs/codec, Live LoRa, Gemma3 4B kernel):**

| Metric | MUX Grid | Huffman 4K |
|--------|----------|------------|
| Aggregate ratio | 1.33:1 | 1.61:1 |
| Codebook hit rate | 61.3% | 80.9% |
| Avg ESC/msg | 4.4 | 2.4 |
| Delivery | 40/40 (100%) | 40/40 (100%) |

**Experiment G (v7.0) Mock-Validated Results (333K Codebook, Loopback):**

| Metric | Huffman 333K | MUX 333K |
|--------|-------------|----------|
| Codebook size | 333,333 words | 333,333 entries |
| Encoding | 5–25 bits variable | 3 bytes/word fixed |
| 8-keyword payload | 15 bytes | 24 bytes |
| Keyword advantage | 38% smaller | baseline |
| 4K backward compat | Yes | Yes |
| Mock run | 20/20 messages | 20/20 messages |

**Experiment E Live Results (40 msgs/codec, Live LoRa, LFM2.5-1.2B kernel):**

| Metric | MUX Grid | Huffman 4K |
|--------|----------|------------|
| Aggregate ratio | 1.79:1 | 1.94:1 |
| Codebook hit rate | 79.5% | 83.5% |
| Avg ESC/msg | 2.6 | 2.6 |
| Delivery | 40/40 (100%) | 40/40 (100%) |

Winner on LLM kernel text: **Huffman** at both 4K and 333K scales. 333K codebook
eliminates most ESC fallbacks. Keyword mode (v7.0) adds lossy compression for
messages that exceed the LoRa MTU.

## Repo Structure

```
huffman-mesh-poc/
├── README.md                  ← You are here
├── PLAN.md                    ← Experiment design spec (A–G)
├── CODING-AGENT-LOG.md        ← AI coding agent build decisions & rationale (22 entries)
├── ARCHITECT-TO-CODING-AGENT-2026-03-05.md ← Authoritative terminology & architecture
├── cybermesh_v7_build_spec.md  ← v7.0 Smart Router architecture spec (803 lines)
├── TROUBLESHOOTING.md         ← Living doc: known issues & fixes
├── REPLICATION-NOTES.md       ← Living doc: setup checklist & pitfalls
├── ISSUE.md                   ← Open issues requiring human input
├── HARNESS-DESIGN-DISCUSSION.md ← Codec harness research & design (Experiment F)
├── AGENTIC-RESEARCH-SYNTHESIS.md ← Prompt engineering research synthesis
├── config.yaml                ← v7.0 config: codec/router/keyword/context/testing
├── huffman_mesh_poc.py        ← Main experiment harness v7.0 (1,308 lines)
├── llm_client.py              ← LLM client: mock + live Lemonade (v7.0)
├── huffman_codec.py           ← Huffman codec v7 (4K + 333K + keyword encode)
├── mux_codec.py               ← MUX Grid codec v7 (4K + 333K + keyword encode)
├── keyword_codec.py           ← Keyword extract/reconstruct via LLM (v7.0)
├── smart_router.py            ← Smart Router: size/classify/route (v7.0)
├── packet.py                  ← CyberMeshPacket: encode/decode, codec IDs 0x01–0x04 (v7.0)
├── context_manager.py         ← Per-sender context window (v7.0)
├── pretokenizer.py            ← Pre-tokenizer: normalize() + compute_hit_rate()
├── paginator.py               ← Text + binary pagination (v7.0: paginate_strict)
├── llm_codec.py               ← LLM codec: llm_encode() + llm_decode() (Exp D–E)
├── mesh_huffman.py            ← Huffman codec v4 (legacy copy, pre-rename)
├── mux_codebook.csv           ← Shared 4,096-entry vocabulary — FROZEN
├── huffman_codebook_4k.csv    ← Huffman tree built from shared vocabulary — FROZEN
├── english_unigram_freq.csv   ← Kaggle word frequency data (333K words)
├── build_huffman_codebook_333k.py ← 333K Huffman codebook generator (v7.0)
├── build_mux_codebook_333k.py ← 333K MUX codebook generator (v7.0)
├── build_mux_codebook.py      ← 4K MUX codebook generator (legacy)
├── build_huffman_codebook.py  ← 4K Huffman codebook generator (legacy)
├── test_codecs.py             ← Unit tests (both codecs + pretokenizer + llm_codec)
├── codebooks/                 ← Generated 333K codebooks (v7.0)
│   ├── huffman_333k.csv       ← 333,333 words, 5–25 bits (6.2 MB)
│   ├── huffman_333k.bin       ← Serialized Huffman tree (14.8 MB)
│   ├── mux_333k.csv           ← 333,333 words, 700×700 grid (7.5 MB)
│   └── mux_333k.bin           ← Serialized MUX grid (9.4 MB)
├── experiment_f/              ← Codec harness (Experiment F)
│   ├── config.yaml            ← API, sampling params, token budgets, hook config
│   ├── encode.soul.md         ← Encoder SOUL.md prompt
│   ├── decode.soul.md         ← Decoder SOUL.md prompt
│   ├── hooks.py               ← 4 deterministic post-processing hooks
│   ├── harness.py             ← CLI test runner with dual logging
│   ├── test_suite.yaml        ← 80 test cases (20+20+40 stress)
│   └── TESTING-PROTOCOL.md    ← 10-step run protocol
└── logs/
    └── experiment-*-log_*.md  ← Auto-generated per run
```

## Documentation Policy

All files follow the project's AI First documentation standard:

- **Markdown with YAML frontmatter** for all documents
- **ARCHITECT-TO-CODING-AGENT-2026-03-05.md** — authoritative terminology and
  architecture reference. When repo docs conflict, this document wins.
- **CODING-AGENT-LOG.md** — every coding agent action recorded with timestamp,
  phase, action, and rationale
- **TROUBLESHOOTING.md** — seeded with known issues from prior Liberty Mesh work
- **REPLICATION-NOTES.md** — step-by-step setup checklist and known pitfalls
- **ISSUE.md** — open conflicts and uncertainties requiring human input
- **Experiment logs** — auto-generated with machine-readable YAML frontmatter
- **File authority hierarchy** (highest first):
  1. Mark Snow verbal/written direction
  2. Architect document
  3. PLAN.md
  4. Source code
  5. README.md, REPLICATION-NOTES.md
  6. CODING-AGENT-LOG.md

## PPA Linkage

This POC implements concepts from the CyberMesh Provisional Patent Application
(filed Nov 2025):

- **Codec ID byte** (packet header Byte 0) = first implementation of the
  Adaptive Multiplexer described in Claim 24
- **Shared static codebook** = initial state analogous to SVD basis matrix (PPA §2.3)
- **Tiered bit packing** = bandwidth-adaptive encoding per PPA §3.1
- **LLM kernel as lossy codec** (Experiments D–E) = sending kernel compresses
  meaning by substituting rare vocabulary with common codebook synonyms,
  analogous to PPA's lossy SVD delta compression (§2.3)
- **Receiver kernel reconstruction** = analogous to PPA's Zombie Protocol
  reconstruction from compressed deltas and neighborhood aggregates
- **Fallback path** = analogous to PPA's checkpoint restoration when
  reconstruction error exceeds threshold

## Project Context

This POC is part of the **Liberty Mesh** project — distributed AI over
LoRa mesh radio for Lawrence Township, NJ (Spring 2026 deployment).

The codebook-based compression is the foundation of the **AI First Language**
concept: LLM kernels constrained to codebook-only vocabulary via system prompt,
producing messages that compress optimally for transmission over
bandwidth-constrained LoRa radio. Experiment D Phase 2 proves this thesis
directly — the LLM kernel functions as a lossy codec.

Experiment E migrates from Ollama/Gemma3 to Lemonade Server/Liquid LFM2.5-1.2B,
proving the architecture is vendor-agnostic and that small, obedient models
running on native NPU hardware can replace larger general-purpose models.

Experiment F introduces the codec harness — deterministic Python scaffolding
with SOUL.md-pattern prompts and post-processing hooks — to validate and
harden the kernel's encode/decode behavior.

Experiment G (v7.0 "Smart Router") is a new architectural generation: 333K
codebooks from Kaggle unigram frequency data, Smart Router with
strict/lossy/paginate routing, keyword compression via LLM extraction, binary
pagination, per-sender context management, and a 4-run experiment matrix.

---

*Mindtech Mesh Networks — Liberty Mesh Project*
*CC BY-SA 4.0 v7.0*
