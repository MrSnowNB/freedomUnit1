#!/usr/bin/env python3
"""
Generate Sheet1_MCU.kicad_sch for Freedom Unit V2

Components:
  - U1: nRF52840-QIAA (custom symbol, key pins only — simplified)
  - Y1: ABM8-32.000MHZ-B2-T (32MHz crystal)
  - Y2: ABS07-120-32.768KHZ-T (32.768kHz LFXO crystal)
  - ANT1: Johanson 2450AT18D0100 (BLE chip antenna)
  - L1: 3.9nH matching inductor
  - C19: 0.8pF matching cap
  - C20: 0.5pF matching cap
  - C21, C22: 12pF load caps for 32MHz crystal
  - C23, C24: 6pF load caps for 32.768kHz crystal
  - C25-C30: 100nF VDD decoupling caps (x6)
  - C31: 1uF VDD bulk cap
  - C32: 100nF DEC1 cap
  - C33: 1uF DEC4 cap
  - C34: 100nF DEC6 cap
  - C35: 4.7uF DECUSB cap
  - C36: 100nF DECUSB cap
"""

import uuid
import re

def uid():
    return str(uuid.uuid4())

ROOT_UUID = "00000000-0000-0000-0000-000000000001"
SHEET_UUID = "00000000-0000-0000-0000-000000000002"

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

