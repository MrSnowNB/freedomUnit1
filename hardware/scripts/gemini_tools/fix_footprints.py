#!/usr/bin/env python3
"""
Freedom Unit V2 — Footprint Fix Script
=======================================
Fixes THREE problems preventing "Update PCB from Schematic":

1. MISSING LIBRARIES in fp-lib-table (9 libraries to add)
2. WRONG FOOTPRINT ASSIGNMENTS in schematics (5 components)
3. EMPTY FOOTPRINT FIELDS in schematics (4 components)

Run with standard Python (NOT KiCad Python):
    python fix_footprints.py

Then open KiCad → Tools → Update PCB from Schematic (F8).
Then run placement_guide.py with KiCad Python.

IMPORTANT: Close KiCad before running this script!
"""

import os
import re
import sys

# ---------------------------------------------------------------------------
# CONFIG — edit these paths if needed
# ---------------------------------------------------------------------------
REPO_DIR = r"C:\Users\AMD\FreedomUnit_V2_Repo"

FP_LIB_TABLE = os.path.join(REPO_DIR, "fp-lib-table")
SYM_LIB_TABLE = os.path.join(REPO_DIR, "sym-lib-table")

SCHEMATIC_FILES = {
    "Sheet1_MCU": os.path.join(REPO_DIR, "Sheet1_MCU.kicad_sch"),
    "Sheet2_LoRa": os.path.join(REPO_DIR, "Sheet2_LoRa.kicad_sch"),
    "Sheet3_Power": os.path.join(REPO_DIR, "Sheet3_Power.kicad_sch"),
    "Sheet4_USB": os.path.join(REPO_DIR, "Sheet4_USB.kicad_sch"),
    "Sheet5_Peripherals": os.path.join(REPO_DIR, "Sheet5_Peripherals.kicad_sch"),
}

# ---------------------------------------------------------------------------
# FIX 1: Missing footprint libraries
# All names verified against https://kicad.github.io/footprints/
# ---------------------------------------------------------------------------
MISSING_FP_LIBS = [
    ('Connector_JST', 'C:/Program Files/KiCad/9.0/share/kicad/footprints/Connector_JST.pretty'),
    ('Connector_PinHeader_2.54mm', 'C:/Program Files/KiCad/9.0/share/kicad/footprints/Connector_PinHeader_2.54mm.pretty'),
    ('Crystal', 'C:/Program Files/KiCad/9.0/share/kicad/footprints/Crystal.pretty'),
    ('LED_SMD', 'C:/Program Files/KiCad/9.0/share/kicad/footprints/LED_SMD.pretty'),
    ('Package_SON', 'C:/Program Files/KiCad/9.0/share/kicad/footprints/Package_SON.pretty'),
    ('Diode_SMD', 'C:/Program Files/KiCad/9.0/share/kicad/footprints/Diode_SMD.pretty'),
    ('Battery', 'C:/Program Files/KiCad/9.0/share/kicad/footprints/Battery.pretty'),
    ('RF_GPS', 'C:/Program Files/KiCad/9.0/share/kicad/footprints/RF_GPS.pretty'),
    ('RF_Antenna', 'C:/Program Files/KiCad/9.0/share/kicad/footprints/RF_Antenna.pretty'),
]

MISSING_SYM_LIBS = [
    ('Connector', 'C:/Program Files/KiCad/9.0/share/kicad/symbols/Connector.kicad_sym'),
    ('LED', 'C:/Program Files/KiCad/9.0/share/kicad/symbols/LED.kicad_sym'),
    ('Switch', 'C:/Program Files/KiCad/9.0/share/kicad/symbols/Switch.kicad_sym'),
    ('Power_Management', 'C:/Program Files/KiCad/9.0/share/kicad/symbols/Power_Management.kicad_sym'),
]

# ---------------------------------------------------------------------------
# FIX 2 + 3: Footprint corrections
# Format: { "RefDes": ("sheet_key", "correct_footprint") }
# All footprint names verified against official KiCad library index
# ---------------------------------------------------------------------------
ALL_FOOTPRINT_FIXES = {
    # WRONG assignments (currently have incorrect footprints):
    "ANT1": ("Sheet1_MCU", "RF_Antenna:Johanson_2450AT18x100"),
    "BT1":  ("Sheet3_Power", "Battery:BatteryHolder_Keystone_1042_1x18650"),
    "D1":   ("Sheet3_Power", "Diode_SMD:D_SOD-323"),
    "J4":   ("Sheet5_Peripherals", "Connector_FFC-FPC:Hirose_FH12-10S-0.5SH_1x10-1MP_P0.50mm_Horizontal"),
    "U5":   ("Sheet3_Power", "Package_TO_SOT_SMD:SOT-23-5"),

    # EMPTY footprint fields (currently blank):
    "U1":   ("Sheet1_MCU", "Package_DFN_QFN:Nordic_AQFN-73-1EP_7x7mm_P0.5mm"),
    "J2":   ("Sheet2_LoRa", "FreedomUnit:CONSMA006.062"),
    "J3":   ("Sheet4_USB", "Connector_USB:USB_C_Receptacle_GCT_USB4085"),
    "U9":   ("Sheet5_Peripherals", "RF_GPS:ublox_MAX"),
}


