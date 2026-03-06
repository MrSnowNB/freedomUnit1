#!/usr/bin/env python3
"""
Generate Sheet4_USB.kicad_sch for Freedom Unit V2

Components:
  - J3: GCT USB4085-GF-A USB-C connector (custom symbol, 6 pins: VBUS, D+, D-, CC1, CC2, GND, SHIELD)
  - U6: TPD2E001DRLR ESD protection (custom symbol, 5 pins: VCC, IO1, IO2, GND, NC)
  - R5: 5.1k CC1 pulldown resistor
  - R6: 5.1k CC2 pulldown resistor

Nets (global labels connecting to other sheets):
  - USB_DP (D+ to MCU P1.14)
  - USB_DN (D- to MCU P1.13)
  - VBUS (5V to MCP73831 on Sheet3 Power)

Power:
  - VBUS -> global label for MCP73831
  - GND -> ground
"""

import uuid
import re

def uid():
    return str(uuid.uuid4())

ROOT_UUID = "00000000-0000-0000-0000-000000000001"
SHEET_UUID = "00000000-0000-0000-0000-000000000006"  # USB sheet

def sym_to_abs(sx, sy, px, py):
    """Convert symbol-relative pin coords to absolute schematic coords.
    Symbol Y is inverted relative to schematic Y."""
    return (round(sx + px, 2), round(sy - py, 2))

def wire(x1, y1, x2, y2):
    return f'  (wire (pts (xy {x1} {y1}) (xy {x2} {y2})) (stroke (width 0) (type default)) (uuid "{uid()}"))'

def junction(x, y):
    return f'  (junction (at {x} {y}) (diameter 0) (color 0 0 0 0) (uuid "{uid()}"))'

def no_connect(x, y):
    return f'  (no_connect (at {x} {y}) (uuid "{uid()}"))'

def global_label(name, x, y, shape="input", angle=0):
    return (f'  (global_label "{name}" (shape {shape}) (at {x} {y} {angle}) '
            f'(effects (font (size 1.27 1.27))) (uuid "{uid()}")  '
            f'(property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at 0 0 0) '
            f'(effects (font (size 1.27 1.27)) hide)))')

def power_sym(lib_id, ref, value, x, y, angle=0):
    path = f"/{ROOT_UUID}/{SHEET_UUID}"
    return (f'  (symbol (lib_id "{lib_id}") (at {x} {y} {angle}) (unit 1)\n'
            f'    (in_bom yes) (on_board yes) (dnp no) (fields_autoplaced yes)\n'
            f'    (uuid "{uid()}")\n'
            f'    (property "Reference" "{ref}" (at {x} {y - 2.54} 0) (effects (font (size 1.27 1.27)) hide))\n'
            f'    (property "Value" "{value}" (at {x} {y + 2.54} 0) (effects (font (size 1.27 1.27))))\n'
            f'    (property "Footprint" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
            f'    (property "Datasheet" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
            f'    (instances (project "FreedomUnit_V2" (path "{path}" (reference "{ref}") (unit 1))))\n'
            f'  )')

def comp(lib_id, ref, value, x, y, angle=0, footprint=""):
    path = f"/{ROOT_UUID}/{SHEET_UUID}"
    return (f'  (symbol (lib_id "{lib_id}") (at {x} {y} {angle}) (unit 1)\n'
            f'    (in_bom yes) (on_board yes) (dnp no) (fields_autoplaced yes)\n'
            f'    (uuid "{uid()}")\n'
            f'    (property "Reference" "{ref}" (at {x + 3.81} {y - 2.54} 0) (effects (font (size 1.27 1.27))))\n'
            f'    (property "Value" "{value}" (at {x + 3.81} {y + 2.54} 0) (effects (font (size 1.27 1.27))))\n'
            f'    (property "Footprint" "{footprint}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
            f'    (property "Datasheet" "~" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
            f'    (instances (project "FreedomUnit_V2" (path "{path}" (reference "{ref}") (unit 1))))\n'
            f'  )')

