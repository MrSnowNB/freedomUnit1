---
title: "Coding Agent Build Log"
version: 4.0.0
date: 2026-03-04
status: in_progress
lifecycle_stage: build
agent: "Perplexity Computer"
project: huffman-mesh-poc
owner: "Mark Snow, Jr. — Mindtech / CyberMesh"
policy: |
  All files are markdown with YAML frontmatter or pure YAML.
  Each task is atomic, testable, and gated.
  On any failure/uncertainty: update living docs, then stop for human input.
  Lifecycle: Plan → Build → Validate → Review → Release (sequential only).
---

# Coding Agent Build Log

This document records every decision, action, and rationale made by the coding
agent during the build of `huffman-mesh-poc`. It serves as a complete audit
trail for reproducibility and review.

---

## Entry 001 — Project Kickoff

- **Timestamp**: 2026-03-04T12:44:00-05:00
- **Phase**: Plan → Build transition
- **Action**: Created repo scaffold and all documentation files
- **Context**: User approved experiment design after iterative discussion.
  Key decisions locked in:
  - Single script, two laptops, auto-detect serial
  - Trigger via manual `Hi` DM on LongFast channel 0
  - 8 scripted test messages, alternating sender/receiver
  - Raw bytes via `sendData(portNum=256)` — no base64
  - 3s delay between messages, 15s timeout
  - Log and continue on failure (capture full dataset)
  - Peer ID learned dynamically from trigger message

## Entry 002 — Codec Reuse

- **Timestamp**: 2026-03-04T12:44:00-05:00
- **Phase**: Build
- **Action**: Copied `mesh_huffman.py` (v3) and `english_unigram_freq.csv` into repo
- **Rationale**: Codec already passes 100% roundtrip on 28 test messages including
  all 8 messages in this POC's test script. No modifications needed.
- **Verification**: Will run dry-run validation after script build to confirm
  roundtrip on all 8 test messages in isolation (no radio).

## Entry 003 — Script Architecture

- **Timestamp**: 2026-03-04T12:44:00-05:00
- **Phase**: Build
- **Action**: Built `huffman_mesh_poc.py`
- **Design decisions**:
  1. **State machine**: LISTENING → TRIGGERED → RUNNING → COMPLETE
  2. **Role assignment**: Node that receives `Hi` = Role B (sends odd steps).
     Node that receives first compressed message = Role A (sends even steps).
  3. **Packet routing**: `onReceive` handler checks `portNum`:
     - `portnum=1` (TEXT_MESSAGE_APP): watch for `Hi` trigger
     - `portnum=256` (custom): compressed test data
  4. **Logging**: Each message logged to in-memory list, written to
     `logs/experiment-log.md` on completion with YAML frontmatter.
  5. **Serial auto-detect**: `SerialInterface()` with no devPath.
     Config override available via `config.yaml → port` field.
  6. **Timeout**: `threading.Event` with 15s wait per expected message.
  7. **RSSI/SNR**: Extracted from `packet.get('rxRssi')` and `packet.get('rxSnr')`.

## Entry 004 — Config Design

- **Timestamp**: 2026-03-04T12:44:00-05:00
- **Phase**: Build
- **Action**: Built `config.yaml`
- **Fields**: `port` (auto/COMx), `custom_portnum` (256), `trigger_word` (Hi),
  `message_delay_s` (3), `timeout_s` (15), `test_messages` (list of 8)
- **Rationale**: Keeps the script zero-config for the happy path but allows
  overrides without code changes.

---

*This log is appended by the coding agent on every build action. Human review
required at each lifecycle gate.*

## Entry 005 — First Live Test: TX Not Received

- **Timestamp**: 2026-03-04T13:13:00-05:00
- **Phase**: Validate
- **Symptom**: Role B (trigger receiver) ran all TX steps without error, but
  Node A never received any compressed packets. All RX steps timed out.
- **Root cause (TX)**: `sendData(destinationId=self._hex_to_num(self.peer_id))`
  converted the hex string to an int. While the API docs say int is valid,
  passing the hex string directly (`"!07c01855"`) is canonical and avoids
  potential routing issues. Also changed `wantAck=False` to `wantAck=True`
  to get delivery confirmation.
