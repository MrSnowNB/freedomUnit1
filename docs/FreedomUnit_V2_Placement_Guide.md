# Freedom Unit V2 — Component Placement Guide (AI-First)

> **Purpose:** This document maps every component on the Freedom Unit V2 PCB
> to exact (x, y) coordinates on an 80×50 mm board. It is designed for an
> AI agent (Gemini CLI, Claude, etc.) to execute programmatically via the
> KiCad `pcbnew` Python API.
>
> **Companion script:** `placement_guide.py` — run it to auto-place all components.
>
> **Source of truth:** `Freedom-Unit-Board-Layout-v2.2.md` (830-line master spec)
> and `Freedom-Unit-Prototype-Concept-2.jpg` (product concept render).

---

## Board Coordinate System

```
          X →  (0 to 80 mm)
     (0,0)─────────────────────────────────(80,0)
       │                                        │
   Y   │          80 mm × 50 mm                 │
   ↓   │          4-layer FR4                   │
       │          ENIG finish                   │
       │                                        │
     (0,50)────────────────────────────────(80,50)
```

- **Origin:** Top-left corner = (0, 0)
- **+X:** Right
- **+Y:** Down
- **Units:** All values in millimeters
- **KiCad note:** pcbnew uses nanometers internally. Use `pcbnew.FromMM(value)` to convert.

---

## Zone Map

