"""
Shared KiCad schematic generation helpers for Freedom Unit V2.
All coordinates in mm. KiCad schematic Y increases downward.
Symbol-relative Y increases upward (inverted).
"""
import uuid

def uid():
    return str(uuid.uuid4())

ROOT_UUID = "00000000-0000-0000-0000-000000000001"

# Sheet UUIDs (must be consistent across all files)
SHEET_UUIDS = {
    "mcu":         "00000000-0000-0000-0000-000000000002",
    "power":       "00000000-0000-0000-0000-000000000003",
    "peripherals": "00000000-0000-0000-0000-000000000004",
    "lora":        "00000000-0000-0000-0000-000000000005",
    "usb":         "00000000-0000-0000-0000-000000000006",
}

def sym_to_abs(sx, sy, px, py):
    """Convert symbol-relative pin coords to absolute schematic coords.
    Symbol Y is inverted relative to schematic Y."""
    return (round(sx + px, 2), round(sy - py, 2))

def wire(x1, y1, x2, y2):
    """Generate a wire element. Coordinates must be exact pin endpoints."""
    return f'  (wire (pts (xy {x1} {y1}) (xy {x2} {y2})) (stroke (width 0) (type default)) (uuid "{uid()}"))'

def junction(x, y):
    """Generate a junction dot where wires cross/meet."""
    return f'  (junction (at {x} {y}) (diameter 0) (color 0 0 0 0) (uuid "{uid()}"))'

def no_connect(x, y):
    """Generate a no-connect flag."""
    return f'  (no_connect (at {x} {y}) (uuid "{uid()}"))'

def global_label(name, x, y, shape="input", angle=0):
    """Generate a global label.
    angle: 0=points right (wire attaches on right), 180=points left (wire attaches on left)
    shape: input, output, bidirectional, passive, tri_state"""
    return (f'  (global_label "{name}" (shape {shape}) (at {x} {y} {angle}) '
            f'(effects (font (size 1.27 1.27))) (uuid "{uid()}")  '
            f'(property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at 0 0 0) '
            f'(effects (font (size 1.27 1.27)) hide)))')

def power_symbol(lib_id, ref, value, x, y, angle=0, sheet_key="mcu"):
    """Generate a power symbol instance (+3V3, GND, etc.)."""
    path = f"/{ROOT_UUID}/{SHEET_UUIDS[sheet_key]}"
    return (f'  (symbol (lib_id "{lib_id}") (at {x} {y} {angle}) (unit 1)\n'
            f'    (in_bom yes) (on_board yes) (dnp no) (fields_autoplaced yes)\n'
            f'    (uuid "{uid()}")\n'
            f'    (property "Reference" "{ref}" (at {x} {y - 2.54} 0) (effects (font (size 1.27 1.27)) hide))\n'
            f'    (property "Value" "{value}" (at {x} {y + 2.54} 0) (effects (font (size 1.27 1.27))))\n'
            f'    (property "Footprint" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
            f'    (property "Datasheet" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
            f'    (instances (project "FreedomUnit_V2" (path "{path}" (reference "{ref}") (unit 1))))\n'
            f'  )')

def component(lib_id, ref, value, x, y, angle=0, footprint="", sheet_key="mcu"):
    """Generate a component instance."""
    path = f"/{ROOT_UUID}/{SHEET_UUIDS[sheet_key]}"
    fp_prop = f'    (property "Footprint" "{footprint}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))'
    return (f'  (symbol (lib_id "{lib_id}") (at {x} {y} {angle}) (unit 1)\n'
            f'    (in_bom yes) (on_board yes) (dnp no) (fields_autoplaced yes)\n'
            f'    (uuid "{uid()}")\n'
            f'    (property "Reference" "{ref}" (at {x + 3.81} {y - 2.54} 0) (effects (font (size 1.27 1.27))))\n'
            f'    (property "Value" "{value}" (at {x + 3.81} {y + 2.54} 0) (effects (font (size 1.27 1.27))))\n'
            f'{fp_prop}\n'
            f'    (property "Datasheet" "~" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
            f'    (instances (project "FreedomUnit_V2" (path "{path}" (reference "{ref}") (unit 1))))\n'
            f'  )')

