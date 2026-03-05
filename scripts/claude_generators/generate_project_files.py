#!/usr/bin/env python3
"""Generate root schematic and project support files for Freedom Unit V2."""

import uuid
import json

def uid():
    return str(uuid.uuid4())

ROOT_UUID = "00000000-0000-0000-0000-000000000001"

# Sheet definitions
sheets = [
    {"name": "Sheet1_MCU",         "title": "MCU (nRF52840)",       "uuid": "00000000-0000-0000-0000-000000000002", "file": "Sheet1_MCU.kicad_sch",         "x": 30,  "y": 40,  "w": 50, "h": 20},
    {"name": "Sheet2_LoRa",        "title": "LoRa Radio",           "uuid": "00000000-0000-0000-0000-000000000005", "file": "Sheet2_LoRa.kicad_sch",        "x": 100, "y": 40,  "w": 50, "h": 20},
    {"name": "Sheet3_Power",       "title": "Power Management",     "uuid": "00000000-0000-0000-0000-000000000003", "file": "Sheet3_Power.kicad_sch",       "x": 30,  "y": 80,  "w": 50, "h": 20},
    {"name": "Sheet4_USB",         "title": "USB Interface",        "uuid": "00000000-0000-0000-0000-000000000006", "file": "Sheet4_USB.kicad_sch",         "x": 100, "y": 80,  "w": 50, "h": 20},
    {"name": "Sheet5_Peripherals", "title": "Peripherals",          "uuid": "00000000-0000-0000-0000-000000000004", "file": "Sheet5_Peripherals.kicad_sch", "x": 170, "y": 40,  "w": 50, "h": 20},
]

# ═══════════════════════════════════════════════════════════════
# ROOT SCHEMATIC
# ═══════════════════════════════════════════════════════════════
lines = []
lines.append('(kicad_sch')
lines.append('  (version 20231120)')
lines.append('  (generator "FreedomUnit_Generator")')
lines.append('  (generator_version "2.2")')
lines.append(f'  (uuid "{ROOT_UUID}")')
lines.append('  (paper "A4")')
lines.append('  (title_block')
lines.append('    (title "Freedom Unit V2 — Root Schematic")')
lines.append('    (date "2026-03-03")')
lines.append('    (rev "V2.2")')
lines.append('    (company "GarageAGI LLC")')
lines.append('  )')
lines.append('  (lib_symbols')
lines.append('  )')

# Add hierarchical sheet references
for s in sheets:
    x, y, w, h = s["x"], s["y"], s["w"], s["h"]
    lines.append(f'  (sheet (at {x} {y}) (size {w} {h})')
    lines.append(f'    (stroke (width 0.1524) (type solid))')
    lines.append(f'    (fill (color 255 255 194 1.0))')
    lines.append(f'    (uuid "{s["uuid"]}")')
    lines.append(f'    (property "Sheetname" "{s["title"]}" (at {x} {y - 2} 0) (effects (font (size 1.27 1.27))))')
    lines.append(f'    (property "Sheetfile" "{s["file"]}" (at {x} {y + h + 2} 0) (effects (font (size 1.27 1.27))))')
    lines.append(f'    (instances (project "FreedomUnit_V2" (path "/{ROOT_UUID}" (page "1"))))')
    lines.append(f'  )')

lines.append(')')

root_path = '/home/user/workspace/FreedomUnit_V2.kicad_sch'
with open(root_path, 'w') as f:
    f.write('\n'.join(lines))
print(f"Generated: {root_path}")

