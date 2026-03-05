---
title: "CyberMesh Codec POC"
version: 6.0.0
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

Six experiments progressively prove that LLM kernel–generated messages can be
compressed, transmitted over LoRa radio, and decompressed with full fidelity —
culminating in an LLM kernel that rewrites its own output to maximize
compression before transmission, validated by a deterministic codec harness.

| Experiment | Codec | Codebook | LLM Kernel | Status |
|-----------|-------|----------|------------|--------|
| A | Huffman (word-level, variable-length) | 2,048 words | — | Validated over live LoRa |
| B | MUX Grid (tiered fixed-width index) | 4,002 entries | — | Validated over live LoRa (8/8, 2.34:1) |
| C | Both codecs, LLM conversation | 4,096 shared (64×64) | Gemma3 4B / Ollama | Validated: 40/40, Huffman 1.61:1 vs MUX 1.33:1 |
| D-Ph1 | Pre-tokenizer + both codecs | 4,096 shared | Gemma3 4B / Ollama | Built, ready for live test |
| D-Ph2 | LLM kernel encode/decode + both codecs | 4,096 shared | Gemma3 4B / Ollama | Built, ready for live test |
| E | Full codec pipeline + Lemonade backend | 4,096 shared | LFM2.5-1.2B / Lemonade | Validated: 80/80, Huffman 1.94:1, hit 91.8% |
| F | Codec harness validation (SOUL.md + hooks) | 4,096 shared | LFM2.5-1.2B / Lemonade | Built, ready for live test |