The board is divided into 9 functional zones. Components within each zone
are physically grouped for short trace routing and RF isolation.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ZONE 1: GPS+LoRa (Y: 0–25)                                                │
│                                                                             │
│  ┌─────────────┐                    ┌──────────────┐   ┌───┐               │
│  │  GPS PATCH   │                    │  Lambda62C    │   │SMA│               │
│  │  25×25mm     │    ┌──LCD FPC──┐   │  23×20mm     │   │   │               │
│  │  (15, 12.5)  │    │ (40, 5)   │   │  (64, 14)    │   │J2 │               │
│  └─────────────┘    └───────────┘   └──────────────┘   └───┘               │
│                                                                             │
│  ┌─MAX-M10S──┐   ┌──BQ25504──┐                                             │
│  │  (15, 22) │   │  (10, 20) │                                             │
│  └───────────┘   └───────────┘                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ ZONE 3: LEDs (Y: 25–30)          │  ZONE 6: Slide Switch (right edge)      │
│  ●R (33,27) ●G (40,27) ●B (47,27)│  SW1 (78, 25) rotated 90°              │
├────────────────────────────────────┤                                        │
│ ZONE 4: Buttons (Y: 30–42)       │  ZONE 8: Power (X: 2–20)               │
│                                    │  U4 BQ25504 (10, 20)                   │
│  [A](15,31)  [▲](32.5,31)  [B](50,31)  U5 MCP73831 (10, 26)              │
│        [◄](26.5,36) [●](32.5,36) [►](38.5,36)  D1 BAT54J (10, 30)       │
│              [▼](32.5,41)         │  U7 TPS7A02 (10, 33)                   │
│                                    │  U8 TPS22918 (10, 36)                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ ZONE 5: MCU (Y: 34–45, centered)                                           │
│                                                                             │
│  BLE ant ←─── nRF52840 (40, 38) ───→ QSPI flash                           │
│  (3, 47)      Y1 32MHz (46, 34.5)     U10 (50, 42)                        │
│               Y2 32.768k (34, 34.5)                                        │
│                                                                             │
├──────────────────────────┬──────────────────────────────────────────────────┤
│ ZONE 7: USB-C (bottom)  │  BT1 Battery holder (20, 45) — back side        │
│  J3 (40, 49)             │  J5 I2C header (78, 40) — right edge            │
│  U6 ESD (35, 46)         │                                                  │
└──────────────────────────┴──────────────────────────────────────────────────┘
```

---

## Complete Placement Table

### Zone 1 — RF: GPS Antenna + LoRa Module + SMA

| RefDes | Component | X (mm) | Y (mm) | Rot | Footprint Size | Constraints |
|--------|-----------|--------|--------|-----|----------------|-------------|
| ANT_GPS | Taoglas CGGBP.25.4.A.02 | 15.0 | 12.5 | 0° | 25×25 mm | Solid GND on L2 underneath. No traces under patch. |
| J2 | TE/Linx CONSMA006.062 SMA | 76.0 | 5.0 | 270° | Edge-mount | At board edge. Short u.FL pigtail to Lambda62. |
| U3 | Lambda62C-9S LoRa | 64.0 | 14.0 | 0° | 23×20 mm | Near SMA. Module has internal RF shielding. |
| C10 | 100nF (Lambda62 decoup) | 56.0 | 8.0 | 0° | 0402 | |
| C11 | 100nF (Lambda62 decoup) | 56.0 | 11.0 | 0° | 0402 | |

### Zone 2 — LCD Connector

| RefDes | Component | X (mm) | Y (mm) | Rot | Footprint Size | Constraints |
|--------|-----------|--------|--------|-----|----------------|-------------|
| J4 | Molex 5051100892 FPC | 40.0 | 5.0 | 0° | 10-pin, 0.5mm pitch | Centered on top edge. Ribbon cable routes to LCD. |

### Zone 3 — Status LEDs

| RefDes | Component | X (mm) | Y (mm) | Rot | Notes |
|--------|-----------|--------|--------|-----|-------|
| D2 | Red LED | 33.0 | 27.0 | 0° | Fault / SOS |
| D3 | Green LED | 40.0 | 27.0 | 0° | Mesh connected |
| D4 | Blue LED | 47.0 | 27.0 | 0° | BLE connected |
| R7 | 680Ω (Red) | 33.0 | 29.0 | 0° | Series resistor |
| R8 | 680Ω (Green) | 40.0 | 29.0 | 0° | Series resistor |
| R9 | 680Ω (Blue) | 47.0 | 29.0 | 0° | Series resistor |

### Zone 4 — Buttons (D-Pad + A/B)

| RefDes | Component | X (mm) | Y (mm) | Rot | Pin Map |
|--------|-----------|--------|--------|-----|---------|
| SW2 | BTN_A (SOS) | 15.0 | 31.0 | 0° | P1.00 → PIN_BUTTON1 |
| SW3 | BTN_B (back) | 50.0 | 31.0 | 0° | P1.01 → PIN_BUTTON2 |
| SW4 | BTN_UP | 32.5 | 31.0 | 0° | P1.10 |
| SW5 | BTN_LEFT | 26.5 | 36.0 | 0° | P0.11 |
| SW6 | BTN_CENTER | 32.5 | 36.0 | 0° | P0.08 |
| SW7 | BTN_RIGHT | 38.5 | 36.0 | 0° | P0.06 |
| SW8 | BTN_DOWN | 32.5 | 41.0 | 0° | P0.18 |
| C12–C18 | 100nF debounce (×7) | near each button | | 0° | One per button |

### Zone 5 — MCU Core (nRF52840 + Crystals + Flash)

| RefDes | Component | X (mm) | Y (mm) | Rot | Constraints |
|--------|-----------|--------|--------|-----|-------------|
| U1 | nRF52840-QIAA (AQFN-73) | 40.0 | 38.0 | 0° | Central placement. All decoupling within 2mm. |
| Y1 | 32 MHz crystal (Abracon ABM8) | 46.0 | 34.5 | 0° | Within 5mm of XC1/XC2. Symmetric traces. |
| Y2 | 32.768 kHz crystal (Abracon ABS07) | 34.0 | 34.5 | 0° | Within 5mm of XL1/XL2. |
| C32 | 12pF (32MHz XC1) | 48.5 | 33.5 | 0° | Adjacent to Y1 |
| C33 | 12pF (32MHz XC2) | 48.5 | 35.5 | 0° | Adjacent to Y1 |
| C34 | 6pF (32.768k XL1) | 31.5 | 33.5 | 0° | Adjacent to Y2 |
| C35 | 6pF (32.768k XL2) | 31.5 | 35.5 | 0° | Adjacent to Y2 |
| C19–C22 | 100nF VDD decoupling (×4) | around U1 | | 0° | Within 2mm of each VDD pin |
| C23 | 1µF bulk | 37.0 | 43.0 | 0° | Near U1 |
| C24 | 100nF DEC1 | 43.0 | 43.0 | 0° | Within 2mm, short GND |
| C36 | 1µF DEC4 | 40.0 | 43.5 | 0° | Within 2mm, short GND |
| U10 | MX25R6435F QSPI flash | 50.0 | 42.0 | 0° | Short QSPI traces to U1 |

### Zone 5b — BLE Antenna (Bottom-Left Edge)

| RefDes | Component | X (mm) | Y (mm) | Rot | Constraints |
|--------|-----------|--------|--------|-----|-------------|
| L1 | 3.9nH inductor (pi match) | 6.0 | 44.0 | 90° | Part of BLE matching network |
| ANT1 | Johanson 2450AT18D0100 | 3.0 | 47.0 | 0° | Board edge. 5mm GND keepout around it. Opposite end from LoRa SMA. |

### Zone 6 — Slide Switch (Right Edge)

| RefDes | Component | X (mm) | Y (mm) | Rot | Notes |
|--------|-----------|--------|--------|-----|-------|
| SW1 | C&K JS102011SAQN | 78.0 | 25.0 | 90° | Through-hole. Accessible through all enclosure variants. |

### Zone 7 — USB-C (Bottom Edge)

| RefDes | Component | X (mm) | Y (mm) | Rot | Notes |
|--------|-----------|--------|--------|-----|-------|
| J3 | GCT USB4085-GF-A | 40.0 | 49.0 | 0° | Centered on bottom edge |
| U6 | TPD2E001 ESD | 35.0 | 46.0 | 0° | Between connector and MCU |
| R5 | 5.1kΩ CC1 pulldown | 44.0 | 46.0 | 0° | Close to J3 |
| R6 | 5.1kΩ CC2 pulldown | 46.0 | 46.0 | 0° | Close to J3 |

### Zone 8 — Power (Left Side)

| RefDes | Component | X (mm) | Y (mm) | Rot | Notes |
|--------|-----------|--------|--------|-----|-------|
| J1 | JST S2B-PH-K-S solar | 2.0 | 25.0 | 90° | Left edge, THT right-angle |
| U4 | BQ25504 solar MPPT | 10.0 | 20.0 | 0° | Thermal pad to GND plane |
| C1–C4 | BQ25504 caps | 7–13 | 18–22 | 0° | Around U4 |
| R1 | OV threshold resistor | 16.0 | 18.0 | 0° | BQ25504 programming |
| R2 | UV threshold resistor | 16.0 | 20.0 | 0° | BQ25504 programming |
| U5 | MCP73831 USB charger | 10.0 | 26.0 | 0° | VBUS from USB-C |
| C5–C6 | MCP73831 caps | 7, 13 | 26.0 | 0° | Around U5 |
| R3 | 2kΩ PROG resistor | 16.0 | 26.0 | 0° | Sets 500mA charge |
| D1 | BAT54JFILM Schottky | 10.0 | 30.0 | 0° | OR-ing diode |
| U7 | TPS7A02 LDO 3.3V | 10.0 | 33.0 | 0° | |
| C7 | 1µF LDO input | 7.0 | 33.0 | 0° | |
| C8 | 1µF LDO output | 13.0 | 33.0 | 0° | |
| U8 | TPS22918 load switch | 10.0 | 36.0 | 0° | EN ← P0.12 |
| R10 | 100kΩ battery divider | 20.0 | 30.0 | 90° | ADC on P0.04 (AIN2) |
| BT1 | Keystone 1042P 18650 holder | 20.0 | 45.0 | 0° | Back side of board |

### Zone 9 — GPS Module

| RefDes | Component | X (mm) | Y (mm) | Rot | Notes |
|--------|-----------|--------|--------|-----|-------|
| U9 | u-blox MAX-M10S | 15.0 | 22.0 | 0° | Near GPS patch antenna |
| R4 | 4.7kΩ I2C pull-up | 22.0 | 22.0 | 0° | Shared with I2C expansion |

### Expansion / Debug

| RefDes | Component | X (mm) | Y (mm) | Rot | Notes |
|--------|-----------|--------|--------|-----|-------|
| J5 | I2C expansion header (4-pin) | 78.0 | 40.0 | 90° | Right edge, not populated in initial run |

---

## RF Keepout Zones

These areas must be free of copper (except dedicated ground planes where noted).

| Zone | Corners (mm) | Layer Restriction | Reason |
|------|-------------|-------------------|--------|
| GPS Antenna | (2.5, 0) → (27.5, 25) | No traces on F.Cu or B.Cu. Solid GND on In1.Cu. | GPS patch needs clean ground plane reference. |
| BLE Antenna | (0, 42) → (8, 50) | No copper on any layer within 5mm of chip antenna. | BLE radiation pattern requires clear zone at board edge. |

---

## Mounting Holes

4× M2.5 plated through-holes for standoffs.

| Hole | X (mm) | Y (mm) |
|------|--------|--------|
| MH1 | 3.0 | 3.0 |
| MH2 | 77.0 | 3.0 |
| MH3 | 3.0 | 47.0 |
| MH4 | 77.0 | 47.0 |

---

## How to Use This Guide

### For Gemini CLI / AI Agents

```bash
# Option 1: Run the placement script directly
"C:\Program Files\KiCad\9.0\bin\python.exe" placement_guide.py

