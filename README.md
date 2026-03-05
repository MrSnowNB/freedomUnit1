# Freedom Unit V2 — KiCad Project

4-layer 80x50mm LoRa mesh node PCB. Protocol-agnostic platform supporting Meshtastic, LoRaWAN, Reticulum, and MeshCore.

## Project Status

| Phase | Status | Tool |
|-------|--------|------|
| Board spec | Complete | Manual (v2.2) |
| Schematic generation | Complete | Claude (Perplexity Computer) |
| Schematic validation | Passes in KiCad 9 | KiCad 9.0 |
| Footprint assignment | Complete | Gemini CLI |
| Netlist export | Complete | kicad-cli |
| PCB layout (initial) | In progress | Gemini CLI + KiCad GUI |
| Routing | Not started | — |
| Fabrication outputs | Not started | — |

## Architecture

```
nRF52840 (MCU) ──SPI──> Lambda62C-9S (LoRa) ──u.FL──> SMA
    │
    ├──SPI──> MX25R6435F (QSPI Flash)
    ├──SPI──> LCD (10-pin FPC)
    ├──I2C──> MAX-M10S (GPS)
    ├──USB──> USB4085 (USB-C) + TPD2E001 (ESD)
    │
    └──GPIO──> 7x Buttons, 3x LEDs

Power: Solar ──> BQ25504 ──> MCP73831 ──> Battery
                                └──> TPS7A02 (3.3V LDO)
                                └──> TPS22918 (Load Switch)
```

## Repository Structure

```
freedomUnit1/
├── docs/
│   ├── Freedom-Unit-Board-Layout-v2.2.md    # Master PCB spec (830 lines)
│   └── FreedomUnit_V2_Placement_Guide.md    # Component placement reference
├── libs/
│   ├── FreedomUnit.kicad_sym                # Custom symbol library
│   └── FreedomUnit.pretty/                  # Custom footprint library
│       ├── Lambda62C-9S.kicad_mod           # LoRa module (placeholder)
│       ├── CONSMA006.062.kicad_mod          # SMA connector (placeholder)
│       ├── Taoglas_CGGBP.25.4.A.02.kicad_mod
│       └── Johanson_2450AT18D0100.kicad_mod
├── scripts/
│   ├── claude_generators/                   # Reusable schematic generators
│   │   ├── kicad_gen.py                     # Shared helper (symbols, wires, labels)
│   │   ├── generate_sheet1_mcu.py
│   │   ├── generate_sheet2_lora.py
│   │   ├── generate_sheet3_power.py
│   │   ├── generate_sheet4_usb.py
│   │   ├── generate_sheet5_peripherals.py
│   │   └── generate_project_files.py        # Root schematic + .kicad_pro
│   └── gemini_tools/                        # Post-processing utilities
│       ├── assign_footprints.py             # Map lib_id → footprint
│       ├── create_placeholders.py           # Generate placeholder .kicad_mod
│       └── placement_guide.py               # Auto-placement script
├── fab/                                     # Manufacturing outputs
│   ├── FreedomUnit_V2.xml                   # Netlist export
│   └── *.json                               # ERC/DRC reports
├── archive/                                 # Previous attempts (reference only)
│   └── gemini_passes/                       # Gemini's earlier generation scripts
├── FreedomUnit_V2.kicad_pro                 # Project file
├── FreedomUnit_V2.kicad_sch                 # Root schematic (5 sheet refs)
├── Sheet1_MCU.kicad_sch                     # nRF52840 + decoupling + crystals + BLE
├── Sheet2_LoRa.kicad_sch                    # Lambda62C-9S + SMA
├── Sheet3_Power.kicad_sch                   # BQ25504, MCP73831, TPS7A02, TPS22918
├── Sheet4_USB.kicad_sch                     # USB-C + TPD2E001 ESD
├── Sheet5_Peripherals.kicad_sch             # GPS, LCD, buttons, LEDs, flash, I2C
├── FreedomUnit_V2.kicad_pcb                 # PCB layout (in progress)
├── fp-lib-table                             # Footprint library paths
├── sym-lib-table                            # Symbol library paths
├── GEMINI.md                                # AI agent instructions + pin table
└── README.md                                # This file
```

## AI-First Workflow

This project is designed for AI-assisted hardware development. Two AI agents contributed:

