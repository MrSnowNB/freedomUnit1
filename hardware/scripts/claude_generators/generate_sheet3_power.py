#!/usr/bin/env python3
"""
Generate Sheet3_Power.kicad_sch for Freedom Unit V2

Components:
  - U4: BQ25504 Solar Energy Harvester (VQFN-20, custom symbol)
  - U5: MCP73831T USB Li-Ion Charger (SOT-23-5, custom symbol)
  - D1: BAT54JFILM Schottky OR-ing diode (SOD-323)
  - U7: TPS7A02 LDO 3.3V regulator (SOT-23-5, custom symbol)
  - U8: TPS22918 Load Switch (SOT-23-5, custom symbol)
  - SW1: C&K JS102011SAQN Slide Switch (SPDT)
  - BT1: Keystone 1042P Battery Holder (18650)
  - J1: JST S2B-PH-K-S Solar Connector (2-pin)
  - R1: 100k (battery voltage divider top)
  - R2: 100k (battery voltage divider bottom)
  - R3: 2k (MCP73831 PROG resistor for 500mA)
  - C1-C9: Various decoupling caps

Nets (global labels):
  - VBUS (from USB sheet)
  - +3V3 (always-on 3.3V rail to MCU)
  - +3V3_SW (switched 3.3V rail to peripherals)
  - BATTERY_ADC (to MCU P0.04/AIN2)
  - POWER_EN (from MCU P0.12)
  - BQ_VBAT_OK (to MCU P0.16)
"""

import uuid
import re

def uid():
    return str(uuid.uuid4())

ROOT_UUID = "00000000-0000-0000-0000-000000000001"
SHEET_UUID = "00000000-0000-0000-0000-000000000003"

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

def net_label(name, x, y, angle=0):
    return (f'  (label "{name}" (at {x} {y} {angle}) '
            f'(effects (font (size 1.27 1.27))) (uuid "{uid()}"))')

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

# BQ25504 — Solar Energy Harvester (simplified symbol with key pins)
# Key pins: VIN, VSS, VBAT, VBAT_OK, VRDIV, OT_PROG, VREF_SAMP, OK_PROG, OK_HYST
# We'll use a simplified rectangular symbol with the critical pins
SYM_BQ25504 = '''    (symbol "FreedomUnit:BQ25504" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 19.05 0) (effects (font (size 1.27 1.27))))
      (property "Value" "BQ25504" (at 0 -19.05 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "https://www.ti.com/lit/ds/symlink/bq25504.pdf" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "BQ25504_0_1"
        (rectangle (start -12.7 17.78) (end 12.7 -17.78) (stroke (width 0.254) (type default)) (fill (type background)))
        (text "BQ25504" (at 0 0 0) (effects (font (size 1.27 1.27))))
        (text "Solar MPPT" (at 0 -2.54 0) (effects (font (size 1.0 1.0))))
      )
      (symbol "BQ25504_1_1"
        (pin power_in line (at -17.78 12.7 0) (length 5.08) (name "VIN_DC" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at -17.78 -12.7 0) (length 5.08) (name "VSS" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin power_out line (at 17.78 12.7 180) (length 5.08) (name "VBAT" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
        (pin output line (at 17.78 5.08 180) (length 5.08) (name "VBAT_OK" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 17.78 -5.08 180) (length 5.08) (name "VRDIV" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -17.78 5.08 0) (length 5.08) (name "VREF_SAMP" (effects (font (size 1.27 1.27)))) (number "6" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -17.78 -5.08 0) (length 5.08) (name "OK_PROG" (effects (font (size 1.27 1.27)))) (number "7" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 17.78 -12.7 180) (length 5.08) (name "OK_HYST" (effects (font (size 1.27 1.27)))) (number "8" (effects (font (size 1.27 1.27)))))
      )
    )'''

# MCP73831 — USB Li-Ion Charger (SOT-23-5)
# Pin 1: STAT, Pin 2: VSS, Pin 3: VBAT, Pin 4: VDD (VBUS), Pin 5: PROG
SYM_MCP73831 = '''    (symbol "FreedomUnit:MCP73831" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 10.16 0) (effects (font (size 1.27 1.27))))
      (property "Value" "MCP73831" (at 0 -10.16 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "MCP73831_0_1"
        (rectangle (start -10.16 8.89) (end 10.16 -8.89) (stroke (width 0.254) (type default)) (fill (type background)))
        (text "MCP73831" (at 0 0 0) (effects (font (size 1.27 1.27))))
        (text "Li-Ion Charger" (at 0 -2.54 0) (effects (font (size 1.0 1.0))))
      )
      (symbol "MCP73831_1_1"
        (pin power_in line (at -15.24 5.08 0) (length 5.08) (name "VDD" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
        (pin power_out line (at 15.24 5.08 180) (length 5.08) (name "VBAT" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 0 -13.97 90) (length 5.08) (name "VSS" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin output line (at 15.24 -2.54 180) (length 5.08) (name "STAT" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -15.24 -2.54 0) (length 5.08) (name "PROG" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27)))))
      )
    )'''

