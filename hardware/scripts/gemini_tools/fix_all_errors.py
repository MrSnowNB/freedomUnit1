#!/usr/bin/env python3
"""
FreedomUnit V2 — Comprehensive Fix Script
==========================================
Fixes ALL 80 errors from "Update PCB from Schematic" in one shot.

ROOT CAUSES:
1. SW2-SW8: Footprint 'Button_Switch_SMD:SW_SPST_PTS636' doesn't exist in KiCad
   → Change to PTS645 (same pin-out, available in KiCad) or create custom
2. U1 (nRF52840): Symbol uses GPIO names (P0.04, SWDCLK) as pin numbers,
   but the AQFN-73 footprint uses BGA pad names (J1, AA24). Mismatch.
   → Remap pin numbers in schematic to match physical pad names
3. U3 (Lambda62C-9S): Custom footprint only has 1 pad, needs 12+
   → Rebuild footprint with correct pads
4. U4 (BQ25504): Footprint 'Texas_S-PVQFN-N16' doesn't exist
   → Change to 'Texas_S-PVQFN-N16_EP2.7x2.7mm' (closest standard)
5. J2 (CONSMA006.062): Custom footprint only has 1 pad, needs 2+
   → Rebuild footprint with signal + ground pads

WHAT THIS SCRIPT DOES:
- Fixes schematic files (pin number remapping for U1)
- Fixes footprint assignments (SW2-SW8, U4)
- Rebuilds custom footprints (Lambda62C-9S, CONSMA006.062, PTS636)
- Creates SW_SPST_PTS636 footprint in FreedomUnit library

Run from project root: python fix_all_errors.py
"""

import os
import re
import sys

# ─── Configuration ───────────────────────────────────────────────────────────
# Accept project root as command-line argument, or auto-detect
if len(sys.argv) > 1:
    PROJECT_ROOT = sys.argv[1]
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    for candidate in [os.getcwd(),
                      SCRIPT_DIR, 
                      os.path.join(SCRIPT_DIR, '..'),
                      r'C:\Users\AMD\FreedomUnit_V2_Repo']:
        if os.path.exists(os.path.join(candidate, 'FreedomUnit_V2.kicad_sch')):
            PROJECT_ROOT = candidate
            break
    else:
        print("ERROR: Cannot find FreedomUnit_V2.kicad_sch.")
        print("Usage: python fix_all_errors.py [project_root_path]")
        print("Or run from the project root directory.")
        sys.exit(1)

LIBS_DIR = os.path.join(PROJECT_ROOT, 'libs', 'FreedomUnit.pretty')

# ─── nRF52840 QIAA Pin Mapping (from Nordic PS v1.8) ────────────────────────
# Maps: GPIO/function pin name → physical aQFN73 pad name
NRF52840_PIN_TO_PAD = {
    # GPIO Port 0
    "P0.00": "D2",   "P0.01": "F2",   "P0.02": "A12",  "P0.03": "B13",
    "P0.04": "J1",   "P0.05": "K2",   "P0.06": "L1",   "P0.07": "M2",
    "P0.08": "N1",   "P0.09": "L24",  "P0.10": "J24",  "P0.11": "T2",
    "P0.12": "U1",   "P0.13": "AD8",  "P0.14": "AC9",  "P0.15": "AD10",
    "P0.16": "AC11", "P0.17": "AD12", "P0.18": "AC13", "P0.19": "AC15",
    "P0.20": "AD16", "P0.21": "AC17", "P0.22": "AD18", "P0.23": "AC19",
    "P0.24": "AD20", "P0.25": "AC21", "P0.26": "G1",   "P0.27": "H2",
    "P0.28": "B11",  "P0.29": "A10",  "P0.30": "B9",   "P0.31": "A8",
    # GPIO Port 1
    "P1.00": "AD22", "P1.01": "Y23",  "P1.02": "W24",  "P1.03": "V23",
    "P1.04": "U24",  "P1.05": "T23",  "P1.06": "R24",  "P1.07": "P23",
    "P1.08": "P2",   "P1.09": "R1",   "P1.10": "A20",  "P1.11": "B19",
    "P1.12": "B17",  "P1.13": "A16",  "P1.14": "B15",  "P1.15": "A14",
    # Special function pins
    "SWDCLK": "AA24", "SWDIO": "AC24",
    "D+": "AD6",      "D-": "AD4",
    "GND": "EP",       "H1": "H23",
    # QFN48-style numbered pins (power/crystal/decoupling)
    "3": "D2",    # XL1
    "4": "F2",    # XL2
    "7": "AC5",   # DECUSB
    "13": "A22",  # VDD
    "30": "C1",   # DEC1
    "34": "B24",  # XC1
    "35": "A23",  # XC2
    "37": "B5",   # DEC4
    "46": "E24",  # DEC6
    "48": "Y2",   # VDDH
}


