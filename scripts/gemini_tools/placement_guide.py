#!/usr/bin/env python3
"""
Freedom Unit V2 — AI-First Component Placement Script
======================================================
Run with KiCad 9's bundled Python:
    "C:\Program Files\KiCad\9.0\bin\python.exe" placement_guide.py

This script opens FreedomUnit_V2.kicad_pcb, places every component at its
target (x, y) coordinate with correct orientation, then saves.

COORDINATE SYSTEM
-----------------
KiCad origin (0,0) is top-left. +X is right, +Y is DOWN.
All coordinates below are in mm, referenced to a board whose:
  - Top-left corner = (0, 0)
  - Bottom-right corner = (80, 50)
  - Center = (40, 25)

The concept render (Freedom-Unit-Prototype-Concept-2.jpg) maps to this
80×50 mm rectangle as follows:

  BOARD TOP (Y=0)
  ┌──────────────────────────────────────────────────────┐
  │  GPS patch antenna (top-left)    SMA connector (top- │
  │  25×25mm ceramic                 right, edge-mount)  │
  │                                                      │
  │         ┌────────────────────────┐                   │
  │         │  Sharp Memory LCD      │                   │
  │         │  (centered, upper)     │                   │
  │         └────────────────────────┘                   │
  │              ● ● ●  (3 LEDs)                         │
  │                                                      │
  │  [A]   [▲]              [B]        Slide switch ──── │ (right edge)
  │     [◄][●][►]                                        │
  │        [▼]                                           │
  │                                                      │
  │  BLE antenna              nRF52840 (center-bottom)   │
  │  (bottom-left edge)       + crystals + flash         │
  │               ┌──┐                                   │
  │               │USB│                                  │
  └───────────────┴──┴───────────────────────────────────┘
  BOARD BOTTOM (Y=50)

EXECUTION
---------
The script:
  1. Opens the .kicad_pcb file
  2. Iterates through PLACEMENTS dict
  3. For each refdes, calls SetPosition() and SetOrientationDegrees()
  4. Saves the file

If a refdes is missing from the PCB (not yet imported from netlist),
the script prints a warning and continues.

AFTER RUNNING: Open the PCB in KiCad, run DRC, and visually verify.
"""

import sys
import os

# ---------------------------------------------------------------------------
# CONFIG — edit this path to match the user's machine
# ---------------------------------------------------------------------------
PCB_PATH = r"C:\Users\AMD\FreedomUnit_V2_Repo\FreedomUnit_V2.kicad_pcb"

# ---------------------------------------------------------------------------
# PLACEMENT TABLE
# Each entry: "RefDes": (x_mm, y_mm, rotation_degrees, "description")
#
# Rotation: 0° = component as drawn in footprint (pin 1 top-left)
#           90° = rotated 90° clockwise
#           180° = flipped
#           270° = rotated 90° counter-clockwise
# ---------------------------------------------------------------------------