# nRF52840 — Simplified symbol with grouped pins
# Left side: SPI0 (LoRa), SPI1 (LCD), I2C, Control signals
# Right side: Buttons, LEDs, QSPI, USB
# Top: VDD, DEC pins
# Bottom: GND, clocks
SYM_NRF52840 = '''    (symbol "FreedomUnit:nRF52840" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 62.23 0) (effects (font (size 1.27 1.27))))
      (property "Value" "nRF52840-QIAA" (at 0 -62.23 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "nRF52840_0_1"
        (rectangle (start -25.4 60.96) (end 25.4 -60.96) (stroke (width 0.254) (type default)) (fill (type background)))
        (text "nRF52840" (at 0 2.54 0) (effects (font (size 2.54 2.54))))
        (text "QFN73" (at 0 -2.54 0) (effects (font (size 1.27 1.27))))
      )
      (symbol "nRF52840_1_1"
        (pin power_in line (at -5.08 66.04 270) (length 5.08) (name "VDD" (effects (font (size 1.0 1.0)))) (number "13" (effects (font (size 1.0 1.0)))))
        (pin passive line (at 0 66.04 270) (length 5.08) (name "DEC1" (effects (font (size 1.0 1.0)))) (number "30" (effects (font (size 1.0 1.0)))))
        (pin passive line (at 5.08 66.04 270) (length 5.08) (name "DEC4" (effects (font (size 1.0 1.0)))) (number "37" (effects (font (size 1.0 1.0)))))
        (pin passive line (at 10.16 66.04 270) (length 5.08) (name "DEC6" (effects (font (size 1.0 1.0)))) (number "46" (effects (font (size 1.0 1.0)))))
        (pin passive line (at 15.24 66.04 270) (length 5.08) (name "VDDH" (effects (font (size 1.0 1.0)))) (number "48" (effects (font (size 1.0 1.0)))))
        (pin passive line (at 20.32 66.04 270) (length 5.08) (name "DECUSB" (effects (font (size 1.0 1.0)))) (number "7" (effects (font (size 1.0 1.0)))))
        (pin power_in line (at 0 -66.04 90) (length 5.08) (name "VSS" (effects (font (size 1.0 1.0)))) (number "GND" (effects (font (size 1.0 1.0)))))
        (pin passive line (at -10.16 -66.04 90) (length 5.08) (name "XC1" (effects (font (size 1.0 1.0)))) (number "34" (effects (font (size 1.0 1.0)))))
        (pin passive line (at -5.08 -66.04 90) (length 5.08) (name "XC2" (effects (font (size 1.0 1.0)))) (number "35" (effects (font (size 1.0 1.0)))))
        (pin passive line (at 5.08 -66.04 90) (length 5.08) (name "XL1" (effects (font (size 1.0 1.0)))) (number "3" (effects (font (size 1.0 1.0)))))
        (pin passive line (at 10.16 -66.04 90) (length 5.08) (name "XL2" (effects (font (size 1.0 1.0)))) (number "4" (effects (font (size 1.0 1.0)))))
        (pin passive line (at -20.32 -66.04 90) (length 5.08) (name "ANT" (effects (font (size 1.0 1.0)))) (number "H1" (effects (font (size 1.0 1.0)))))
        (pin output line (at -30.48 55.88 0) (length 5.08) (name "P0.19/SCK" (effects (font (size 1.0 1.0)))) (number "P0.19" (effects (font (size 1.0 1.0)))))
        (pin output line (at -30.48 53.34 0) (length 5.08) (name "P0.22/MOSI" (effects (font (size 1.0 1.0)))) (number "P0.22" (effects (font (size 1.0 1.0)))))
        (pin input line (at -30.48 50.8 0) (length 5.08) (name "P0.23/MISO" (effects (font (size 1.0 1.0)))) (number "P0.23" (effects (font (size 1.0 1.0)))))
        (pin output line (at -30.48 48.26 0) (length 5.08) (name "P0.24/LORA_CS" (effects (font (size 1.0 1.0)))) (number "P0.24" (effects (font (size 1.0 1.0)))))
        (pin input line (at -30.48 43.18 0) (length 5.08) (name "P0.20/DIO1" (effects (font (size 1.0 1.0)))) (number "P0.20" (effects (font (size 1.0 1.0)))))
        (pin input line (at -30.48 40.64 0) (length 5.08) (name "P0.17/BUSY" (effects (font (size 1.0 1.0)))) (number "P0.17" (effects (font (size 1.0 1.0)))))
        (pin output line (at -30.48 38.1 0) (length 5.08) (name "P0.25/RESET" (effects (font (size 1.0 1.0)))) (number "P0.25" (effects (font (size 1.0 1.0)))))
        (pin output line (at -30.48 33.02 0) (length 5.08) (name "P1.06/RXEN" (effects (font (size 1.0 1.0)))) (number "P1.06" (effects (font (size 1.0 1.0)))))
        (pin output line (at -30.48 30.48 0) (length 5.08) (name "P1.07/TXEN" (effects (font (size 1.0 1.0)))) (number "P1.07" (effects (font (size 1.0 1.0)))))
        (pin output line (at -30.48 25.4 0) (length 5.08) (name "P0.31/LCD_SCK" (effects (font (size 1.0 1.0)))) (number "P0.31" (effects (font (size 1.0 1.0)))))
        (pin output line (at -30.48 22.86 0) (length 5.08) (name "P0.29/LCD_MOSI" (effects (font (size 1.0 1.0)))) (number "P0.29" (effects (font (size 1.0 1.0)))))
        (pin output line (at -30.48 20.32 0) (length 5.08) (name "P0.30/LCD_CS" (effects (font (size 1.0 1.0)))) (number "P0.30" (effects (font (size 1.0 1.0)))))
        (pin output line (at -30.48 17.78 0) (length 5.08) (name "P0.28/EXTCOMIN" (effects (font (size 1.0 1.0)))) (number "P0.28" (effects (font (size 1.0 1.0)))))
        (pin output line (at -30.48 15.24 0) (length 5.08) (name "P1.11/LCD_DISP" (effects (font (size 1.0 1.0)))) (number "P1.11" (effects (font (size 1.0 1.0)))))
        (pin bidirectional line (at -30.48 10.16 0) (length 5.08) (name "P0.26/SDA" (effects (font (size 1.0 1.0)))) (number "P0.26" (effects (font (size 1.0 1.0)))))
        (pin bidirectional line (at -30.48 7.62 0) (length 5.08) (name "P0.27/SCL" (effects (font (size 1.0 1.0)))) (number "P0.27" (effects (font (size 1.0 1.0)))))
        (pin input line (at -30.48 2.54 0) (length 5.08) (name "P1.04/PPS" (effects (font (size 1.0 1.0)))) (number "P1.04" (effects (font (size 1.0 1.0)))))
        (pin output line (at -30.48 0 0) (length 5.08) (name "P1.05/GPS_RST" (effects (font (size 1.0 1.0)))) (number "P1.05" (effects (font (size 1.0 1.0)))))
        (pin output line (at -30.48 -2.54 0) (length 5.08) (name "P1.02/GPS_EXT" (effects (font (size 1.0 1.0)))) (number "P1.02" (effects (font (size 1.0 1.0)))))
        (pin output line (at -30.48 -7.62 0) (length 5.08) (name "P0.12/PWR_EN" (effects (font (size 1.0 1.0)))) (number "P0.12" (effects (font (size 1.0 1.0)))))
        (pin input line (at -30.48 -10.16 0) (length 5.08) (name "P0.16/VBOK" (effects (font (size 1.0 1.0)))) (number "P0.16" (effects (font (size 1.0 1.0)))))
        (pin input line (at -30.48 -12.7 0) (length 5.08) (name "P0.04/AIN2" (effects (font (size 1.0 1.0)))) (number "P0.04" (effects (font (size 1.0 1.0)))))
        (pin input line (at 30.48 55.88 180) (length 5.08) (name "P1.10/BTN_UP" (effects (font (size 1.0 1.0)))) (number "P1.10" (effects (font (size 1.0 1.0)))))
        (pin input line (at 30.48 53.34 180) (length 5.08) (name "P0.18/BTN_DN" (effects (font (size 1.0 1.0)))) (number "P0.18" (effects (font (size 1.0 1.0)))))
        (pin input line (at 30.48 50.8 180) (length 5.08) (name "P0.11/BTN_LT" (effects (font (size 1.0 1.0)))) (number "P0.11" (effects (font (size 1.0 1.0)))))
        (pin input line (at 30.48 48.26 180) (length 5.08) (name "P0.06/BTN_RT" (effects (font (size 1.0 1.0)))) (number "P0.06" (effects (font (size 1.0 1.0)))))
        (pin input line (at 30.48 45.72 180) (length 5.08) (name "P0.08/BTN_CTR" (effects (font (size 1.0 1.0)))) (number "P0.08" (effects (font (size 1.0 1.0)))))
        (pin input line (at 30.48 43.18 180) (length 5.08) (name "P1.00/BTN_A" (effects (font (size 1.0 1.0)))) (number "P1.00" (effects (font (size 1.0 1.0)))))
        (pin input line (at 30.48 40.64 180) (length 5.08) (name "P1.01/BTN_B" (effects (font (size 1.0 1.0)))) (number "P1.01" (effects (font (size 1.0 1.0)))))
        (pin output line (at 30.48 35.56 180) (length 5.08) (name "P0.14/LED_R" (effects (font (size 1.0 1.0)))) (number "P0.14" (effects (font (size 1.0 1.0)))))
        (pin output line (at 30.48 33.02 180) (length 5.08) (name "P0.13/LED_G" (effects (font (size 1.0 1.0)))) (number "P0.13" (effects (font (size 1.0 1.0)))))
        (pin output line (at 30.48 30.48 180) (length 5.08) (name "P0.15/LED_B" (effects (font (size 1.0 1.0)))) (number "P0.15" (effects (font (size 1.0 1.0)))))
        (pin output line (at 30.48 25.4 180) (length 5.08) (name "P1.14/QSPI_SCK" (effects (font (size 1.0 1.0)))) (number "P1.14" (effects (font (size 1.0 1.0)))))
        (pin output line (at 30.48 22.86 180) (length 5.08) (name "P1.15/QSPI_CS" (effects (font (size 1.0 1.0)))) (number "P1.15" (effects (font (size 1.0 1.0)))))
        (pin bidirectional line (at 30.48 20.32 180) (length 5.08) (name "P1.12/QSPI_IO0" (effects (font (size 1.0 1.0)))) (number "P1.12" (effects (font (size 1.0 1.0)))))
        (pin bidirectional line (at 30.48 17.78 180) (length 5.08) (name "P1.13/QSPI_IO1" (effects (font (size 1.0 1.0)))) (number "P1.13" (effects (font (size 1.0 1.0)))))
        (pin bidirectional line (at 30.48 15.24 180) (length 5.08) (name "P0.07/QSPI_IO2" (effects (font (size 1.0 1.0)))) (number "P0.07" (effects (font (size 1.0 1.0)))))
        (pin bidirectional line (at 30.48 12.7 180) (length 5.08) (name "P0.05/QSPI_IO3" (effects (font (size 1.0 1.0)))) (number "P0.05" (effects (font (size 1.0 1.0)))))
        (pin bidirectional line (at 30.48 7.62 180) (length 5.08) (name "P1.14/USB_DP" (effects (font (size 1.0 1.0)))) (number "D+" (effects (font (size 1.0 1.0)))))
        (pin bidirectional line (at 30.48 5.08 180) (length 5.08) (name "P1.13/USB_DN" (effects (font (size 1.0 1.0)))) (number "D-" (effects (font (size 1.0 1.0)))))
        (pin output line (at 30.48 0 180) (length 5.08) (name "P1.08/UART_TX" (effects (font (size 1.0 1.0)))) (number "P1.08" (effects (font (size 1.0 1.0)))))
        (pin input line (at 30.48 -2.54 180) (length 5.08) (name "P1.09/UART_RX" (effects (font (size 1.0 1.0)))) (number "P1.09" (effects (font (size 1.0 1.0)))))
        (pin bidirectional line (at 30.48 -7.62 180) (length 5.08) (name "SWDIO" (effects (font (size 1.0 1.0)))) (number "SWDIO" (effects (font (size 1.0 1.0)))))
        (pin input line (at 30.48 -10.16 180) (length 5.08) (name "SWDCLK" (effects (font (size 1.0 1.0)))) (number "SWDCLK" (effects (font (size 1.0 1.0)))))
        (pin passive line (at 30.48 -15.24 180) (length 5.08) (name "P0.09" (effects (font (size 1.0 1.0)))) (number "P0.09" (effects (font (size 1.0 1.0)))))
        (pin passive line (at 30.48 -17.78 180) (length 5.08) (name "P0.10" (effects (font (size 1.0 1.0)))) (number "P0.10" (effects (font (size 1.0 1.0)))))
        (pin passive line (at 30.48 -20.32 180) (length 5.08) (name "P0.21" (effects (font (size 1.0 1.0)))) (number "P0.21" (effects (font (size 1.0 1.0)))))
        (pin passive line (at 30.48 -22.86 180) (length 5.08) (name "P1.03" (effects (font (size 1.0 1.0)))) (number "P1.03" (effects (font (size 1.0 1.0)))))
      )
    )'''