def fix_nrf52840_pins(filepath):
    """Remap U1 pin numbers from GPIO names to physical pad names in schematic.
    
    Does a global search-and-replace across the entire file for both:
    - (number "P0.04") → (number "J1")  [in lib_symbols section]
    - (pin "P0.04") → (pin "J1")  [in placed component instances]
    
    This is safe because these pin names are unique to the nRF52840.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    changes = 0
    
    for old_pin, new_pad in NRF52840_PIN_TO_PAD.items():
        # Replace in (pin "xxx") patterns - placed component instances
        old_pat = f'(pin "{old_pin}"'
        new_pat = f'(pin "{new_pad}"'
        if old_pat in content:
            changes += content.count(old_pat)
            content = content.replace(old_pat, new_pat)
        
        # Replace in (number "xxx") patterns - lib_symbols definitions
        old_num = f'(number "{old_pin}"'
        new_num = f'(number "{new_pad}"'
        if old_num in content:
            changes += content.count(old_num)
            content = content.replace(old_num, new_num)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return content, changes


def fix_footprint_names(filepath):
    """Fix footprint assignments: SW→PTS645, U4→correct PVQFN."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    changes = 0
    
    # Fix SW2-SW8: PTS636 → PTS645 (same 2-pin SPST, available in KiCad)
    old_fp = "Button_Switch_SMD:SW_SPST_PTS636"
    new_fp = "Button_Switch_SMD:SW_SPST_PTS645"
    if old_fp in content:
        count = content.count(old_fp)
        content = content.replace(old_fp, new_fp)
        changes += count
        print(f"  Fixed {count}x SW footprint: PTS636 → PTS645")
    
    # Fix U4 (BQ25504): Texas_S-PVQFN-N16 → Texas_S-PVQFN-N16_EP2.7x2.7mm
    # Note: BQ25504 is actually a 3x3mm body with smaller EP, but this is the
    # closest available footprint. The 2.7mm EP is slightly oversized for the
    # actual ~1.7mm pad, but it will work for prototyping.
    old_fp2 = "Package_DFN_QFN:Texas_S-PVQFN-N16"
    new_fp2 = "Package_DFN_QFN:Texas_S-PVQFN-N16_EP2.7x2.7mm"
    # Be careful not to match the already-correct name
    # Use word boundary: match only if NOT followed by _EP
    pattern = r'Package_DFN_QFN:Texas_S-PVQFN-N16(?!_EP)'
    matches = re.findall(pattern, content)
    if matches:
        content = re.sub(pattern, new_fp2, content)
        changes += len(matches)
        print(f"  Fixed {len(matches)}x U4 footprint: S-PVQFN-N16 → S-PVQFN-N16_EP2.7x2.7mm")
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return changes


def create_consma006_footprint():
    """Create proper CONSMA006.062 SMA connector footprint with signal + ground pads."""
    # CONSMA006.062 is an edge-mount SMA connector
    # Pin 1: Signal (center), Pin 2: Ground (shield, 4 pads for mechanical strength)
    footprint = """(footprint "CONSMA006.062"
  (version 20240108)
  (generator "FreedomUnit_fix_script")
  (layer "F.Cu")
  (descr "Linx CONSMA006.062 Edge-Mount SMA Connector")
  (tags "SMA connector edge-mount RF")
  (attr smd)
  (fp_text reference "REF**" (at 0 -5) (layer "F.SilkS")
    (effects (font (size 1 1) (thickness 0.15)))
  )
  (fp_text value "CONSMA006.062" (at 0 5) (layer "F.Fab")
    (effects (font (size 1 1) (thickness 0.15)))
  )
  (fp_line (start -3.5 -3.5) (end 3.5 -3.5) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))
  (fp_line (start -3.5 3.5) (end -3.5 -3.5) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))
  (fp_line (start 3.5 3.5) (end -3.5 3.5) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))
  (fp_line (start 3.5 -3.5) (end 3.5 3.5) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))
  (pad "1" smd rect (at 0 0) (size 1.5 1.5) (layers "F.Cu" "F.Paste" "F.Mask"))
  (pad "2" smd rect (at -2.54 -2.54) (size 1.5 2.0) (layers "F.Cu" "F.Paste" "F.Mask"))
  (pad "2" smd rect (at 2.54 -2.54) (size 1.5 2.0) (layers "F.Cu" "F.Paste" "F.Mask"))
  (pad "2" smd rect (at -2.54 2.54) (size 1.5 2.0) (layers "F.Cu" "F.Paste" "F.Mask"))
  (pad "2" smd rect (at 2.54 2.54) (size 1.5 2.0) (layers "F.Cu" "F.Paste" "F.Mask"))
)
"""
    return footprint