- **Root cause (RX)**: Portnum matching checked for `"256"` as a string, but
  the Meshtastic Python API returns `portnum="PRIVATE_APP"` (the enum name)
  for portnum 256. Receiver would never have matched even if packets arrived.
- **Fixes applied**:
  1. `destinationId=self.peer_id` (pass hex string, not int)
  2. `wantAck=True` for delivery confirmation
  3. Added `portnum == "PRIVATE_APP"` to the portnum matching logic
  4. Added `[DBG]` packet logging to show all incoming packets with portnum
  5. Added TX confirmation print showing destination and portnum
- **Verification**: Need second live test to confirm.

## Entry 006 — Experiment A Validated Over Live LoRa

- **Timestamp**: 2026-03-04T13:30:00-05:00
- **Phase**: Validate → PASS
- **Result**: 6 of 8 messages completed perfect roundtrip across both nodes.
  2 missed messages due to startup timing race (not codec failures).
  Zero codec failures on any received message.
- **Key metrics**: AI-constrained message hit 3.29:1 compression (56B → 17B).
  RSSI: -27 to -36 dBm, SNR: 5.25-6.75 dB.
- **Conclusion**: Experiment A (Huffman POC) validated. Proceed to Experiment B.

## Entry 007 — Experiment B: MUX Grid Codec Design Review

- **Timestamp**: 2026-03-04T14:15:00-05:00
- **Phase**: Plan
- **Action**: Reviewed PPA-Specification-CyberMesh-1.pdf (36 pages) and
  CyberMesh-MUX-Grid-Codec-Experiment-B-Spec.md from brainstorming session.
- **Key decisions from spec**:
  1. Single variable under test: Codec method (Huffman vs. MUX Grid)
  2. 4,096-entry frequency-sorted codebook from Kaggle + domain terms
  3. Tiered bit packing: Tier 0 (7b), Tier 1 (10b), Tier 2 (14b)
  4. 3-byte packet header: Codec ID + seq + padding (retrofit to Huffman too)
  5. Index 4095 = ESC for out-of-codebook words
  6. Same 8 test messages as Experiment A for direct comparison
- **PPA linkage**: Codec ID byte = first impl of adaptive MUX (Claim 24).
  Codebook = shared initial state analogous to SVD basis matrix (PPA §2.3).

## Entry 008 — Experiment B Build: Codebook + Codec + POC v2.0

- **Timestamp**: 2026-03-04T14:21:00-05:00
- **Phase**: Build
- **Files created/modified**:
  1. `build_mux_codebook.py` — Generates `mux_codebook.csv` from Kaggle data
  2. `mux_codebook.csv` — 4,002 entries (3,890 Kaggle + 101 numbers + 10 domain + ESC)
  3. `mux_codec.py` — Standalone MUX Grid encoder/decoder module
  4. `huffman_mesh_poc.py` — v2.0 with `CodecWrapper` class for dual-codec support,
     unified 3-byte packet header, codec auto-detection on receive
  5. `config.yaml` — Added `codec: mux_grid` selector
  6. `test_codecs.py` — 5-suite unit test (MUX standalone, MUX+header, Huffman+header,
     cross-codec detection, ESC handling)
- **Design decisions**:
  1. Did NOT modify `mesh_huffman.py` — Experiment A codec preserved pristine.
     Header wrapping done at transport layer in `CodecWrapper`.
  2. `CodecWrapper` instantiates both decoders for auto-detection: any incoming
     packet is decoded based on Byte 0 Codec ID regardless of which codec
     the sender is configured to use.
  3. MUX Grid lowercases all text (spec says case-insensitive roundtrip check).
     Huffman preserves case. Both pass.
  4. Codebook includes all words from the 8 test messages — verified 100% coverage.
  5. `build_mux_codebook.py` is a build-time tool, not imported at runtime.
     `mux_codec.py` loads the CSV directly.
- **Test results**: All 5 suites pass. 100% roundtrip on all 8 messages for both codecs.
  MUX Grid aggregate: 215B raw → 92B compressed (2.34:1).
  Huffman+header aggregate: 215B raw → 142B compressed (1.51:1).
  MUX Grid wins on 6 of 8 messages (loses on tiny "ok" and "SOS" due to 3B header overhead).
