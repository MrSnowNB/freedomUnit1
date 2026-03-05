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

# Sheet 4: USB-C and ESD Protection
usb_symbols = [
    ("Connector:USB_C_Receptacle_USB2.0_16P", "J4", "USB-C", (100, 100), "USB4085-GF-A", "Connector_USB:USB_C_Receptacle_GCT_USB4085"),
    ("FreedomUnit:TPD2E001", "D2", "USB ESD", (140, 100), "TPD2E001DRLR", "Package_TO_SOT_SMD:SOT-23-5"),
    ("Device:R", "R3", "5.1k", (90, 120), "Various 0402", "Resistor_SMD:R_0402_1005Metric"),
    ("Device:R", "R4", "5.1k", (110, 120), "Various 0402", "Resistor_SMD:R_0402_1005Metric"),
]

usb_labels = [
    global_label("VBUS", (100, 90)),
    global_label("GND", (100, 130)),
    global_label("USB_D+", (120, 90)),
    global_label("USB_D-", (120, 110)),
]

content = f"""(kicad_sch
  (version 20240108)
  (generator "Gemini CLI")
  (generator_version "1.1")
  (uuid "{get_uuid()}")
  (paper "A4")
  (title_block
    (title "Sheet 4 — USB-C Architecture")
    (company "GarageAGI LLC")
    (rev "V2.2")
    (date "2026-03-03")
  )
{"".join([symbol(*s) for s in usb_symbols])}
{"".join([l for l in usb_labels])}
)"""

with open("FreedomUnit_V2/Sheet4_USB.kicad_sch", "w", encoding='utf-8') as f:
    f.write(content)
print("Generated Sheet4_USB.kicad_sch with CC resistors and ESD.")
