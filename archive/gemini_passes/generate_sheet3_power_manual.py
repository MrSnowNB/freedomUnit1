import uuid

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
    (property "Datasheet" "~" (at {x} {y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "mpn" "{mpn}" (at {x} {y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "populate" "1" (at {x} {y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )"""

content = f"""(kicad_sch
  (version 20240108)
  (generator "Gemini CLI")
  (generator_version "1.0")
  (uuid "{get_uuid()}")
  (paper "A4")
  (title_block
    (title "Sheet 3 — Power (Chargers, LDO, Load Switch)")
    (company "GarageAGI LLC")
    (rev "V2.2")
    (date "2026-03-03")
  )
{symbol("Power_Management:BQ25504RGTR", "U2", "BQ25504RGTR", (100, 100), "BQ25504RGTR")}
{symbol("Power_Management:MCP73831T-2ACI_OT", "U3", "MCP73831T", (150, 100), "MCP73831T-2ACI/OT")}
{symbol("Power_Management:TPS7A0233DBVR", "U4", "TPS7A0233DBVR", (200, 100), "TPS7A0233DBVR")}
{symbol("Power_Management:TPS22918DBVR", "U5", "TPS22918DBVR", (250, 100), "TPS22918DBVR")}
{symbol("Device:D_Schottky", "D1", "BAT54JFILM", (175, 80), "BAT54JFILM")}
{symbol("Switch:SW_SPDT", "SW1", "JS102011SAQN", (50, 50), "JS102011SAQN")}
{symbol("Device:Battery_Cell", "BT1", "NCR18650B", (50, 100), "NCR18650B")}
{symbol("Connector:Conn_01x02_Male", "J1", "Solar Input", (80, 50), "S2B-PH-K-S(LF)(SN)")}
{symbol("Device:R", "R1", "100k", (70, 120), "Various 0402")}
{symbol("Device:R", "R2", "100k", (70, 130), "Various 0402")}
)"""

with open("FreedomUnit_V2/Sheet3_Power.kicad_sch", "w") as f:
    f.write(content)
print("Generated Sheet3_Power.kicad_sch")