### Claude (Perplexity Computer) — Schematic Generation
- Built `kicad_gen.py` helper module that enforces KiCad S-expression format rules
- Generated all 5 sheet schematics + root + project files
- Key insight: use Python generators with format-enforcing helpers, not raw text output

### Gemini CLI — Post-Processing & PCB
- Assigned footprints to all schematic components
- Created custom placeholder footprints
- Exported netlist, ran ERC/DRC
- Generated initial PCB layout with component placement

### For AI agents working on this project
1. Read `GEMINI.md` for technical mandates and pin assignments
2. Read `docs/Freedom-Unit-Board-Layout-v2.2.md` for the full board spec
3. Generator scripts in `scripts/claude_generators/` are the reusable framework
4. Run validation: `kicad-cli sch erc <file>` and `kicad-cli pcb drc <file>`

## Fabrication Target
- **PCB Fab:** MacroFab (Houston, TX) or OSH Park
- **Gerbers:** RS-274X (No X2), separate PTH/NPTH drill files
- **Board:** 4-layer, 80x50mm, 1.6mm thickness

---

# CyberMesh Codec POC

Dual-codec text compression over LoRa mesh radio with LLM-driven conversation
and LLM-as-codec. Two laptops, two Heltec V3 nodes, Gemma3 4B, zero internet.

## What This Proves

Four experiments progressively prove that LLM-generated messages can be compressed,
transmitted over LoRa radio, and decompressed with full fidelity — culminating in
an LLM that rewrites its own output to maximize compression before transmission.

| Experiment | Codec | Codebook | Status |
|-----------|-------|----------|--------|
| A | Huffman (word-level, variable-length) | 2,048 words | Validated over live LoRa |
| B | MUX Grid (tiered fixed-width index) | 4,002 entries | Validated over live LoRa (8/8, 2.34:1) |
| C | Both codecs, LLM conversation | 4,096 shared (64×64) | Validated: 40/40, Huffman 1.61:1 vs MUX 1.33:1 |
| D-Ph1 | Pre-tokenizer + both codecs, LLM conversation | 4,096 shared | Built, ready for live test |
| D-Ph2 | LLM encode/decode + both codecs | 4,096 shared | Built, ready for live test |

```
Laptop A                    LoRa 915 MHz                    Laptop B
┌──────────┐                                          ┌──────────┐
│ Gemma3 4B│  generate → [LLM encode] → normalize()   │ Gemma3 4B│
│ +codecs  │  → codec.encode() → sendData(raw)        │ +codecs  │
│ pretok   │  → [3B hdr + data] → LoRa →              │ pretok   │
│ llm_codec│  codec.decode() → [LLM decode] → history │ llm_codec│
└──────────┘                                          └──────────┘
        Heltec V3 ◄────── LoRa ──────► Heltec V3
```

## Quick Start

### Requirements