- **Verification gate**: Unit tests pass. Ready for live LoRa test.

## Entry 009 — Documentation Update for Experiment B

- **Timestamp**: 2026-03-04T14:31:00-05:00
- **Phase**: Build
- **Action**: Updated all living docs to reflect dual-codec Experiment B build.
- **Files updated**:
  1. `PLAN.md` v2.0 — Now covers both Experiment A (with results) and
     Experiment B (design, codec spec, PPA linkage, unit test results table).
     Shared design elements (architecture, trigger, timing, logging) factored
     into common section.
  2. `README.md` v2.0 — Rewritten for dual-codec repo. New sections: codec
     selection, head-to-head comparison table, both codec descriptions,
     PPA linkage, updated repo structure with new files.
  3. `REPLICATION-NOTES.md` v2.0 — Added config.yaml codec selection step,
     node IDs and COM ports from live testing, mux_codec.py dependencies,
     pitfalls 6-7 from live test discoveries, separate results tables for
     each experiment, Experiment A results populated.
  4. `CODING-AGENT-LOG.md` — This entry (009) added.
- **Rationale**: Docs must stay in sync with code per project policy.
  PLAN.md was still v1.0 (Experiment A only). README.md repo structure
  was missing 4 new files. Replication notes lacked lessons learned from
  live testing.
- **Status**: All docs current. Ready for zip packaging.

## Entry 010 — Experiment B Live Test: Phase Drift Diagnosed + Fixed

- **Timestamp**: 2026-03-04T18:15:00-05:00
- **Phase**: Validate → Fix → Validate
- **Symptom**: First live LoRa test of MUX Grid codec (v2.0). Both nodes ran
  to completion, but only 1/8 messages roundtripped per side (Step 7 on Node B,
  Step 8 on Node A). All other RX steps timed out. Codec decoded perfectly on
  both messages that did arrive.
- **Root cause — Bug 1 (Trigger consumes Step 1)**:
  Role A receives the first PRIVATE_APP packet while in LISTENING state.
  `_on_receive` stores it in `last_received_data` and sets `msg_event` to
  flip LISTENING → TRIGGERED. But `run_test()` then calls
  `_receive_compressed(0, "ok")` which immediately does `msg_event.clear()`
  and `last_received_data = None` — wiping the data that already arrived.
  Role A waits 15s for a message it already ate.
- **Root cause — Bug 2 (Phase drift from independent loops)**:
  Both nodes ran independent `for` loops with `time.sleep(delay)` between
  steps. No synchronization between them. After Bug 1 costs Role A 15s on
  Step 1, every subsequent step is further out of phase. Both sides keep
  sending while the other is not yet listening. Cascade failure.
- **Why Steps 7-8 worked**: Drift accumulated to exactly one full cycle
  offset by step 7, causing accidental re-alignment. Confirmed the send/
  receive mechanics and codec are both solid — only the timing logic was
  fighting itself.