# TPS7A02 — 3.3V LDO (SOT-23-5)
# Pin 1: OUT, Pin 2: GND, Pin 3: EN, Pin 4: NC, Pin 5: IN
SYM_TPS7A02 = '''    (symbol "FreedomUnit:TPS7A02" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 10.16 0) (effects (font (size 1.27 1.27))))
      (property "Value" "TPS7A02" (at 0 -10.16 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "TPS7A02_0_1"
        (rectangle (start -10.16 8.89) (end 10.16 -8.89) (stroke (width 0.254) (type default)) (fill (type background)))
        (text "TPS7A02" (at 0 0 0) (effects (font (size 1.27 1.27))))
        (text "3.3V LDO" (at 0 -2.54 0) (effects (font (size 1.0 1.0))))
      )
      (symbol "TPS7A02_1_1"
        (pin power_in line (at -15.24 5.08 0) (length 5.08) (name "IN" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27)))))
        (pin power_out line (at 15.24 5.08 180) (length 5.08) (name "OUT" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin input line (at -15.24 -2.54 0) (length 5.08) (name "EN" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 0 -13.97 90) (length 5.08) (name "GND" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 15.24 -2.54 180) (length 5.08) (name "NC" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
      )
    )'''

# TPS22918 — Load Switch (SOT-23-5)
# Pin 1: IN, Pin 2: GND, Pin 3: ON, Pin 4: NC, Pin 5: OUT
SYM_TPS22918 = '''    (symbol "FreedomUnit:TPS22918" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 10.16 0) (effects (font (size 1.27 1.27))))
      (property "Value" "TPS22918" (at 0 -10.16 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "TPS22918_0_1"
        (rectangle (start -10.16 8.89) (end 10.16 -8.89) (stroke (width 0.254) (type default)) (fill (type background)))
        (text "TPS22918" (at 0 0 0) (effects (font (size 1.27 1.27))))
        (text "Load Switch" (at 0 -2.54 0) (effects (font (size 1.0 1.0))))
      )
      (symbol "TPS22918_1_1"
        (pin power_in line (at -15.24 5.08 0) (length 5.08) (name "IN" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin power_out line (at 15.24 5.08 180) (length 5.08) (name "OUT" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27)))))
        (pin input line (at -15.24 -2.54 0) (length 5.08) (name "ON" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 0 -13.97 90) (length 5.08) (name "GND" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 15.24 -2.54 180) (length 5.08) (name "NC" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
      )
    )'''

# Diode symbol for BAT54J
SYM_DIODE = '''    (symbol "Device:D_Schottky" (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
      (property "Reference" "D" (at 0 3.81 0) (effects (font (size 1.27 1.27))))
      (property "Value" "D_Schottky" (at 0 -3.81 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "D_Schottky_0_1"
        (polyline (pts (xy 1.27 0) (xy -1.27 0)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 1.27 -1.27) (xy 1.27 1.27) (xy -1.27 0) (xy 1.27 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy -1.27 1.27) (xy -1.27 -1.27) (xy -0.762 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
      )
      (symbol "D_Schottky_1_1"
        (pin passive line (at -3.81 0 0) (length 2.54) (name "K" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 3.81 0 180) (length 2.54) (name "A" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )'''

