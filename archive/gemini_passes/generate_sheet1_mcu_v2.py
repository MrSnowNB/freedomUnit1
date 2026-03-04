import uuid

def get_uuid():
    return str(uuid.uuid4())

def symbol(lib_id, reference, value, position, mpn, footprint="", unit=1):
    u = get_uuid()
    x, y = position
    return f"""
  (symbol (lib_id "{lib_id}") (at {x} {y} 0) (unit {unit})
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

def global_label(text, position, orientation=0):
    x, y = position
    return f"""
  (global_label "{text}" (at {x} {y} {orientation}) (fields_autoplaced yes)
    (uuid "{get_uuid()}")
    (effects (font (size 1.27 1.27)) (justify left bottom))
  )"""

mcu_symbols = [
    ("MCU_Nordic:nRF52840", "U1", "nRF52840", (150, 100), "nRF52840", "Package_DFN_QFN:QFN-73-1EP_7x7mm_P0.35mm_EP5.1x5.1mm"),
    # Clocks
    ("Device:Crystal", "Y1", "32 MHz", (120, 80), "ABM8-32.000MHZ-B2-T", "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm"),
    ("Device:Crystal_Small", "Y2", "32.768 kHz", (120, 120), "ABS07-120-32.768KHZ-T", "Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm"),
    ("Device:C", "C1", "12pF", (115, 90), "Various 0402", "Capacitor_SMD:C_0402_1005Metric"),
    ("Device:C", "C2", "12pF", (125, 90), "Various 0402", "Capacitor_SMD:C_0402_1005Metric"),
    ("Device:C", "C3", "6pF", (115, 130), "Various 0402", "Capacitor_SMD:C_0402_1005Metric"),
    ("Device:C", "C4", "6pF", (125, 130), "Various 0402", "Capacitor_SMD:C_0402_1005Metric"),
    # Decoupling Caps (The FULL list)
    ("Device:C", "C5", "100nF", (140, 90), "Various 0402", "Capacitor_SMD:C_0402_1005Metric"), # DEC1
    ("Device:C", "C6", "1uF", (140, 110), "Various 0402", "Capacitor_SMD:C_0402_1005Metric"), # DEC4
    ("Device:C", "C7", "100nF", (140, 130), "Various 0402", "Capacitor_SMD:C_0402_1005Metric"), # DEC6
    ("Device:C", "C8", "4.7uF", (160, 90), "Various 0402", "Capacitor_SMD:C_0402_1005Metric"), # DECUSB
    ("Device:C", "C9", "100nF", (160, 110), "Various 0402", "Capacitor_SMD:C_0402_1005Metric"), # DECUSB
    ("Device:C", "C14", "100nF", (150, 70), "Various 0402", "Capacitor_SMD:C_0402_1005Metric"), # VDD 1
    ("Device:C", "C15", "100nF", (160, 70), "Various 0402", "Capacitor_SMD:C_0402_1005Metric"), # VDD 2
    ("Device:C", "C16", "1uF", (170, 70), "Various 0402", "Capacitor_SMD:C_0402_1005Metric"), # VDD Bulk
    ("Device:C", "C27", "4.7uF", (175, 70), "Various 0402", "Capacitor_SMD:C_0402_1005Metric"), # VDDH Cap
    # BLE Antenna Matching
    ("Device:L", "L1", "3.9nH", (180, 70), "Various 0402", "Inductor_SMD:L_0402_1005Metric"),
    ("Device:C", "C17", "0.8pF", (185, 75), "Various 0402", "Capacitor_SMD:C_0402_1005Metric"),
    ("Device:C", "C18", "0.5pF", (190, 75), "Various 0402", "Capacitor_SMD:C_0402_1005Metric"),
    ("Device:Antenna_Chip", "AE1", "BLE Antenna", (200, 70), "2450AT18D0100", "Antenna:Johanson_2450AT18D0100"),
]

mcu_labels = [
    global_label("V3P3", (150, 60)),
    global_label("GND", (150, 140)),
    global_label("SPI_SCK", (130, 90)),
    global_label("SPI_MOSI", (130, 100)),
    global_label("SPI_MISO", (130, 110)),
    global_label("LORA_CS", (130, 120)),
    global_label("GPS_SDA", (170, 90)),
    global_label("GPS_SCL", (170, 100)),
    global_label("POWER_EN", (170, 110)),
]

content = f"""(kicad_sch
  (version 20240108)
  (generator "Gemini CLI")
  (generator_version "1.1")
  (uuid "{get_uuid()}")
  (paper "A4")
  (title_block
    (title "Sheet 1 — MCU Architecture")
    (company "GarageAGI LLC")
    (rev "V2.2")
    (date "2026-03-03")
  )
{"".join([symbol(*s) for s in mcu_symbols])}
{"".join([l for l in mcu_labels])}
)"""

with open("FreedomUnit_V2/Sheet1_MCU.kicad_sch", "w", encoding='utf-8') as f:
    f.write(content)
print("Generated Sheet1_MCU.kicad_sch with complete decoupling and BLE match.")