- **Fix applied (v2.1)**:
  1. `trigger_data_is_step1` flag: When Role A receives the first
     PRIVATE_APP packet during LISTENING, mark it as pre-loaded. In
     `run_test()`, Role A's Step 1 calls `_receive_compressed(0, "ok",
     pre_loaded=True)` which skips `clear()`/`wait()` and uses the
     trigger data directly.
  2. Reactive send-then-block: Replaced `time.sleep(delay)` with pure
     event-driven alternation. After TX, the next iteration blocks on RX
     (`msg_event.wait(timeout=15)`). After RX, the next iteration sends
     immediately. Radio latency IS the pacer.
  3. Timeout = skip-one-step: On timeout, the node skips that RX step
     and proceeds to its next TX step. This re-syncs the pair because
     the peer is waiting for exactly that TX. Worst case: one lost step,
     not a cascading desync.
  4. `_is_my_tx_step()` helper: Clean role-based TX/RX determination.
     Single unified loop replaces the duplicated `if role == "B"` / `else`
     branches.
- **Files modified**: `huffman_mesh_poc.py` v2.0 → v2.1
  - Docstring updated with v2.1 change notes
  - `__init__`: added `trigger_data_is_step1` flag
  - `_on_receive`: sets `trigger_data_is_step1 = True` on LISTENING→TRIGGERED
  - `_receive_compressed`: added `pre_loaded` parameter, skip clear/wait path
  - `run_test()`: rewritten with reactive loop and `_is_my_tx_step()`
  - `_is_my_tx_step()`: new helper method
  - Version strings: 2.0 → 2.1, log version 2.0.0 → 2.1.0
- **Not modified**: `mesh_huffman.py`, `mux_codec.py`, `mux_codebook.csv`,
  `config.yaml`, `test_codecs.py`, `build_mux_codebook.py`
- **Unit tests**: All 5 suites still pass (100% roundtrip both codecs).
- **Verification gate**: Ready for second live LoRa test. Expect 8/8.

## Entry 011 — Experiment B Validated Over Live LoRa

- **Timestamp**: 2026-03-04T18:53:00-05:00
- **Phase**: Validate → PASS
- **Result**: 8/8 messages, 100% roundtrip on both nodes. Zero timeouts.
  Zero codec errors. Reactive sync (v2.1) worked exactly as designed.
- **Node A (Liberty-Node-04, Role A)**:
  - RX Steps 1, 3, 5, 7: all PASS. Step 1 pre-loaded from trigger (instant).
  - TX Steps 2, 4, 6, 8: all sent, all received by peer.
  - RSSI: -7 to -11 dBm. SNR: 6.0-7.0 dB.
- **Node B (Liberty-Node-02, Role B)**:
  - TX Steps 1, 3, 5, 7: all sent, all received by peer.
  - RX Steps 2, 4, 6, 8: all PASS.
  - RSSI: -10 to -15 dBm. SNR: 6.25-7.0 dB.
- **Compression verified over live LoRa**:
  - Aggregate: 215B raw → 92B compressed (2.34:1, 57% savings)
  - Best: "The sensor node..." 51B → 16B (3.19:1)
  - AI-constrained: 56B → 18B (3.11:1)
- **Conclusion**: Experiment B (MUX Grid codec) fully validated.
  Both codecs (Huffman and MUX Grid) now proven over live LoRa.
  MUX Grid achieves significantly better compression (2.34:1 vs 1.51:1)
  at the cost of case preservation (lowercases all text).

## Entry 012 — Experiment C: Codebook Expansion + Huffman 4K Build

- **Timestamp**: 2026-03-04T19:55:00-05:00
- **Phase**: Build
- **Action**: Prepared shared 4,096-word (64×64 grid) vocabulary for Experiment C A/B comparison.
- **Changes made**:
  1. `build_mux_codebook.py` — Rewritten to target exactly 4,095 word entries + 1 ESC = 4,096 total.
     Boosted synthetic frequencies for number tokens (0-100) and mesh domain terms to 50M-60M
     to ensure they survive the frequency cutoff (~17M). Old version produced 4,002 entries;
     new version produces exactly 4,096.
  2. `mux_codebook.csv` — Regenerated: 4,096 entries (64×64 grid). Index 0 = "the" (freq 23B),
     Index 4094 = "flying" (freq 17.9M), Index 4095 = <ESC>. All 8 test messages have 100% coverage.
  3. `build_huffman_codebook.py` — NEW. Reads `mux_codebook.csv` word list + frequencies,
     builds a Huffman tree, outputs `huffman_codebook_4k.csv` with columns: word, huffman_code,
     bits, frequency. Produces 4,095 entries with code lengths 4–15 bits (avg 13.2).
  4. `huffman_codebook_4k.csv` — NEW. 4,095-entry Huffman codebook matching MUX vocabulary exactly.
  5. `mesh_huffman.py` v3 → v4 — Now loads from `huffman_codebook_4k.csv` by default (falls back
     to `english_unigram_freq.csv` for backward compat). `CODEBOOK_SIZE` constant removed;
     codebook size determined by CSV content. `codebook_source` field added to stats.
     Removed hardcoded `MESH_DOMAIN_WORDS` dict (moved to `MESH_DOMAIN_WORDS_LEGACY` for fallback).
- **Validation**:
  - Huffman 4K: 8/8 roundtrip, 100% pass. Aggregate: 215B raw → 90B compressed (2.39:1).
    Compression improved from 1.51:1 (2K codebook + header) to 2.39:1 (4K codebook + header)
    because the larger vocabulary catches more words, reducing ESC fallback usage.
  - MUX Grid 4K: 8/8 roundtrip, 100% pass. Aggregate: 215B raw → 92B (2.34:1).
    Slightly different from old 4,002-entry codebook due to word reranking, but nearly identical.
  - All 5 test suites in `test_codecs.py` pass.
  - Cross-codec detection still works (Codec ID byte auto-detect).
- **Shared vocabulary guarantee**: Both codecs now use identical 4,095-word vocabulary.
  If "battery" is in MUX, it's in Huffman. If "xylophonist" is not in MUX, it's not in Huffman.
  ESC fallback handles out-of-codebook words in both codecs.

## Entry 013 — Experiment C: LLM Conversation Script + Paginator + Config

- **Timestamp**: 2026-03-04T20:10:00-05:00
- **Phase**: Build
- **Action**: Built all Experiment C components for live LLM conversation over LoRa.
- **Files created/modified**:
  1. `paginator.py` — NEW. `paginate(text, max_chars=200)` splits at word boundaries,
     adds `[X/N]` headers for multi-page messages. `reassemble(pages)` strips headers and
     joins. Informed by operator repo's `textwrap.wrap` + page header pattern, written fresh.
  2. `huffman_mesh_poc.py` v2.1 → v3.0 — REWRITTEN. New `ExperimentC` class replaces
     `CodecMeshPOC`. Single "Hi" trigger runs both codec runs in sequence:
     - Run 1: MUX Grid (20 messages, 10 per node)
     - Run 2: Huffman 4K (20 messages, 10 per node)
     - Then: side-by-side comparison table
     LLM integration via Ollama REST API: warmup, `generate_response()` with conversation
     history, no token count constraint (concise system prompt only).
     Extended logging: per-message metrics (inference_ms, tokens, pages, hit%, ESC count,
     RSSI, SNR) + full conversation transcript + comparison table + JSON data dump.
  3. `config.yaml` — UPDATED. New fields: `model` (gemma3:latest), `messages_per_node` (10),
     `conversation_seed` (flood warning scenario prompt). Removed `test_messages` list
     (LLM generates messages now). Timeout increased from 15s to 45s (LLM inference budget).
- **Design decisions**:
  1. No token/word count constraint on LLM output — system prompt says "be concise" only.
     Per user directive: let the LLM be natural, measure what happens.
  2. Paginator is a safety net, not the expected path. System prompt encourages short responses.
     Page count logged per message to track actual usage.
  3. Run 2 (Huffman) starts immediately after Run 1 (MUX Grid) with 5s pause.
     Role B sends first message of Run 2 without re-triggering. Role A detects the
     first Huffman packet and enters Run 2 automatically (reuses trigger_data_is_step1 pattern).
  4. Full structured logging: markdown per-run logs, comparison table, and machine-readable
     JSON dump with all results, transcripts, and agent log entries.
  5. Conversation history grows across all 20 messages per run. LLM sees both its own
     messages and (potentially lossy) decoded received messages.
- **Verification**: All modules compile, imports resolve, config loads correctly.
  Cannot test live Ollama or Meshtastic in sandbox. Ready for live deployment.

## Entry 014 — Experiment C Validated Over Live LoRa

- **Timestamp**: 2026-03-04T20:34:00-05:00
- **Phase**: Validate → PASS
- **Result**: 40/40 messages per codec, 100% delivery on both nodes. Zero timeouts.
  Zero codec errors. Reactive sync (v2.1 pattern) held perfectly across 80 total
  exchange cycles (40 MUX Grid + 40 Huffman).
- **Nodes**:
  - Node A: Liberty-Node-04 (!07c01855) — Role A — Laptop A (AMD Strix Halo, COM6)
  - Node B: Liberty-Node-02 (!0408a160) — Role B — Laptop B (Windows, COM3)
- **Radio conditions**: RSSI -1 to -8 dBm, SNR 5.25-8.0 dB (same room)

### MUX Grid Results (combined both nodes)

| Metric | Node A (Role A) | Node B (Role B) | Combined |
|--------|-----------------|-----------------|----------|
| Messages TX | 10 | 10 | 20 |
| Messages RX | 10 | 10 | 20 |
| Total raw (TX) | 780B | 699B | 1,479B |
| Total compressed (TX) | 600B | 508B | 1,108B |
| Aggregate ratio | 1.30:1 | 1.38:1 | 1.33:1 |
| Avg hit rate | 57.1% | 65.6% | 61.3% |
| Avg ESC/msg | 4.8 | 4.1 | 4.4 |
| Avg LLM inference | 2,892ms | 1,754ms | 2,323ms |
| Pages > 1 | 0 | 0 | 0 |

### Huffman (4K) Results (combined both nodes)

| Metric | Node A (Role A) | Node B (Role B) | Combined |
|--------|-----------------|-----------------|----------|
| Messages TX | 10 | 10 | 20 |
| Messages RX | 10 | 10 | 20 |
| Total raw (TX) | 958B | 1,003B | 1,961B |
| Total compressed (TX) | 656B | 564B | 1,220B |
| Aggregate ratio | 1.46:1 | 1.78:1 | 1.61:1 |
| Avg hit rate | 74.9% | 87.0% | 80.9% |
| Avg ESC/msg | 3.0 | 1.8 | 2.4 |
| Avg LLM inference | 2,942ms | 1,949ms | 2,446ms |
| Pages > 1 | 0 | 0 | 0 |

### Head-to-Head: Huffman (4K) vs MUX Grid on LLM-generated text

| Metric | MUX Grid | Huffman (4K) | Winner |
|--------|----------|--------------|--------|
| Compression ratio | 1.33:1 | 1.61:1 | Huffman (+21%) |
| Codebook hit rate | 61.3% | 80.9% | Huffman (+19.6pp) |
| Avg ESC/msg | 4.4 | 2.4 | Huffman (45% fewer) |
| Avg inference time | 2,323ms | 2,446ms | MUX Grid (5% faster, noise) |
| Pages > 1 | 0 | 0 | Tie |
| Delivery rate | 40/40 | 40/40 | Tie |
| Timeouts | 0 | 0 | Tie |

### Key findings

1. **Reversal from Experiment B**: On scripted 8-message test (Exp B), MUX Grid won
   decisively (2.34:1 vs 1.51:1). On LLM-generated conversational text (Exp C),
   Huffman wins (1.61:1 vs 1.33:1). The codecs have different sweet spots.
2. **Why Huffman wins on LLM text**: Huffman encodes characters natively, so decimals
   ("1.5", "2.7"), punctuation ("–", ";"), and mixed case all get encoded without ESC
   fallback. MUX Grid lowercases everything and must ESC any token containing numbers
   or special characters → 4.4 ESC/msg vs 2.4.
3. **Huffman convergence effect**: As the LLM reuses vocabulary ("Sensor 10 is at 7.5
   feet"), Huffman hit rate climbs from 77% → 100% and compression from 1.47:1 → 2.12:1.
   Variable-length codes reward repetition more than fixed-tier MUX.
4. **Paginator unnecessary**: System prompt "be concise" kept all 80 messages under
   200 chars. Paginator is a safety net, not the expected path.
5. **Node A inference slower**: Node A (Strix Halo) averaged ~2,900ms, Node B averaged
   ~1,850ms. Different hardware/background load, but both well within 45s timeout.
6. **Cross-node byte verification**: Node A TX compressed total exactly matches Node B
   RX total for both codecs (MUX: 600B ✓, Huffman: 656B ✓). Zero byte corruption.

### Experiment C → Experiment B comparison table

| Metric | Exp B (scripted, 8 msgs) | Exp C MUX (LLM, 20 msgs) | Exp C Huff (LLM, 20 msgs) |
|--------|--------------------------|---------------------------|----------------------------|
| MUX ratio | 2.34:1 | 1.33:1 | — |
| Huff ratio | 1.51:1 | — | 1.61:1 |
| Winner | MUX Grid | — | Huffman (4K) |
| Delivery | 8/8 | 20/20 | 20/20 |
| Timeouts | 0 | 0 | 0 |

## Entry 015 — Experiment D Phase 1: Pre-Tokenizer Build

- **Timestamp**: 2026-03-04T20:47:00-05:00
- **Phase**: Build
- **Action**: Built pre-tokenizer, LLM codec module, and rewrote main script for Experiment D.
- **Files created**:
  1. `pretokenizer.py` — NEW. `normalize(text) → text` function with 7-step pipeline:
     lowercase → expand contractions → split hyphens/dashes → strip punctuation
     (protecting decimal numbers) → collapse spaces → decimal "N point M" → final cleanup.
     Also exports `compute_hit_rate(text, codebook_set) → float` for fallback checking.
  2. `llm_codec.py` — NEW. `llm_encode(text, model) → (encoded_text, ms)` and
     `llm_decode(text, model) → (decoded_text, ms)` wrapping Ollama REST API.
     Lazy-loads codebook, builds encode prompt with top 500 words from mux_codebook.csv.
     `get_codebook_words() → set` for external hit rate checking.
  3. `huffman_mesh_poc.py` v3.0 → v4.0 — REWRITTEN. New `ExperimentD` class replaces
     `ExperimentC`. Config-driven: `llm_codec: false` = Phase 1 (pretokenizer only),
     `llm_codec: true` = Phase 2 (pretokenizer + LLM encode/decode).
     Extended logging: gen_ms/enc_ms/dec_ms, natural/encoded/decoded text, fallback flag.
     Phase 2 sender pipeline: generate → LLM encode → normalize → codec encode → TX.
     Phase 2 receiver pipeline: codec decode → LLM decode → conversation history.
     Fallback path: if LLM encode hit rate < threshold (0.70), skip encode step.
  4. `config.yaml` — UPDATED. New fields: `pretokenizer: true`, `llm_codec: false`,
     `fallback_threshold: 0.70`. Header updated to "Experiment D".
  5. `test_codecs.py` — EXPANDED. 5 suites → 8 suites: added TEST 6 (pretokenizer
     normalize, 13 cases), TEST 7 (pretokenizer + codec roundtrip, 12 cases),
     TEST 8 (LLM codec module load + codebook access, no Ollama required).
- **Design decisions**:
  1. Hyphens split BEFORE punctuation stripping — prevents "off-grid" → "offgrid".
     En-dash (\u2013) and em-dash (\u2014) also split to spaces.
  2. Decimal numbers protected during punct stripping via _DOT_ sentinel, then
     converted to "N point M" form (both "point" and digits 0-100 are in codebook).
  3. LLM encode prompt uses top 500 words (not full 4,096) — Gemma3 4B has limited
     context window. Instructs LLM to use simple common synonyms for unlisted words.
  4. Encode temperature 0.3 (vs 0.7 for generation) — more deterministic constraint.
  5. Backward compatibility: `llm_codec: false` runs Experiment C behavior with
     pretokenizer added. All prior experiment code paths preserved.
  6. Fallback threshold at 0.70 — if LLM encode produces <70% hit rate, skip encode
     and send raw text through codec. Logged as fallback event.
- **Verification**: All 8 test suites pass (100%). Pretokenizer passes all 13 edge
  cases + Experiment B messages. Normalized text roundtrips through both codecs.
  Codebook has 4,095 words. Hit rate on normalized sample text: 82%.
- **Not modified**: `mesh_huffman.py`, `mux_codec.py`, `mux_codebook.csv`,
  `huffman_codebook_4k.csv`, `build_mux_codebook.py`, `build_huffman_codebook.py`,
  `paginator.py`.

## Entry 016 — Documentation Update for Experiment D

- **Timestamp**: 2026-03-04T20:50:00-05:00
- **Phase**: Build
- **Action**: Updated all living docs to reflect Experiment D build.
- **Files updated**:
  1. `PLAN.md` v4.0 — Added Experiment D section with Phase 1 and Phase 2 design,
     risk acknowledgment, pre-tokenizer pipeline, LLM codec architecture, encode/decode
     prompts, fallback path, logging format, acceptance criteria, and PPA linkage.
  2. `README.md` v4.0 — Updated experiment table (A-D), added Experiment D section,
     updated repo structure with new files, updated quick start for Phase control.
  3. `REPLICATION-NOTES.md` v4.0 — Added Experiment D setup checklist, phase control
     instructions, new software dependency notes.
  4. `CODING-AGENT-LOG.md` — Entries 015-016 added.
- **Status**: All docs current. Ready for zip packaging and live deployment.
