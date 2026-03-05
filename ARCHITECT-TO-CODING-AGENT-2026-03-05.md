---
title: "Architect → Coding Agent: Terminology & Architecture Clarification"
date: 2026-03-05T11:06:00-05:00
from: "Architect Agent (supervised by Mark Snow, Jr.)"
to: "Coding Agent"
project: "CyberMesh Codec POC / Liberty Mesh"
repo: "/home/user/workspace/huffman-mesh-poc/"
authority: "This document is authoritative for terminology and architecture. When repo docs conflict with this document, this document wins. When this document conflicts with Mark Snow's verbal direction, Mark wins."
---

# Architect → Coding Agent: Terms & Architecture Clarification

This message establishes precise terminology and architectural boundaries for all
coding work on the CyberMesh Codec POC. Read fully before writing any code or docs.

---

## 1. Correct Terminology — Use These Exact Terms

The following terms are authoritative. Do not substitute synonyms. Do not use
industry-standard meanings where they conflict with the definitions below.

### 1a. LLM Kernel

The LLM (large language model) running inside the codec pipeline. It is a **kernel**
in the operating systems sense: a hot-swappable compute unit that the harness
schedules, constrains, and validates. The LLM does not make decisions. It does not
select tools. It does not loop autonomously. It receives one prompt and returns one
completion. The harness decides everything else.

**Current kernel:** Gemma3 4B via Ollama (validated in Experiments C and D).
**Target kernel:** LFM2-2.6B via AMD Lemonade Server (not yet tested).
**Any model behind an OpenAI-compatible chat completions endpoint is a valid kernel.**

The kernel is evaluated on one metric: **instruction-following accuracy**, measured
as codebook hit rate (%). IFEval score is the proxy benchmark. Parameter count,
reasoning capability, and general chat quality are irrelevant to kernel selection.

### 1b. Codec Harness

The deterministic Python scaffolding that wraps the LLM kernel. The harness:

1. Constructs the prompt (system soul + codebook subset + few-shot examples + user message)
2. Calls the LLM kernel via OpenAI-compatible REST API
3. Intercepts the raw response
4. Runs post-processing hooks (strip framing, strip noise, validate codebook compliance, detect meta-loops)
5. Accepts or retries based on deterministic validation

The harness is **not agentic**. The LLM does not decide what happens next. The harness
enforces the contract. If the LLM output fails validation, the harness retries or
falls back — the LLM is not consulted about the failure.

**Source file:** `llm_codec.py` (current), to be extended with hook architecture.

### 1c. Codec Pipeline

The full encode/decode path from plaintext to LoRa packet and back. Sequential,
deterministic, no branching based on LLM judgment:

```
ENCODE (TX side):
  plaintext
  → LLM kernel encode (rewrite to codebook vocabulary)
  → pretokenizer normalization
  → codec compress (Huffman 4K or MUX Grid, selected by Codec ID byte)
  → paginator (chunk for LoRa MTU)
  → serial TX to Meshtastic node

DECODE (RX side):
  serial RX from Meshtastic node
  → depaginator (reassemble chunks)
  → codec decompress (selected by Codec ID byte in header)
  → LLM kernel decode (rewrite to natural language)
  → plaintext
```

### 1d. Codec ID Byte

First byte of every transmitted packet. Identifies which codec compressed the payload.

- `0x01` = Huffman 4K
- `0x02` = MUX Grid

This implements PPA Claim 24 (Adaptive Multiplexer). The receiver reads this byte
to select the correct decompression path. **This is a wire protocol constant. Do not
change these values.**

### 1e. Codebook

A shared, static vocabulary file that both the encoder and decoder must have identical
copies of. The codebook is the instruction set for the LLM kernel — "use only these
words."

- **Huffman 4K:** `huffman_codebook_4k.csv` — 4,095 entries, frequency-ranked from
  `english_unigram_freq.csv` (Kaggle, 333K source words). Huffman tree assigns
  variable-length binary codes by frequency.
