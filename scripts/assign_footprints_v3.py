import os
import re

FOOTPRINT_MAPPING = {
    "MCU_Nordic:nRF52840": "Package_DFN_QFN:Nordic_AQFN-73-1EP_7x7mm_P0.5mm",
    "FreedomUnit:Lambda62C-9S": "FreedomUnit:Lambda62C-9S",
    "RF_GPS:MAX-M10S": "RF_GPS:u-blox_MAX-M10S",
    "FreedomUnit:BQ25504": "Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.1x1.1mm",
    "Battery_Management:BQ25504": "Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.1x1.1mm",
    "Battery_Management:MCP73831-2-OT": "Package_TO_SOT_SMD:SOT-23-5",
    "FreedomUnit:TPS7A02": "Package_TO_SOT_SMD:SOT-23-5",
    "FreedomUnit:TPS22918": "Package_TO_SOT_SMD:SOT-23-5",
    "FreedomUnit:TPD2E001": "Package_TO_SOT_SMD:SOT-23-5",
    "FreedomUnit:MX25R6435F": "Package_SON:WSON-8-1EP_6x5mm_P1.27mm_EP3.4x4.3mm",
    "FreedomUnit:CONSMA006.062": "FreedomUnit:CONSMA006.062",
    "Device:Antenna_Chip": "Antenna:Johanson_2450AT18D0100",
    "Device:Antenna": "Antenna:Taoglas_CGGBP.25.4.A.02",
    "Device:Crystal": "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
    "Device:Crystal_Small": "Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm",
    "Device:Battery_Cell": "Battery:BatteryHolder_Keystone_1042_1x18650",
    "Switch:SW_SPDT": "Button_Switch_SMD:SW_SPDT_CK_JS102011SAQN",
    "Switch:SW_Push": "Button_Switch_SMD:SW_SPST_PTS636",
    "Connector:USB_C_Receptacle_USB2.0_16P": "Connector_USB:USB_C_Receptacle_GCT_USB4085",
    "Connector_Generic:Conn_01x02": "Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal",
    "Connector_Generic:Conn_01x04": "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
    "Connector_Generic:Conn_01x10": "Connector_Molex:Molex_505110-0892_1x10-1MP_P0.50mm_Vertical",
    "Diode:BAT54J": "Diode_SMD:D_SOD-323",
    "Device:LED": "LED_SMD:LED_0603_1608Metric",
    "Device:C": "Capacitor_SMD:C_0402_1005Metric",
    "Device:R": "Resistor_SMD:R_0402_1005Metric",
    "Device:L": "Inductor_SMD:L_0402_1005Metric",
}

def process_file(filepath):
    print(f"Processing {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = content
    
    # KiCad 9 symbol instances usually have (property "Footprint" "" ...)
    # Let's find each symbol block and its lib_id
    
    # We'll search for (symbol ... (lib_id "...") ... (property "Footprint" "" ...) ...)
    # Non-greedy match for symbol block
    pattern = re.compile(r'\(symbol\s+\(lib_id\s+"([^"]+)"\).*?\(property\s+"Footprint"\s+""', re.DOTALL)
    
    # We need to use finditer and replace from end to start to maintain indices
    matches = list(pattern.finditer(content))
    for match in reversed(matches):
        lib_id = match.group(1)
        footprint = FOOTPRINT_MAPPING.get(lib_id)
        
        if not footprint:
            # Try generic mappings
            if ':' in lib_id:
                lib, name = lib_id.split(':')
                # Try Lib:BasePart (e.g. Device:C_Small -> Device:C)
                footprint = FOOTPRINT_MAPPING.get(f"{lib}:{name.split('_')[0]}")
                if not footprint:
                    # Try just Lib:FirstChar (e.g. Device:C -> Device:C)
                    footprint = FOOTPRINT_MAPPING.get(f"{lib}:{name[0]}")

        if footprint:
            start, end = match.span()
            # Replacement: symbol_block_start with the empty footprint replaced
            # The match ends exactly at (property "Footprint" ""
            # So we replace the last two characters "" with the footprint
            new_content = new_content[:end-1] + footprint + new_content[end-1:]
            
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

SCHEMATICS = [
    "C:/Users/AMD/Desktop/FreedomUnit_V2/Sheet1_MCU.kicad_sch",
    "C:/Users/AMD/Desktop/FreedomUnit_V2/Sheet2_LoRa.kicad_sch",
    "C:/Users/AMD/Desktop/FreedomUnit_V2/Sheet3_Power.kicad_sch",
    "C:/Users/AMD/Desktop/FreedomUnit_V2/Sheet4_USB.kicad_sch",
    "C:/Users/AMD/Desktop/FreedomUnit_V2/Sheet5_Peripherals.kicad_sch",
]

for sch in SCHEMATICS:
    if os.path.exists(sch):
        process_file(sch)
    else:
        print(f"File not found: {sch}")
