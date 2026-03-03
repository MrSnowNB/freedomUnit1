# GEMINI.md — Freedom Unit KiCad Project (Updated)

## Project Context
You are building KiCad 8 project files for the Freedom Unit V2, a 4-layer 80x50mm LoRa mesh node PCB.

## Technical Mandates
- **File Formats:** `.kicad_pro` MUST be JSON. `.kicad_sch` MUST be S-expression.
- **Encoding:** All files MUST be written in UTF-8.
- **Connectivity:** Every component must have Nets or Labels. Use Hierarchical Labels for inter-sheet busing (SPI, I2C).
- **Passives:** NEVER omit decoupling caps (100nF/1uF per VDD/DEC pin), I2C pull-ups (4.7k), or button debounce (100nF).
- **RF Rules:** 50Ω microstrip for BLE. Lambda62 handles LoRa RF internally (u.FL). No copper under antennas.

## Pin Assignment Table (Source of Truth)
| Signal | nRF52840 Pin | Function |
|--------|-------------|----------|
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
- All symbols must have an `mpn` property.