def add_libs_to_table(table_path, libs, table_type="footprint"):
    """Add missing libraries to a lib-table file."""
    with open(table_path, 'r', encoding='utf-8') as f:
        content = f.read()

    added = 0
    for name, uri in libs:
        if f'(name "{name}")' in content:
            print(f"  SKIP: {name} already present")
            continue

        lib_entry = f'  (lib (name "{name}")(type "KiCad")(uri "{uri}")(options "")(descr ""))\n'
        # Insert before final closing paren
        content = content.rstrip()
        if content.endswith(')'):
            content = content[:-1] + lib_entry + ')\n'
        print(f"  ADDED: {name}")
        added += 1

    with open(table_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return added


def fix_footprint_for_ref(filepath, target_ref, new_footprint):
    """
    Find the symbol with target_ref and set its Footprint property to new_footprint.
    
    Strategy: Read all lines. Find the line with (reference "TARGET_REF").
    Walk backwards to find the enclosing (symbol block.
    Within that block, find the (property "Footprint" "...") line and replace the value.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Step 1: Find the line containing (reference "TARGET_REF")
    ref_line_idx = None
    for i, line in enumerate(lines):
        if f'(reference "{target_ref}")' in line:
            ref_line_idx = i
            break

    if ref_line_idx is None:
        return False, f"reference \"{target_ref}\" not found"

    # Step 2: Walk backwards to find the start of the enclosing (symbol block
    # The symbol block starts with a line matching: \t(symbol
    sym_start = None
    for i in range(ref_line_idx, -1, -1):
        if lines[i].startswith('\t(symbol'):
            sym_start = i
            break

    if sym_start is None:
        return False, "could not find enclosing (symbol block"

    # Step 3: Find the (property "Footprint" "...") line within this symbol block
    # It will be between sym_start and ref_line_idx (properties come before instances)
    fp_line_idx = None
    for i in range(sym_start, ref_line_idx + 20):  # small buffer past ref
        if i >= len(lines):
            break
        if '"Footprint"' in lines[i]:
            fp_line_idx = i
            break

    if fp_line_idx is None:
        return False, "Footprint property not found in symbol block"

    # Step 4: Replace the footprint value in that line
    old_line = lines[fp_line_idx]
    # Pattern: (property "Footprint" "ANYTHING")
    new_line = re.sub(
        r'(property "Footprint" )"[^"]*"',
        f'\\1"{new_footprint}"',
        old_line
    )

    if old_line == new_line:
        return False, "regex replacement had no effect"

    old_fp = re.search(r'"Footprint" "([^"]*)"', old_line)
    old_fp_val = old_fp.group(1) if old_fp else "?"

    lines[fp_line_idx] = new_line

    # Step 5: Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    return True, f'"{old_fp_val}" → "{new_footprint}"'


def main():
    print("Freedom Unit V2 — Footprint Fix Script")
    print("=" * 55)

    # Verify paths
    if not os.path.exists(REPO_DIR):
        print(f"ERROR: Repo not found: {REPO_DIR}")
        print("Edit REPO_DIR at top of script.")
        sys.exit(1)

    missing = [f for f in SCHEMATIC_FILES.values() if not os.path.exists(f)]
    if missing:
        print(f"ERROR: Missing files: {missing}")
        sys.exit(1)

    # FIX 1: Library tables
    print("\n--- FIX 1: Adding missing footprint libraries ---")
    n = add_libs_to_table(FP_LIB_TABLE, MISSING_FP_LIBS)
    print(f"  → {n} footprint libraries added")

    print("\n--- FIX 1b: Adding missing symbol libraries ---")
    n = add_libs_to_table(SYM_LIB_TABLE, MISSING_SYM_LIBS)
    print(f"  → {n} symbol libraries added")

    # FIX 2+3: Footprint assignments
    print("\n--- FIX 2+3: Correcting footprint assignments ---")
    success_count = 0
    fail_count = 0

    for ref, (sheet_key, correct_fp) in ALL_FOOTPRINT_FIXES.items():
        filepath = SCHEMATIC_FILES[sheet_key]
        ok, msg = fix_footprint_for_ref(filepath, ref, correct_fp)
        status = "OK" if ok else "FAIL"
        print(f"  {ref:6s} [{status}] {msg}")
        if ok:
            success_count += 1
        else:
            fail_count += 1

    # Summary
    print("\n" + "=" * 55)
    print(f"RESULTS: {success_count} fixed, {fail_count} failed")
    print("")
    print("NEXT STEPS:")
    print("  1. Open FreedomUnit_V2.kicad_pro in KiCad 9")
    print("  2. Tools → Update PCB from Schematic (F8)")
    print("  3. Click 'Update PCB'")
    print("  4. Close the dialog")
    print('  5. Run: "C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" placement_guide.py')
    print("")
    if fail_count > 0:
        print(f"WARNING: {fail_count} fixes failed — check messages above.")


if __name__ == "__main__":
    main()