PLACEMENTS = {
    # ===========================================================================
    # ZONE 1 — TOP EDGE: GPS antenna + SMA connector + LoRa module
    # ===========================================================================
    # GPS ceramic patch antenna — 25×25mm — top-left quadrant
    # CONSTRAINT: solid GND plane underneath on L2, no traces under patch
    # CONSTRAINT: opposite end from LoRa SMA for RF isolation
    # NOTE: The GPS patch antenna may not have a schematic symbol / refdes.
    # If it was added as a board-only footprint, its refdes might be ANT2, ANT_GPS,
    # or a custom designator. The script will skip it if not found.
    # MANUAL STEP: If missing, add the Taoglas CGGBP.25.4.A.02 footprint manually
    # at position (15.0, 12.5) with solid GND pour on L2 underneath.
    "ANT_GPS": (15.0, 12.5, 0, "Taoglas CGGBP.25.4.A.02 — 25x25mm GPS patch, centered at (15, 12.5)"),

    # SMA edge-mount connector — top-right corner
    # CONSTRAINT: at board edge, short u.FL pigtail to Lambda62
    "J2": (76.0, 5.0, 270, "TE/Linx CONSMA006.062 SMA — edge-mount, top-right"),

    # Lambda62C-9S LoRa module — 23×20mm — near SMA connector
    # CONSTRAINT: close to SMA for short u.FL cable, near board edge
    "U3": (64.0, 14.0, 0, "Lambda62C-9S LoRa module — top-right area, near SMA"),

    # Lambda62 decoupling
    "C10": (56.0, 8.0, 0, "Lambda62 100nF decoupling"),
    "C11": (56.0, 11.0, 0, "Lambda62 100nF decoupling"),

    # ===========================================================================
    # ZONE 2 — UPPER-CENTER: LCD display connector
    # ===========================================================================
    # Sharp Memory LCD FPC connector (Molex 10-pin, 0.5mm pitch)
    # The LCD visible area is ~35×25mm per concept render
    # FPC connector goes near top edge, LCD ribbon routes up/out
    "J4": (40.0, 5.0, 0, "Molex 5051100892 LCD FPC connector — centered top edge"),

    # ===========================================================================
    # ZONE 3 — MID-BAND: LEDs (below LCD window)
    # ===========================================================================
    # Three status LEDs in a row — concept shows Red, Green, Blue left-to-right
    # Positioned just below where the LCD display area would be visible
    "D2": (33.0, 27.0, 0, "Red LED — left"),
    "D3": (40.0, 27.0, 0, "Green LED — center"),
    "D4": (47.0, 27.0, 0, "Blue LED — right"),

    # LED series resistors (680Ω each) — behind/below their LEDs
    "R7": (33.0, 29.0, 0, "680Ω for Red LED"),
    "R8": (40.0, 29.0, 0, "680Ω for Green LED"),
    "R9": (47.0, 29.0, 0, "680Ω for Blue LED"),

    # ===========================================================================
    # ZONE 4 — BUTTON AREA: A, B, D-pad (5 buttons + 2 action buttons)
    # ===========================================================================
    # Layout from concept render:
    #   [A]    [▲]         [B]
    #      [◄] [●] [►]
    #          [▼]
    #
    # A button — top-left of button cluster
    "SW2": (15.0, 31.0, 0, "BTN_A — primary action (SOS)"),

    # B button — top-right of button cluster
    "SW3": (50.0, 31.0, 0, "BTN_B — back/cancel"),

    # D-pad UP
    "SW4": (32.5, 31.0, 0, "BTN_UP — D-pad up"),

    # D-pad LEFT
    "SW5": (26.5, 36.0, 0, "BTN_LEFT — D-pad left"),

    # D-pad CENTER (confirm/select)
    "SW6": (32.5, 36.0, 0, "BTN_CENTER — D-pad center press"),

    # D-pad RIGHT
    "SW7": (38.5, 36.0, 0, "BTN_RIGHT — D-pad right"),

    # D-pad DOWN
    "SW8": (32.5, 41.0, 0, "BTN_DOWN — D-pad down"),

    # Button debounce caps (100nF each) — clustered near buttons, back side ok
    "C12": (18.0, 33.0, 0, "100nF debounce — BTN_A"),
    "C13": (53.0, 33.0, 0, "100nF debounce — BTN_B"),
    "C14": (35.5, 31.0, 0, "100nF debounce — BTN_UP"),
    "C15": (26.5, 38.5, 0, "100nF debounce — BTN_LEFT"),
    "C16": (35.5, 36.0, 0, "100nF debounce — BTN_CENTER"),
    "C17": (38.5, 38.5, 0, "100nF debounce — BTN_RIGHT"),
    "C18": (35.5, 41.0, 0, "100nF debounce — BTN_DOWN"),

    # ===========================================================================
    # ZONE 5 — CENTER/BOTTOM: nRF52840 MCU + support components
    # ===========================================================================
    # nRF52840 AQFN-73 — the brain — center-bottom area of board
    # CONSTRAINT: decoupling within 2mm, crystals within 5mm
    "U1": (40.0, 38.0, 0, "nRF52840-QIAA — AQFN-73, board center-lower"),

    # 32 MHz crystal — within 5mm of XC1/XC2 (near nRF52840)
    "Y1": (46.0, 34.5, 0, "Abracon ABM8 32MHz HFXO — near nRF52840"),

    # 32 MHz crystal load caps (12pF each)
    "C32": (48.5, 33.5, 0, "12pF load cap — 32MHz XC1"),
    "C33": (48.5, 35.5, 0, "12pF load cap — 32MHz XC2"),

    # 32.768 kHz crystal — within 5mm of XL1/XL2
    "Y2": (34.0, 34.5, 0, "Abracon ABS07 32.768kHz LFXO — near nRF52840"),

    # 32.768 kHz crystal load caps (6pF each)
    "C34": (31.5, 33.5, 0, "6pF load cap — 32.768kHz XL1"),
    "C35": (31.5, 35.5, 0, "6pF load cap — 32.768kHz XL2"),

    # nRF52840 VDD decoupling — 100nF on each VDD, within 2mm
    "C19": (36.0, 35.0, 0, "100nF VDD decoupling — nRF52840"),
    "C20": (44.0, 35.0, 0, "100nF VDD decoupling — nRF52840"),
    "C21": (36.0, 41.0, 0, "100nF VDD decoupling — nRF52840"),
    "C22": (44.0, 41.0, 0, "100nF VDD decoupling — nRF52840"),

    # nRF52840 bulk cap (1µF)
    "C23": (37.0, 43.0, 0, "1µF bulk — nRF52840"),

    # DEC1 (100nF), DEC4 (1µF), DEC6 (100nF) — internal regulators, within 2mm
    "C24": (43.0, 43.0, 0, "100nF DEC1 — nRF52840 internal reg"),
    "C36": (40.0, 43.5, 0, "1µF DEC4 — nRF52840 internal reg"),
    # C35 is already used for 32.768kHz load cap above
    # DEC6 100nF — use a new refdes if available, otherwise place manually
    # "C_DEC6": (38.0, 43.5, 90, "100nF DEC6 — nRF52840 internal reg"),

    # QSPI Flash — close to nRF52840 for short traces
    "U10": (50.0, 42.0, 0, "Macronix MX25R6435F QSPI flash — near nRF52840"),

    # BLE matching network + chip antenna
    # CONSTRAINT: antenna at board edge, 5mm ground keepout around it
    # CONSTRAINT: opposite end from LoRa SMA (so bottom-left)
    "L1": (6.0, 44.0, 90, "3.9nH matching inductor — BLE pi network"),
    "ANT1": (3.0, 47.0, 0, "Johanson 2450AT18D0100 BLE chip antenna — bottom-left edge"),

    # ===========================================================================
    # ZONE 6 — RIGHT EDGE: Slide switch
    # ===========================================================================
    # Physical slide switch — accessible through enclosure
    "SW1": (78.0, 25.0, 90, "C&K JS102011SAQN slide switch — right edge, mid-height"),

    # ===========================================================================
    # ZONE 7 — BOTTOM EDGE: USB-C connector
    # ===========================================================================
    # USB-C centered on bottom edge
    "J3": (40.0, 49.0, 0, "GCT USB4085-GF-A USB-C — centered bottom edge"),

    # USB ESD protection — close to connector
    "U6": (35.0, 46.0, 0, "TPD2E001 ESD — near USB-C"),

    # CC pulldown resistors (5.1kΩ) — close to USB-C
    "R5": (44.0, 46.0, 0, "5.1kΩ CC1 pulldown — USB-C"),
    "R6": (46.0, 46.0, 0, "5.1kΩ CC2 pulldown — USB-C"),

    # ===========================================================================
    # ZONE 8 — POWER SECTION: left side, between GPS and buttons
    # ===========================================================================
    # Power ICs grouped together, away from RF areas
    #
    # Battery holder — large component, bottom-left area (back of board)
    "BT1": (20.0, 45.0, 0, "Keystone 1042P 18650 holder — bottom area (back side)"),

    # Solar connector — left edge
    "J1": (2.0, 25.0, 90, "JST S2B-PH-K-S solar — left edge, mid-height"),

    # BQ25504 solar energy harvester
    "U4": (10.0, 20.0, 0, "TI BQ25504 solar MPPT — left side power zone"),

    # BQ25504 support caps
    "C1": (7.0, 18.0, 0, "BQ25504 input cap"),
    "C2": (13.0, 18.0, 0, "BQ25504 output cap"),
    "C3": (7.0, 22.0, 0, "BQ25504 storage cap"),
    "C4": (13.0, 22.0, 0, "BQ25504 bypass cap"),

    # BQ25504 programming resistors
    "R1": (16.0, 18.0, 0, "BQ25504 OV threshold resistor"),
    "R2": (16.0, 20.0, 0, "BQ25504 UV threshold resistor"),

    # MCP73831 USB charger
    "U5": (10.0, 26.0, 0, "MCP73831 USB Li-Ion charger"),

    # MCP73831 support
    "C5": (7.0, 26.0, 0, "MCP73831 input cap"),
    "C6": (13.0, 26.0, 0, "MCP73831 output cap"),
    "R3": (16.0, 26.0, 0, "2kΩ PROG resistor — sets 500mA charge"),

    # OR-ing Schottky diode
    "D1": (10.0, 30.0, 0, "BAT54JFILM Schottky OR-ing diode"),

    # LDO regulator
    "U7": (10.0, 33.0, 0, "TPS7A02 3.3V LDO"),
    "C7": (7.0, 33.0, 0, "1µF LDO input cap"),
    "C8": (13.0, 33.0, 0, "1µF LDO output cap"),

    # Load switch
    "U8": (10.0, 36.0, 0, "TPS22918 load switch"),

    # Battery voltage divider
    "R10": (20.0, 30.0, 90, "100kΩ top — battery voltage divider"),
    # Note: R10 is the only divider resistor in the schematic;
    # if a second resistor exists with a different refdes, add it here.

    # ===========================================================================
    # ZONE 9 — GPS MODULE
    # ===========================================================================
    # u-blox MAX-M10S — near GPS patch antenna
    "U9": (15.0, 22.0, 0, "u-blox MAX-M10S GPS — near GPS patch antenna"),

    # GPS I2C pull-ups (4.7kΩ) — near GPS/I2C bus
    "R4": (22.0, 22.0, 0, "4.7kΩ I2C SDA pull-up"),
    # (If there's a second I2C pullup with a different refdes, add here)

    # I2C expansion header — near board edge
    "J5": (78.0, 40.0, 90, "I2C expansion header — right edge, lower"),
}