- **MUX Grid:** `mux_codebook.csv` — 4,096 entries in a 64×64 grid. Fixed-length
  12-bit codes (6-bit row + 6-bit column).

**Both codebook files are frozen. DO NOT MODIFY.**

### 1f. Escape (ESC) Encoding

When the LLM kernel outputs a word not in the codebook, the codec falls back to
literal byte encoding with an escape prefix. Each ESC-encoded word costs more bytes
than a codebook hit. The ESC rate per message is a primary quality metric — lower is
better.

- Experiment D best result: **0.7 ESC/message** (Huffman 4K + LLM codec)
- Target: <0.5 ESC/message with improved kernel (LFM2-2.6B)

### 1g. Hit Rate

Percentage of words in LLM kernel output that exist in the active codebook. This is
the single most important codec quality metric.

- Experiment D best result: **91.8%** (Huffman 4K + LLM codec, Gemma3 4B kernel)
- This is the **floor**, not the ceiling. Gemma3 4B scores lower on IFEval than
  LFM2-2.6B. A better instruction-following kernel should produce higher hit rates.

### 1h. Fallback

When LLM kernel encode produces output below the hit rate threshold (currently 70%),
the harness discards the LLM output and falls back to pretokenizer-only encoding.
This is a deterministic gate in the harness, not an LLM decision.

- Experiment D fallback rate: 3/20 messages (Huffman 4K), 2/20 messages (MUX Grid)

### 1i. Inference Server

The software process that loads the model weights and serves the OpenAI-compatible
API. This is the runtime, not the model.

| Server | Status | API | Hardware Optimization |
|--------|--------|-----|----------------------|
| Ollama | Current, validated | OpenAI-compatible | Vulkan/ROCm generic fallback |
| AMD Lemonade Server | Target, not yet tested | OpenAI-compatible | NPU + iGPU hybrid native |
| llama.cpp | Compatible, not tested | OpenAI-compatible | CPU / CUDA / Metal |
| vLLM | Compatible, not tested | OpenAI-compatible | CUDA |

**Swapping inference servers is a config.yaml change (base_url field). No code changes
required.** This is by design.

### 1j. Substrate

The physical or logical communication medium carrying CyberMesh protocol messages.
Per the PPA, the protocol is substrate-independent — identical semantics over any
transport.

Validated substrates: LoRa (Heltec V3, Seeed Wio Tracker), localhost UDP, LAN TCP, gRPC.
Contemplated substrates: Wi-Fi mesh (802.11s), BLE, Ethernet, satellite (NTN via
APAL Hestia A2), power-line (PLC), optical, acoustic.

---

## 2. Architecture Principles — Non-Negotiable

### 2a. Vendor Agnostic

No component may bind to a specific vendor's SDK, proprietary API, or hardware-specific
code path. Every integration point uses a standard interface:

- LLM kernel ↔ harness: OpenAI-compatible REST (`/v1/chat/completions`)
- Harness ↔ radio: Meshtastic serial protocol (works with any Meshtastic-compatible node)
- Codebook: CSV file (portable, no runtime dependencies)
- Config: YAML file (portable, human-readable)
- Language: Python 3.10+ with stdlib + requests + PyYAML + NumPy (no vendor SDKs)

### 2b. Hardware Agnostic

The codec pipeline runs identically on:

- AMD Strix Halo 395 (128GB RAM, Ryzen AI NPU) — validated
- Upcycled eSports laptop (commodity x86) — validated
- Any machine that runs Python 3.10 and an OpenAI-compatible inference server

The radio nodes are heterogeneous by design:

- Node A: Heltec V3 (ESP32-S3 + SX1262) — validated
- Node B: Seeed Wio Tracker L1 (nRF52840 + SX1262) — validated
- Any Meshtastic-compatible hardware is a valid node

**Diversity in the node fleet is a security and resilience property, not a bug.**
Heterogeneous hardware means no single firmware exploit compromises all nodes.

### 2c. Software Agnostic