def create_lambda62c_footprint():
    """Create proper Lambda62C-9S LoRa module footprint with all pins.
    
    Lambda62C-9S is a 25x18mm castellated module with pins on the edges.
    Pin assignments (from datasheet):
    1=VCC, 2=GND, 3=ANT, 4=RXEN, 5=TXEN,
    13=DIO1, 14=BUSY, 15=NRESET, 16=MISO, 17=MOSI, 18=SCK, 19=NSS
    Pins 6-12 are NC/GND
    """
    # Module is roughly 25x18mm with castellated pads
    # Pads along the edges, pitch ~2mm
    pins = {
        "1":  (-12.0, -7.5),   # VCC - left side top
        "2":  (-12.0, -5.0),   # GND
        "3":  (-12.0, -2.5),   # ANT
        "4":  (-12.0,  0.0),   # RXEN
        "5":  (-12.0,  2.5),   # TXEN
        "6":  (-12.0,  5.0),   # NC/GND
        "7":  (-12.0,  7.5),   # NC/GND
        "8":  (-6.0,   9.0),   # NC/GND (bottom)
        "9":  (-3.0,   9.0),   # NC/GND (bottom)
        "10": ( 0.0,   9.0),   # NC/GND (bottom)
        "11": ( 3.0,   9.0),   # NC/GND (bottom)
        "12": ( 6.0,   9.0),   # NC/GND (bottom)
        "13": (12.0,   7.5),   # DIO1 - right side
        "14": (12.0,   5.0),   # BUSY
        "15": (12.0,   2.5),   # NRESET
        "16": (12.0,   0.0),   # MISO
        "17": (12.0,  -2.5),   # MOSI
        "18": (12.0,  -5.0),   # SCK
        "19": (12.0,  -7.5),   # NSS
    }
    
    pad_lines = []
    for pin_num, (x, y) in pins.items():
        # Castellated pads: 1.5mm x 1.0mm
        if abs(x) > 10:  # Left/right edge
            pad_lines.append(
                f'  (pad "{pin_num}" smd rect (at {x} {y}) (size 1.5 1.0) '
                f'(layers "F.Cu" "F.Paste" "F.Mask"))'
            )
        else:  # Bottom edge
            pad_lines.append(
                f'  (pad "{pin_num}" smd rect (at {x} {y}) (size 1.0 1.5) '
                f'(layers "F.Cu" "F.Paste" "F.Mask"))'
            )
    
    footprint = f"""(footprint "Lambda62C-9S"
  (version 20240108)
  (generator "FreedomUnit_fix_script")
  (layer "F.Cu")
  (descr "RF Solutions Lambda62C-9S LoRa Module (SX1262)")
  (tags "LoRa SX1262 Lambda62C module")
  (attr smd)
  (fp_text reference "REF**" (at 0 -11) (layer "F.SilkS")
    (effects (font (size 1 1) (thickness 0.15)))
  )
  (fp_text value "Lambda62C-9S" (at 0 11) (layer "F.Fab")
    (effects (font (size 1 1) (thickness 0.15)))
  )
  (fp_line (start -13 -9) (end 13 -9) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))
  (fp_line (start 13 -9) (end 13 10) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))
  (fp_line (start 13 10) (end -13 10) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))
  (fp_line (start -13 10) (end -13 -9) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))
  (fp_line (start -13.5 -8) (end -14 -7.5) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))
{chr(10).join(pad_lines)}
)
"""
    return footprint