# Option 2: Use the PLACEMENTS dict in your own script
import placement_guide
for ref, (x, y, rot, desc) in placement_guide.PLACEMENTS.items():
    print(f"{ref}: ({x}, {y}) @ {rot}°")
```

### For Manual KiCad Editing

1. Open `FreedomUnit_V2.kicad_pcb` in KiCad PCB Editor
2. Select a component, press `E` to edit properties
3. Set X and Y position from the table above
4. Set rotation angle
5. Repeat for all components

### Post-Placement Checklist

- [ ] Run DRC (Inspect → Design Rules Check)
- [ ] Verify all decoupling caps are within 2mm of their IC
- [ ] Verify both crystals are within 5mm of nRF52840
- [ ] Verify GPS keepout zone has no traces
- [ ] Verify BLE keepout zone has no copper
- [ ] Verify SMA connector is at board edge with short path to Lambda62 u.FL
- [ ] Verify USB-C connector is centered on bottom edge
- [ ] Verify slide switch is accessible at right edge
- [ ] Check that battery holder doesn't overlap with bottom-side components

---

## Design Rationale

The placement follows these principles from the master spec:

1. **RF isolation** — GPS patch (1575 MHz) at top-left, LoRa SMA (915 MHz) at top-right, BLE chip antenna (2.4 GHz) at bottom-left. Maximum physical separation.
2. **User interface forward** — LCD, LEDs, and buttons face the user in the handheld enclosure. Their positions match the concept render exactly.
3. **Power isolation** — All power management ICs are on the left side, away from RF sections.
4. **Short critical traces** — nRF52840 is central, with crystals, decoupling, and QSPI flash within a few mm.
5. **Enclosure compatibility** — USB-C bottom-center, slide switch right edge, SMA top-right all match the 3D-printed enclosure design for all three variants (Handheld, Repeater, Anchor).

---

## File Manifest

| File | Purpose |
|------|---------|
| `placement_guide.py` | Executable Python script — run with KiCad 9 Python to auto-place all components |
| `FreedomUnit_V2_Placement_Guide.md` | This document — human + AI readable reference |
| `Freedom-Unit-Board-Layout-v2.2.md` | Master PCB spec (source of truth for all design decisions) |
| `Freedom-Unit-Prototype-Concept-2.jpg` | Product concept render (target layout) |
