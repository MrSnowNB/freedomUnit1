#!/usr/bin/env python3
"""
Generate Sheet2_LoRa.kicad_sch for Freedom Unit V2
Fully wired, correct pin assignments per v2.2 spec.

Components:
  - U3: Lambda62C-9S LoRa module (custom symbol, 11 pins)
  - J2: CONSMA006.062 SMA edge-mount connector (custom symbol, 2 pins)
  - C10: 100nF decoupling cap on Lambda62 VCC
  - C11: 10uF bulk cap on Lambda62 VCC

Nets (global labels connecting to Sheet 1 MCU):
  - SPI_SCK (P0.19 -> Lambda62 pin 18)
  - SPI_MOSI (P0.22 -> Lambda62 pin 17)
  - SPI_MISO (P0.23 -> Lambda62 pin 16)
  - LORA_CS (P0.24 -> Lambda62 pin 19 / NSS)
  - LORA_DIO1 (P0.20 -> Lambda62 pin 13)
  - LORA_BUSY (P0.17 -> Lambda62 pin 14)
  - LORA_RESET (P0.25 -> Lambda62 pin 15 / NRESET)
  - LORA_RXEN (P1.06 -> Lambda62 pin 4)
  - LORA_TXEN (P1.07 -> Lambda62 pin 5)

Power:
  - +3V3_SW (switched 3.3V from TPS22918) -> Lambda62 VCC (pin 1)
  - GND -> Lambda62 GND (pin 2)
  - Antenna: Lambda62 u.FL (internal) -> SMA connector J2
"""

import uuid
import textwrap

def uid():
    return str(uuid.uuid4())

# ── Coordinates (in mils, KiCad uses mm internally but we'll use mm) ──
# All coordinates in mm. KiCad schematic grid is 1.27mm (50 mils).
# We'll place things on a clean grid.

# Lambda62C-9S symbol center
MOD_X, MOD_Y = 127.0, 88.9  # roughly center of A4 sheet

# Lambda62 pin positions (relative to module center, from our custom symbol def)
# Left side pins (pointing left, entry from left at x - 15.24):
#   VCC  (pin 1):  (-15.24, 10.16)  -> absolute endpoint: (MOD_X - 15.24, MOD_Y - 10.16)
#   GND  (pin 2):  (-15.24, -12.7)
#   SCK  (pin 18): (-15.24, 5.08)
#   MOSI (pin 17): (-15.24, 2.54)
#   MISO (pin 16): (-15.24, 0)
#   NSS  (pin 19): (-15.24, -2.54)
# Right side pins (pointing right, entry from right at x + 15.24):
#   RXEN    (pin 4):  (15.24, 10.16)
#   TXEN    (pin 5):  (15.24, 7.62)
#   BUSY    (pin 14): (15.24, 2.54)
#   DIO1    (pin 13): (15.24, 0)
#   NRESET  (pin 15): (15.24, -5.08)
# Top pin:
#   ANT     (pin 3):  (0, 15.24) pointing up

# Pin endpoint positions (absolute) — where wires must connect
def mod_pin(rel_x, rel_y):
    return (round(MOD_X + rel_x, 2), round(MOD_Y + rel_y, 2))

# Left side pin endpoints (tip of pin, where wire connects)
PIN_VCC    = mod_pin(-15.24, -10.16)   # We'll redesign: put VCC at top-left
PIN_GND    = mod_pin(-15.24, 12.7)
PIN_SCK    = mod_pin(-15.24, -5.08)
PIN_MOSI   = mod_pin(-15.24, -2.54)
PIN_MISO   = mod_pin(-15.24, 0)
PIN_NSS    = mod_pin(-15.24, 2.54)

# Right side pin endpoints
PIN_RXEN   = mod_pin(15.24, -10.16)
PIN_TXEN   = mod_pin(15.24, -7.62)
PIN_BUSY   = mod_pin(15.24, -2.54)
PIN_DIO1   = mod_pin(15.24, 0)
PIN_NRESET = mod_pin(15.24, 5.08)

# Top pin endpoint
PIN_ANT    = mod_pin(0, -15.24)