def clean_floats(content):
    def round_coord(match):
        num = float(match.group(0))
        rounded = round(num, 2)
        if rounded == int(rounded):
            return f'{int(rounded)}.0'
        return f'{rounded}'
    return re.sub(r'-?\d+\.\d{3,}', round_coord, content)

# ═══════════════════════════════════════════════════════════════
# SYMBOL DEFINITIONS
# ═══════════════════════════════════════════════════════════════

# USB-C Connector: GCT USB4085-GF-A
# Simplified as a 6-pin connector: VBUS, D+, D-, CC1, CC2, GND(+Shield)
SYM_USB_C = '''    (symbol "FreedomUnit:USB4085-GF-A" (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 16.51 0) (effects (font (size 1.27 1.27))))
      (property "Value" "USB4085-GF-A" (at 0 -16.51 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "USB4085-GF-A_0_1"
        (rectangle (start -7.62 15.24) (end 7.62 -15.24) (stroke (width 0.254) (type default)) (fill (type background)))
        (text "USB-C" (at 0 0 0) (effects (font (size 1.27 1.27))))
        (text "GCT" (at 0 -2.54 0) (effects (font (size 1.0 1.0))))
      )
      (symbol "USB4085-GF-A_1_1"
        (pin power_out line (at 12.7 12.7 180) (length 5.08) (name "VBUS" (effects (font (size 1.27 1.27)))) (number "A4" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 12.7 5.08 180) (length 5.08) (name "D+" (effects (font (size 1.27 1.27)))) (number "A6" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 12.7 2.54 180) (length 5.08) (name "D-" (effects (font (size 1.27 1.27)))) (number "A7" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 12.7 -2.54 180) (length 5.08) (name "CC1" (effects (font (size 1.27 1.27)))) (number "A5" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 12.7 -5.08 180) (length 5.08) (name "CC2" (effects (font (size 1.27 1.27)))) (number "B5" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 12.7 -10.16 180) (length 5.08) (name "GND" (effects (font (size 1.27 1.27)))) (number "A1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 12.7 -12.7 180) (length 5.08) (name "SHIELD" (effects (font (size 1.27 1.27)))) (number "S1" (effects (font (size 1.27 1.27)))))
      )
    )'''

