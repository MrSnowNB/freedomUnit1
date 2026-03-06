#!/usr/bin/env python3
"""
Freedom Unit V2 — Final Library Table Fix
==========================================
Adds the 8 missing footprint libraries to fp-lib-table so that
"Update PCB from Schematic" can resolve all 69 component footprints.

Run with standard Python:
    python fix_fp_lib_table.py

Then in KiCad: Tools → Update PCB from Schematic (F8)
Then: "C:\Program Files\KiCad\9.0\bin\python.exe" placement_guide.py
"""

import os
import re
import sys

REPO_DIR = r"C:\Users\AMD\FreedomUnit_V2_Repo"
FP_LIB_TABLE = os.path.join(REPO_DIR, "fp-lib-table")

# These 8 libraries are referenced by schematic footprints but missing from fp-lib-table
LIBS_TO_ADD = [
    ("Button_Switch_SMD", "C:/Program Files/KiCad/9.0/share/kicad/footprints/Button_Switch_SMD.pretty"),
    ("Capacitor_SMD", "C:/Program Files/KiCad/9.0/share/kicad/footprints/Capacitor_SMD.pretty"),
    ("Connector_FFC-FPC", "C:/Program Files/KiCad/9.0/share/kicad/footprints/Connector_FFC-FPC.pretty"),
    ("Connector_USB", "C:/Program Files/KiCad/9.0/share/kicad/footprints/Connector_USB.pretty"),
    ("Inductor_SMD", "C:/Program Files/KiCad/9.0/share/kicad/footprints/Inductor_SMD.pretty"),
    ("Package_DFN_QFN", "C:/Program Files/KiCad/9.0/share/kicad/footprints/Package_DFN_QFN.pretty"),
    ("Package_TO_SOT_SMD", "C:/Program Files/KiCad/9.0/share/kicad/footprints/Package_TO_SOT_SMD.pretty"),
    ("Resistor_SMD", "C:/Program Files/KiCad/9.0/share/kicad/footprints/Resistor_SMD.pretty"),
]


def main():
    if not os.path.exists(FP_LIB_TABLE):
        print(f"ERROR: {FP_LIB_TABLE} not found")
        sys.exit(1)

    with open(FP_LIB_TABLE, 'r', encoding='utf-8') as f:
        content = f.read()

    added = 0
    for name, uri in LIBS_TO_ADD:
        if f'(name "{name}")' in content:
            print(f"  SKIP: {name} already present")
            continue

        entry = f'  (lib (name "{name}")(type "KiCad")(uri "{uri}")(options "")(descr ""))\n'
        content = content.rstrip()
        if content.endswith(')'):
            content = content[:-1] + entry + ')\n'
        print(f"  ADDED: {name}")
        added += 1

    with open(FP_LIB_TABLE, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\nDone. {added} libraries added to fp-lib-table.")
    print(f"\nTotal libraries now: {content.count('(lib ')}")
    print("\nNEXT STEPS:")
    print("  1. Close and reopen KiCad (so it picks up the new lib table)")
    print("  2. Tools → Update PCB from Schematic (F8)")
    print("  3. Click 'Update PCB' — all 69 components should import")
    print('  4. Run: "C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" placement_guide.py')


if __name__ == "__main__":
    main()
