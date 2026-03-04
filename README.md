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
│   └── Freedom-Unit-Board-Layout-v2.2.md    # Master PCB spec (830 lines)
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
│       └── create_placeholders.py           # Generate placeholder .kicad_mod
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