# TPD2E001 ESD Protection (SOT-23-6 style, but we'll use 5 active pins)
# Pin 1: NC, Pin 2: IO1, Pin 3: VCC, Pin 4: IO2, Pin 5: GND
SYM_TPD2E001 = '''    (symbol "FreedomUnit:TPD2E001" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 8.89 0) (effects (font (size 1.27 1.27))))
      (property "Value" "TPD2E001" (at 0 -8.89 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "https://www.ti.com/lit/ds/symlink/tpd2e001.pdf" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "TPD2E001_0_1"
        (rectangle (start -7.62 7.62) (end 7.62 -7.62) (stroke (width 0.254) (type default)) (fill (type background)))
        (text "TPD2E001" (at 0 0 0) (effects (font (size 1.27 1.27))))
        (text "ESD" (at 0 -2.54 0) (effects (font (size 1.0 1.0))))
      )
      (symbol "TPD2E001_1_1"
        (pin power_in line (at 0 12.7 270) (length 5.08) (name "VCC" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -12.7 2.54 0) (length 5.08) (name "IO1" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -12.7 -2.54 0) (length 5.08) (name "IO2" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 0 -12.7 90) (length 5.08) (name "GND" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 12.7 0 180) (length 5.08) (name "NC" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
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

SYM_PWR_5V = '''    (symbol "power:+5V" (power) (pin_names (offset 0)) (in_bom yes) (on_board yes)
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

# ═══════════════════════════════════════════════════════════════
# COMPONENT PLACEMENT
# ═══════════════════════════════════════════════════════════════

# Layout: USB-C connector on left, TPD2E001 in middle, labels on right
# CC resistors below USB-C connector

# USB-C connector J3
J3_X, J3_Y = 80.0, 90.0

# TPD2E001 U6
U6_X, U6_Y = 140.0, 90.0

# CC pulldown resistors (vertical orientation)
R5_X, R5_Y = 100.0, 115.0   # CC1 pulldown
R6_X, R6_Y = 107.62, 115.0  # CC2 pulldown

# ═══════════════════════════════════════════════════════════════
# PIN ABSOLUTE POSITIONS
# ═══════════════════════════════════════════════════════════════

# USB-C J3 pins (right side, angle=180, connection at symbol_x + 12.7)
P_J3_VBUS   = sym_to_abs(J3_X, J3_Y, 12.7, 12.7)   # (92.7, 77.3)
P_J3_DP     = sym_to_abs(J3_X, J3_Y, 12.7, 5.08)    # (92.7, 84.92)
P_J3_DN     = sym_to_abs(J3_X, J3_Y, 12.7, 2.54)    # (92.7, 87.46)
P_J3_CC1    = sym_to_abs(J3_X, J3_Y, 12.7, -2.54)   # (92.7, 92.54)
P_J3_CC2    = sym_to_abs(J3_X, J3_Y, 12.7, -5.08)   # (92.7, 95.08)
P_J3_GND    = sym_to_abs(J3_X, J3_Y, 12.7, -10.16)  # (92.7, 100.16)
P_J3_SHIELD = sym_to_abs(J3_X, J3_Y, 12.7, -12.7)   # (92.7, 102.7)

# TPD2E001 U6 pins
P_U6_VCC = sym_to_abs(U6_X, U6_Y, 0, 12.7)       # (140, 77.3)
P_U6_IO1 = sym_to_abs(U6_X, U6_Y, -12.7, 2.54)   # (127.3, 87.46)
P_U6_IO2 = sym_to_abs(U6_X, U6_Y, -12.7, -2.54)  # (127.3, 92.54)
P_U6_GND = sym_to_abs(U6_X, U6_Y, 0, -12.7)      # (140, 102.7)
P_U6_NC  = sym_to_abs(U6_X, U6_Y, 12.7, 0)       # (152.7, 90)

# Resistor pins (vertical, pin1=top at y-3.81, pin2=bottom at y+3.81)
P_R5_1 = (R5_X, round(R5_Y - 3.81, 2))   # top
P_R5_2 = (R5_X, round(R5_Y + 3.81, 2))   # bottom
P_R6_1 = (R6_X, round(R6_Y - 3.81, 2))
P_R6_2 = (R6_X, round(R6_Y + 3.81, 2))

print("=== USB Sheet Pin Positions ===")
print(f"J3 VBUS:   {P_J3_VBUS}")
print(f"J3 D+:     {P_J3_DP}")
print(f"J3 D-:     {P_J3_DN}")
print(f"J3 CC1:    {P_J3_CC1}")
print(f"J3 CC2:    {P_J3_CC2}")
print(f"J3 GND:    {P_J3_GND}")
print(f"J3 SHIELD: {P_J3_SHIELD}")
print(f"U6 VCC:    {P_U6_VCC}")
print(f"U6 IO1:    {P_U6_IO1}")
print(f"U6 IO2:    {P_U6_IO2}")
print(f"U6 GND:    {P_U6_GND}")
print(f"U6 NC:     {P_U6_NC}")
print(f"R5 top:    {P_R5_1}")
print(f"R5 bot:    {P_R5_2}")
print(f"R6 top:    {P_R6_1}")
print(f"R6 bot:    {P_R6_2}")

# ═══════════════════════════════════════════════════════════════
# BUILD SCHEMATIC
# ═══════════════════════════════════════════════════════════════

lines = []

# Header
lines.append('(kicad_sch')
lines.append('  (version 20231120)')
lines.append('  (generator "FreedomUnit_Generator")')
lines.append('  (generator_version "2.2")')
lines.append(f'  (uuid "{uid()}")')
lines.append('  (paper "A4")')
lines.append('  (title_block')
lines.append('    (title "Sheet 4 — USB Interface")')
lines.append('    (date "2026-03-03")')
lines.append('    (rev "V2.2")')
lines.append('    (company "GarageAGI LLC")')
lines.append('  )')

# lib_symbols
lines.append('  (lib_symbols')
lines.append(SYM_USB_C)
lines.append(SYM_TPD2E001)
lines.append(SYM_R)
lines.append(SYM_PWR_5V)
lines.append(SYM_GND)
lines.append('  )')

# ── Components ──
lines.append(comp("FreedomUnit:USB4085-GF-A", "J3", "USB4085-GF-A", J3_X, J3_Y))
lines.append(comp("FreedomUnit:TPD2E001", "U6", "TPD2E001", U6_X, U6_Y))
lines.append(comp("Device:R", "R5", "5.1k", R5_X, R5_Y))
lines.append(comp("Device:R", "R6", "5.1k", R6_X, R6_Y))

# ── Power Symbols ──
# +5V (VBUS) above the VBUS line
lines.append(power_sym("power:+5V", "#PWR020", "+5V", P_J3_VBUS[0] + 10.16, P_J3_VBUS[1] - 5.08))
# Also +5V for TPD2E001 VCC
lines.append(power_sym("power:+5V", "#PWR021", "+5V", P_U6_VCC[0], P_U6_VCC[1] - 5.08))

# GND symbols
lines.append(power_sym("power:GND", "#PWR022", "GND", P_J3_GND[0] + 5.08, P_J3_GND[1] + 5.08))
lines.append(power_sym("power:GND", "#PWR023", "GND", P_U6_GND[0], P_U6_GND[1] + 5.08))
lines.append(power_sym("power:GND", "#PWR024", "GND", R5_X, P_R5_2[1] + 2.54))  # Below R5
lines.append(power_sym("power:GND", "#PWR025", "GND", R6_X, P_R6_2[1] + 2.54))  # Below R6
# Shield GND
lines.append(power_sym("power:GND", "#PWR026", "GND", P_J3_SHIELD[0] + 5.08, P_J3_SHIELD[1] + 2.54))

# ── Global Labels ──
LABEL_USB_DP_X = 165.0
LABEL_USB_DN_X = 165.0
LABEL_VBUS_X   = 165.0

# USB D+/D- labels on right side of TPD2E001 (going to MCU)
# D+ and D- pass through TPD2E001 — the TPD2E001 IO1/IO2 connect on one side to USB,
# and the same traces continue to MCU. We'll put labels on the MCU side.
# Actually TPD2E001 has IO1/IO2 on the LEFT — connector side.
# The data lines pass through (it's transparent). So we wire:
# J3 D+ -> U6 IO1 and then continue right from the same wire to MCU label
# Wait — TPD2E001 doesn't have separate in/out. It's a TVS clamp — 
# IO1 and IO2 are just the protected lines. So the topology is:
# J3.D+ ─── wire ──┬── U6.IO1 (TVS clamp to GND)
#                   └── wire ── global_label USB_DP → MCU
# Same for D-.

# So we wire J3.D+ to U6.IO1, and also from that same junction to a label going right.
# Let me put the labels to the right of U6.

# Global labels for USB data (going to MCU)
lines.append(global_label("USB_DP", LABEL_USB_DP_X, P_U6_IO1[1], "bidirectional", 180))
lines.append(global_label("USB_DN", LABEL_USB_DN_X, P_U6_IO2[1], "bidirectional", 180))
# VBUS label going to power sheet
lines.append(global_label("VBUS", LABEL_VBUS_X, P_J3_VBUS[1], "output", 180))

# ── Wires ──

# VBUS: J3 VBUS pin -> horizontal right -> +5V symbol and VBUS label
vbus_rail_y = P_J3_VBUS[1]
# Wire from J3 VBUS to midpoint
vbus_mid_x = P_J3_VBUS[0] + 10.16
lines.append(wire(P_J3_VBUS[0], vbus_rail_y, vbus_mid_x, vbus_rail_y))
# Wire from midpoint up to +5V symbol
lines.append(wire(vbus_mid_x, vbus_rail_y, vbus_mid_x, vbus_rail_y - 5.08))
# Wire from midpoint right to U6 VCC x, then up to U6 VCC
lines.append(wire(vbus_mid_x, vbus_rail_y, P_U6_VCC[0], vbus_rail_y))
lines.append(wire(P_U6_VCC[0], vbus_rail_y, P_U6_VCC[0], P_U6_VCC[1] - 5.08))
# Wire from U6 VCC pin down to rail
lines.append(wire(P_U6_VCC[0], P_U6_VCC[1], P_U6_VCC[0], vbus_rail_y))
# Wire from VBUS label
lines.append(wire(P_U6_VCC[0], vbus_rail_y, LABEL_VBUS_X, vbus_rail_y))
# Junction at VBUS rail points
lines.append(junction(vbus_mid_x, vbus_rail_y))
lines.append(junction(P_U6_VCC[0], vbus_rail_y))

# D+: J3 D+ -> U6 IO1, and from junction to label
lines.append(wire(P_J3_DP[0], P_J3_DP[1], P_U6_IO1[0], P_U6_IO1[1]))
# Continue from U6 IO1 rightward. Since TPD2E001 IO1 is on the left side,
# the data line enters from the left. To get it to the MCU label,
# we run a wire from the connector pin all the way through to the label.
# The U6 IO1 pin taps into this wire.
lines.append(wire(P_U6_IO1[0], P_U6_IO1[1], LABEL_USB_DP_X, P_U6_IO1[1]))

# D-: J3 D- -> U6 IO2, and from junction to label
lines.append(wire(P_J3_DN[0], P_J3_DN[1], P_U6_IO2[0], P_U6_IO2[1]))
lines.append(wire(P_U6_IO2[0], P_U6_IO2[1], LABEL_USB_DN_X, P_U6_IO2[1]))

# CC1: J3 CC1 -> wire down to R5 top
lines.append(wire(P_J3_CC1[0], P_J3_CC1[1], R5_X, P_J3_CC1[1]))
lines.append(wire(R5_X, P_J3_CC1[1], R5_X, P_R5_1[1]))

# CC2: J3 CC2 -> wire down to R6 top
lines.append(wire(P_J3_CC2[0], P_J3_CC2[1], R6_X, P_J3_CC2[1]))
lines.append(wire(R6_X, P_J3_CC2[1], R6_X, P_R6_1[1]))

# R5 bottom to GND
lines.append(wire(R5_X, P_R5_2[1], R5_X, P_R5_2[1] + 2.54))

# R6 bottom to GND
lines.append(wire(R6_X, P_R6_2[1], R6_X, P_R6_2[1] + 2.54))

# GND: J3 GND -> GND symbol
gnd_junction_x = P_J3_GND[0] + 5.08
lines.append(wire(P_J3_GND[0], P_J3_GND[1], gnd_junction_x, P_J3_GND[1]))
lines.append(wire(gnd_junction_x, P_J3_GND[1], gnd_junction_x, P_J3_GND[1] + 5.08))

# SHIELD: J3 Shield -> GND
lines.append(wire(P_J3_SHIELD[0], P_J3_SHIELD[1], P_J3_SHIELD[0] + 5.08, P_J3_SHIELD[1]))
lines.append(wire(P_J3_SHIELD[0] + 5.08, P_J3_SHIELD[1], P_J3_SHIELD[0] + 5.08, P_J3_SHIELD[1] + 2.54))

# U6 GND pin -> GND symbol
lines.append(wire(P_U6_GND[0], P_U6_GND[1], P_U6_GND[0], P_U6_GND[1] + 5.08))

# U6 NC pin -> no connect flag
lines.append(no_connect(P_U6_NC[0], P_U6_NC[1]))

# Close
lines.append(')')

# ═══════════════════════════════════════════════════════════════
# WRITE OUTPUT
# ═══════════════════════════════════════════════════════════════

output = '\n'.join(lines)
output = clean_floats(output)

output_path = '/home/user/workspace/Sheet4_USB.kicad_sch'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(output)

print(f"\nGenerated: {output_path}")
print(f"File size: {len(output)} bytes")
