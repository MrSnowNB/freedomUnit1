# GEMINI.md — Freedom Unit KiCad Project

## Project Context
You are building KiCad 9 project files for the Freedom Unit V2, a 4-layer 80x50mm LoRa mesh node PCB.

## Technical Mandates
- **Target EDA:** KiCad 9.0 (`.kicad_sch` version 20231120)
- **File Formats:** `.kicad_pro` MUST be JSON. `.kicad_sch` and `.kicad_pcb` MUST be S-expression.
- **Encoding:** All files MUST be UTF-8.
- **Connectivity:** Every component must have Nets or Labels. Use global labels for inter-sheet busing (SPI, I2C, power rails).
- **Passives:** NEVER omit decoupling caps (100nF/1uF per VDD/DEC pin), I2C pull-ups (4.7k), or button debounce (100nF).
- **RF Rules:** 50-ohm microstrip for BLE. Lambda62 handles LoRa RF internally (u.FL). No copper under antennas.

## Critical KiCad S-Expression Rules
These rules were discovered through multiple failed generation attempts. Violating any of them will cause KiCad to reject the file.

1. **lib_symbols parent/child naming:** Parent symbol uses `(symbol "Library:Name" ...)`. Child sub-symbols use BARE name only: `(symbol "Name_0_1" ...)` and `(symbol "Name_1_1" ...)`. NEVER put the `Library:` prefix on child sub-symbols.
2. **No `extends` keyword:** Every component needs a full standalone definition in the `(lib_symbols ...)` block. Do NOT use `(extends ...)`.
3. **Power symbols:** Must include the `(power)` flag and proper `_0_1` / `_1_1` sub-symbol structure.
4. **Instance paths:** Must be `/{root_uuid}/{sheet_uuid}` format. The root UUID is the uuid from the root `.kicad_sch`, and the sheet UUID is the uuid of the `(sheet ...)` block in the root schematic that references this sub-sheet.
5. **Y-axis convention:** Symbol coordinates: Y increases upward. Schematic coordinates: Y increases downward. Pin absolute position: `abs_y = symbol_center_y - relative_pin_y`.
6. **Pin convention:** `(at px py angle)` gives the ELECTRICAL connection point. The body extends inward by `length`.
7. **Float cleanup:** Python float arithmetic produces artifacts (e.g., `10.000000000000002`). Round all coordinates to reasonable precision.

## UUID Convention
- Root: `00000000-0000-0000-0000-000000000001`
- Sheet1_MCU: `...0002`
- Sheet3_Power: `...0003`
- Sheet5_Peripherals: `...0004`
- Sheet2_LoRa: `...0005`
- Sheet4_USB: `...0006`

## Pin Assignment Table (Source of Truth)
| Signal | nRF52840 Pin | Function |
|---|---|---|
| SPI_SCK | P0.19 | LoRa SCK |
| SPI_MOSI | P0.22 | LoRa MOSI |
| SPI_MISO | P0.23 | LoRa MISO |
| LORA_CS | P0.24 | LoRa NSS |
| LORA_DIO1 | P0.20 | LoRa IRQ |
| LORA_BUSY | P0.17 | LoRa BUSY |
| LORA_RESET | P0.25 | LoRa RESET |
| LORA_RXEN | P1.06 | RF Switch RX |
| LORA_TXEN | P1.07 | RF Switch TX |
| LCD_SCLK | P0.31 | LCD SCK |
| LCD_MOSI | P0.29 | LCD SI |
| LCD_CS | P0.30 | LCD SCS |
| GPS_SDA | P0.26 | I2C Data |
| GPS_SCL | P0.27 | I2C Clock |
| POWER_EN | P0.12 | Load Switch EN |
| BTN_A | P1.00 | Primary User Button |
| BTN_B | P1.01 | Back Button |

## MacroFab Requirements
- Gerber RS-274X (No X2).
- Separate PTH/NPTH drill files.
- XYRS origin: Bottom-left of board bounding box.
- All symbols must have an `mpn` (Manufacturer Part Number) property matching the BOM exactly.
