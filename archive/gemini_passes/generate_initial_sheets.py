import uuid
import time

def generate_empty_sch(filename, title):
    u = str(uuid.uuid4())
    content = f"""(kicad_sch
  (version 20240108)
  (generator "Gemini CLI")
  (generator_version "1.0")
  (uuid "{u}")
  (paper "A4")
  (title_block
    (title "{title}")
    (company "GarageAGI LLC")
    (rev "V2.2")
    (date "2026-03-03")
  )
)"""
    with open(filename, "w") as f:
        f.write(content)

sheets = [
    ("FreedomUnit_V2.kicad_sch", "Freedom Unit V2 — Root Schematic"),
    ("Sheet1_MCU.kicad_sch", "Sheet 1 — MCU (nRF52840 + Clocks + BLE)"),
    ("Sheet2_LoRa.kicad_sch", "Sheet 2 — LoRa (Lambda62C-9S module)"),
    ("Sheet3_Power.kicad_sch", "Sheet 3 — Power (Chargers, LDO, Load Switch)"),
    ("Sheet4_USB.kicad_sch", "Sheet 4 — USB (USB-C, ESD, CC)"),
    ("Sheet5_Peripherals.kicad_sch", "Sheet 5 — Peripherals (LCD, GPS, UI)")
]

for filename, title in sheets:
    generate_empty_sch(f"FreedomUnit_V2/{filename}", title)
    print(f"Generated {filename}")
