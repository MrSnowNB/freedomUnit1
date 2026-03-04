#!/usr/bin/env python3
"""Assign footprints to schematic components based on lib_id mapping.

Usage: python assign_footprints.py [project_dir]
  project_dir defaults to the repo root (two levels up from this script).

This script finds all (property "Footprint" "") entries in .kicad_sch files
and fills them in based on the FOOTPRINT_MAPPING dictionary.
"""
import os
import re
import sys

FOOTPRINT_MAPPING = {
    # MCU
    "MCU_Nordic:nRF52840": "Package_DFN_QFN:Nordic_AQFN-73-1EP_7x7mm_P0.5mm",
    # LoRa
    "FreedomUnit:Lambda62C-9S": "FreedomUnit:Lambda62C-9S",
    # GPS
    "RF_GPS:MAX-M10S": "RF_GPS:u-blox_MAX-M10S",
    # Power ICs
    "FreedomUnit:BQ25504": "Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.1x1.1mm",
    "Battery_Management:BQ25504": "Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.1x1.1mm",
    "Battery_Management:MCP73831-2-OT": "Package_TO_SOT_SMD:SOT-23-5",
    "FreedomUnit:TPS7A02": "Package_TO_SOT_SMD:SOT-23-5",
    "FreedomUnit:TPS22918": "Package_TO_SOT_SMD:SOT-23-5",
    # USB ESD
    "FreedomUnit:TPD2E001": "Package_TO_SOT_SMD:SOT-23-5",
    # Flash
    "FreedomUnit:MX25R6435F": "Package_SON:WSON-8-1EP_6x5mm_P1.27mm_EP3.4x4.3mm",
    # Connectors
    "FreedomUnit:CONSMA006.062": "FreedomUnit:CONSMA006.062",
    "Connector:USB_C_Receptacle_USB2.0_16P": "Connector_USB:USB_C_Receptacle_GCT_USB4085",
    "Connector_Generic:Conn_01x02": "Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal",
    "Connector_Generic:Conn_01x04": "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
    "Connector_Generic:Conn_01x10": "Connector_FFC-FPC:Molex_54548-1071_1x10-1MP_P0.5mm_Horizontal",
    # Antennas
    "Device:Antenna_Chip": "RF_Antenna:Johanson_2450AT18D0100",
    "Device:Antenna": "RF_Antenna:Taoglas_CGGBP.25.4.A.02",
    # Crystals
    "Device:Crystal": "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
    "Device:Crystal_Small": "Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm",
    # Battery / Switch
    "Device:Battery_Cell": "Battery:BatteryHolder_Keystone_1042_1x18650",
    "Switch:SW_SPDT": "Button_Switch_SMD:SW_SPDT_CK_JS102011SAQN",
    "Switch:SW_Push": "Button_Switch_SMD:SW_SPST_PTS636",
    # Diodes / LEDs
    "Diode:BAT54J": "Diode_SMD:D_SOD-323",
    "Device:LED": "LED_SMD:LED_0603_1608Metric",
    # Passives (0402)
    "Device:C": "Capacitor_SMD:C_0402_1005Metric",
    "Device:R": "Resistor_SMD:R_0402_1005Metric",
    "Device:L": "Inductor_SMD:L_0402_1005Metric",
}


def process_file(filepath):
    print(f"Processing {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = content
    pattern = re.compile(
        r'\(symbol\s+\(lib_id\s+"([^"]+)"\).*?\(property\s+"Footprint"\s+""',
        re.DOTALL
    )

    matches = list(pattern.finditer(content))
    replaced = 0
    for match in reversed(matches):
        lib_id = match.group(1)
        footprint = FOOTPRINT_MAPPING.get(lib_id)

        if not footprint and ':' in lib_id:
            lib, name = lib_id.split(':')
            footprint = FOOTPRINT_MAPPING.get(f"{lib}:{name.split('_')[0]}")
            if not footprint:
                footprint = FOOTPRINT_MAPPING.get(f"{lib}:{name[0]}")

        if footprint:
            start, end = match.span()
            new_content = new_content[:end-1] + footprint + new_content[end-1:]
            replaced += 1
        else:
            print(f"  WARNING: No footprint mapping for {lib_id}")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"  Assigned {replaced}/{len(matches)} footprints")


def main():
    if len(sys.argv) > 1:
        project_dir = sys.argv[1]
    else:
        project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

    schematics = [
        os.path.join(project_dir, f"Sheet{i}_{name}.kicad_sch")
        for i, name in [(1, "MCU"), (2, "LoRa"), (3, "Power"), (4, "USB"), (5, "Peripherals")]
    ]

    for sch in schematics:
        if os.path.exists(sch):
            process_file(sch)
        else:
            print(f"File not found: {sch}")


if __name__ == "__main__":
    main()