SYM_CRYSTAL = '''    (symbol "Device:Crystal_Small" (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
      (property "Reference" "Y" (at 0 3.81 0) (effects (font (size 1.27 1.27))))
      (property "Value" "Crystal_Small" (at 0 -3.81 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "Crystal_Small_0_1"
        (polyline (pts (xy -1.524 -0.762) (xy -1.524 0.762)) (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy 1.524 -0.762) (xy 1.524 0.762)) (stroke (width 0.254) (type default)) (fill (type none)))
        (rectangle (start -1.016 -0.762) (end 1.016 0.762) (stroke (width 0.254) (type default)) (fill (type none)))
      )
      (symbol "Crystal_Small_1_1"
        (pin passive line (at -2.54 0 0) (length 1.016) (name "1" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 2.54 0 180) (length 1.016) (name "2" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
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

SYM_L = '''    (symbol "Device:L" (pin_numbers hide) (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
      (property "Reference" "L" (at -1.016 0 90) (effects (font (size 1.27 1.27))))
      (property "Value" "L" (at 1.524 0 90) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "L_0_1"
        (arc (start 0 -2.54) (mid 0.635 -1.905) (end 0 -1.27) (stroke (width 0) (type default)) (fill (type none)))
        (arc (start 0 -1.27) (mid 0.635 -0.635) (end 0 0) (stroke (width 0) (type default)) (fill (type none)))
        (arc (start 0 0) (mid 0.635 0.635) (end 0 1.27) (stroke (width 0) (type default)) (fill (type none)))
        (arc (start 0 1.27) (mid 0.635 1.905) (end 0 2.54) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "L_1_1"
        (pin passive line (at 0 3.81 270) (length 1.27) (name "1" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 0 -3.81 90) (length 1.27) (name "2" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )'''

# Chip antenna (2 pin passive)
SYM_ANT = '''    (symbol "FreedomUnit:Antenna_Chip" (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
      (property "Reference" "ANT" (at 0 5.08 0) (effects (font (size 1.27 1.27))))
      (property "Value" "Antenna_Chip" (at 0 -5.08 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "Antenna_Chip_0_1"
        (polyline (pts (xy -2.54 2.54) (xy 0 2.54) (xy 0 0)) (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy 0 2.54) (xy 2.54 2.54)) (stroke (width 0.254) (type default)) (fill (type none)))
      )
      (symbol "Antenna_Chip_1_1"
        (pin passive line (at 0 -2.54 90) (length 2.54) (name "FEED" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -5.08 -2.54 0) (length 5.08) (name "GND" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
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
# PLACEMENT
# ═══════════════════════════════════════════════════════════════

# MCU centered on A3 landscape (420x297mm)
U1_X, U1_Y = 200.0, 150.0

# 32MHz crystal below MCU
Y1_X, Y1_Y = 187.0, 230.0
C21_X, C21_Y = 180.0, 240.0   # 12pF load cap for XC1
C22_X, C22_Y = 194.0, 240.0   # 12pF load cap for XC2

# 32.768kHz crystal below MCU
Y2_X, Y2_Y = 210.0, 230.0
C23_X, C23_Y = 203.0, 240.0   # 6pF load cap for XL1
C24_X, C24_Y = 217.0, 240.0   # 6pF load cap for XL2

# BLE antenna matching network and antenna (below-left of MCU)
L1_X, L1_Y = 165.0, 240.0     # 3.9nH matching inductor
C19_X, C19_Y = 155.0, 250.0   # 0.8pF shunt cap
C20_X, C20_Y = 175.0, 250.0   # 0.5pF shunt cap
ANT1_X, ANT1_Y = 185.0, 250.0 # Chip antenna

# Decoupling caps above MCU (top row)
dec_y = 75.0
# VDD cap row
C25_X = 170.0
C26_X = 177.62
C27_X = 185.24
C28_X = 192.86
C29_X = 200.48
C30_X = 208.1
C31_X = 215.72  # 1uF bulk

# DEC caps
C32_X = 200.0  # DEC1 100nF
C32_Y = 72.0
C33_X = 207.0  # DEC4 1uF
C33_Y = 72.0
C34_X = 214.0  # DEC6 100nF
C34_Y = 72.0
C35_X = 221.0  # DECUSB 4.7uF
C35_Y = 72.0
C36_X = 228.0  # DECUSB 100nF
C36_Y = 72.0

# ═══════════════════════════════════════════════════════════════
# PIN POSITIONS
# ═══════════════════════════════════════════════════════════════

# MCU top pins (DEC/VDD) — at MCU_Y - 66.04 = 83.96 in schematic
P_VDD   = sym_to_abs(U1_X, U1_Y, -5.08, 66.04)   # (194.92, 83.96)
P_DEC1  = sym_to_abs(U1_X, U1_Y, 0, 66.04)       # (200, 83.96)
P_DEC4  = sym_to_abs(U1_X, U1_Y, 5.08, 66.04)    # (205.08, 83.96)
P_DEC6  = sym_to_abs(U1_X, U1_Y, 10.16, 66.04)   # (210.16, 83.96)
P_VDDH  = sym_to_abs(U1_X, U1_Y, 15.24, 66.04)   # (215.24, 83.96)
P_DECUSB = sym_to_abs(U1_X, U1_Y, 20.32, 66.04)  # (220.32, 83.96)

# MCU bottom pins
P_VSS  = sym_to_abs(U1_X, U1_Y, 0, -66.04)        # (200, 216.04)
P_XC1  = sym_to_abs(U1_X, U1_Y, -10.16, -66.04)   # (189.84, 216.04)
P_XC2  = sym_to_abs(U1_X, U1_Y, -5.08, -66.04)    # (194.92, 216.04)
P_XL1  = sym_to_abs(U1_X, U1_Y, 5.08, -66.04)     # (205.08, 216.04)
P_XL2  = sym_to_abs(U1_X, U1_Y, 10.16, -66.04)    # (210.16, 216.04)
P_ANT  = sym_to_abs(U1_X, U1_Y, -20.32, -66.04)   # (179.68, 216.04)

# Left side pins (x = U1_X - 30.48 = 169.52)
left_x = U1_X - 30.48

# Right side pins (x = U1_X + 30.48 = 230.48)
right_x = U1_X + 30.48

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
lines.append('    (title "Sheet 1 — MCU (nRF52840)")')
lines.append('    (date "2026-03-03")')
lines.append('    (rev "V2.2")')
lines.append('    (company "GarageAGI LLC")')
lines.append('  )')

lines.append('  (lib_symbols')
lines.append(SYM_NRF52840)
lines.append(SYM_CRYSTAL)
lines.append(SYM_C)
lines.append(SYM_L)
lines.append(SYM_ANT)
lines.append(SYM_PWR_3V3)
lines.append(SYM_GND)
lines.append('  )')

pwr_idx = 60

# ── Main MCU ──
lines.append(comp("FreedomUnit:nRF52840", "U1", "nRF52840-QIAA", U1_X, U1_Y))

# ── VDD Power Rail ──
# +3V3 above VDD pin
lines.append(pwr("power:+3V3", f"#PWR0{pwr_idx}", "+3V3", P_VDD[0], P_VDD[1] - 5.08))
pwr_idx += 1
lines.append(wire(P_VDD[0], P_VDD[1], P_VDD[0], P_VDD[1] - 5.08))

# VDD rail line (horizontal at P_VDD[1] - 5.08)
vdd_rail_y = P_VDD[1] - 5.08

# VDDH connects to VDD rail
lines.append(wire(P_VDDH[0], P_VDDH[1], P_VDDH[0], vdd_rail_y))
lines.append(wire(P_VDD[0], vdd_rail_y, P_VDDH[0], vdd_rail_y))
lines.append(junction(P_VDD[0], vdd_rail_y))

# GND below MCU
lines.append(pwr("power:GND", f"#PWR0{pwr_idx}", "GND", P_VSS[0], P_VSS[1] + 5.08))
pwr_idx += 1
lines.append(wire(P_VSS[0], P_VSS[1], P_VSS[0], P_VSS[1] + 5.08))

# ── DEC pins to caps ──
# DEC1 -> C32
lines.append(comp("Device:C", "C32", "100nF", C32_X, C32_Y))
lines.append(wire(P_DEC1[0], P_DEC1[1], P_DEC1[0], C32_Y + 3.81))
lines.append(pwr("power:GND", f"#PWR0{pwr_idx}", "GND", C32_X, C32_Y - 3.81 - 2.54))
pwr_idx += 1
lines.append(wire(C32_X, C32_Y - 3.81, C32_X, C32_Y - 3.81 - 2.54))

# DEC4 -> C33
lines.append(comp("Device:C", "C33", "1uF", C33_X, C33_Y))
lines.append(wire(P_DEC4[0], P_DEC4[1], P_DEC4[0], C33_Y + 3.81))
lines.append(pwr("power:GND", f"#PWR0{pwr_idx}", "GND", C33_X, C33_Y - 3.81 - 2.54))
pwr_idx += 1
lines.append(wire(C33_X, C33_Y - 3.81, C33_X, C33_Y - 3.81 - 2.54))

# DEC6 -> C34
lines.append(comp("Device:C", "C34", "100nF", C34_X, C34_Y))
lines.append(wire(P_DEC6[0], P_DEC6[1], P_DEC6[0], C34_Y + 3.81))
lines.append(pwr("power:GND", f"#PWR0{pwr_idx}", "GND", C34_X, C34_Y - 3.81 - 2.54))
pwr_idx += 1
lines.append(wire(C34_X, C34_Y - 3.81, C34_X, C34_Y - 3.81 - 2.54))

# DECUSB -> C35 (4.7uF) + C36 (100nF)
lines.append(comp("Device:C", "C35", "4.7uF", C35_X, C35_Y))
lines.append(comp("Device:C", "C36", "100nF", C36_X, C36_Y))
lines.append(wire(P_DECUSB[0], P_DECUSB[1], P_DECUSB[0], C35_Y + 3.81))
lines.append(wire(P_DECUSB[0], C35_Y + 3.81, C36_X, C35_Y + 3.81))
lines.append(wire(C36_X, C35_Y + 3.81, C36_X, C36_Y + 3.81))
lines.append(junction(P_DECUSB[0], C35_Y + 3.81))

lines.append(pwr("power:GND", f"#PWR0{pwr_idx}", "GND", C35_X, C35_Y - 3.81 - 2.54))
pwr_idx += 1
lines.append(wire(C35_X, C35_Y - 3.81, C35_X, C35_Y - 3.81 - 2.54))
lines.append(pwr("power:GND", f"#PWR0{pwr_idx}", "GND", C36_X, C36_Y - 3.81 - 2.54))
pwr_idx += 1
lines.append(wire(C36_X, C36_Y - 3.81, C36_X, C36_Y - 3.81 - 2.54))

# ── 32MHz Crystal ──
lines.append(comp("Device:Crystal_Small", "Y1", "32MHz", Y1_X, Y1_Y))
lines.append(comp("Device:C", "C21", "12pF", C21_X, C21_Y))
lines.append(comp("Device:C", "C22", "12pF", C22_X, C22_Y))

# XC1 -> Y1 pin1, XC2 -> Y1 pin2
# Crystal pins: pin1 at (Y1_X-2.54, Y1_Y), pin2 at (Y1_X+2.54, Y1_Y)
P_Y1_1 = (Y1_X - 2.54, Y1_Y)
P_Y1_2 = (Y1_X + 2.54, Y1_Y)

lines.append(wire(P_XC1[0], P_XC1[1], P_XC1[0], Y1_Y))
lines.append(wire(P_XC1[0], Y1_Y, P_Y1_1[0], P_Y1_1[1]))
lines.append(wire(P_XC2[0], P_XC2[1], P_XC2[0], Y1_Y))
lines.append(wire(P_XC2[0], Y1_Y, P_Y1_2[0], P_Y1_2[1]))

# Load caps for 32MHz
# C21 top connects to XC1 line, C21 bottom to GND
lines.append(wire(C21_X, C21_Y - 3.81, C21_X, Y1_Y))
lines.append(wire(C21_X, Y1_Y, P_XC1[0], Y1_Y))
lines.append(junction(P_XC1[0], Y1_Y))
lines.append(pwr("power:GND", f"#PWR0{pwr_idx}", "GND", C21_X, C21_Y + 3.81 + 2.54))
pwr_idx += 1
lines.append(wire(C21_X, C21_Y + 3.81, C21_X, C21_Y + 3.81 + 2.54))

lines.append(wire(C22_X, C22_Y - 3.81, C22_X, Y1_Y))
lines.append(wire(C22_X, Y1_Y, P_XC2[0], Y1_Y))
lines.append(junction(P_XC2[0], Y1_Y))
lines.append(pwr("power:GND", f"#PWR0{pwr_idx}", "GND", C22_X, C22_Y + 3.81 + 2.54))
pwr_idx += 1
lines.append(wire(C22_X, C22_Y + 3.81, C22_X, C22_Y + 3.81 + 2.54))

# ── 32.768kHz Crystal ──
lines.append(comp("Device:Crystal_Small", "Y2", "32.768kHz", Y2_X, Y2_Y))
lines.append(comp("Device:C", "C23", "6pF", C23_X, C23_Y))
lines.append(comp("Device:C", "C24", "6pF", C24_X, C24_Y))

P_Y2_1 = (Y2_X - 2.54, Y2_Y)
P_Y2_2 = (Y2_X + 2.54, Y2_Y)

lines.append(wire(P_XL1[0], P_XL1[1], P_XL1[0], Y2_Y))
lines.append(wire(P_XL1[0], Y2_Y, P_Y2_1[0], P_Y2_1[1]))
lines.append(wire(P_XL2[0], P_XL2[1], P_XL2[0], Y2_Y))
lines.append(wire(P_XL2[0], Y2_Y, P_Y2_2[0], P_Y2_2[1]))

lines.append(wire(C23_X, C23_Y - 3.81, C23_X, Y2_Y))
lines.append(wire(C23_X, Y2_Y, P_XL1[0], Y2_Y))
lines.append(junction(P_XL1[0], Y2_Y))
lines.append(pwr("power:GND", f"#PWR0{pwr_idx}", "GND", C23_X, C23_Y + 3.81 + 2.54))
pwr_idx += 1
lines.append(wire(C23_X, C23_Y + 3.81, C23_X, C23_Y + 3.81 + 2.54))

lines.append(wire(C24_X, C24_Y - 3.81, C24_X, Y2_Y))
lines.append(wire(C24_X, Y2_Y, P_XL2[0], Y2_Y))
lines.append(junction(P_XL2[0], Y2_Y))
lines.append(pwr("power:GND", f"#PWR0{pwr_idx}", "GND", C24_X, C24_Y + 3.81 + 2.54))
pwr_idx += 1
lines.append(wire(C24_X, C24_Y + 3.81, C24_X, C24_Y + 3.81 + 2.54))

# ── BLE Antenna Matching Network ──
lines.append(comp("Device:L", "L1", "3.9nH", L1_X, L1_Y))
lines.append(comp("Device:C", "C19", "0.8pF", C19_X, C19_Y))
lines.append(comp("Device:C", "C20", "0.5pF", C20_X, C20_Y))
lines.append(comp("FreedomUnit:Antenna_Chip", "ANT1", "2450AT18D", ANT1_X, ANT1_Y))

# ANT pin -> L1 top -> L1 bottom -> C20 top -> ANT1
# Also: L1 top -> C19 top (shunt), C19 bottom -> GND
# And: L1 bottom -> C20 top (shunt), C20 bottom -> GND

# ANT pin at P_ANT = (179.68, 216.04)
# L1 at (165, 240): pin1 top at (165, 236.19), pin2 bottom at (165, 243.81)
PL1_1 = (L1_X, round(L1_Y - 3.81, 2))
PL1_2 = (L1_X, round(L1_Y + 3.81, 2))

lines.append(wire(P_ANT[0], P_ANT[1], P_ANT[0], PL1_1[1]))
lines.append(wire(P_ANT[0], PL1_1[1], PL1_1[0], PL1_1[1]))

# C19 shunt: top connects to L1 top node, bottom to GND
PC19_1 = (C19_X, round(C19_Y - 3.81, 2))
PC19_2 = (C19_X, round(C19_Y + 3.81, 2))
lines.append(wire(PC19_1[0], PC19_1[1], PC19_1[0], PL1_1[1]))
lines.append(wire(PC19_1[0], PL1_1[1], PL1_1[0], PL1_1[1]))
lines.append(junction(PL1_1[0], PL1_1[1]))
lines.append(pwr("power:GND", f"#PWR0{pwr_idx}", "GND", C19_X, PC19_2[1] + 2.54))
pwr_idx += 1
lines.append(wire(PC19_2[0], PC19_2[1], C19_X, PC19_2[1] + 2.54))

# C20 shunt: top connects to L1 bottom node, bottom to GND
PC20_1 = (C20_X, round(C20_Y - 3.81, 2))
PC20_2 = (C20_X, round(C20_Y + 3.81, 2))
lines.append(wire(PL1_2[0], PL1_2[1], PC20_1[0], PL1_2[1]))
lines.append(wire(PC20_1[0], PL1_2[1], PC20_1[0], PC20_1[1]))
lines.append(pwr("power:GND", f"#PWR0{pwr_idx}", "GND", C20_X, PC20_2[1] + 2.54))
pwr_idx += 1
lines.append(wire(PC20_2[0], PC20_2[1], C20_X, PC20_2[1] + 2.54))

# ANT1 feed pin at (ANT1_X, ANT1_Y-2.54) = (185, 247.46)
# Connect from L1 bottom through to antenna
lines.append(wire(PL1_2[0], PL1_2[1], ANT1_X, PL1_2[1]))
lines.append(wire(ANT1_X, PL1_2[1], ANT1_X, ANT1_Y - 2.54))
lines.append(junction(PL1_2[0], PL1_2[1]))

# ANT1 GND pin at (ANT1_X-5.08, ANT1_Y-2.54)
lines.append(pwr("power:GND", f"#PWR0{pwr_idx}", "GND", ANT1_X - 5.08, ANT1_Y - 2.54 + 5.08))
pwr_idx += 1
lines.append(wire(ANT1_X - 5.08, ANT1_Y - 2.54, ANT1_X - 5.08, ANT1_Y - 2.54 + 5.08))

# ── Left side Global Labels (LoRa SPI, LCD SPI, I2C, GPS, Power) ──
left_labels = [
    ("SPI_SCK",      left_x, sym_to_abs(U1_X, U1_Y, -30.48, 55.88)[1], "output", 0),
    ("SPI_MOSI",     left_x, sym_to_abs(U1_X, U1_Y, -30.48, 53.34)[1], "output", 0),
    ("SPI_MISO",     left_x, sym_to_abs(U1_X, U1_Y, -30.48, 50.8)[1], "input", 0),
    ("LORA_CS",      left_x, sym_to_abs(U1_X, U1_Y, -30.48, 48.26)[1], "output", 0),
    ("LORA_DIO1",    left_x, sym_to_abs(U1_X, U1_Y, -30.48, 43.18)[1], "input", 0),
    ("LORA_BUSY",    left_x, sym_to_abs(U1_X, U1_Y, -30.48, 40.64)[1], "input", 0),
    ("LORA_RESET",   left_x, sym_to_abs(U1_X, U1_Y, -30.48, 38.1)[1], "output", 0),
    ("LORA_RXEN",    left_x, sym_to_abs(U1_X, U1_Y, -30.48, 33.02)[1], "output", 0),
    ("LORA_TXEN",    left_x, sym_to_abs(U1_X, U1_Y, -30.48, 30.48)[1], "output", 0),
    ("LCD_SCLK",     left_x, sym_to_abs(U1_X, U1_Y, -30.48, 25.4)[1], "output", 0),
    ("LCD_MOSI",     left_x, sym_to_abs(U1_X, U1_Y, -30.48, 22.86)[1], "output", 0),
    ("LCD_CS",       left_x, sym_to_abs(U1_X, U1_Y, -30.48, 20.32)[1], "output", 0),
    ("LCD_EXTCOMIN", left_x, sym_to_abs(U1_X, U1_Y, -30.48, 17.78)[1], "output", 0),
    ("LCD_DISP",     left_x, sym_to_abs(U1_X, U1_Y, -30.48, 15.24)[1], "output", 0),
    ("GPS_SDA",      left_x, sym_to_abs(U1_X, U1_Y, -30.48, 10.16)[1], "bidirectional", 0),
    ("GPS_SCL",      left_x, sym_to_abs(U1_X, U1_Y, -30.48, 7.62)[1], "bidirectional", 0),
    ("GPS_PPS",      left_x, sym_to_abs(U1_X, U1_Y, -30.48, 2.54)[1], "input", 0),
    ("GPS_RESET",    left_x, sym_to_abs(U1_X, U1_Y, -30.48, 0)[1], "output", 0),
    ("GPS_EXTINT",   left_x, sym_to_abs(U1_X, U1_Y, -30.48, -2.54)[1], "output", 0),
    ("POWER_EN",     left_x, sym_to_abs(U1_X, U1_Y, -30.48, -7.62)[1], "output", 0),
    ("BQ_VBAT_OK",   left_x, sym_to_abs(U1_X, U1_Y, -30.48, -10.16)[1], "input", 0),
    ("BATTERY_ADC",  left_x, sym_to_abs(U1_X, U1_Y, -30.48, -12.7)[1], "input", 0),
]

for name, lx, ly, shape, angle in left_labels:
    lines.append(global_label(name, lx - 12.7, ly, shape, angle))
    lines.append(wire(lx - 12.7, ly, lx, ly))

# ── Right side Global Labels ──
right_labels = [
    ("BTN_UP",    right_x, sym_to_abs(U1_X, U1_Y, 30.48, 55.88)[1], "input", 180),
    ("BTN_DOWN",  right_x, sym_to_abs(U1_X, U1_Y, 30.48, 53.34)[1], "input", 180),
    ("BTN_LEFT",  right_x, sym_to_abs(U1_X, U1_Y, 30.48, 50.8)[1], "input", 180),
    ("BTN_RIGHT", right_x, sym_to_abs(U1_X, U1_Y, 30.48, 48.26)[1], "input", 180),
    ("BTN_CENTER",right_x, sym_to_abs(U1_X, U1_Y, 30.48, 45.72)[1], "input", 180),
    ("BTN_A",     right_x, sym_to_abs(U1_X, U1_Y, 30.48, 43.18)[1], "input", 180),
    ("BTN_B",     right_x, sym_to_abs(U1_X, U1_Y, 30.48, 40.64)[1], "input", 180),
    ("LED_RED",   right_x, sym_to_abs(U1_X, U1_Y, 30.48, 35.56)[1], "output", 180),
    ("LED_GREEN", right_x, sym_to_abs(U1_X, U1_Y, 30.48, 33.02)[1], "output", 180),
    ("LED_BLUE",  right_x, sym_to_abs(U1_X, U1_Y, 30.48, 30.48)[1], "output", 180),
    ("QSPI_SCK",  right_x, sym_to_abs(U1_X, U1_Y, 30.48, 25.4)[1], "output", 180),
    ("QSPI_CS",   right_x, sym_to_abs(U1_X, U1_Y, 30.48, 22.86)[1], "output", 180),
    ("QSPI_IO0",  right_x, sym_to_abs(U1_X, U1_Y, 30.48, 20.32)[1], "bidirectional", 180),
    ("QSPI_IO1",  right_x, sym_to_abs(U1_X, U1_Y, 30.48, 17.78)[1], "bidirectional", 180),
    ("QSPI_IO2",  right_x, sym_to_abs(U1_X, U1_Y, 30.48, 15.24)[1], "bidirectional", 180),
    ("QSPI_IO3",  right_x, sym_to_abs(U1_X, U1_Y, 30.48, 12.7)[1], "bidirectional", 180),
    ("USB_DP",    right_x, sym_to_abs(U1_X, U1_Y, 30.48, 7.62)[1], "bidirectional", 180),
    ("USB_DN",    right_x, sym_to_abs(U1_X, U1_Y, 30.48, 5.08)[1], "bidirectional", 180),
]

for name, lx, ly, shape, angle in right_labels:
    lines.append(global_label(name, lx + 12.7, ly, shape, angle))
    lines.append(wire(lx, ly, lx + 12.7, ly))

# Unassigned/unused pins -> no connect
unused_pins_y = [
    sym_to_abs(U1_X, U1_Y, 30.48, 0)[1],     # UART_TX
    sym_to_abs(U1_X, U1_Y, 30.48, -2.54)[1],  # UART_RX
    sym_to_abs(U1_X, U1_Y, 30.48, -7.62)[1],  # SWDIO
    sym_to_abs(U1_X, U1_Y, 30.48, -10.16)[1], # SWDCLK
    sym_to_abs(U1_X, U1_Y, 30.48, -15.24)[1], # P0.09
    sym_to_abs(U1_X, U1_Y, 30.48, -17.78)[1], # P0.10
    sym_to_abs(U1_X, U1_Y, 30.48, -20.32)[1], # P0.21
    sym_to_abs(U1_X, U1_Y, 30.48, -22.86)[1], # P1.03
]

for py in unused_pins_y:
    lines.append(no_connect(right_x, py))

# Close
lines.append(')')

output = '\n'.join(lines)
output = clean_floats(output)

output_path = '/home/user/workspace/Sheet1_MCU.kicad_sch'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(output)

print(f"\nGenerated: {output_path}")
print(f"File size: {len(output)} bytes")