# ── Let me reconsider the symbol layout more carefully ──
# The Lambda62 custom symbol should have a clean, logical pin arrangement.
# I'll define the symbol fresh here with careful coordinates.

# Symbol body: rectangle from (-12.7, -13.97) to (12.7, 13.97) centered at origin
# This gives us a nice box roughly 25.4 x 27.94 mm

# Pin layout (all positions relative to symbol origin):
#   LEFT SIDE (pins enter from left, angle=0, length=5.08):
#     VCC     pin 1   at (-17.78,  11.43)   power_in
#     SCK     pin 18  at (-17.78,   6.35)   input
#     MOSI    pin 17  at (-17.78,   1.27)   input  
#     MISO    pin 16  at (-17.78,  -3.81)   output
#     NSS     pin 19  at (-17.78,  -8.89)   input
#     GND     pin 2   at (-17.78, -13.97)   power_in (actually at bottom but left is fine)
#
#   RIGHT SIDE (pins enter from right, angle=180, length=5.08):
#     RXEN    pin 4   at (17.78,   8.89)    input
#     TXEN    pin 5   at (17.78,   3.81)    input
#     BUSY    pin 14  at (17.78,  -1.27)    output
#     DIO1    pin 13  at (17.78,  -6.35)    output
#     NRESET  pin 15  at (17.78, -11.43)    input
#
#   TOP (pin enters from top, angle=270, length=5.08):
#     ANT     pin 3   at (0, -19.05)        passive (antenna connection)

# Absolute pin TIP positions (where wires attach):
# For left-side pins (angle=0), tip is at (symbol_x + pin_x, symbol_y + pin_y)
# where pin_x already includes the -17.78 offset
# For right-side pins (angle=180), tip is at (symbol_x + pin_x, ...)
# For top pin (angle=270), tip is at (..., symbol_y + pin_y)

# Let's use cleaner grid-aligned positions
# Module placed at (127, 88.9)

# Actually, let me just carefully build everything with exact coordinates.
# I'll define component positions, then compute wire paths.

# ═══════════════════════════════════════════════════════════════
# SYMBOL DEFINITIONS (to embed in lib_symbols)
# ═══════════════════════════════════════════════════════════════

LAMBDA62_SYMBOL = '''    (symbol "FreedomUnit:Lambda62C-9S" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 16.51 0) (effects (font (size 1.27 1.27))))
      (property "Value" "Lambda62C-9S" (at 0 -16.51 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "https://www.rfsolutions.co.uk/content/download-files/LAMBDA-62-6-DATASHEET.pdf" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "Lambda62C-9S_0_1"
        (rectangle (start -12.7 15.24) (end 12.7 -15.24) (stroke (width 0.254) (type default)) (fill (type background)))
        (text "Lambda62C-9S" (at 0 0 0) (effects (font (size 1.27 1.27))))
        (text "LoRa SX1262" (at 0 -2.54 0) (effects (font (size 1.0 1.0))))
      )
      (symbol "Lambda62C-9S_1_1"
        (pin power_in line (at -17.78 11.43 0) (length 5.08) (name "VCC" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at -17.78 -11.43 0) (length 5.08) (name "GND" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 0 20.32 270) (length 5.08) (name "ANT" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
        (pin input line (at 17.78 11.43 180) (length 5.08) (name "RXEN" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
        (pin input line (at 17.78 8.89 180) (length 5.08) (name "TXEN" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27)))))
        (pin output line (at 17.78 1.27 180) (length 5.08) (name "DIO1" (effects (font (size 1.27 1.27)))) (number "13" (effects (font (size 1.27 1.27)))))
        (pin output line (at 17.78 -1.27 180) (length 5.08) (name "BUSY" (effects (font (size 1.27 1.27)))) (number "14" (effects (font (size 1.27 1.27)))))
        (pin input line (at 17.78 -6.35 180) (length 5.08) (name "NRESET" (effects (font (size 1.27 1.27)))) (number "15" (effects (font (size 1.27 1.27)))))
        (pin output line (at -17.78 -3.81 0) (length 5.08) (name "MISO" (effects (font (size 1.27 1.27)))) (number "16" (effects (font (size 1.27 1.27)))))
        (pin input line (at -17.78 -1.27 0) (length 5.08) (name "MOSI" (effects (font (size 1.27 1.27)))) (number "17" (effects (font (size 1.27 1.27)))))
        (pin input line (at -17.78 1.27 0) (length 5.08) (name "SCK" (effects (font (size 1.27 1.27)))) (number "18" (effects (font (size 1.27 1.27)))))
        (pin input line (at -17.78 3.81 0) (length 5.08) (name "NSS" (effects (font (size 1.27 1.27)))) (number "19" (effects (font (size 1.27 1.27)))))
      )
    )'''

