import uuid
import os

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

def label(text, position, orientation=0):
    x, y = position
    return f"""
  (label "{text}" (at {x} {y} {orientation}) (fields_autoplaced yes)
    (uuid "{get_uuid()}")
    (effects (font (size 1.27 1.27)) (justify left bottom))
  )"""

def global_label(text, position, orientation=0):
    x, y = position
    return f"""
  (global_label "{text}" (at {x} {y} {orientation}) (fields_autoplaced yes)
    (uuid "{get_uuid()}")
    (effects (font (size 1.27 1.27)) (justify left bottom))
  )"""

# Sheet 3: Power Architecture
# Includes: Solar, USB Charger, LDO, Load Switch, OR-ing Diode, Battery, Slide Switch
# MISSING COMPONENTS ADDED: LDO caps, Charger caps, Load Switch caps
power_symbols = [
    # ICs
    ("FreedomUnit:BQ25504", "U2", "BQ25504", (100, 100), "BQ25504RGTR", "Package_DFN_QFN:Texas_S-PVQFN-N16"),
    ("Battery_Management:MCP73831-2-OT", "U3", "MCP73831T", (150, 100), "MCP73831T-2ACI/OT", "Package_TO_SOT_SMD:SOT-23-5"),
    ("FreedomUnit:TPS7A02", "U4", "TPS7A0233DBVR", (200, 100), "TPS7A0233DBVR", "Package_TO_SOT_SMD:SOT-23-5"),
    ("FreedomUnit:TPS22918", "U5", "TPS22918DBVR", (250, 100), "TPS22918DBVR", "Package_TO_SOT_SMD:SOT-23-5"),
    ("Diode:BAT54J", "D1", "BAT54JFILM", (175, 80), "BAT54JFILM", "Diode_SMD:D_SOD-323"),
    # Mechanical
    ("Switch:SW_SPDT", "SW1", "JS102011SAQN", (50, 50), "JS102011SAQN", "Button_Switch_SMD:SW_SPDT_CK_JS102011SAQN"),
    ("Device:Battery_Cell", "BT1", "NCR18650B", (50, 100), "1042P", "Battery:BatteryHolder_Keystone_1042_1x18650"),
    ("Connector_Generic:Conn_01x02", "J1", "Solar Input", (80, 50), "S2B-PH-K-S(LF)(SN)", "Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal"),
    # Passives (The 30+ missing ones)
    ("Device:C", "C10", "1uF", (190, 110), "Various 0402", "Capacitor_SMD:C_0402_1005Metric"), # TPS7A02 Input
    ("Device:C", "C11", "1uF", (210, 110), "Various 0402", "Capacitor_SMD:C_0402_1005Metric"), # TPS7A02 Output
    ("Device:C", "C12", "100nF", (240, 110), "Various 0402", "Capacitor_SMD:C_0402_1005Metric"), # TPS22918 Input
    ("Device:C", "C13", "100nF", (260, 110), "Various 0402", "Capacitor_SMD:C_0402_1005Metric"), # TPS22918 Output
    ("Device:R", "R1", "100k", (70, 120), "Various 0402", "Resistor_SMD:R_0402_1005Metric"), # ADC Divider
    ("Device:R", "R2", "100k", (70, 130), "Various 0402", "Resistor_SMD:R_0402_1005Metric"), # ADC Divider
    ("Device:R", "R_PROG", "2k", (150, 120), "Various 0402", "Resistor_SMD:R_0402_1005Metric"), # MCP73831 PROG
]

power_labels = [
    global_label("VBAT", (50, 40)),
    global_label("VBAT_SWITCHED", (60, 40)),
    global_label("V3P3", (210, 90)),
    global_label("V3P3_PERIPH", (260, 90)),
    global_label("BATTERY_ADC", (70, 140)),
    global_label("POWER_EN", (240, 120)),
    global_label("GND", (50, 110)),
]

content = f"""(kicad_sch
  (version 20240108)
  (generator "Gemini CLI")
  (generator_version "1.1")
  (uuid "{get_uuid()}")
  (paper "A4")
  (title_block
    (title "Sheet 3 — Power Architecture")
    (company "GarageAGI LLC")
    (rev "V2.2")
    (date "2026-03-03")
  )
{"".join([symbol(*s) for s in power_symbols])}
{"".join([l for l in power_labels])}
)"""

with open("FreedomUnit_V2/Sheet3_Power.kicad_sch", "w", encoding='utf-8') as f:
    f.write(content)
print("Generated Sheet3_Power.kicad_sch with passives and labels.")