def header(title, sheet_uuid):
    """Generate the schematic file header."""
    return (f'(kicad_sch\n'
            f'  (version 20231120)\n'
            f'  (generator "FreedomUnit_Generator")\n'
            f'  (generator_version "2.2")\n'
            f'  (uuid "{sheet_uuid}")\n'
            f'  (paper "A4")\n'
            f'  (title_block\n'
            f'    (title "{title}")\n'
            f'    (date "2026-03-03")\n'
            f'    (rev "V2.2")\n'
            f'    (company "GarageAGI LLC")\n'
            f'  )')

def footer():
    return ')'

# ═══════════════════════════════════════════════════════════════
# COMMON SYMBOL DEFINITIONS
# ═══════════════════════════════════════════════════════════════

SYM_CAP = '''    (symbol "Device:C" (pin_numbers hide) (pin_names (offset 0.254) hide) (in_bom yes) (on_board yes)
      (property "Reference" "C" (at 0.635 2.54 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Value" "C" (at 0.635 -2.54 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Footprint" "" (at 0.9652 -3.81 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "C_0_1"
        (polyline (pts (xy -2.032 -0.762) (xy 2.032 -0.762)) (stroke (width 0.508) (type default)) (fill (type none)))
        (polyline (pts (xy -2.032 0.762) (xy 2.032 0.762)) (stroke (width 0.508) (type default)) (fill (type none)))
      )
      (symbol "C_1_1"
        (pin passive line (at 0 3.81 270) (length 2.794) (name "~" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 0 -3.81 90) (length 2.794) (name "~" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )'''

SYM_R = '''    (symbol "Device:R" (pin_numbers hide) (pin_names (offset 0)) (in_bom yes) (on_board yes)
      (property "Reference" "R" (at 2.032 0 90) (effects (font (size 1.27 1.27))))
      (property "Value" "R" (at 0 0 90) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at -1.778 0 90) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "R_0_1"
        (rectangle (start -1.016 -2.54) (end 1.016 2.54) (stroke (width 0.254) (type default)) (fill (type none)))
      )
      (symbol "R_1_1"
        (pin passive line (at 0 3.81 270) (length 1.27) (name "~" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 0 -3.81 90) (length 1.27) (name "~" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )'''

SYM_LED = '''    (symbol "Device:LED" (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
      (property "Reference" "D" (at 0 4.064 0) (effects (font (size 1.27 1.27))))
      (property "Value" "LED" (at 0 -4.064 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "LED_0_1"
        (polyline (pts (xy -1.27 -1.27) (xy -1.27 1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy -1.27 0) (xy 1.27 0)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 1.27 -1.27) (xy 1.27 1.27) (xy -1.27 0) (xy 1.27 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
      )
      (symbol "LED_1_1"
        (pin passive line (at -3.81 0 0) (length 2.54) (name "K" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 3.81 0 180) (length 2.54) (name "A" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )'''

SYM_SW = '''    (symbol "Switch:SW_Push" (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
      (property "Reference" "SW" (at 0 3.81 0) (effects (font (size 1.27 1.27))))
      (property "Value" "SW_Push" (at 0 -3.048 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "SW_Push_0_1"
        (circle (center -2.032 0) (radius 0.508) (stroke (width 0) (type default)) (fill (type none)))
        (circle (center 2.032 0) (radius 0.508) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 1.524) (xy 0 3.048)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy -2.54 0) (xy -2.032 0)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 2.032 0) (xy 2.54 0)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy -1.524 1.524) (xy 1.524 1.524)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "SW_Push_1_1"
        (pin passive line (at -5.08 0 0) (length 2.54) (name "1" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 5.08 0 180) (length 2.54) (name "2" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )'''

SYM_CONN_2 = '''    (symbol "Connector_Generic:Conn_01x02" (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 2.54 0) (effects (font (size 1.27 1.27))))
      (property "Value" "Conn_01x02" (at 0 -5.08 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "Conn_01x02_0_1"
        (rectangle (start -1.27 -2.413) (end 0 -2.667) (stroke (width 0.1524) (type default)) (fill (type none)))
        (rectangle (start -1.27 0.127) (end 0 -0.127) (stroke (width 0.1524) (type default)) (fill (type none)))
      )
      (symbol "Conn_01x02_1_1"
        (pin passive line (at -5.08 0 0) (length 3.81) (name "Pin_1" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -5.08 -2.54 0) (length 3.81) (name "Pin_2" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )'''