# SMA connector: 2 pins — SIG and GND
CONSMA_SYMBOL = '''    (symbol "FreedomUnit:CONSMA006.062" (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 5.08 0) (effects (font (size 1.27 1.27))))
      (property "Value" "CONSMA006.062" (at 0 -5.08 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "https://www.te.com/en/product-L9000271-01.html" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "CONSMA006.062_0_1"
        (rectangle (start -2.54 3.81) (end 2.54 -3.81) (stroke (width 0.254) (type default)) (fill (type background)))
        (text "SMA" (at 0 0 0) (effects (font (size 1.27 1.27))))
      )
      (symbol "CONSMA006.062_1_1"
        (pin passive line (at 0 8.89 270) (length 5.08) (name "SIG" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 0 -8.89 90) (length 5.08) (name "GND" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )'''

# Standard capacitor from Device library
CAP_SYMBOL = '''    (symbol "Device:C" (pin_numbers hide) (pin_names (offset 0.254) hide) (in_bom yes) (on_board yes)
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

# Power symbols
PWR_3V3_SYMBOL = '''    (symbol "power:+3V3" (power) (pin_names (offset 0)) (in_bom yes) (on_board yes)
      (property "Reference" "#PWR" (at 0 -3.81 0) (effects (font (size 1.27 1.27)) hide))
      (property "Value" "+3V3" (at 0 3.556 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (+3V3_0_1
        (polyline (pts (xy -0.762 1.27) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 0) (xy 0 1.27)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 2.54) (xy 0.762 1.27)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (+3V3_1_1
        (pin power_in line (at 0 0 90) (length 0) (name "+3V3" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
      )
    )'''

GND_SYMBOL = '''    (symbol "power:GND" (power) (pin_names (offset 0)) (in_bom yes) (on_board yes)
      (property "Reference" "#PWR" (at 0 -6.35 0) (effects (font (size 1.27 1.27)) hide))
      (property "Value" "GND" (at 0 -3.81 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (GND_0_1
        (polyline (pts (xy 0 0) (xy 0 -1.27) (xy 1.27 -1.27) (xy 0 -2.54) (xy -1.27 -1.27) (xy 0 -1.27)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (GND_1_1
        (pin power_in line (at 0 0 270) (length 0) (name "GND" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
      )
    )'''

# Hmm, the power symbols have sub-symbols that need the "symbol" keyword.
# Let me fix the power symbol format:

PWR_3V3_SYMBOL = '''    (symbol "power:+3V3" (power) (pin_names (offset 0)) (in_bom yes) (on_board yes)
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

GND_SYMBOL = '''    (symbol "power:GND" (power) (pin_names (offset 0)) (in_bom yes) (on_board yes)
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

PWR_FLAG_SYMBOL = '''    (symbol "power:PWR_FLAG" (power) (pin_names (offset 0)) (in_bom yes) (on_board yes)
      (property "Reference" "#FLG" (at 0 1.905 0) (effects (font (size 1.27 1.27)) hide))
      (property "Value" "PWR_FLAG" (at 0 3.81 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "PWR_FLAG_0_1"
        (pin power_out line (at 0 0 90) (length 0) (name "pwr" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
      )
    )'''


# ═══════════════════════════════════════════════════════════════
# LAYOUT PLAN
# ═══════════════════════════════════════════════════════════════
#
# A4 sheet: 297 x 210 mm. KiCad puts (0,0) at top-left.
# We'll use a clean layout:
#
#   Global labels (SPI bus)    Lambda62C-9S (U3)     Global labels (control)
#   on left side          ──── center of sheet ────  on right side
#                                    |
#                               ANT (top)
#                                    |
#                              SMA connector (J2)
#
#   +3V3_SW power rail at top, GND at bottom
#   Decoupling caps (C10, C11) near VCC pin
#

# Component positions (center of each symbol, in mm)
U3_X, U3_Y = 148.59, 100.33     # Lambda62 module, center of sheet
J2_X, J2_Y = 148.59, 55.88      # SMA connector, above module (antenna path goes up)

# Decoupling caps near VCC pin (left side of module, above)
C10_X, C10_Y = 120.65, 82.55    # 100nF near VCC
C11_X, C11_Y = 113.03, 82.55    # 10uF bulk, next to C10

# Power symbols
PWR_VCC_X, PWR_VCC_Y = 120.65, 74.93     # +3V3 above caps
PWR_GND_MOD_X, PWR_GND_MOD_Y = 130.81, 118.11  # GND below module GND pin
PWR_GND_J2_X, PWR_GND_J2_Y = 148.59, 69.85     # GND below SMA connector
PWR_GND_C_X, PWR_GND_C_Y = 116.84, 90.17       # GND below caps

# Global label positions (left side - SPI signals)
LABEL_SCK_X, LABEL_SCK_Y = 111.76, 101.6
LABEL_MOSI_X, LABEL_MOSI_Y = 111.76, 99.06
LABEL_MISO_X, LABEL_MISO_Y = 111.76, 96.52   # Note: MISO is output from module
LABEL_NSS_X, LABEL_NSS_Y = 111.76, 104.14

# Global label positions (right side - control signals)  
LABEL_RXEN_X, LABEL_RXEN_Y = 185.42, 88.9
LABEL_TXEN_X, LABEL_TXEN_Y = 185.42, 91.44
LABEL_DIO1_X, LABEL_DIO1_Y = 185.42, 101.6
LABEL_BUSY_X, LABEL_BUSY_Y = 185.42, 99.06
LABEL_NRESET_X, LABEL_NRESET_Y = 185.42, 106.68

# ═══════════════════════════════════════════════════════════════
# Now I need to compute actual pin TIP coordinates.
# For a symbol placed at (sx, sy):
#   Left pin at relative (-17.78, ry) with angle=0, length=5.08:
#     Pin TIP at (sx - 17.78, sy + ry)  [KiCad Y increases downward in schematic]
#     Wait — KiCad schematic Y axis: POSITIVE Y is DOWN in the file,
#     but in the GUI, Y increases upward. The .kicad_sch format uses
#     screen coordinates where Y increases downward.
#     
#     Actually in KiCad S-expression schematics:
#     - (at X Y) uses a coordinate system where Y increases downward
#     - Pin positions in the symbol are relative to symbol center
#     - When symbol is at (sx, sy), a pin defined at (px, py) with angle A
#       has its BASE at (sx+px, sy+py) and its TIP at:
#         angle 0 (pointing right): tip at (sx+px-length, sy+py) -- NO
#         
# Let me think about this more carefully.
# In KiCad symbol definition:
#   (pin ... (at px py angle) (length L) ...)
#   - The pin BODY starts at (px, py) relative to symbol origin
#   - angle 0: pin extends to the LEFT (toward the wire), body is at right
#     Actually: angle 0 means pin points RIGHT. The pin graphic goes from
#     (px-L, py) to (px, py), with the connection point at (px-L, py).
#     Wait no... Let me check KiCad convention:
#
# KiCad pin convention:
#   angle 0:   pin points RIGHT  → connection at (px + length, py) relative to symbol? No...
#   
# Actually the standard is:
#   The (at px py angle) gives the ELECTRICAL connection point of the pin.
#   The pin body extends INWARD from that point by 'length' in the direction
#   opposite to 'angle'.
#   
#   angle 0:   connection point is at (px, py), body goes LEFT (toward symbol center)
#   angle 180: connection point is at (px, py), body goes RIGHT (toward symbol center)
#   angle 90:  connection point is at (px, py), body goes DOWN
#   angle 270: connection point is at (px, py), body goes UP
#
# So for our Lambda62 symbol:
#   VCC pin at (-17.78, 11.43, angle=0): connection point at (-17.78, 11.43)
#   Body extends from (-17.78, 11.43) rightward to (-17.78+5.08, 11.43) = (-12.7, 11.43)
#   This makes sense — pin sticks out to the left of the rectangle.
#
# When symbol U3 is placed at (U3_X, U3_Y):
#   VCC connection point absolute = (U3_X + (-17.78), U3_Y + 11.43)
#   Wait — but KiCad Y in schematic is inverted from symbol Y?
#   
# Actually no. In .kicad_sch files, the symbol's (at X Y angle) places it,
# and pin positions are transformed by the symbol's placement.
# If symbol is at (sx, sy) with angle 0 (no rotation):
#   pin at relative (px, py) → absolute (sx + px, sy - py)
#   because KiCad schematic Y increases downward but symbol Y increases upward.
#
# Wait, I need to verify. Let me just use a simpler approach and make sure
# everything lines up by using consistent coordinates.

# ACTUALLY - in KiCad .kicad_sch format:
# - Schematic coordinate: Y increases DOWNWARD (screen coordinates)
# - Symbol definition: Y increases UPWARD (mathematical coordinates)
# - When a symbol at (sx, sy) angle=0 has a pin at relative (px, py):
#   The absolute position is (sx + px, sy - py)

# So for U3 at (148.59, 100.33):
#   VCC pin at symbol-relative (-17.78, 11.43):
#   Absolute = (148.59 + (-17.78), 100.33 - 11.43) = (130.81, 88.9)

def sym_to_abs(sx, sy, px, py):
    """Convert symbol-relative pin coords to absolute schematic coords."""
    return (round(sx + px, 2), round(sy - py, 2))

# Lambda62 pin absolute positions
P_VCC    = sym_to_abs(U3_X, U3_Y, -17.78,  11.43)  # (130.81, 88.9)
P_GND    = sym_to_abs(U3_X, U3_Y, -17.78, -11.43)  # (130.81, 111.76)
P_ANT    = sym_to_abs(U3_X, U3_Y,   0,     20.32)   # (148.59, 80.01)
P_RXEN   = sym_to_abs(U3_X, U3_Y,  17.78,  11.43)  # (166.37, 88.9)
P_TXEN   = sym_to_abs(U3_X, U3_Y,  17.78,   8.89)  # (166.37, 91.44)
P_DIO1   = sym_to_abs(U3_X, U3_Y,  17.78,   1.27)  # (166.37, 99.06)
P_BUSY   = sym_to_abs(U3_X, U3_Y,  17.78,  -1.27)  # (166.37, 101.6)
P_NRESET = sym_to_abs(U3_X, U3_Y,  17.78,  -6.35)  # (166.37, 106.68)
P_MISO   = sym_to_abs(U3_X, U3_Y, -17.78,  -3.81)  # (130.81, 104.14)
P_MOSI   = sym_to_abs(U3_X, U3_Y, -17.78,  -1.27)  # (130.81, 101.6)
P_SCK    = sym_to_abs(U3_X, U3_Y, -17.78,   1.27)  # (130.81, 99.06)
P_NSS    = sym_to_abs(U3_X, U3_Y, -17.78,   3.81)  # (130.81, 96.52)

# SMA connector pin absolute positions  
P_SMA_SIG = sym_to_abs(J2_X, J2_Y, 0, 8.89)         # (148.59, 46.99)
P_SMA_GND = sym_to_abs(J2_X, J2_Y, 0, -8.89)        # (148.59, 64.77)

# Cap pin positions
# C10 at (120.65, 82.55): pin 1 (top) at (120.65, 82.55-3.81)=(120.65, 78.74)
#                          pin 2 (bot) at (120.65, 82.55+3.81)=(120.65, 86.36)
P_C10_1 = (C10_X, round(C10_Y - 3.81, 2))  # top pin
P_C10_2 = (C10_X, round(C10_Y + 3.81, 2))  # bottom pin

P_C11_1 = (C11_X, round(C11_Y - 3.81, 2))
P_C11_2 = (C11_X, round(C11_Y + 3.81, 2))

print("=== Pin positions (absolute) ===")
print(f"U3 VCC:    {P_VCC}")
print(f"U3 GND:    {P_GND}")
print(f"U3 ANT:    {P_ANT}")
print(f"U3 SCK:    {P_SCK}")
print(f"U3 MOSI:   {P_MOSI}")
print(f"U3 MISO:   {P_MISO}")
print(f"U3 NSS:    {P_NSS}")
print(f"U3 RXEN:   {P_RXEN}")
print(f"U3 TXEN:   {P_TXEN}")
print(f"U3 DIO1:   {P_DIO1}")
print(f"U3 BUSY:   {P_BUSY}")
print(f"U3 NRESET: {P_NRESET}")
print(f"J2 SIG:    {P_SMA_SIG}")
print(f"J2 GND:    {P_SMA_GND}")
print(f"C10 pin1:  {P_C10_1}")
print(f"C10 pin2:  {P_C10_2}")
print(f"C11 pin1:  {P_C11_1}")
print(f"C11 pin2:  {P_C11_2}")

# ═══════════════════════════════════════════════════════════════
# Now update label positions to match pin positions exactly
# Labels must be AT the pin endpoint or connected via wire
# ═══════════════════════════════════════════════════════════════

# Left side labels - place them to the left of pin tips, with wires connecting
LABEL_GAP = 10.16  # mm gap from pin tip to label

# For global labels on the left (SPI signals):
# Pin tips are at x = 130.81
# Labels at x = 130.81 - LABEL_GAP = 120.65
# Wire from (120.65, y) to (130.81, y)

LABEL_SCK  = (P_SCK[0] - LABEL_GAP, P_SCK[1])
LABEL_MOSI = (P_MOSI[0] - LABEL_GAP, P_MOSI[1])
LABEL_MISO = (P_MISO[0] - LABEL_GAP, P_MISO[1])
LABEL_NSS  = (P_NSS[0] - LABEL_GAP, P_NSS[1])

# Right side labels - place them to the right of pin tips
LABEL_RXEN   = (P_RXEN[0] + LABEL_GAP, P_RXEN[1])
LABEL_TXEN   = (P_TXEN[0] + LABEL_GAP, P_TXEN[1])
LABEL_DIO1   = (P_DIO1[0] + LABEL_GAP, P_DIO1[1])
LABEL_BUSY   = (P_BUSY[0] + LABEL_GAP, P_BUSY[1])
LABEL_NRESET = (P_NRESET[0] + LABEL_GAP, P_NRESET[1])

# ═══════════════════════════════════════════════════════════════
# BUILD THE SCHEMATIC
# ═══════════════════════════════════════════════════════════════

def wire(x1, y1, x2, y2):
    return f'  (wire (pts (xy {x1} {y1}) (xy {x2} {y2})) (stroke (width 0) (type default)) (uuid "{uid()}"))'

def global_label(name, x, y, shape="input", angle=180):
    """angle: 0=pointing right, 180=pointing left"""
    return f'  (global_label "{name}" (shape {shape}) (at {x} {y} {angle}) (effects (font (size 1.27 1.27))) (uuid "{uid()}")  (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide)))'

def power_symbol(lib_id, ref, value, x, y, angle=0, unit=1):
    return f'''  (symbol (lib_id "{lib_id}") (at {x} {y} {angle}) (unit {unit})
    (in_bom yes) (on_board yes) (dnp no) (fields_autoplaced yes)
    (uuid "{uid()}")
    (property "Reference" "{ref}" (at {x} {y + 2.54 if angle == 0 else y} 0) (effects (font (size 1.27 1.27)) hide))
    (property "Value" "{value}" (at {x} {y - 2.54 if angle == 0 else y} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))
    (instances (project "FreedomUnit_V2" (path "/{{root_uuid}}/{{sheet_uuid}}" (reference "{ref}") (unit 1))))
  )'''

def component(lib_id, ref, value, x, y, angle=0, unit=1, footprint="", extra_props=""):
    fp_line = f'    (property "Footprint" "{footprint}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))' if footprint else f'    (property "Footprint" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))'
    return f'''  (symbol (lib_id "{lib_id}") (at {x} {y} {angle}) (unit {unit})
    (in_bom yes) (on_board yes) (dnp no) (fields_autoplaced yes)
    (uuid "{uid()}")
    (property "Reference" "{ref}" (at {x + 2.54} {y - 2.54} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "{value}" (at {x + 2.54} {y + 2.54} 0) (effects (font (size 1.27 1.27))))
{fp_line}
    (property "Datasheet" "~" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))
{extra_props}    (instances (project "FreedomUnit_V2" (path "/{{root_uuid}}/{{sheet_uuid}}" (reference "{ref}") (unit 1))))
  )'''

# UUIDs for the sheet
root_uuid = "00000000-0000-0000-0000-000000000001"
sheet_uuid = "00000000-0000-0000-0000-000000000005"  # Sheet 2 LoRa = page 5 in hierarchy

# Build the schematic content
lines = []

# Header
lines.append(f'(kicad_sch')
lines.append(f'  (version 20231120)')
lines.append(f'  (generator "FreedomUnit_Generator")')
lines.append(f'  (generator_version "2.2")')
lines.append(f'  (uuid "{uid()}")')
lines.append(f'  (paper "A4")')
lines.append(f'  (title_block')
lines.append(f'    (title "Sheet 2 — LoRa Radio (Lambda62C-9S)")')
lines.append(f'    (date "2026-03-03")')
lines.append(f'    (rev "V2.2")')
lines.append(f'    (company "GarageAGI LLC")')
lines.append(f'  )')

# lib_symbols block
lines.append(f'  (lib_symbols')
lines.append(LAMBDA62_SYMBOL)
lines.append(CONSMA_SYMBOL)
lines.append(CAP_SYMBOL)
lines.append(PWR_3V3_SYMBOL)
lines.append(GND_SYMBOL)
lines.append(PWR_FLAG_SYMBOL)
lines.append(f'  )')

# ── Components ──

# U3: Lambda62C-9S
lines.append(component("FreedomUnit:Lambda62C-9S", "U3", "Lambda62C-9S", U3_X, U3_Y))

# J2: SMA connector
lines.append(component("FreedomUnit:CONSMA006.062", "J2", "CONSMA006.062", J2_X, J2_Y))

# C10: 100nF decoupling
lines.append(component("Device:C", "C10", "100nF", C10_X, C10_Y))

# C11: 10uF bulk  
lines.append(component("Device:C", "C11", "10uF", C11_X, C11_Y))

# Power symbols
# +3V3 above decoupling caps
lines.append(power_symbol("power:+3V3", "#PWR010", "+3V3", P_C10_1[0], P_C10_1[1] - 2.54))

# GND symbols
lines.append(power_symbol("power:GND", "#PWR011", "GND", P_GND[0], P_GND[1] + 2.54, angle=0))
lines.append(power_symbol("power:GND", "#PWR012", "GND", P_SMA_GND[0], P_SMA_GND[1] + 2.54, angle=0))
lines.append(power_symbol("power:GND", "#PWR013", "GND", 
    round((P_C10_2[0] + P_C11_2[0]) / 2, 2), P_C10_2[1] + 2.54, angle=0))

# ── Global Labels ──
# Left side (SPI) - pointing left (angle=180), so wire goes right to pin
lines.append(global_label("SPI_SCK", LABEL_SCK[0], LABEL_SCK[1], "input", 0))
lines.append(global_label("SPI_MOSI", LABEL_MOSI[0], LABEL_MOSI[1], "input", 0))
lines.append(global_label("SPI_MISO", LABEL_MISO[0], LABEL_MISO[1], "output", 0))
lines.append(global_label("LORA_CS", LABEL_NSS[0], LABEL_NSS[1], "input", 0))

# Right side (control) - pointing right (angle=0)
lines.append(global_label("LORA_RXEN", LABEL_RXEN[0], LABEL_RXEN[1], "output", 180))
lines.append(global_label("LORA_TXEN", LABEL_TXEN[0], LABEL_TXEN[1], "output", 180))
lines.append(global_label("LORA_DIO1", LABEL_DIO1[0], LABEL_DIO1[1], "input", 180))
lines.append(global_label("LORA_BUSY", LABEL_BUSY[0], LABEL_BUSY[1], "input", 180))
lines.append(global_label("LORA_RESET", LABEL_NRESET[0], LABEL_NRESET[1], "output", 180))

# ── Wires ──

# SPI signals: label -> pin tip
lines.append(wire(LABEL_SCK[0], LABEL_SCK[1], P_SCK[0], P_SCK[1]))
lines.append(wire(LABEL_MOSI[0], LABEL_MOSI[1], P_MOSI[0], P_MOSI[1]))
lines.append(wire(LABEL_MISO[0], LABEL_MISO[1], P_MISO[0], P_MISO[1]))
lines.append(wire(LABEL_NSS[0], LABEL_NSS[1], P_NSS[0], P_NSS[1]))

# Control signals: pin tip -> label
lines.append(wire(P_RXEN[0], P_RXEN[1], LABEL_RXEN[0], LABEL_RXEN[1]))
lines.append(wire(P_TXEN[0], P_TXEN[1], LABEL_TXEN[0], LABEL_TXEN[1]))
lines.append(wire(P_DIO1[0], P_DIO1[1], LABEL_DIO1[0], LABEL_DIO1[1]))
lines.append(wire(P_BUSY[0], P_BUSY[1], LABEL_BUSY[0], LABEL_BUSY[1]))
lines.append(wire(P_NRESET[0], P_NRESET[1], LABEL_NRESET[0], LABEL_NRESET[1]))

# Power: VCC pin -> wire to decoupling cap top -> wire to +3V3 symbol
# VCC pin is at P_VCC = (130.81, 88.9)
# C10 top pin at P_C10_1 = (120.65, 78.74)
# Need to route: VCC pin -> horizontal to C10 x -> vertical to C10 pin1
lines.append(wire(P_VCC[0], P_VCC[1], P_C10_1[0], P_VCC[1]))  # horizontal
lines.append(wire(P_C10_1[0], P_VCC[1], P_C10_1[0], P_C10_1[1]))  # vertical to cap

# C10 top to +3V3 symbol
lines.append(wire(P_C10_1[0], P_C10_1[1], P_C10_1[0], P_C10_1[1] - 2.54))

# C11 top to C10 top (shared power rail)
lines.append(wire(P_C11_1[0], P_C11_1[1], P_C10_1[0], P_C10_1[1]))

# C10 bottom to GND
lines.append(wire(P_C10_2[0], P_C10_2[1], P_C10_2[0], P_C10_2[1] + 2.54))

# C11 bottom to same GND node
lines.append(wire(P_C11_2[0], P_C11_2[1], P_C10_2[0], P_C10_2[1] + 2.54))

# GND pin on Lambda62 to GND symbol
lines.append(wire(P_GND[0], P_GND[1], P_GND[0], P_GND[1] + 2.54))

# Antenna: Lambda62 ANT pin -> wire to SMA SIG pin
# ANT pin at P_ANT = (148.59, 80.01)
# SMA SIG at P_SMA_SIG = (148.59, 46.99)
# Same X, so just a vertical wire
lines.append(wire(P_ANT[0], P_ANT[1], P_SMA_SIG[0], P_SMA_SIG[1]))

# SMA GND to GND symbol
lines.append(wire(P_SMA_GND[0], P_SMA_GND[1], P_SMA_GND[0], P_SMA_GND[1] + 2.54))

# Close the file
lines.append(f')')

# ═══════════════════════════════════════════════════════════════
# POST-PROCESS: Replace template UUIDs
# ═══════════════════════════════════════════════════════════════

output = '\n'.join(lines)
output = output.replace('{root_uuid}', root_uuid)
output = output.replace('{sheet_uuid}', sheet_uuid)

# Write the file
output_path = '/home/user/workspace/Sheet2_LoRa.kicad_sch'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(output)

print(f"\nGenerated: {output_path}")
print(f"File size: {len(output)} bytes")