# Slide switch (SPDT)
SYM_SW_SPDT = '''    (symbol "Switch:SW_SPDT" (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
      (property "Reference" "SW" (at 0 5.08 0) (effects (font (size 1.27 1.27))))
      (property "Value" "SW_SPDT" (at 0 -5.08 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "SW_SPDT_0_1"
        (circle (center -2.032 0) (radius 0.4064) (stroke (width 0) (type default)) (fill (type none)))
        (circle (center 2.032 2.54) (radius 0.4064) (stroke (width 0) (type default)) (fill (type none)))
        (circle (center 2.032 -2.54) (radius 0.4064) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy -1.524 0.254) (xy 1.524 2.286)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "SW_SPDT_1_1"
        (pin passive line (at -5.08 0 0) (length 2.54) (name "COM" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 5.08 2.54 180) (length 2.54) (name "A" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 5.08 -2.54 180) (length 2.54) (name "B" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
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

# ═══════════════════════════════════════════════════════════════
# LAYOUT — Organized into functional groups on A3 landscape
# ═══════════════════════════════════════════════════════════════
# We'll use A3 paper for the power sheet since it has many components.
# Layout left-to-right:
#   Solar input → BQ25504 → Diode OR → Battery → Slide Switch → VBAT rail
#   USB VBUS → MCP73831 → Diode OR (same junction)
#   VBAT rail → TPS7A02 → +3V3 always-on → nRF
#   +3V3 → TPS22918 → +3V3_SW switched → peripherals
#   VBAT → voltage divider → ADC

# Group 1: Solar input + BQ25504 (top-left)
J1_X, J1_Y = 40.0, 50.0     # Solar JST connector
U4_X, U4_Y = 85.0, 55.0     # BQ25504

# Group 2: USB charger (bottom-left)
U5_X, U5_Y = 85.0, 115.0    # MCP73831

# Group 3: OR-ing diode + battery + slide switch (center)
D1A_X, D1A_Y = 130.0, 50.0   # BAT54J from BQ25504 (anode=right side)
D1B_X, D1B_Y = 130.0, 110.0  # Second BAT54J from MCP73831
# Actually we have ONE diode, not two. The topology from the spec:
# BQ25504 VBAT output -> battery (direct)
# MCP73831 VBAT output -> BAT54J diode -> battery (prevents backfeed)
# Let me re-read the spec... "OR-ing Schottky diode between BQ25504 VBAT and MCP73831 output"
# So: BQ25504 charges battery directly. MCP73831 charges through the diode.
# The diode prevents MCP73831 from backfeeding into BQ25504.

D1_X, D1_Y = 130.0, 115.0   # BAT54J diode (cathode->battery, anode<-MCP73831)

# Battery + switch
BT1_X, BT1_Y = 165.0, 55.0  # Battery holder
SW1_X, SW1_Y = 195.0, 55.0   # Slide switch

# Group 4: LDO + Load switch (right side)
U7_X, U7_Y = 235.0, 55.0     # TPS7A02 LDO
U8_X, U8_Y = 235.0, 115.0    # TPS22918 Load Switch

# Group 5: Voltage divider (far right, near VBAT rail)
R1_X, R1_Y = 200.0, 85.0     # 100k top
R2_X, R2_Y = 200.0, 100.0    # 100k bottom

# Decoupling caps
C1_X, C1_Y = 55.0, 75.0      # BQ25504 input cap
C2_X, C2_Y = 115.0, 75.0     # BQ25504 VBAT cap
C3_X, C3_Y = 65.0, 130.0     # MCP73831 VDD cap
C4_X, C4_Y = 115.0, 130.0    # MCP73831 VBAT cap
C5_X, C5_Y = 220.0, 75.0     # TPS7A02 input cap (1uF)
C6_X, C6_Y = 255.0, 75.0     # TPS7A02 output cap (1uF)
C7_X, C7_Y = 220.0, 130.0    # TPS22918 input cap (100nF)
C8_X, C8_Y = 255.0, 130.0    # TPS22918 output cap (100nF)

# PROG resistor for MCP73831
R3_X, R3_Y = 65.0, 115.0     # 2k PROG

# ═══════════════════════════════════════════════════════════════
# PIN POSITIONS
# ═══════════════════════════════════════════════════════════════

# BQ25504 U4 pins
P_U4_VIN   = sym_to_abs(U4_X, U4_Y, -17.78, 12.7)
P_U4_VSS   = sym_to_abs(U4_X, U4_Y, -17.78, -12.7)
P_U4_VBAT  = sym_to_abs(U4_X, U4_Y, 17.78, 12.7)
P_U4_VBOK  = sym_to_abs(U4_X, U4_Y, 17.78, 5.08)
P_U4_VRDIV = sym_to_abs(U4_X, U4_Y, 17.78, -5.08)
P_U4_VREF  = sym_to_abs(U4_X, U4_Y, -17.78, 5.08)
P_U4_OKPG  = sym_to_abs(U4_X, U4_Y, -17.78, -5.08)
P_U4_OKHYS = sym_to_abs(U4_X, U4_Y, 17.78, -12.7)

# MCP73831 U5 pins
P_U5_VDD  = sym_to_abs(U5_X, U5_Y, -15.24, 5.08)
P_U5_VBAT = sym_to_abs(U5_X, U5_Y, 15.24, 5.08)
P_U5_VSS  = sym_to_abs(U5_X, U5_Y, 0, -13.97)
P_U5_STAT = sym_to_abs(U5_X, U5_Y, 15.24, -2.54)
P_U5_PROG = sym_to_abs(U5_X, U5_Y, -15.24, -2.54)

# BAT54J D1 (horizontal) — K=pin1 left, A=pin2 right
P_D1_K = (D1_X - 3.81, D1_Y)
P_D1_A = (D1_X + 3.81, D1_Y)

# TPS7A02 U7 pins
P_U7_IN  = sym_to_abs(U7_X, U7_Y, -15.24, 5.08)
P_U7_OUT = sym_to_abs(U7_X, U7_Y, 15.24, 5.08)
P_U7_EN  = sym_to_abs(U7_X, U7_Y, -15.24, -2.54)
P_U7_GND = sym_to_abs(U7_X, U7_Y, 0, -13.97)
P_U7_NC  = sym_to_abs(U7_X, U7_Y, 15.24, -2.54)

# TPS22918 U8 pins
P_U8_IN  = sym_to_abs(U8_X, U8_Y, -15.24, 5.08)
P_U8_OUT = sym_to_abs(U8_X, U8_Y, 15.24, 5.08)
P_U8_ON  = sym_to_abs(U8_X, U8_Y, -15.24, -2.54)
P_U8_GND = sym_to_abs(U8_X, U8_Y, 0, -13.97)
P_U8_NC  = sym_to_abs(U8_X, U8_Y, 15.24, -2.54)

# Solar connector J1 pins (Conn_01x02, left side)
P_J1_1 = sym_to_abs(J1_X, J1_Y, -5.08, 0)
P_J1_2 = sym_to_abs(J1_X, J1_Y, -5.08, -2.54)

# Battery holder BT1 (Conn_01x02)
P_BT1_1 = sym_to_abs(BT1_X, BT1_Y, -5.08, 0)
P_BT1_2 = sym_to_abs(BT1_X, BT1_Y, -5.08, -2.54)

# Slide switch SW1 (SPDT)
P_SW1_COM = sym_to_abs(SW1_X, SW1_Y, -5.08, 0)
P_SW1_A   = sym_to_abs(SW1_X, SW1_Y, 5.08, 2.54)
P_SW1_B   = sym_to_abs(SW1_X, SW1_Y, 5.08, -2.54)

# Resistor pins
P_R1_1 = (R1_X, round(R1_Y - 3.81, 2))
P_R1_2 = (R1_X, round(R1_Y + 3.81, 2))
P_R2_1 = (R2_X, round(R2_Y - 3.81, 2))
P_R2_2 = (R2_X, round(R2_Y + 3.81, 2))
P_R3_1 = (R3_X, round(R3_Y - 3.81, 2))
P_R3_2 = (R3_X, round(R3_Y + 3.81, 2))

# Cap pins (all vertical)
def cap_pins(cx, cy):
    return ((cx, round(cy - 3.81, 2)), (cx, round(cy + 3.81, 2)))

PC1 = cap_pins(C1_X, C1_Y)
PC2 = cap_pins(C2_X, C2_Y)
PC3 = cap_pins(C3_X, C3_Y)
PC4 = cap_pins(C4_X, C4_Y)
PC5 = cap_pins(C5_X, C5_Y)
PC6 = cap_pins(C6_X, C6_Y)
PC7 = cap_pins(C7_X, C7_Y)
PC8 = cap_pins(C8_X, C8_Y)

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
lines.append('    (title "Sheet 3 — Power Management")')
lines.append('    (date "2026-03-03")')
lines.append('    (rev "V2.2")')
lines.append('    (company "GarageAGI LLC")')
lines.append('  )')

# lib_symbols
lines.append('  (lib_symbols')
lines.append(SYM_BQ25504)
lines.append(SYM_MCP73831)
lines.append(SYM_TPS7A02)
lines.append(SYM_TPS22918)
lines.append(SYM_DIODE)
lines.append(SYM_SW_SPDT)
lines.append(SYM_C)
lines.append(SYM_R)
lines.append(SYM_CONN_2)
lines.append(SYM_PWR_3V3)
lines.append(SYM_GND)
lines.append(SYM_VBAT)
lines.append('  )')

# ── Components ──
lines.append(comp("Connector_Generic:Conn_01x02", "J1", "Solar JST-PH", J1_X, J1_Y))
lines.append(comp("FreedomUnit:BQ25504", "U4", "BQ25504", U4_X, U4_Y))
lines.append(comp("FreedomUnit:MCP73831", "U5", "MCP73831", U5_X, U5_Y))
lines.append(comp("Device:D_Schottky", "D1", "BAT54JFILM", D1_X, D1_Y))
lines.append(comp("Connector_Generic:Conn_01x02", "BT1", "18650 Holder", BT1_X, BT1_Y))
lines.append(comp("Switch:SW_SPDT", "SW1", "JS102011SAQN", SW1_X, SW1_Y))
lines.append(comp("FreedomUnit:TPS7A02", "U7", "TPS7A02", U7_X, U7_Y))
lines.append(comp("FreedomUnit:TPS22918", "U8", "TPS22918", U8_X, U8_Y))
lines.append(comp("Device:R", "R1", "100k", R1_X, R1_Y))
lines.append(comp("Device:R", "R2", "100k", R2_X, R2_Y))
lines.append(comp("Device:R", "R3", "2k", R3_X, R3_Y))
lines.append(comp("Device:C", "C1", "10uF", C1_X, C1_Y))
lines.append(comp("Device:C", "C2", "10uF", C2_X, C2_Y))
lines.append(comp("Device:C", "C3", "4.7uF", C3_X, C3_Y))
lines.append(comp("Device:C", "C4", "4.7uF", C4_X, C4_Y))
lines.append(comp("Device:C", "C5", "1uF", C5_X, C5_Y))
lines.append(comp("Device:C", "C6", "1uF", C6_X, C6_Y))
lines.append(comp("Device:C", "C7", "100nF", C7_X, C7_Y))
lines.append(comp("Device:C", "C8", "100nF", C8_X, C8_Y))

# ── Power Symbols ──
# GND symbols throughout
pwr_idx = 30
gnd_positions = [
    (P_U4_VSS[0], P_U4_VSS[1] + 5.08),      # BQ25504 VSS
    (P_U5_VSS[0], P_U5_VSS[1] + 5.08),       # MCP73831 VSS
    (P_U7_GND[0], P_U7_GND[1] + 5.08),       # TPS7A02 GND
    (P_U8_GND[0], P_U8_GND[1] + 5.08),       # TPS22918 GND
    (P_J1_2[0] - 5.08, P_J1_2[1] + 2.54),    # Solar GND
    (P_BT1_2[0] - 5.08, P_BT1_2[1] + 2.54),  # Battery GND
    (PC1[1][0], PC1[1][1] + 2.54),             # C1 GND
    (PC2[1][0], PC2[1][1] + 2.54),             # C2 GND
    (PC3[1][0], PC3[1][1] + 2.54),             # C3 GND
    (PC4[1][0], PC4[1][1] + 2.54),             # C4 GND
    (PC5[1][0], PC5[1][1] + 2.54),             # C5 GND
    (PC6[1][0], PC6[1][1] + 2.54),             # C6 GND
    (PC7[1][0], PC7[1][1] + 2.54),             # C7 GND
    (PC8[1][0], PC8[1][1] + 2.54),             # C8 GND
    (P_R2_2[0], P_R2_2[1] + 2.54),            # R2 bottom GND
]

for gx, gy in gnd_positions:
    lines.append(pwr("power:GND", f"#PWR0{pwr_idx}", "GND", gx, gy))
    pwr_idx += 1

# VBAT power symbol on switched VBAT rail (after slide switch)
vbat_rail_y = 42.0  # VBAT rail horizontal line
lines.append(pwr("power:VBAT", f"#PWR0{pwr_idx}", "VBAT", P_SW1_A[0] + 5.08, vbat_rail_y - 5.08))
pwr_idx += 1

# +3V3 on LDO output
lines.append(pwr("power:+3V3", f"#PWR0{pwr_idx}", "+3V3", P_U7_OUT[0] + 5.08, P_U7_OUT[1] - 5.08))
pwr_idx += 1

# ── Global Labels ──
# VBUS input from USB sheet
lines.append(global_label("VBUS", P_U5_VDD[0] - 10.16, P_U5_VDD[1], "input", 0))
# +3V3_SW output to peripherals
lines.append(global_label("+3V3_SW", P_U8_OUT[0] + 10.16, P_U8_OUT[1], "output", 180))
# BATTERY_ADC to MCU
lines.append(global_label("BATTERY_ADC", P_R1_2[0] + 10.16, P_R1_2[1], "output", 180))
# POWER_EN from MCU
lines.append(global_label("POWER_EN", P_U8_ON[0] - 10.16, P_U8_ON[1], "input", 0))
# BQ_VBAT_OK to MCU
lines.append(global_label("BQ_VBAT_OK", P_U4_VBOK[0] + 10.16, P_U4_VBOK[1], "output", 180))

# ── Wires ──

# Solar connector J1 pin1 -> BQ25504 VIN
lines.append(wire(P_J1_1[0], P_J1_1[1], P_U4_VIN[0], P_U4_VIN[1]))

# Solar connector J1 pin2 (GND) -> down to GND
lines.append(wire(P_J1_2[0], P_J1_2[1], P_J1_2[0] - 5.08, P_J1_2[1]))
lines.append(wire(P_J1_2[0] - 5.08, P_J1_2[1], P_J1_2[0] - 5.08, P_J1_2[1] + 2.54))

# BQ25504 VSS -> GND
lines.append(wire(P_U4_VSS[0], P_U4_VSS[1], P_U4_VSS[0], P_U4_VSS[1] + 5.08))

# BQ25504 VBAT output -> horizontal to battery area
# BQ25504 VBAT -> C2 top -> Battery BT1 pin1
lines.append(wire(P_U4_VBAT[0], P_U4_VBAT[1], PC2[0][0], P_U4_VBAT[1]))
lines.append(wire(PC2[0][0], P_U4_VBAT[1], PC2[0][0], PC2[0][1]))
lines.append(wire(PC2[0][0], P_U4_VBAT[1], P_BT1_1[0], P_U4_VBAT[1]))
lines.append(wire(P_BT1_1[0], P_U4_VBAT[1], P_BT1_1[0], P_BT1_1[1]))
lines.append(junction(PC2[0][0], P_U4_VBAT[1]))

# BQ25504 VBAT_OK -> label
lines.append(wire(P_U4_VBOK[0], P_U4_VBOK[1], P_U4_VBOK[0] + 10.16, P_U4_VBOK[1]))

# BQ25504 programming pins — no connect for now (they need external resistors but simplified)
lines.append(no_connect(P_U4_VRDIV[0], P_U4_VRDIV[1]))
lines.append(no_connect(P_U4_VREF[0], P_U4_VREF[1]))
lines.append(no_connect(P_U4_OKPG[0], P_U4_OKPG[1]))
lines.append(no_connect(P_U4_OKHYS[0], P_U4_OKHYS[1]))

# C1 (BQ25504 input) near J1/VIN
lines.append(wire(PC1[0][0], PC1[0][1], PC1[0][0], P_U4_VIN[1]))
lines.append(wire(PC1[0][0], P_U4_VIN[1], P_U4_VIN[0], P_U4_VIN[1]))
lines.append(junction(PC1[0][0], P_U4_VIN[1]))
lines.append(wire(PC1[1][0], PC1[1][1], PC1[1][0], PC1[1][1] + 2.54))

# C2 bottom -> GND
lines.append(wire(PC2[1][0], PC2[1][1], PC2[1][0], PC2[1][1] + 2.54))

# VBUS label -> MCP73831 VDD
lines.append(wire(P_U5_VDD[0] - 10.16, P_U5_VDD[1], P_U5_VDD[0], P_U5_VDD[1]))

# C3 (MCP73831 VDD cap)
lines.append(wire(PC3[0][0], PC3[0][1], PC3[0][0], P_U5_VDD[1]))
lines.append(wire(PC3[0][0], P_U5_VDD[1], P_U5_VDD[0], P_U5_VDD[1]))
lines.append(junction(PC3[0][0], P_U5_VDD[1]))
lines.append(wire(PC3[1][0], PC3[1][1], PC3[1][0], PC3[1][1] + 2.54))

# MCP73831 VSS -> GND
lines.append(wire(P_U5_VSS[0], P_U5_VSS[1], P_U5_VSS[0], P_U5_VSS[1] + 5.08))

# MCP73831 PROG -> R3 top, R3 bottom -> GND using GND symbol at R3 bottom
lines.append(wire(P_U5_PROG[0], P_U5_PROG[1], P_R3_1[0], P_U5_PROG[1]))
lines.append(wire(P_R3_1[0], P_U5_PROG[1], P_R3_1[0], P_R3_1[1]))
# R3 bottom -> GND — add a GND symbol
lines.append(pwr("power:GND", f"#PWR0{pwr_idx}", "GND", R3_X, P_R3_2[1] + 2.54))
pwr_idx += 1
lines.append(wire(P_R3_2[0], P_R3_2[1], R3_X, P_R3_2[1] + 2.54))

# MCP73831 STAT -> no connect (or could route to LED, but simplified)
lines.append(no_connect(P_U5_STAT[0], P_U5_STAT[1]))

# MCP73831 VBAT output -> D1 (BAT54J diode, anode side)
# D1: anode (pin2, right side at D1_X+3.81) connects to MCP73831 VBAT
# D1: cathode (pin1, left side at D1_X-3.81) connects to battery VBAT rail
lines.append(wire(P_U5_VBAT[0], P_U5_VBAT[1], P_D1_A[0], P_U5_VBAT[1]))
lines.append(wire(P_D1_A[0], P_U5_VBAT[1], P_D1_A[0], P_D1_A[1]))

# C4 (MCP73831 VBAT cap) between MCP73831 VBAT and GND
lines.append(wire(PC4[0][0], PC4[0][1], PC4[0][0], P_U5_VBAT[1]))
lines.append(wire(PC4[0][0], P_U5_VBAT[1], P_U5_VBAT[0], P_U5_VBAT[1]))
lines.append(junction(PC4[0][0], P_U5_VBAT[1]))
lines.append(wire(PC4[1][0], PC4[1][1], PC4[1][0], PC4[1][1] + 2.54))

# D1 cathode -> battery rail (horizontal line at battery+ level)
bat_rail_y = P_U4_VBAT[1]  # Same Y as BQ25504 VBAT
lines.append(wire(P_D1_K[0], P_D1_K[1], P_D1_K[0], bat_rail_y))
lines.append(wire(P_D1_K[0], bat_rail_y, P_BT1_1[0], bat_rail_y))
lines.append(junction(P_BT1_1[0], bat_rail_y))

# Battery BT1 pin2 (GND) -> GND
lines.append(wire(P_BT1_2[0], P_BT1_2[1], P_BT1_2[0] - 5.08, P_BT1_2[1]))
lines.append(wire(P_BT1_2[0] - 5.08, P_BT1_2[1], P_BT1_2[0] - 5.08, P_BT1_2[1] + 2.54))

# Battery BT1 pin1 -> Slide Switch COM
lines.append(wire(P_BT1_1[0], P_BT1_1[1], P_SW1_COM[0], P_SW1_COM[1]))

# Slide Switch A (ON position) -> VBAT rail going right
lines.append(wire(P_SW1_A[0], P_SW1_A[1], P_SW1_A[0] + 5.08, P_SW1_A[1]))
# VBAT power symbol
lines.append(wire(P_SW1_A[0] + 5.08, P_SW1_A[1], P_SW1_A[0] + 5.08, vbat_rail_y - 5.08))

# Switch B (OFF position) -> no connect
lines.append(no_connect(P_SW1_B[0], P_SW1_B[1]))

# VBAT rail -> TPS7A02 IN
vbat_x = P_SW1_A[0] + 5.08
lines.append(wire(vbat_x, P_SW1_A[1], vbat_x, P_U7_IN[1]))
lines.append(wire(vbat_x, P_U7_IN[1], P_U7_IN[0], P_U7_IN[1]))

# VBAT rail -> TPS22918 IN (through +3V3)
# Actually TPS22918 IN gets +3V3 (from LDO output), not VBAT directly
# The spec says: +3V3 → TPS22918 → +3V3_SW
# So: VBAT → TPS7A02 → +3V3 → TPS22918 → +3V3_SW

# TPS7A02 EN -> tie to IN (always enabled)
lines.append(wire(P_U7_EN[0], P_U7_EN[1], P_U7_EN[0] - 5.08, P_U7_EN[1]))
lines.append(wire(P_U7_EN[0] - 5.08, P_U7_EN[1], P_U7_EN[0] - 5.08, P_U7_IN[1]))
lines.append(wire(P_U7_EN[0] - 5.08, P_U7_IN[1], P_U7_IN[0], P_U7_IN[1]))
lines.append(junction(P_U7_IN[0], P_U7_IN[1]))

# TPS7A02 GND
lines.append(wire(P_U7_GND[0], P_U7_GND[1], P_U7_GND[0], P_U7_GND[1] + 5.08))

# TPS7A02 NC -> no connect
lines.append(no_connect(P_U7_NC[0], P_U7_NC[1]))

# TPS7A02 OUT -> +3V3 power symbol + wire to TPS22918
ldo_out_x = P_U7_OUT[0] + 5.08
lines.append(wire(P_U7_OUT[0], P_U7_OUT[1], ldo_out_x, P_U7_OUT[1]))
# +3V3 symbol
lines.append(wire(ldo_out_x, P_U7_OUT[1], ldo_out_x, P_U7_OUT[1] - 5.08))

# TPS7A02 OUT -> TPS22918 IN (vertical down then horizontal)
lines.append(wire(ldo_out_x, P_U7_OUT[1], ldo_out_x, P_U8_IN[1]))
lines.append(wire(ldo_out_x, P_U8_IN[1], P_U8_IN[0], P_U8_IN[1]))
lines.append(junction(ldo_out_x, P_U7_OUT[1]))

# C5 (TPS7A02 input cap)
lines.append(wire(PC5[0][0], PC5[0][1], PC5[0][0], P_U7_IN[1]))
lines.append(wire(PC5[0][0], P_U7_IN[1], P_U7_IN[0], P_U7_IN[1]))
lines.append(junction(PC5[0][0], P_U7_IN[1]))
lines.append(wire(PC5[1][0], PC5[1][1], PC5[1][0], PC5[1][1] + 2.54))

# C6 (TPS7A02 output cap)
lines.append(wire(PC6[0][0], PC6[0][1], PC6[0][0], P_U7_OUT[1]))
lines.append(wire(PC6[0][0], P_U7_OUT[1], P_U7_OUT[0], P_U7_OUT[1]))
lines.append(junction(PC6[0][0], P_U7_OUT[1]))
lines.append(wire(PC6[1][0], PC6[1][1], PC6[1][0], PC6[1][1] + 2.54))

# TPS22918 ON <- POWER_EN label
lines.append(wire(P_U8_ON[0] - 10.16, P_U8_ON[1], P_U8_ON[0], P_U8_ON[1]))

# TPS22918 GND
lines.append(wire(P_U8_GND[0], P_U8_GND[1], P_U8_GND[0], P_U8_GND[1] + 5.08))

# TPS22918 NC -> no connect
lines.append(no_connect(P_U8_NC[0], P_U8_NC[1]))

# TPS22918 OUT -> +3V3_SW label
lines.append(wire(P_U8_OUT[0], P_U8_OUT[1], P_U8_OUT[0] + 10.16, P_U8_OUT[1]))

# C7 (TPS22918 input cap)
lines.append(wire(PC7[0][0], PC7[0][1], PC7[0][0], P_U8_IN[1]))
lines.append(wire(PC7[0][0], P_U8_IN[1], P_U8_IN[0], P_U8_IN[1]))
lines.append(junction(PC7[0][0], P_U8_IN[1]))
lines.append(wire(PC7[1][0], PC7[1][1], PC7[1][0], PC7[1][1] + 2.54))

# C8 (TPS22918 output cap)
lines.append(wire(PC8[0][0], PC8[0][1], PC8[0][0], P_U8_OUT[1]))
lines.append(wire(PC8[0][0], P_U8_OUT[1], P_U8_OUT[0], P_U8_OUT[1]))
lines.append(junction(PC8[0][0], P_U8_OUT[1]))
lines.append(wire(PC8[1][0], PC8[1][1], PC8[1][0], PC8[1][1] + 2.54))

# Voltage divider: VBAT -> R1 -> R2 -> GND
# R1 top connects to VBAT rail
lines.append(wire(P_R1_1[0], P_R1_1[1], P_R1_1[0], P_U7_IN[1]))
lines.append(wire(P_R1_1[0], P_U7_IN[1], vbat_x, P_U7_IN[1]))
lines.append(junction(vbat_x, P_U7_IN[1]))

# R1 bottom connects to R2 top (midpoint = ADC)
lines.append(wire(P_R1_2[0], P_R1_2[1], P_R2_1[0], P_R2_1[1]))
# BATTERY_ADC label at midpoint
lines.append(wire(P_R1_2[0], P_R1_2[1], P_R1_2[0] + 10.16, P_R1_2[1]))
lines.append(junction(P_R1_2[0], P_R1_2[1]))

# R2 bottom -> GND
lines.append(wire(P_R2_2[0], P_R2_2[1], P_R2_2[0], P_R2_2[1] + 2.54))

# Close
lines.append(')')

# ═══════════════════════════════════════════════════════════════
# WRITE OUTPUT
# ═══════════════════════════════════════════════════════════════

output = '\n'.join(lines)
output = clean_floats(output)

output_path = '/home/user/workspace/Sheet3_Power.kicad_sch'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(output)

print(f"\nGenerated: {output_path}")
print(f"File size: {len(output)} bytes")
