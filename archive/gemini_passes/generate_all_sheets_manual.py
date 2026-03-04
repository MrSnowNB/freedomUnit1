import uuid
import os

def get_uuid():
    return str(uuid.uuid4())

def symbol(lib_id, reference, value, position, mpn, footprint=""):
    u = get_uuid()
    x, y = position
    return f"""
  (symbol (lib_id "{lib_id}") (at {x} {y} 0) (unit 1)
    (in_bom yes) (on_board yes) (dnp no) (fields_autoplaced yes)
    (uuid "{u}")
    (property "Reference" "{reference}" (at {x} {y-5} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "{value}" (at {x} {y+5} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "{footprint}" (at {x+10} {y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "mpn" "{mpn}" (at {x} {y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "populate" "1" (at {x} {y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )"""

def generate_sheet(filename, title, symbols_data):
    symbols_str = "\n".join([symbol(*data) for data in symbols_data])
    content = f"""(kicad_sch
  (version 20240108)
  (generator "Gemini CLI")
  (generator_version "1.0")
  (uuid "{get_uuid()}")
  (paper "A4")
  (title_block
    (title "{title}")
    (company "GarageAGI LLC")
    (rev "V2.2")
    (date "2026-03-03")
  )
{symbols_str}
)"""
    with open(filename, "w") as f:
        f.write(content)
    print(f"Generated {filename}")

# MCU Sheet
mcu_symbols = [
    ("RF_Module:nRF52840-QIAA", "U1", "nRF52840-QIAA", (150, 100), "nRF52840-QIAA"),
    ("Device:Crystal", "Y1", "32 MHz", (120, 80), "ABM8-32.000MHZ-B2-T"),
    ("Device:Crystal_Small", "Y2", "32.768 kHz", (120, 120), "ABS07-120-32.768KHZ-T"),
    ("Device:Antenna_Chip", "AE1", "BLE Antenna", (180, 80), "2450AT18D0100"),
    ("Device:C", "C1", "12pF", (115, 90), "Various 0402"),
    ("Device:C", "C2", "12pF", (125, 90), "Various 0402"),
    ("Device:C", "C3", "6pF", (115, 130), "Various 0402"),
    ("Device:C", "C4", "6pF", (125, 130), "Various 0402"),
    # Decoupling caps (per Nordic spec)
    ("Device:C", "C5", "100nF", (140, 90), "Various 0402"),
    ("Device:C", "C6", "100nF", (140, 110), "Various 0402"),
    ("Device:C", "C7", "1uF", (140, 130), "Various 0402"),
]

# LoRa Sheet
lora_symbols = [
    ("FreedomUnit:Lambda62C-9S", "M1", "Lambda62C-9S", (100, 100), "Lambda62C-9S"),
    ("Connector:Conn_Coaxial", "J2", "u.FL", (140, 100), "u.FL"),
    ("Connector:Conn_Coaxial", "J3", "SMA", (160, 100), "CONSMA006.062"),
]

# USB Sheet
usb_symbols = [
    ("Connector:USB_C_Receptacle_USB2.0", "J4", "USB-C", (100, 100), "USB4085-GF-A"),
    ("Power_Protection:TPD2E001", "D2", "USB ESD", (120, 100), "TPD2E001DRLR"),
    ("Device:R", "R3", "5.1k", (90, 120), "Various 0402"),
    ("Device:R", "R4", "5.1k", (110, 120), "Various 0402"),
]

# Peripherals Sheet
periph_symbols = [
    ("Connector:Conn_01x10_Female", "J5", "LCD FPC", (100, 100), "5051100892"),
    ("RF_GPS:MAX-M10S", "U6", "MAX-M10S", (150, 100), "MAX-M10S-00B"),
    ("Device:Antenna", "AE2", "GPS Patch", (180, 100), "CGGBP.25.4.A.02"),
    ("Connector:Conn_01x04_Male", "J6", "I2C Expansion", (100, 150), "Samtec TSW"),
    ("Switch:SW_Push", "SW2", "BTN_UP", (50, 180), "PTS636"),
    ("Switch:SW_Push", "SW3", "BTN_DOWN", (60, 180), "PTS636"),
    ("Switch:SW_Push", "SW4", "BTN_LEFT", (70, 180), "PTS636"),
    ("Switch:SW_Push", "SW5", "BTN_RIGHT", (80, 180), "PTS636"),
    ("Switch:SW_Push", "SW6", "BTN_CENTER", (90, 180), "PTS636"),
    ("Switch:SW_Push", "SW7", "BTN_A", (100, 180), "PTS636"),
    ("Switch:SW_Push", "SW8", "BTN_B", (110, 180), "PTS636"),
    ("Device:LED", "D3", "RED", (50, 200), "Various 0603"),
    ("Device:LED", "D4", "GREEN", (60, 200), "Various 0603"),
    ("Device:LED", "D5", "BLUE", (70, 200), "Various 0603"),
    ("Memory_Flash:MX25R6435F", "U7", "64M QSPI", (200, 150), "MX25R6435F"),
]

generate_sheet("FreedomUnit_V2/Sheet1_MCU.kicad_sch", "Sheet 1 — MCU (nRF52840 + Clocks + BLE)", mcu_symbols)
generate_sheet("FreedomUnit_V2/Sheet2_LoRa.kicad_sch", "Sheet 2 — LoRa (Lambda62C-9S module)", lora_symbols)
generate_sheet("FreedomUnit_V2/Sheet4_USB.kicad_sch", "Sheet 4 — USB (USB-C, ESD, CC)", usb_symbols)
generate_sheet("FreedomUnit_V2/Sheet5_Peripherals.kicad_sch", "Sheet 5 — Peripherals (LCD, GPS, UI)", periph_symbols)
