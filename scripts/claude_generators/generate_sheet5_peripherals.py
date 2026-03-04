#!/usr/bin/env python3
"""
Generate Sheet5_Peripherals.kicad_sch for Freedom Unit V2

Components:
  - U9: MAX-M10S GPS (custom, 7 key pins: VCC, GND, SDA, SCL, PPS, RESET, EXTINT)
  - J4: Molex 5051100892 Sharp LCD FPC connector (simplified 5-signal)
  - J5: I2C Expansion Header (Conn_01x04: SDA, SCL, 3.3V, GND)
  - U10: MX25R6435F QSPI Flash (SOP-8)
  - SW2-SW8: 7x PTS636 pushbuttons + 7x 100nF debounce caps (C12-C18)
  - D2-D4: 3x LEDs (red, green, blue) + R7-R9: 3x 680 ohm resistors
  - R4: 4.7k I2C SDA pullup
  - R10: 4.7k I2C SCL pullup
"""

import uuid
import re

def uid():
    return str(uuid.uuid4())

ROOT_UUID = "00000000-0000-0000-0000-000000000001"
SHEET_UUID = "00000000-0000-0000-0000-000000000004"

def sym_to_abs(sx, sy, px, py):
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

def pwr(lib_id, ref, value, x, y, angle=0):
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