# ---------------------------------------------------------------------------
# ZONES — keepout / special areas (for reference and ground pour config)
# ---------------------------------------------------------------------------
KEEPOUT_ZONES = [
    {
        "name": "GPS_ANTENNA_KEEPOUT",
        "description": "No traces on any layer under GPS ceramic patch. Solid GND on L2.",
        "x_min": 2.5, "y_min": 0.0, "x_max": 27.5, "y_max": 25.0,
        "layers": ["F.Cu", "B.Cu"],  # Keep signal traces away; GND plane on In1.Cu is OK
    },
    {
        "name": "BLE_ANTENNA_KEEPOUT",
        "description": "No copper pour within 5mm of BLE chip antenna at bottom-left corner.",
        "x_min": 0.0, "y_min": 42.0, "x_max": 8.0, "y_max": 50.0,
        "layers": ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"],
    },
]

# ---------------------------------------------------------------------------
# BOARD OUTLINE
# ---------------------------------------------------------------------------
BOARD_OUTLINE = {
    "width_mm": 80.0,
    "height_mm": 50.0,
    "corner_radius_mm": 1.5,  # Slight rounding for enclosure fit
    "mounting_holes": [
        # M2.5 mounting holes at 4 corners, 3mm inset
        (3.0, 3.0),
        (77.0, 3.0),
        (3.0, 47.0),
        (77.0, 47.0),
    ],
}