- 2 laptops (Windows/Linux/Mac)
- 2 Heltec V3 Meshtastic nodes (USB serial)
- Python 3.10+
- `pip install meshtastic pyyaml requests`
- Ollama with `gemma3:latest` pre-pulled (Experiments C & D)

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
llm_codec: true            # Phase 2: pretokenizer + LLM encode/decode + codec
fallback_threshold: 0.70   # Phase 2 only: skip LLM encode if hit rate < 70%
```

Backward compatible: `llm_codec: false` runs Experiment C behavior with pre-tokenizer added.

### Output

- Console: real-time TX/RX log with compression ratios, hit rates, inference timing
- `logs/experiment-log_YYYYMMDD_HHMMSS.md`: full results with YAML frontmatter

## How It Works

1. **Trigger**: You DM `Hi` from one physical Heltec to the other
2. **Role assignment**: Receiver of `Hi` = Role B (sends first). Other node = Role A
3. **LLM generates** a response from conversation history (Gemma3 4B via Ollama)
4. **LLM encodes** (Phase 2 only): rewrites output using codebook words only
5. **Pre-tokenizer normalizes**: lowercase, expand contractions, strip punctuation
6. **Codec encodes**: Huffman or MUX Grid compress to binary
7. **Transport**: `sendData(portNum=256)` — 3-byte header + compressed payload
8. **Codec decodes**: receiver auto-detects codec from header Byte 0
9. **LLM decodes** (Phase 2 only): expands compressed text to natural English
10. **Conversation continues**: decoded text enters history for next LLM turn
11. **Logging**: every message logged with full pipeline metrics

## The Codecs

### Huffman — `mesh_huffman.py` v4 (Experiments A, C, D)

- 4,095-word codebook from shared `huffman_codebook_4k.csv` (64×64 grid vocabulary)
- Variable-length Huffman codes — frequent words get shorter codes (4-15 bits)
- Implicit spaces between tokens (1-bit NOSPACE flag for exceptions)
- Case encoding: 1-bit lowercase, 2-bit capitalized/UPPER
- Number encoding: variable-width binary (8/16/32 bit)
- Unknown words: ESC + 5-bit length + 7-bit ASCII fallback
- Case-sensitive roundtrip

### MUX Grid — `mux_codec.py` (Experiments B, C, D)

- 4,096-entry frequency-sorted codebook (`mux_codebook.csv`, 64×64 grid)
- Tiered bit packing: 7-bit (top 64), 10-bit (next 192), 14-bit (rest)
- ESC fallback for unknown words (index 4095)
- Case-insensitive (all text lowercased at encode)
- Generated by `build_mux_codebook.py` from Kaggle data

### Pre-Tokenizer — `pretokenizer.py` (Experiment D)

- Normalizes LLM output before codec encoding: lowercase, expand contractions,
  split hyphens, strip punctuation, convert decimals ("2.1" → "2 point 1")
- Reduces ESC-triggering patterns from Experiment C
- `compute_hit_rate()` checks codebook coverage for fallback decisions

### LLM Codec — `llm_codec.py` (Experiment D Phase 2)

- LLM rewrites its own output using only codebook vocabulary before encoding
- Receiver LLM expands compressed text back to natural English
- Encode prompt: top 500 codebook words as examples, temperature 0.3
- Fallback: if hit rate <70%, skip encode and send raw through codec

### Head-to-Head Results

**Unit Test (4K Shared Codebook, No Radio):**

| Metric | Huffman 4K | MUX Grid |
|--------|-----------|----------|
| Aggregate (8 msgs) | 90B (2.39:1) | 92B (2.34:1) |
| Codebook size | 4,095 words | 4,095 entries + ESC |
| Case preservation | Yes | No (lowercases) |

**Experiment C Live Results (40 msgs/codec, Live LoRa):**

| Metric | MUX Grid | Huffman 4K |
|--------|----------|------------|
| Aggregate ratio | 1.33:1 | 1.61:1 |
| Codebook hit rate | 61.3% | 80.9% |
| Avg ESC/msg | 4.4 | 2.4 |
| Delivery | 40/40 (100%) | 40/40 (100%) |

Winner on LLM text: **Huffman 4K**. Winner on scripted text: **MUX Grid**.
Codecs have complementary strengths depending on vocabulary predictability.

## PPA Linkage

This POC implements concepts from the CyberMesh Provisional Patent Application
(filed Nov 2025):

- **Codec ID byte** (packet header Byte 0) = first implementation of the
  Adaptive Multiplexer described in Claim 24
- **Shared static codebook** = initial state analogous to SVD basis matrix (PPA §2.3)
- **Tiered bit packing** = bandwidth-adaptive encoding per PPA §3.1
- **LLM as lossy codec** (Experiment D) = sending LLM compresses meaning by
  substituting rare vocabulary with common codebook synonyms, analogous to PPA's
  lossy SVD delta compression (§2.3)
- **Receiver LLM reconstruction** = analogous to PPA's Zombie Protocol reconstruction
  from compressed deltas and neighborhood aggregates
- **Fallback path** = analogous to PPA's checkpoint restoration when reconstruction
  error exceeds threshold

## Project Context

This POC is part of the **Liberty Mesh** project — distributed AI over
LoRa mesh radio for Lawrence Township, NJ (Spring 2026 deployment).

The codebook-based compression is the foundation of the **AI First Language**
concept: LLMs constrained to codebook-only vocabulary via system prompt,
producing messages that compress optimally for transmission over
bandwidth-constrained LoRa radio. Experiment D Phase 2 proves this thesis
directly — the LLM functions as a lossy codec.

---

*Mindtech Mesh Networks — Liberty Mesh Project*
*CC BY-SA 4.0 v4.0*