The LLM kernel is a function call, not a dependency. Swap Ollama for Lemonade,
llama.cpp, vLLM, or a cloud API — the harness doesn't change. The harness validates
output, not origin.

### 2d. The LLM Is a Kernel, Not an Agent

The LLM does not:
- Decide what to encode
- Choose which codec to use
- Select retry strategy
- Evaluate its own output quality
- Loop autonomously

The harness does all of these things deterministically. The LLM receives a prompt
and returns tokens. That is its entire contract.

### 2e. Diversity = Resilience

A mesh where every node runs identical hardware, firmware, and inference stack has
one attack surface. The architecture intentionally supports heterogeneous deployments:
different radio hardware, different compute hardware, different LLM kernels, different
inference servers. The shared contract is the codebook, the Codec ID byte, the wire
format, and the OpenAI-compatible API. Everything else varies.

---

## 3. Validated Experimental Data — Ground Truth

All data below was measured on live LoRa transmissions, March 4, 2026. 120 total
messages. Zero codec errors. Zero timeouts.

### 3a. Experiment D Phase 2 (Best Results)

| Codec | Messages | Compression Ratio | Hit Rate | ESC/msg | Fallbacks |
|-------|----------|-------------------|----------|---------|-----------|
| Huffman 4K | 40/40 | 1.94:1 | 91.8% | 0.7 | 3/20 |
| MUX Grid | 40/40 | 1.83:1 | 84.7% | 1.5 | 2/20 |

**Winner: Huffman 4K + LLM Codec.** This is the baseline all future experiments
must beat or match.

### 3b. Known Hardware Anomaly

Ollama on AMD Strix Halo 395 runs 3.7x slower than an upcycled eSports laptop
(~11,400ms vs ~3,092ms encode time). Cause: Ollama uses generic Vulkan/ROCm
fallback, does not utilize Strix Halo's NPU or iGPU natively. This is an Ollama
limitation, not a codec limitation. Lemonade Server with RyzenLLM-AI engine is the
expected fix (not yet validated).

---

## 4. What You May and May Not Do

### Allowed
- Update documentation per HANDOFF-2026-03-04.md Section 5 tasks
- Extend `llm_codec.py` with hook architecture (post-processing validation)
- Add new test cases to `test_codecs.py`
- Create new documentation files (e.g., `ARCHITECTURE-DIRECTION.md`)
- Modify `config.yaml` for new experiment parameters

### Prohibited
- Modify `mux_codec.py` or `mux_codebook.csv` (frozen, standing directive)
- Modify `huffman_codebook_4k.csv` (frozen for baseline comparison)
- Add vendor-specific dependencies (no AMD SDK, no NVIDIA SDK, no proprietary libs)
- Implement autonomous LLM decision-making in the codec pipeline
- Start new experiments without explicit approval from Mark Snow
- Assume any information in project docs is correct without cross-referencing
  against this document and the codebase itself

### On Uncertainty
Stop. Update `TROUBLESHOOTING.md` with what you found. Open `ISSUE.md` with the
question. Wait for human input. Do not guess. Do not proceed with assumptions.

---

## 5. File Authority Hierarchy

When documents conflict, resolve in this order (highest authority first):

1. **Mark Snow verbal/written direction** (real-time)
2. **This document** (architecture and terminology)
3. **HANDOFF-2026-03-04.md** (project state and task list)
4. **PLAN.md** (experiment design)
5. **Repo source code** (implementation)
6. **README.md, REPLICATION-NOTES.md** (documentation)
7. **CODING-AGENT-LOG.md** (historical decisions)

If you find a conflict between any two levels, flag it in `ISSUE.md` and halt.
Do not resolve conflicts by choosing the lower-authority source.

---

*Issued by Architect Agent under supervision of Mark Snow, Jr.*
*Date: March 5, 2026, 11:06 AM EST*
*Project: CyberMesh Codec POC — Liberty Mesh*
*Repo: /home/user/workspace/huffman-mesh-poc/*
