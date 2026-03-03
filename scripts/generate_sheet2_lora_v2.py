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

# Sheet 2: LoRa Module (Lambda62C-9S)
lora_symbols = [
    ("FreedomUnit:Lambda62C-9S", "M1", "Lambda62C-9S", (100, 100), "Lambda62C-9S", "FreedomUnit:Lambda62C-9S"),
    ("Connector:Conn_Coaxial", "J2", "u.FL", (140, 100), "u.FL", "Connector_Coaxial:U.FL_Molex_MCRF_73412-0110_Vertical"),
    ("FreedomUnit:CONSMA006.062", "J3", "SMA", (160, 100), "CONSMA006.062", "FreedomUnit:CONSMA006.062"),
]

lora_labels = [
    global_label("V3P3_PERIPH", (100, 90)),
    global_label("GND", (100, 110)),
    global_label("SPI_SCK", (80, 95)),
    global_label("SPI_MOSI", (80, 100)),
    global_label("SPI_MISO", (80, 105)),
    global_label("LORA_CS", (80, 110)),
    global_label("LORA_RESET", (80, 115)),
    global_label("LORA_BUSY", (120, 85)),
    global_label("LORA_DIO1", (120, 90)),
    global_label("LORA_RXEN", (120, 95)),
    global_label("LORA_TXEN", (120, 105)),
]

content = f"""(kicad_sch
  (version 20240108)
  (generator "Gemini CLI")
  (generator_version "1.1")
  (uuid "{get_uuid()}")
  (paper "A4")
  (title_block
    (title "Sheet 2 — LoRa Architecture")
    (company "GarageAGI LLC")
    (rev "V2.2")
    (date "2026-03-03")
  )
{"".join([symbol(*s) for s in lora_symbols])}
{"".join([l for l in lora_labels])}
)"""

with open("FreedomUnit_V2/Sheet2_LoRa.kicad_sch", "w", encoding='utf-8') as f:
    f.write(content)
print("Generated Sheet2_LoRa.kicad_sch with global labels and footprints.")