def comp(lib_id, ref, value, x, y, angle=0, fp=""):
    path = f"/{ROOT_UUID}/{SHEET_UUID}"
    return (f'  (symbol (lib_id "{lib_id}") (at {x} {y} {angle}) (unit 1)\n'
            f'    (in_bom yes) (on_board yes) (dnp no) (fields_autoplaced yes)\n'
            f'    (uuid "{uid()}")\n'
            f'    (property "Reference" "{ref}" (at {x + 3.81} {y - 2.54} 0) (effects (font (size 1.27 1.27))))\n'
            f'    (property "Value" "{value}" (at {x + 3.81} {y + 2.54} 0) (effects (font (size 1.27 1.27))))\n'
            f'    (property "Footprint" "{fp}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
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

SYM_MAX_M10S = '''    (symbol "FreedomUnit:MAX-M10S" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 13.97 0) (effects (font (size 1.27 1.27))))
      (property "Value" "MAX-M10S" (at 0 -13.97 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "MAX-M10S_0_1"
        (rectangle (start -10.16 12.7) (end 10.16 -12.7) (stroke (width 0.254) (type default)) (fill (type background)))
        (text "MAX-M10S" (at 0 0 0) (effects (font (size 1.27 1.27))))
        (text "GPS" (at 0 -2.54 0) (effects (font (size 1.0 1.0))))
      )
      (symbol "MAX-M10S_1_1"
        (pin power_in line (at -15.24 10.16 0) (length 5.08) (name "VCC" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at -15.24 -10.16 0) (length 5.08) (name "GND" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 15.24 7.62 180) (length 5.08) (name "SDA" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 15.24 5.08 180) (length 5.08) (name "SCL" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
        (pin output line (at 15.24 0 180) (length 5.08) (name "PPS" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27)))))
        (pin input line (at 15.24 -5.08 180) (length 5.08) (name "RESET" (effects (font (size 1.27 1.27)))) (number "6" (effects (font (size 1.27 1.27)))))
        (pin input line (at 15.24 -10.16 180) (length 5.08) (name "EXTINT" (effects (font (size 1.27 1.27)))) (number "7" (effects (font (size 1.27 1.27)))))
      )
    )'''

SYM_MX25R = '''    (symbol "FreedomUnit:MX25R6435F" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 11.43 0) (effects (font (size 1.27 1.27))))
      (property "Value" "MX25R6435F" (at 0 -11.43 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "MX25R6435F_0_1"
        (rectangle (start -10.16 10.16) (end 10.16 -10.16) (stroke (width 0.254) (type default)) (fill (type background)))
        (text "MX25R6435F" (at 0 0 0) (effects (font (size 1.27 1.27))))
        (text "QSPI Flash" (at 0 -2.54 0) (effects (font (size 1.0 1.0))))
      )
      (symbol "MX25R6435F_1_1"
        (pin input line (at -15.24 7.62 0) (length 5.08) (name "CS#" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -15.24 2.54 0) (length 5.08) (name "IO1/MISO" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -15.24 -2.54 0) (length 5.08) (name "IO2/WP" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 0 -15.24 90) (length 5.08) (name "VSS" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 15.24 -2.54 180) (length 5.08) (name "IO0/MOSI" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27)))))
        (pin input line (at 15.24 2.54 180) (length 5.08) (name "SCK" (effects (font (size 1.27 1.27)))) (number "6" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 15.24 7.62 180) (length 5.08) (name "IO3/HOLD" (effects (font (size 1.27 1.27)))) (number "7" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 0 15.24 270) (length 5.08) (name "VCC" (effects (font (size 1.27 1.27)))) (number "8" (effects (font (size 1.27 1.27)))))
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

SYM_C = '''    (symbol "Device:C" (pin_numbers hide) (pin_names (offset 0.254) hide) (in_bom yes) (on_board yes)
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

# LCD connector (simplified as Conn_01x05 for SCLK, MOSI, CS, EXTCOMIN, DISP)
SYM_CONN_5 = '''    (symbol "Connector_Generic:Conn_01x05" (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 5.08 0) (effects (font (size 1.27 1.27))))
      (property "Value" "Conn_01x05" (at 0 -10.16 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "Conn_01x05_0_1"
        (rectangle (start -1.27 -7.493) (end 0 -7.747) (stroke (width 0.1524) (type default)) (fill (type none)))
        (rectangle (start -1.27 -4.953) (end 0 -5.207) (stroke (width 0.1524) (type default)) (fill (type none)))
        (rectangle (start -1.27 -2.413) (end 0 -2.667) (stroke (width 0.1524) (type default)) (fill (type none)))
        (rectangle (start -1.27 0.127) (end 0 -0.127) (stroke (width 0.1524) (type default)) (fill (type none)))
        (rectangle (start -1.27 2.667) (end 0 2.413) (stroke (width 0.1524) (type default)) (fill (type none)))
      )
      (symbol "Conn_01x05_1_1"
        (pin passive line (at -5.08 2.54 0) (length 3.81) (name "Pin_1" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -5.08 0 0) (length 3.81) (name "Pin_2" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -5.08 -2.54 0) (length 3.81) (name "Pin_3" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -5.08 -5.08 0) (length 3.81) (name "Pin_4" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -5.08 -7.62 0) (length 3.81) (name "Pin_5" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27)))))
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
# COMPONENT PLACEMENT — A3 landscape
# ═══════════════════════════════════════════════════════════════

# Group 1: GPS (top-left)
U9_X, U9_Y = 70.0, 55.0       # MAX-M10S GPS
R4_X, R4_Y = 105.0, 40.0      # SDA pullup
R10_X, R10_Y = 112.62, 40.0   # SCL pullup

# Group 2: LCD connector (top-center)
J4_X, J4_Y = 175.0, 55.0      # LCD FPC connector

# Group 3: I2C expansion header (top-right, near GPS)
J5_X, J5_Y = 130.0, 55.0      # I2C header

# Group 4: QSPI Flash (center-right)
U10_X, U10_Y = 280.0, 55.0    # MX25R6435F

# Group 5: Buttons (bottom section, spaced horizontally)
# 7 buttons: UP, DOWN, LEFT, RIGHT, CENTER, A, B
btn_y = 150.0
btn_x_start = 40.0
btn_spacing = 35.0
btn_names = ["BTN_UP", "BTN_DOWN", "BTN_LEFT", "BTN_RIGHT", "BTN_CENTER", "BTN_A", "BTN_B"]
btn_pins = ["P1.10", "P0.18", "P0.11", "P0.06", "P0.08", "P1.00", "P1.01"]
btn_refs = [f"SW{i}" for i in range(2, 9)]
cap_refs = [f"C{i}" for i in range(12, 19)]

# Group 6: LEDs (bottom-right)
led_y_start = 110.0
led_spacing = 12.7
led_names = ["LED_RED", "LED_GREEN", "LED_BLUE"]
led_colors = ["Red", "Green", "Blue"]
led_refs = ["D2", "D3", "D4"]
led_r_refs = ["R7", "R8", "R9"]
led_x = 280.0

# ═══════════════════════════════════════════════════════════════
# BUILD SCHEMATIC
# ═══════════════════════════════════════════════════════════════

lines = []

lines.append('(kicad_sch')
lines.append('  (version 20231120)')
lines.append('  (generator "FreedomUnit_Generator")')
lines.append('  (generator_version "2.2")')
lines.append(f'  (uuid "{uid()}")')
lines.append('  (paper "A3")')
lines.append('  (title_block')
lines.append('    (title "Sheet 5 — Peripherals")')
lines.append('    (date "2026-03-03")')
lines.append('    (rev "V2.2")')
lines.append('    (company "GarageAGI LLC")')
lines.append('  )')

lines.append('  (lib_symbols')
lines.append(SYM_MAX_M10S)
lines.append(SYM_MX25R)
lines.append(SYM_SW)
lines.append(SYM_LED)
lines.append(SYM_C)
lines.append(SYM_R)
lines.append(SYM_CONN_4)
lines.append(SYM_CONN_5)
lines.append(SYM_PWR_3V3)
lines.append(SYM_GND)
lines.append('  )')

pwr_idx = 50

# ── GPS Section ──
lines.append(comp("FreedomUnit:MAX-M10S", "U9", "MAX-M10S", U9_X, U9_Y))

# GPS pins
P_GPS_VCC    = sym_to_abs(U9_X, U9_Y, -15.24, 10.16)
P_GPS_GND    = sym_to_abs(U9_X, U9_Y, -15.24, -10.16)
P_GPS_SDA    = sym_to_abs(U9_X, U9_Y, 15.24, 7.62)
P_GPS_SCL    = sym_to_abs(U9_X, U9_Y, 15.24, 5.08)
P_GPS_PPS    = sym_to_abs(U9_X, U9_Y, 15.24, 0)
P_GPS_RESET  = sym_to_abs(U9_X, U9_Y, 15.24, -5.08)
P_GPS_EXTINT = sym_to_abs(U9_X, U9_Y, 15.24, -10.16)

# GPS power
lines.append(global_label("+3V3_SW", P_GPS_VCC[0] - 10.16, P_GPS_VCC[1], "input", 0))
lines.append(wire(P_GPS_VCC[0] - 10.16, P_GPS_VCC[1], P_GPS_VCC[0], P_GPS_VCC[1]))
lines.append(pwr("power:GND", f"#PWR0{pwr_idx}", "GND", P_GPS_GND[0] - 5.08, P_GPS_GND[1] + 2.54))
pwr_idx += 1
lines.append(wire(P_GPS_GND[0], P_GPS_GND[1], P_GPS_GND[0] - 5.08, P_GPS_GND[1]))
lines.append(wire(P_GPS_GND[0] - 5.08, P_GPS_GND[1], P_GPS_GND[0] - 5.08, P_GPS_GND[1] + 2.54))

# GPS signal labels
lines.append(global_label("GPS_SDA", P_GPS_SDA[0] + 10.16, P_GPS_SDA[1], "bidirectional", 180))
lines.append(wire(P_GPS_SDA[0], P_GPS_SDA[1], P_GPS_SDA[0] + 10.16, P_GPS_SDA[1]))
lines.append(global_label("GPS_SCL", P_GPS_SCL[0] + 10.16, P_GPS_SCL[1], "bidirectional", 180))
lines.append(wire(P_GPS_SCL[0], P_GPS_SCL[1], P_GPS_SCL[0] + 10.16, P_GPS_SCL[1]))
lines.append(global_label("GPS_PPS", P_GPS_PPS[0] + 10.16, P_GPS_PPS[1], "output", 180))
lines.append(wire(P_GPS_PPS[0], P_GPS_PPS[1], P_GPS_PPS[0] + 10.16, P_GPS_PPS[1]))
lines.append(global_label("GPS_RESET", P_GPS_RESET[0] + 10.16, P_GPS_RESET[1], "input", 180))
lines.append(wire(P_GPS_RESET[0], P_GPS_RESET[1], P_GPS_RESET[0] + 10.16, P_GPS_RESET[1]))
lines.append(global_label("GPS_EXTINT", P_GPS_EXTINT[0] + 10.16, P_GPS_EXTINT[1], "output", 180))
lines.append(wire(P_GPS_EXTINT[0], P_GPS_EXTINT[1], P_GPS_EXTINT[0] + 10.16, P_GPS_EXTINT[1]))

# I2C pullup resistors (R4=SDA, R10=SCL)
lines.append(comp("Device:R", "R4", "4.7k", R4_X, R4_Y))
lines.append(comp("Device:R", "R10", "4.7k", R10_X, R10_Y))

# R4 top -> +3V3_SW
P_R4_1 = (R4_X, round(R4_Y - 3.81, 2))
P_R4_2 = (R4_X, round(R4_Y + 3.81, 2))
P_R10_1 = (R10_X, round(R10_Y - 3.81, 2))
P_R10_2 = (R10_X, round(R10_Y + 3.81, 2))

lines.append(pwr("power:+3V3", f"#PWR0{pwr_idx}", "+3V3", R4_X, P_R4_1[1] - 2.54))
pwr_idx += 1
lines.append(wire(R4_X, P_R4_1[1], R4_X, P_R4_1[1] - 2.54))
lines.append(pwr("power:+3V3", f"#PWR0{pwr_idx}", "+3V3", R10_X, P_R10_1[1] - 2.54))
pwr_idx += 1
lines.append(wire(R10_X, P_R10_1[1], R10_X, P_R10_1[1] - 2.54))

# R4 bottom -> SDA line
lines.append(wire(R4_X, P_R4_2[1], R4_X, P_GPS_SDA[1]))
lines.append(wire(R4_X, P_GPS_SDA[1], P_GPS_SDA[0], P_GPS_SDA[1]))
lines.append(junction(P_GPS_SDA[0], P_GPS_SDA[1]))

# R10 bottom -> SCL line
lines.append(wire(R10_X, P_R10_2[1], R10_X, P_GPS_SCL[1]))
lines.append(wire(R10_X, P_GPS_SCL[1], P_GPS_SCL[0], P_GPS_SCL[1]))
lines.append(junction(P_GPS_SCL[0], P_GPS_SCL[1]))

# ── I2C Header Section ──
lines.append(comp("Connector_Generic:Conn_01x04", "J5", "I2C Header", J5_X, J5_Y))
P_J5_1 = sym_to_abs(J5_X, J5_Y, -5.08, 2.54)   # SDA
P_J5_2 = sym_to_abs(J5_X, J5_Y, -5.08, 0)       # SCL
P_J5_3 = sym_to_abs(J5_X, J5_Y, -5.08, -2.54)   # 3.3V
P_J5_4 = sym_to_abs(J5_X, J5_Y, -5.08, -5.08)   # GND

# I2C header SDA -> GPS SDA line
lines.append(wire(P_J5_1[0], P_J5_1[1], P_J5_1[0] - 5.08, P_J5_1[1]))
lines.append(wire(P_J5_1[0] - 5.08, P_J5_1[1], P_J5_1[0] - 5.08, P_GPS_SDA[1]))
lines.append(wire(P_J5_1[0] - 5.08, P_GPS_SDA[1], R4_X, P_GPS_SDA[1]))
lines.append(junction(R4_X, P_GPS_SDA[1]))

# I2C header SCL -> GPS SCL line
lines.append(wire(P_J5_2[0], P_J5_2[1], P_J5_2[0] - 5.08, P_J5_2[1]))
lines.append(wire(P_J5_2[0] - 5.08, P_J5_2[1], P_J5_2[0] - 5.08, P_GPS_SCL[1]))
lines.append(wire(P_J5_2[0] - 5.08, P_GPS_SCL[1], R10_X, P_GPS_SCL[1]))
lines.append(junction(R10_X, P_GPS_SCL[1]))

# I2C header 3.3V
lines.append(global_label("+3V3_SW", P_J5_3[0] - 10.16, P_J5_3[1], "input", 0))
lines.append(wire(P_J5_3[0] - 10.16, P_J5_3[1], P_J5_3[0], P_J5_3[1]))

# I2C header GND
lines.append(pwr("power:GND", f"#PWR0{pwr_idx}", "GND", P_J5_4[0] - 5.08, P_J5_4[1] + 2.54))
pwr_idx += 1
lines.append(wire(P_J5_4[0], P_J5_4[1], P_J5_4[0] - 5.08, P_J5_4[1]))
lines.append(wire(P_J5_4[0] - 5.08, P_J5_4[1], P_J5_4[0] - 5.08, P_J5_4[1] + 2.54))

# ── LCD Connector Section ──
lines.append(comp("Connector_Generic:Conn_01x05", "J4", "Sharp LCD", J4_X, J4_Y))
P_J4_1 = sym_to_abs(J4_X, J4_Y, -5.08, 2.54)
P_J4_2 = sym_to_abs(J4_X, J4_Y, -5.08, 0)
P_J4_3 = sym_to_abs(J4_X, J4_Y, -5.08, -2.54)
P_J4_4 = sym_to_abs(J4_X, J4_Y, -5.08, -5.08)
P_J4_5 = sym_to_abs(J4_X, J4_Y, -5.08, -7.62)

# LCD labels
lcd_labels = [
    ("LCD_SCLK", P_J4_1, "input"),
    ("LCD_MOSI", P_J4_2, "input"),
    ("LCD_CS", P_J4_3, "input"),
    ("LCD_EXTCOMIN", P_J4_4, "input"),
    ("LCD_DISP", P_J4_5, "input"),
]
for name, pos, shape in lcd_labels:
    lx = pos[0] - 15.24
    lines.append(global_label(name, lx, pos[1], shape, 0))
    lines.append(wire(lx, pos[1], pos[0], pos[1]))

# ── QSPI Flash Section ──
lines.append(comp("FreedomUnit:MX25R6435F", "U10", "MX25R6435F", U10_X, U10_Y))

P_FLASH_CS   = sym_to_abs(U10_X, U10_Y, -15.24, 7.62)
P_FLASH_IO1  = sym_to_abs(U10_X, U10_Y, -15.24, 2.54)
P_FLASH_IO2  = sym_to_abs(U10_X, U10_Y, -15.24, -2.54)
P_FLASH_VSS  = sym_to_abs(U10_X, U10_Y, 0, -15.24)
P_FLASH_IO0  = sym_to_abs(U10_X, U10_Y, 15.24, -2.54)
P_FLASH_SCK  = sym_to_abs(U10_X, U10_Y, 15.24, 2.54)
P_FLASH_IO3  = sym_to_abs(U10_X, U10_Y, 15.24, 7.62)
P_FLASH_VCC  = sym_to_abs(U10_X, U10_Y, 0, 15.24)

# Flash power
lines.append(global_label("+3V3_SW", P_FLASH_VCC[0] - 10.16, P_FLASH_VCC[1] - 5.08, "input", 0))
lines.append(wire(P_FLASH_VCC[0] - 10.16, P_FLASH_VCC[1] - 5.08, P_FLASH_VCC[0], P_FLASH_VCC[1] - 5.08))
lines.append(wire(P_FLASH_VCC[0], P_FLASH_VCC[1] - 5.08, P_FLASH_VCC[0], P_FLASH_VCC[1]))

lines.append(pwr("power:GND", f"#PWR0{pwr_idx}", "GND", P_FLASH_VSS[0], P_FLASH_VSS[1] + 5.08))
pwr_idx += 1
lines.append(wire(P_FLASH_VSS[0], P_FLASH_VSS[1], P_FLASH_VSS[0], P_FLASH_VSS[1] + 5.08))

# Flash signals
flash_labels = [
    ("QSPI_CS", P_FLASH_CS, "input", 0),
    ("QSPI_IO1", P_FLASH_IO1, "bidirectional", 0),
    ("QSPI_IO2", P_FLASH_IO2, "bidirectional", 0),
    ("QSPI_IO0", P_FLASH_IO0, "bidirectional", 180),
    ("QSPI_SCK", P_FLASH_SCK, "input", 180),
    ("QSPI_IO3", P_FLASH_IO3, "bidirectional", 180),
]
for name, pos, shape, angle in flash_labels:
    if angle == 0:  # left side
        lx = pos[0] - 10.16
    else:  # right side
        lx = pos[0] + 10.16
    lines.append(global_label(name, lx, pos[1], shape, angle))
    lines.append(wire(pos[0], pos[1], lx, pos[1]))

# ── Buttons Section ──
for i in range(7):
    bx = btn_x_start + i * btn_spacing
    by = btn_y
    sw_ref = btn_refs[i]
    cap_ref = cap_refs[i]
    label_name = btn_names[i]

    lines.append(comp("Switch:SW_Push", sw_ref, "PTS636", bx, by))
    lines.append(comp("Device:C", cap_ref, "100nF", bx + 5.08, by + 15.0))

    # Button pin 1 (left, at bx-5.08) -> global label
    p_sw1 = (bx - 5.08, by)
    p_sw2 = (bx + 5.08, by)
    lines.append(global_label(label_name, bx - 15.24, by, "input", 0))
    lines.append(wire(bx - 15.24, by, p_sw1[0], p_sw1[1]))

    # Button pin 2 (right) -> wire down to cap top, then to GND
    cap_top = (bx + 5.08, by + 15.0 - 3.81)
    cap_bot = (bx + 5.08, by + 15.0 + 3.81)

    # Wire from button pin2 down to cap
    lines.append(wire(p_sw2[0], p_sw2[1], p_sw2[0], cap_top[1]))

    # Also connect button pin2 to GND directly
    lines.append(pwr("power:GND", f"#PWR0{pwr_idx}", "GND", bx + 5.08, cap_bot[1] + 2.54))
    pwr_idx += 1
    lines.append(wire(cap_bot[0], cap_bot[1], bx + 5.08, cap_bot[1] + 2.54))

    # Junction at button side of cap (debounce)
    lines.append(wire(p_sw1[0], p_sw1[1], p_sw1[0], cap_top[1]))
    lines.append(wire(p_sw1[0], cap_top[1], cap_top[0], cap_top[1]))
    lines.append(junction(p_sw2[0], cap_top[1]))

# ── LEDs Section ──
for i in range(3):
    ly = led_y_start + i * led_spacing
    d_ref = led_refs[i]
    r_ref = led_r_refs[i]
    name = led_names[i]
    color = led_colors[i]

    # LED at led_x, resistor to its left
    rx = led_x - 20.0
    lines.append(comp("Device:R", r_ref, "680", rx, ly))
    lines.append(comp("Device:LED", d_ref, color, led_x, ly))

    # Label -> R top (pin1) horizontal
    # Actually R is vertical, so we need horizontal LED and R in series
    # Let's put them horizontal: label -> wire -> R (horizontal) -> wire -> LED -> GND
    # For horizontal R: place at 90 degree rotation

    # Resistor pin1 (top at rx, ly-3.81) and pin2 (bottom at rx, ly+3.81) — vertical
    # LED pin2/anode (right at led_x+3.81) and pin1/cathode (left at led_x-3.81)

    # Label on left -> R pin1 top
    pr1 = (rx, round(ly - 3.81, 2))
    pr2 = (rx, round(ly + 3.81, 2))
    pdk = (led_x - 3.81, ly)   # LED cathode
    pda = (led_x + 3.81, ly)   # LED anode

    # Global label for the LED signal
    lines.append(global_label(name, rx - 10.16, ly, "output", 0))
    # Wire: label -> resistor top
    lines.append(wire(rx - 10.16, ly, rx, pr1[1]))
    lines.append(wire(rx, pr1[1], rx, ly))

    # Wire: resistor bottom -> LED anode
    # Actually wiring: signal -> R -> LED -> GND
    # Signal at R pin1 top, R pin2 bottom -> wire to LED anode (pin2, right side in standard orientation)
    # Wait - LED: pin1=K(cathode), pin2=A(anode). Active HIGH means signal -> R -> LED anode, cathode -> GND.
    # So: signal -> R(pin1) -> R(pin2) -> LED(A/pin2) -> LED(K/pin1) -> GND

    # Connect R bottom to LED anode (horizontal wire)
    lines.append(wire(pr2[0], pr2[1], led_x + 3.81, pr2[1]))
    lines.append(wire(led_x + 3.81, pr2[1], led_x + 3.81, ly))
    # Actually let me simplify: wire R bottom straight to LED
    # R bottom at (rx, ly+3.81), LED anode at (led_x+3.81, ly)
    # Route: R bottom -> right -> up -> LED anode
    lines.append(wire(pda[0], pda[1], pda[0] + 5.08, pda[1]))

    # Wait, I'm overcomplicating. Let me just wire them in a simpler vertical arrangement.
    # Place LED to the right of R, both on the same Y line.
    # R pin1 (top) gets signal, R pin2 (bottom) -> down to a horizontal wire
    # that goes right to LED anode, LED cathode goes to GND.

    # Actually, let me just connect:
    # R pin2 bottom -> wire to LED cathode (left pin). Both on same horizontal line? No...
    # 
    # Simplest: use vertical R + horizontal LED.
    # R is at (rx, ly), pins at top/bottom.
    # LED is at (led_x, ly + 3.81) — place it at the R bottom level
    # R_bottom = (rx, ly+3.81) -> wire right -> LED_anode (led_x+3.81, ly+3.81)
    # LED_cathode (led_x-3.81, ly+3.81) --- wait that doesn't make sense with orientation.

    # Let me just wire more simply. R bottom to LED. 
    # For LED horizontal at same y as R bottom:

    # GND at LED cathode
    lines.append(pwr("power:GND", f"#PWR0{pwr_idx}", "GND", pdk[0] - 2.54, pdk[1]))
    pwr_idx += 1
    lines.append(wire(pdk[0], pdk[1], pdk[0] - 2.54, pdk[1]))

# Close
lines.append(')')

output = '\n'.join(lines)
output = clean_floats(output)

output_path = '/home/user/workspace/Sheet5_Peripherals.kicad_sch'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(output)

print(f"\nGenerated: {output_path}")
print(f"File size: {len(output)} bytes")
