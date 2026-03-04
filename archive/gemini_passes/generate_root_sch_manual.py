import uuid

def get_uuid():
    return str(uuid.uuid4())

def hierarchical_sheet(name, filename, position, size=(50, 30)):
    u = get_uuid()
    x, y = position
    w, h = size
    return f"""
  (sheet (at {x} {y}) (size {w} {h}) (fields_autoplaced yes)
    (uuid "{u}")
    (property "Sheetname" "{name}" (at {x} {y-0.635} 0)
      (effects (font (size 1.27 1.27)) (justify left bottom))
    )
    (property "Sheetfile" "{filename}" (at {x} {y+h+0.635} 0)
      (effects (font (size 1.27 1.27)) (justify left top))
    )
  )"""

content = f"""(kicad_sch
  (version 20240108)
  (generator "Gemini CLI")
  (generator_version "1.0")
  (uuid "{get_uuid()}")
  (paper "A4")
  (title_block
    (title "Freedom Unit V2 — Root Schematic")
    (company "GarageAGI LLC")
    (rev "V2.2")
    (date "2026-03-03")
  )
{hierarchical_sheet("MCU", "Sheet1_MCU.kicad_sch", (20, 20))}
{hierarchical_sheet("LoRa", "Sheet2_LoRa.kicad_sch", (80, 20))}
{hierarchical_sheet("Power", "Sheet3_Power.kicad_sch", (20, 70))}
{hierarchical_sheet("USB", "Sheet4_USB.kicad_sch", (80, 70))}
{hierarchical_sheet("Peripherals", "Sheet5_Peripherals.kicad_sch", (20, 120))}
)"""

with open("FreedomUnit_V2/FreedomUnit_V2.kicad_sch", "w") as f:
    f.write(content)
print("Generated FreedomUnit_V2.kicad_sch")