# ===========================================================================
# EXECUTION ENGINE
# ===========================================================================

def main():
    """
    Open PCB, apply placements, save.
    Run this with KiCad's Python: the pcbnew module is only available there.
    """
    try:
        import pcbnew
    except ImportError:
        print("ERROR: pcbnew module not found.")
        print("Run with KiCad's Python:")
        print('  "C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" placement_guide.py')
        sys.exit(1)

    if not os.path.exists(PCB_PATH):
        print(f"ERROR: PCB file not found: {PCB_PATH}")
        print("Edit PCB_PATH at the top of this script to point to your .kicad_pcb file.")
        sys.exit(1)

    print(f"Opening: {PCB_PATH}")
    board = pcbnew.LoadBoard(PCB_PATH)

    # Build a lookup of refdes → footprint
    fp_map = {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        fp_map[ref] = fp

    placed = 0
    skipped = 0
    warnings = []

    # KiCad uses nanometers internally. pcbnew.FromMM() converts mm → nm.
    for ref, (x_mm, y_mm, rotation, desc) in PLACEMENTS.items():
        if ref not in fp_map:
            warnings.append(f"  SKIP: {ref} — not found in PCB (not imported from netlist?)")
            skipped += 1
            continue

        fp = fp_map[ref]

        # Set position
        pos = pcbnew.VECTOR2I(pcbnew.FromMM(x_mm), pcbnew.FromMM(y_mm))
        fp.SetPosition(pos)

        # Set rotation
        fp.SetOrientationDegrees(rotation)

        print(f"  PLACED: {ref:8s} → ({x_mm:6.1f}, {y_mm:6.1f}) rot={rotation:3d}°  | {desc}")
        placed += 1

    # Save
    board.Save(PCB_PATH)
    print(f"\nDone. Saved to: {PCB_PATH}")
    print(f"  Placed: {placed}")
    print(f"  Skipped: {skipped}")

    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(w)

    print("\n--- NEXT STEPS ---")
    print("1. Open FreedomUnit_V2.kicad_pcb in KiCad PCB Editor")
    print("2. Tools → Update PCB from Schematic (if components are missing)")
    print("3. Place → Spread Footprints (if any are stacked)")
    print("4. Run DRC (Inspect → Design Rules Check)")
    print("5. Begin routing traces")


if __name__ == "__main__":
    main()