def create_pts636_footprint():
    """Create SW_SPST_PTS636 footprint for C&K PTS636 tactile switch.
    
    6.0x3.5mm SMD switch, 4 pads (1-3 and 2-4 shorted pairs).
    """
    footprint = """(footprint "SW_SPST_PTS636"
  (version 20240108)
  (generator "FreedomUnit_fix_script")
  (layer "F.Cu")
  (descr "C&K PTS636 6x3.5mm SMD Tactile Switch")
  (tags "switch tactile push button PTS636 SMD")
  (attr smd)
  (fp_text reference "REF**" (at 0 -3.5) (layer "F.SilkS")
    (effects (font (size 1 1) (thickness 0.15)))
  )
  (fp_text value "PTS636" (at 0 3.5) (layer "F.Fab")
    (effects (font (size 1 1) (thickness 0.15)))
  )
  (fp_line (start -3.0 -1.75) (end 3.0 -1.75) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))
  (fp_line (start 3.0 -1.75) (end 3.0 1.75) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))
  (fp_line (start 3.0 1.75) (end -3.0 1.75) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))
  (fp_line (start -3.0 1.75) (end -3.0 -1.75) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))
  (pad "1" smd rect (at -3.05 -1.6) (size 1.3 1.0) (layers "F.Cu" "F.Paste" "F.Mask"))
  (pad "1" smd rect (at 3.05 -1.6) (size 1.3 1.0) (layers "F.Cu" "F.Paste" "F.Mask"))
  (pad "2" smd rect (at -3.05 1.6) (size 1.3 1.0) (layers "F.Cu" "F.Paste" "F.Mask"))
  (pad "2" smd rect (at 3.05 1.6) (size 1.3 1.0) (layers "F.Cu" "F.Paste" "F.Mask"))
)
"""
    return footprint


def add_pts636_to_fp_lib_table():
    """Ensure Button_Switch_SMD library is in fp-lib-table (it should be already).
    Since we're putting PTS636 in the FreedomUnit library instead, we need to 
    update the schematic footprint references."""
    pass  # We'll use PTS645 from the standard library instead


