import kicad_sch_api as ksa

sch = ksa.Schematic(name="Sheet 3 — Power (Chargers, LDO, Load Switch)")

# Components from BOM
# BQ25504 Solar Harvester
u2 = sch.add_component("Power_Management:BQ25504RGTR", "U2", "BQ25504RGTR", 
                        position=(100, 100))
u2.set_property("mpn", "BQ25504RGTR")

# MCP73831 USB Charger
u3 = sch.add_component("Power_Management:MCP73831T-2ACI_OT", "U3", "MCP73831T",
                        position=(150, 100))
u3.set_property("mpn", "MCP73831T-2ACI/OT")

# TPS7A02 LDO
u4 = sch.add_component("Power_Management:TPS7A0233DBVR", "U4", "TPS7A0233DBVR",
                        position=(200, 100))
u4.set_property("mpn", "TPS7A0233DBVR")

# TPS22918 Load Switch
u5 = sch.add_component("Power_Management:TPS22918DBVR", "U5", "TPS22918DBVR",
                        position=(250, 100))
u5.set_property("mpn", "TPS22918DBVR")

# BAT54J Schottky OR-ing Diode
d1 = sch.add_component("Device:D_Schottky", "D1", "BAT54JFILM",
                        position=(175, 80))
d1.set_property("mpn", "BAT54JFILM")

# C&K JS102011SAQN Slide Switch
sw1 = sch.add_component("Switch:SW_SPDT", "SW1", "JS102011SAQN",
                         position=(50, 50))
sw1.set_property("mpn", "JS102011SAQN")

# Keystone 1042P Battery Holder
bt1 = sch.add_component("Device:Battery_Cell", "BT1", "NCR18650B",
                         position=(50, 100))
bt1.set_property("mpn", "1042P")

# JST S2B-PH-K-S Solar Connector
j1 = sch.add_component("Connector:Conn_01x02_Male", "J1", "Solar Input",
                        position=(80, 50))
j1.set_property("mpn", "S2B-PH-K-S(LF)(SN)")

# Voltage Divider for Battery ADC (AIN2)
r1 = sch.add_component("Device:R", "R1", "100k", position=(70, 120))
r2 = sch.add_component("Device:R", "R2", "100k", position=(70, 130))

sch.save("FreedomUnit_V2/Sheet3_Power.kicad_sch")
