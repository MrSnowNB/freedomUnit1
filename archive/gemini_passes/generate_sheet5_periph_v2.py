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

periph_symbols = [
    # UI Buttons + MISSING DEBOUNCE CAPS
    ("Switch:SW_Push", "SW2", "BTN_UP", (50, 180), "PTS636", "Button_Switch_SMD:SW_SPST_PTS636"),
    ("Device:C", "C20", "100nF", (55, 185), "Various 0402", "Capacitor_SMD:C_0402_1005Metric"),
    ("Switch:SW_Push", "SW3", "BTN_DOWN", (65, 180), "PTS636", "Button_Switch_SMD:SW_SPST_PTS636"),
    ("Device:C", "C21", "100nF", (70, 185), "Various 0402", "Capacitor_SMD:C_0402_1005Metric"),
    ("Switch:SW_Push", "SW4", "BTN_LEFT", (80, 180), "PTS636", "Button_Switch_SMD:SW_SPST_PTS636"),
    ("Device:C", "C22", "100nF", (85, 185), "Various 0402", "Capacitor_SMD:C_0402_1005Metric"),
    ("Switch:SW_Push", "SW5", "BTN_RIGHT", (95, 180), "PTS636", "Button_Switch_SMD:SW_SPST_PTS636"),
    ("Device:C", "C23", "100nF", (100, 185), "Various 0402", "Capacitor_SMD:C_0402_1005Metric"),
    ("Switch:SW_Push", "SW6", "BTN_CENTER", (110, 180), "PTS636", "Button_Switch_SMD:SW_SPST_PTS636"),
    ("Device:C", "C24", "100nF", (115, 185), "Various 0402", "Capacitor_SMD:C_0402_1005Metric"),
    ("Switch:SW_Push", "SW7", "BTN_A", (125, 180), "PTS636", "Button_Switch_SMD:SW_SPST_PTS636"),
    ("Device:C", "C25", "100nF", (130, 185), "Various 0402", "Capacitor_SMD:C_0402_1005Metric"),
    ("Switch:SW_Push", "SW8", "BTN_B", (140, 180), "PTS636", "Button_Switch_SMD:SW_SPST_PTS636"),
    ("Device:C", "C26", "100nF", (145, 185), "Various 0402", "Capacitor_SMD:C_0402_1005Metric"),
    # LEDs + MISSING RESISTORS
    ("Device:LED", "D3", "RED", (50, 200), "Various 0603", "LED_SMD:LED_0603_1608Metric"),
    ("Device:R", "R30", "680", (50, 210), "Various 0402", "Resistor_SMD:R_0402_1005Metric"),
    ("Device:LED", "D4", "GREEN", (60, 200), "Various 0603", "LED_SMD:LED_0603_1608Metric"),
    ("Device:R", "R31", "680", (60, 210), "Various 0402", "Resistor_SMD:R_0402_1005Metric"),
    ("Device:LED", "D5", "BLUE", (70, 200), "Various 0603", "LED_SMD:LED_0603_1608Metric"),
    ("Device:R", "R32", "680", (70, 210), "Various 0402", "Resistor_SMD:R_0402_1005Metric"),
    # GPS + MISSING I2C PULL-UPS
    ("RF_GPS:MAX-M10S", "U6", "MAX-M10S", (150, 100), "MAX-M10S-00B", "RF_GPS:u-blox_MAX-M10S"),
    ("Device:R", "R40", "4.7k", (160, 80), "Various 0402", "Resistor_SMD:R_0402_1005Metric"),
    ("Device:R", "R41", "4.7k", (170, 80), "Various 0402", "Resistor_SMD:R_0402_1005Metric"),
    ("Device:Antenna", "AE2", "GPS Patch", (180, 100), "CGGBP.25.4.A.02", "Antenna:Taoglas_CGGBP.25.4.A.02"),
    # LCD + QSPI
    ("Connector_Generic:Conn_01x10", "J5", "LCD FPC", (100, 100), "5051100892", "Connector_Molex:Molex_505110-0892_1x10-1MP_P0.50mm_Vertical"),
    ("FreedomUnit:MX25R6435F", "U7", "64M QSPI", (200, 150), "MX25R6435F", "Package_SON:WSON-8-1EP_6x5mm_P1.27mm_EP3.4x4.3mm"),
    ("Connector_Generic:Conn_01x04", "J6", "I2C Expansion", (100, 150), "Samtec TSW", "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"),
]

periph_labels = [
    global_label("V3P3_PERIPH", (100, 90)),
    global_label("GND", (100, 220)),
    global_label("GPS_SDA", (160, 90)),
    global_label("GPS_SCL", (170, 90)),
    global_label("LCD_SCLK", (110, 90)),
    global_label("LCD_MOSI", (120, 90)),
    global_label("LCD_CS", (130, 90)),
    global_label("BTN_A", (125, 170)),
    global_label("BTN_B", (140, 170)),
]

content = f"""(kicad_sch
  (version 20240108)
  (generator "Gemini CLI")
  (generator_version "1.1")
  (uuid "{get_uuid()}")
  (paper "A4")
  (title_block
    (title "Sheet 5 — Peripherals Architecture")
    (company "GarageAGI LLC")
    (rev "V2.2")
    (date "2026-03-03")
  )
{"".join([symbol(*s) for s in periph_symbols])}
{"".join([l for l in periph_labels])}
)"""

with open("FreedomUnit_V2/Sheet5_Peripherals.kicad_sch", "w", encoding='utf-8') as f:
    f.write(content)
print("Generated Sheet5_Peripherals.kicad_sch with debounce, LED resistors, and I2C pull-ups.")