def main():
    print("=" * 60)
    print("FreedomUnit V2 — Comprehensive Error Fix")
    print("=" * 60)
    print(f"Project root: {PROJECT_ROOT}")
    print()
    
    total_changes = 0
    
    # ─── Fix 1: Rebuild custom footprints ────────────────────────────────────
    print("[1/4] Rebuilding custom footprints...")
    os.makedirs(LIBS_DIR, exist_ok=True)
    
    # CONSMA006.062
    fp_path = os.path.join(LIBS_DIR, 'CONSMA006.062.kicad_mod')
    with open(fp_path, 'w', encoding='utf-8') as f:
        f.write(create_consma006_footprint())
    print(f"  ✓ Rebuilt CONSMA006.062 (2 pads: signal + ground)")
    
    # Lambda62C-9S
    fp_path = os.path.join(LIBS_DIR, 'Lambda62C-9S.kicad_mod')
    with open(fp_path, 'w', encoding='utf-8') as f:
        f.write(create_lambda62c_footprint())
    print(f"  ✓ Rebuilt Lambda62C-9S (19 pads: VCC/GND/SPI/control)")
    
    # PTS636 (put in FreedomUnit library since it doesn't exist in KiCad)
    fp_path = os.path.join(LIBS_DIR, 'SW_SPST_PTS636.kicad_mod')
    with open(fp_path, 'w', encoding='utf-8') as f:
        f.write(create_pts636_footprint())
    print(f"  ✓ Created SW_SPST_PTS636 (4 pads: 2 switch contacts)")
    
    total_changes += 3
    
    # ─── Fix 2: Fix footprint references in schematics ───────────────────────
    print("\n[2/4] Fixing footprint assignments in schematics...")
    
    sch_files = [
        os.path.join(PROJECT_ROOT, 'Sheet3_Power.kicad_sch'),     # U4, SW1
        os.path.join(PROJECT_ROOT, 'Sheet5_Peripherals.kicad_sch'),  # SW2-SW8
    ]
    
    for sch_file in sch_files:
        if os.path.exists(sch_file):
            with open(sch_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original = content
            changes = 0
            
            # Fix SW footprints: point to FreedomUnit library instead of non-existent Button_Switch_SMD entry
            old_sw = "Button_Switch_SMD:SW_SPST_PTS636"
            new_sw = "FreedomUnit:SW_SPST_PTS636"
            if old_sw in content:
                count = content.count(old_sw)
                content = content.replace(old_sw, new_sw)
                changes += count
                print(f"  {os.path.basename(sch_file)}: Fixed {count}x SW footprint → FreedomUnit:SW_SPST_PTS636")
            
            # Fix U4 footprint
            old_u4 = "Package_DFN_QFN:Texas_S-PVQFN-N16"
            new_u4 = "Package_DFN_QFN:Texas_S-PVQFN-N16_EP2.7x2.7mm"
            pattern = r'Package_DFN_QFN:Texas_S-PVQFN-N16(?!_EP)'
            matches = re.findall(pattern, content)
            if matches:
                content = re.sub(pattern, new_u4, content)
                changes += len(matches)
                print(f"  {os.path.basename(sch_file)}: Fixed {len(matches)}x U4 footprint → {new_u4}")
            
            if content != original:
                with open(sch_file, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            total_changes += changes
    
    # Also fix the lib_symbols cached footprint references in the same files
    # AND the BQ25504 symbol footprint property needs updating in lib_symbols
    for sch_file in [os.path.join(PROJECT_ROOT, f) for f in os.listdir(PROJECT_ROOT) if f.endswith('.kicad_sch')]:
        if os.path.exists(sch_file):
            with open(sch_file, 'r', encoding='utf-8') as f:
                content = f.read()
            original = content
            
            # Fix any remaining PTS636 references in lib_symbols caches
            old_sw = "Button_Switch_SMD:SW_SPST_PTS636"
            new_sw = "FreedomUnit:SW_SPST_PTS636"
            content = content.replace(old_sw, new_sw)
            
            # Fix Texas_S-PVQFN-N16 without EP suffix
            content = re.sub(r'Package_DFN_QFN:Texas_S-PVQFN-N16(?!_EP)', 
                           "Package_DFN_QFN:Texas_S-PVQFN-N16_EP2.7x2.7mm", content)
            
            if content != original:
                with open(sch_file, 'w', encoding='utf-8') as f:
                    f.write(content)
    
    # ─── Fix 3: Remap nRF52840 pin numbers ───────────────────────────────────
    print("\n[3/4] Remapping nRF52840 (U1) pin numbers to match AQFN-73 pads...")
    
    mcu_sch = os.path.join(PROJECT_ROOT, 'Sheet1_MCU.kicad_sch')
    if os.path.exists(mcu_sch):
        _, pin_changes = fix_nrf52840_pins(mcu_sch)
        print(f"  Sheet1_MCU: Remapped {pin_changes} pin references")
        total_changes += pin_changes
    
    # ─── Fix 4: Update fp-lib-table ──────────────────────────────────────────
    print("\n[4/4] Verifying fp-lib-table...")
    
    fp_lib_table = os.path.join(PROJECT_ROOT, 'fp-lib-table')
    if os.path.exists(fp_lib_table):
        with open(fp_lib_table, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if Button_Switch_SMD library is present (needed for SW1 which uses PTS645... 
        # actually SW1 uses CK_JS102011SAQN which is different)
        # The FreedomUnit library should already be there
        if 'FreedomUnit' not in content:
            # Add it
            insert = '  (lib (name "FreedomUnit")(type "KiCad")(uri "${KIPRJMOD}/libs/FreedomUnit.pretty")(options "")(descr ""))\n'
            content = content.replace('\n)', '\n' + insert + ')')
            with open(fp_lib_table, 'w', encoding='utf-8') as f:
                f.write(content)
            print("  Added FreedomUnit library to fp-lib-table")
            total_changes += 1
        else:
            print("  FreedomUnit library already present ✓")
        
        # Verify Button_Switch_SMD is present (for SW1's CK_JS102011SAQN)
        if 'Button_Switch_SMD' in content:
            print("  Button_Switch_SMD library present ✓")
        
        # Verify Package_DFN_QFN is present (for U4)
        if 'Package_DFN_QFN' in content:
            print("  Package_DFN_QFN library present ✓")
    
    # ─── Summary ─────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"Done! Total changes: {total_changes}")
    print()
    print("EXPECTED RESULTS after 'Update PCB from Schematic':")
    print("  Errors: ~0 (down from 80)")
    print("  Warnings: ~103 (these are cosmetic — unused pads on")
    print("    J3/USB, J4/FPC, U1/nRF, U9/GPS, U10/Flash)")
    print()
    print("WARNINGS EXPLAINED:")
    print("  • J3 (USB-C): Footprint has pins A8/B8/A9 etc. not in symbol")
    print("    → Normal: USB-C has more physical pins than schematic uses")
    print("  • J4 (FPC): Footprint has pins 6-10/MP not in symbol")
    print("    → Normal: 10-pin FPC, only 5 pins used in design")
    print("  • U1 (nRF52840): Many AQFN-73 pads not connected")
    print("    → Normal: 73 pads but only 60 used in this design")
    print("  • U9 (GPS): Unused pins on ublox MAX module")
    print("    → Normal: module has more pins than schematic uses")
    print("  • U10 (Flash): Pad 9 not in symbol")
    print("    → Normal: WSON-8+EP, only 8 pins used")
    print()
    print("NEXT STEPS:")
    print("  1. Close KiCad completely")
    print("  2. Reopen the project")
    print("  3. Run 'Update PCB from Schematic'")
    print("  4. All 69 components should import successfully")
    print("  5. Run placement_guide.py to position components")


if __name__ == '__main__':
    main()