# ═══════════════════════════════════════════════════════════════
# PROJECT FILE (.kicad_pro)
# ═══════════════════════════════════════════════════════════════
project = {
    "board": {"design_settings": {"defaults": {"board_outline_line_width": 0.05}}},
    "boards": [],
    "cvpcb": {"equivalence_files": []},
    "erc": {"meta": {"version": 0}},
    "libraries": {
        "pinned_footprint_libs": [],
        "pinned_symbol_libs": []
    },
    "meta": {
        "filename": "FreedomUnit_V2.kicad_pro",
        "version": 1
    },
    "net_settings": {
        "classes": [
            {
                "bus_width": 12,
                "clearance": 0.2,
                "diff_pair_gap": 0.25,
                "diff_pair_via_gap": 0.25,
                "diff_pair_width": 0.2,
                "line_style": 0,
                "microvia_diameter": 0.3,
                "microvia_drill": 0.1,
                "name": "Default",
                "pcb_color": "rgba(0, 0, 0, 0.000)",
                "schematic_color": "rgba(0, 0, 0, 0.000)",
                "track_width": 0.2,
                "via_diameter": 0.6,
                "via_drill": 0.3,
                "wire_width": 6
            }
        ],
        "meta": {"version": 3},
        "net_colors": None
    },
    "pcbnew": {
        "last_paths": {"gencad": "", "idf": "", "netlist": "", "vrml": ""},
        "page_layout_descr_file": ""
    },
    "schematic": {
        "annotate_start_num": 1,
        "bom_fmt_presets": [],
        "bom_fmt_settings": {"field_delimiter": ",", "ref_delimiter": ",", "ref_range_delimiter": "", "string_delimiter": "\""},
        "bom_presets": [],
        "drawing": {"default_line_thickness": 6.0, "default_text_size": 50.0, "field_names": [], "intersheets_ref_own_page": False, "intersheets_ref_prefix": "", "intersheets_ref_short": False, "intersheets_ref_show": False, "intersheets_ref_suffix": "", "junction_size_choice": 3, "label_size_ratio": 0.25, "overbar_offset_ratio": 1.23, "pin_symbol_size": 0.0, "text_offset_ratio": 0.08},
        "legacy_lib_dir": "",
        "legacy_lib_list": [],
        "meta": {"version": 1},
        "net_format_name": "",
        "page_layout_descr_file": "",
        "plot_directory": "",
        "spice_current_sheet_as_root": False,
        "spice_external_command": "spice \"%I\"",
        "spice_model_current_sheet_as_root": True,
        "spice_save_all_currents": False,
        "spice_save_all_dissipations": False,
        "spice_save_all_voltages": False,
        "subpart_first_id": 65,
        "subpart_id_separator": 0
    },
    "sheets": [
        [ROOT_UUID, ""],
    ],
    "text_variables": {}
}

# Add sheet paths
for s in sheets:
    project["sheets"].append([s["uuid"], s["title"]])

pro_path = '/home/user/workspace/FreedomUnit_V2.kicad_pro'
with open(pro_path, 'w') as f:
    json.dump(project, f, indent=2)
print(f"Generated: {pro_path}")

# ═══════════════════════════════════════════════════════════════
# SYMBOL LIBRARY TABLE (sym-lib-table)
# ═══════════════════════════════════════════════════════════════
# Since all symbols are embedded in lib_symbols within each .kicad_sch,
# we just need minimal entries for KiCad to not complain.
sym_lib = '''(sym_lib_table
  (version 7)
)
'''

sym_path = '/home/user/workspace/sym-lib-table'
with open(sym_path, 'w') as f:
    f.write(sym_lib)
print(f"Generated: {sym_path}")

# ═══════════════════════════════════════════════════════════════
# FOOTPRINT LIBRARY TABLE (fp-lib-table)
# ═══════════════════════════════════════════════════════════════
fp_lib = '''(fp_lib_table
  (version 7)
)
'''

fp_path = '/home/user/workspace/fp-lib-table'
with open(fp_path, 'w') as f:
    f.write(fp_lib)
print(f"Generated: {fp_path}")

print("\n=== All project files generated ===")
print("Files to copy to C:\\Users\\AMD\\FreedomUnit_V2\\:")
print("  FreedomUnit_V2.kicad_pro")
print("  FreedomUnit_V2.kicad_sch (root)")
print("  Sheet1_MCU.kicad_sch")
print("  Sheet2_LoRa.kicad_sch")
print("  Sheet3_Power.kicad_sch")
print("  Sheet4_USB.kicad_sch")
print("  Sheet5_Peripherals.kicad_sch")
print("  sym-lib-table")
print("  fp-lib-table")