SYM_CONN_4 = '''    (symbol "Connector_Generic:Conn_01x04" (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 5.08 0) (effects (font (size 1.27 1.27))))
      (property "Value" "Conn_01x04" (at 0 -7.62 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "Conn_01x04_0_1"
        (rectangle (start -1.27 -4.953) (end 0 -5.207) (stroke (width 0.1524) (type default)) (fill (type none)))
        (rectangle (start -1.27 -2.413) (end 0 -2.667) (stroke (width 0.1524) (type default)) (fill (type none)))
        (rectangle (start -1.27 0.127) (end 0 -0.127) (stroke (width 0.1524) (type default)) (fill (type none)))
        (rectangle (start -1.27 2.667) (end 0 2.413) (stroke (width 0.1524) (type default)) (fill (type none)))
      )
      (symbol "Conn_01x04_1_1"
        (pin passive line (at -5.08 2.54 0) (length 3.81) (name "Pin_1" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -5.08 0 0) (length 3.81) (name "Pin_2" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -5.08 -2.54 0) (length 3.81) (name "Pin_3" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -5.08 -5.08 0) (length 3.81) (name "Pin_4" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
      )
    )'''

SYM_PWR_3V3 = '''    (symbol "power:+3V3" (power) (pin_names (offset 0)) (in_bom yes) (on_board yes)
      (property "Reference" "#PWR" (at 0 -3.81 0) (effects (font (size 1.27 1.27)) hide))
      (property "Value" "+3V3" (at 0 3.556 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "+3V3_0_1"
        (polyline (pts (xy -0.762 1.27) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 0) (xy 0 1.27)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 2.54) (xy 0.762 1.27)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "+3V3_1_1"
        (pin power_in line (at 0 0 90) (length 0) (name "+3V3" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
      )
    )'''

SYM_PWR_VBUS = '''    (symbol "power:+5V" (power) (pin_names (offset 0)) (in_bom yes) (on_board yes)
      (property "Reference" "#PWR" (at 0 -3.81 0) (effects (font (size 1.27 1.27)) hide))
      (property "Value" "+5V" (at 0 3.556 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "+5V_0_1"
        (polyline (pts (xy -0.762 1.27) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 0) (xy 0 1.27)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 2.54) (xy 0.762 1.27)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "+5V_1_1"
        (pin power_in line (at 0 0 90) (length 0) (name "+5V" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
      )
    )'''

SYM_GND = '''    (symbol "power:GND" (power) (pin_names (offset 0)) (in_bom yes) (on_board yes)
      (property "Reference" "#PWR" (at 0 -6.35 0) (effects (font (size 1.27 1.27)) hide))
      (property "Value" "GND" (at 0 -3.81 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "GND_0_1"
        (polyline (pts (xy 0 0) (xy 0 -1.27) (xy 1.27 -1.27) (xy 0 -2.54) (xy -1.27 -1.27) (xy 0 -1.27)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "GND_1_1"
        (pin power_in line (at 0 0 270) (length 0) (name "GND" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
      )
    )'''

SYM_VBAT = '''    (symbol "power:VBAT" (power) (pin_names (offset 0)) (in_bom yes) (on_board yes)
      (property "Reference" "#PWR" (at 0 -3.81 0) (effects (font (size 1.27 1.27)) hide))
      (property "Value" "VBAT" (at 0 3.556 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "VBAT_0_1"
        (polyline (pts (xy -0.762 1.27) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 0) (xy 0 1.27)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 2.54) (xy 0.762 1.27)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "VBAT_1_1"
        (pin power_in line (at 0 0 90) (length 0) (name "VBAT" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
      )
    )'''

def clean_floats(content):
    """Remove floating point artifacts from generated content."""
    import re
    def round_coord(match):
        num = float(match.group(0))
        rounded = round(num, 2)
        if rounded == int(rounded):
            return f'{int(rounded)}.0'
        return f'{rounded}'
    return re.sub(r'-?\d+\.\d{3,}', round_coord, content)

def write_schematic(path, content):
    """Write schematic with float cleanup."""
    content = clean_floats(content)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Generated: {path} ({len(content)} bytes)")