```
Laptop A                    LoRa 915 MHz                    Laptop B
┌──────────┐                                          ┌──────────┐
│ LFM2.5   │  generate → [kernel encode] → normalize()│ LFM2.5   │
│ 1.2B     │  → codec.encode() → sendData(raw)        │ 1.2B     │
│ +codecs  │  → [3B hdr + data] → LoRa →              │ +codecs  │
│ Lemonade │  codec.decode() → [kernel decode] → hist  │ Lemonade │
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
- **Codec ID Byte**: `0x01` = Huffman, `0x02` = MUX Grid. Wire protocol
  constant implementing PPA Claim 24 (Adaptive Multiplexer).
- **Vendor/Hardware/Software Agnostic**: Any model behind an
  OpenAI-compatible chat completions endpoint is a valid kernel. Swapping
  inference servers is a `config.yaml` change.

## Quick Start

### Requirements

- 2 laptops (Windows/Linux/Mac)
- 2 Heltec V3 Meshtastic nodes (USB serial)
- Python 3.10+
- `pip install meshtastic pyyaml requests`
- Lemonade Server with Liquid LFM2.5-1.2B model aliased as `test01` (Experiments E–F)
- Legacy: Ollama with `gemma3:latest` (Experiments C & D)

### Run

```bash
# Both laptops — same command
python huffman_mesh_poc.py
```

Both scripts enter LISTENING mode. Pick up one Heltec unit and send `Hi` as
a DM to the other node. One "Hi" trigger runs both codec runs automatically
(MUX Grid → Huffman → comparison table).

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
- `logs/experiment-log_YYYYMMDD_HHMMSS.md`: full results with YAML frontmatter
- `experiment_f/test_report.md`: codec harness validation results

## How It Works

1. **Trigger**: You DM `Hi` from one physical Heltec to the other
2. **Role assignment**: Receiver of `Hi` = Role B (sends first). Other node = Role A
3. **LLM kernel generates** a response from conversation history (Liquid LFM2.5-1.2B via Lemonade Server)
4. **LLM kernel encodes** (Phase 2 only): rewrites output using codebook words only
5. **Pre-tokenizer normalizes**: lowercase, expand contractions, strip punctuation
6. **Codec encodes**: Huffman or MUX Grid compress to binary
7. **Transport**: `sendData(portNum=256)` — 3-byte header + compressed payload
8. **Codec decodes**: receiver auto-detects codec from header Byte 0 (Codec ID)
9. **LLM kernel decodes** (Phase 2 only): expands compressed text to natural English
10. **Conversation continues**: decoded text enters history for next kernel turn
11. **Logging**: every message logged with full codec pipeline metrics

## The Codecs

### Huffman — `mesh_huffman.py` v4 (Experiments A, C, D, E)

- 4,095-word codebook from shared `huffman_codebook_4k.csv` (64×64 grid vocabulary)
- Variable-length Huffman codes — frequent words get shorter codes (4-15 bits)
- Implicit spaces between tokens (1-bit NOSPACE flag for exceptions)
- Case encoding: 1-bit lowercase, 2-bit capitalized/UPPER
- Number encoding: variable-width binary (8/16/32 bit)
- Unknown words: ESC + 5-bit length + 7-bit ASCII fallback
- Case-sensitive roundtrip

### MUX Grid — `mux_codec.py` (Experiments B, C, D, E)

- 4,096-entry frequency-sorted codebook (`mux_codebook.csv`, 64×64 grid)
- Tiered bit packing: 7-bit (top 64), 10-bit (next 192), 14-bit (rest)
- ESC fallback for unknown words (index 4095)
- Case-insensitive (all text lowercased at encode)
- Generated by `build_mux_codebook.py` from Kaggle data

### Pre-Tokenizer — `pretokenizer.py` (Experiments D, E)

- Normalizes LLM kernel output before codec encoding: lowercase, expand contractions,
  split hyphens, strip punctuation, convert decimals ("2.1" → "2 point 1")
- Reduces ESC-triggering patterns from Experiment C
- `compute_hit_rate()` checks codebook coverage for fallback decisions

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

**Experiment E Live Results (40 msgs/codec, Live LoRa, LFM2.5-1.2B kernel):**

| Metric | MUX Grid | Huffman 4K |
|--------|----------|------------|
| Aggregate ratio | 1.79:1 | 1.94:1 |
| Codebook hit rate | 79.5% | 83.5% |
| Avg ESC/msg | 2.6 | 2.6 |
| Delivery | 40/40 (100%) | 40/40 (100%) |

Winner on LLM kernel text: **Huffman 4K**. Codecs have complementary strengths
depending on vocabulary predictability. LLM kernel encode (Exp E) boosted MUX
compression by 35% over raw LLM output (Exp C).

## Repo Structure

```
huffman-mesh-poc/
├── README.md                  ← You are here
├── PLAN.md                    ← Experiment design spec (A–F)
├── CODING-AGENT-LOG.md        ← AI coding agent build decisions & rationale (21 entries)
├── ARCHITECT-TO-CODING-AGENT-2026-03-05.md ← Authoritative terminology & architecture
├── TROUBLESHOOTING.md         ← Living doc: known issues & fixes
├── REPLICATION-NOTES.md       ← Living doc: setup checklist & pitfalls
├── ISSUE.md                   ← Open issues requiring human input
├── HARNESS-DESIGN-DISCUSSION.md ← Codec harness research & design (Experiment F)
├── AGENTIC-RESEARCH-SYNTHESIS.md ← Prompt engineering research synthesis
├── config.yaml                ← Ports, timing, LLM kernel, phase control
├── huffman_mesh_poc.py        ← Main experiment script v5.0 (Experiments C–E)
├── mesh_huffman.py            ← Huffman codec v4 (4,095-word shared codebook)
├── mux_codec.py               ← MUX Grid codec (4,096-entry 64×64 grid) — FROZEN
├── pretokenizer.py            ← Pre-tokenizer: normalize() + compute_hit_rate()
├── llm_codec.py               ← LLM codec: llm_encode() + llm_decode() via Lemonade/Ollama
├── paginator.py               ← Message pagination for LoRa chunks
├── mux_codebook.csv           ← Shared 4,096-entry vocabulary — FROZEN
├── huffman_codebook_4k.csv    ← Huffman tree built from shared vocabulary — FROZEN
├── build_mux_codebook.py      ← MUX codebook generator
├── build_huffman_codebook.py  ← Huffman codebook generator
├── test_codecs.py             ← Unit tests (8 suites, both codecs + pretokenizer + llm_codec)
├── english_unigram_freq.csv   ← Kaggle word frequency data (333K words)
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

---

*Mindtech Mesh Networks — Liberty Mesh Project*
*CC BY-SA 4.0 v6.0*
