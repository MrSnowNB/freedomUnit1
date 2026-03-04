---
title: "Freedom Unit — PCB Board Layout Design"
version: "2.2"
date: "2026-03-03"
author: "GarageAGI LLC / Mindtech Mesh Networks"
project: "Liberty Mesh — Layer 1"
status: "Design Finalized — Ready for KiCad Entry"
target_fab: "OSH Park (Portland, OR)"
target_assembly: "MacroFab (Houston, TX)"
firmware: "Protocol-agnostic — Meshtastic (default), LoRaWAN, Reticulum, MeshCore"
license: "Open Hardware"
changelog: |
  v2.2 — Supply chain audit and BOM completion. Five new BOM entries added:
         32.768 kHz LFXO crystal (Abracon, Spicewood TX), 18650 battery holder
         (Keystone, New Hyde Park NY), JST-PH solar connector (JST, Japan),
         SMA edge-mount connector (TE/Linx, Merlin OR), Schottky OR-ing diode
         (STMicroelectronics, France). I2C external expansion header spec added.
         Three supply chain violations corrected (Amphenol CN → TE/Linx USA,
         Nexperia HK → STMicro France, onsemi CN → STMicro France).
         variant.h reference updated to V3. All 14 cross-reference issues resolved.
  v2.1 — Multi-protocol positioning update. Freedom Unit is now
         protocol-agnostic: Meshtastic (default), LoRaWAN, Reticulum,
         MeshCore — all on the same SX1262 + nRF52840 hardware.
         Firmware section expanded with per-protocol notes.
         Design philosophy updated: "Variety = Resilience."
  v2.0 — Full architecture rewrite. Lambda62C-9S replaces bare SX1262.
         Board enlarged to 80x50mm. BLE antenna added. 32 MHz crystal
         added (mandatory). USB-C charge IC added (MCP73831) with OR-ing
         diode for solar coexistence. Load switch (TPS22918) added.
         GPS patch antenna on-board. QSPI flash kept, pins reassigned
         to avoid USB conflict. Physical slide switch for hard battery
         disconnect. One PCB, three software-configurable roles.
         12 architecture issues resolved. 6 critical decisions incorporated.
---

# Freedom Unit V2 — PCB Board Layout Design

> Phase 2 American-allied replacement for Chinese Heltec/LILYGO nodes.  
> Protocol-agnostic LoRa platform — firmware determines protocol.  
> Supports: Meshtastic (default), LoRaWAN, Reticulum, MeshCore.  
> 30 units for Lawrence Township, NJ — target Spring 2027.  
> One PCB, three roles: Handheld / Repeater / Anchor — set in software.  
> One radio, one protocol at a time. Variety = Resilience.

---

## Design Philosophy

- **One PCB, three roles.** The board is identical for all deployments. Role (Handheld, Repeater, Anchor) is configured in firmware. Only the power input (battery/solar/USB), antenna choice (SMA whip vs. external), and 3D-printed enclosure differ per role. End-user configurable.
- **Protocol-agnostic.** The SX1262 radio and nRF52840 processor are firmware-defined. The same hardware runs Meshtastic, LoRaWAN, Reticulum, or MeshCore — flash via USB-C. One radio runs one protocol at a time, but a 30-node network can mix protocols across identical hardware.
- **Zero Chinese components at any level.** Every IC, module, passive, connector, and antenna traces back to USA, NATO, or Treaty-allied origins. No exceptions.
- **Physical security.** A slide switch hard-disconnects the battery from all circuits. No software bypass possible. If the switch is OFF, the device is dead.

---

## Board Overview

| Parameter | Spec |
|-----------|------|
| Board dimensions | 80 mm x 50 mm (up from 60x45 — accommodates GPS patch antenna + new components) |
| Layer count | 4-layer (ground plane integrity under nRF52840 and Lambda62 module) |
| Stackup | Signal / GND / Power / Signal |
| Substrate | FR4, Tg 170+, 1.6 mm thickness |
| Surface finish | ENIG (IPC-4552 gold, per OSH Park standard) |
| Copper weight | 1 oz outer, 0.5 oz inner |
| Min trace/space | 6 mil / 6 mil |
| RF trace impedance | 50 Ω microstrip (BLE antenna feed only — LoRa handled inside Lambda62 module) |
| Operating temp | -40°C to +85°C (industrial / mil-spec grade) |
| Supply voltage | 3.3V regulated from battery via LDO, peripheral rail via load switch |

---

## Block Diagram

```
                            ┌────────────────────────────────┐
                            │     PHYSICAL SLIDE SWITCH      │
                            │   C&K JS102011SAQN (SPDT)      │
                            │   Hard battery disconnect       │
                            │   No software bypass possible   │
                            └──────────────┬─────────────────┘
                                           │ Switched VBAT
                ┌──────────────────────────┼──────────────────────────┐
                │                          │                          │
    ┌───────────▼──────────┐   ┌──────────▼──────────┐   ┌──────────▼──────────┐
    │  SOLAR PANEL (6V)    │   │  USB-C (5V VBUS)    │   │ Panasonic NCR18650B │
    │  JST-PH 2-pin        │   │  GCT USB4085-GF-A   │   │ 3.7V, 3400 mAh     │
    └──────────┬───────────┘   │  + TPD2E001 ESD      │   │ Protected cell      │
               │               │  + 5.1kΩ CC pulldowns│   └──────────┬──────────┘
               │               └──────────┬───────────┘              │
               │                          │ VBUS 5V                  │
    ┌──────────▼───────────┐   ┌──────────▼───────────┐              │
    │ TI BQ25504            │   │ Microchip MCP73831   │              │
    │ Solar Energy Harvester│   │ USB Li-Ion Charger   │              │
    │ MPPT @ 80% VOC       │   │ 500 mA programmable  │              │
    │ Cold start: 600 mV   │   │ Chandler, AZ USA     │              │
    └──────────┬───────────┘   └──────────┬───────────┘              │
               │ VBAT charge               │ VBAT charge              │
               │                           │                          │
               └─────────┐   ┌────────────┘                          │
                         │   │                                        │
                    ┌────▼───▼──┐   STMicro BAT54JFILM               │
                    │  OR Gate   │   Schottky OR-ing diode            │
                    │ (Diode OR) │◄──────────────────────────────────┘
                    └─────┬──────┘   Both charge paths feed battery
                          │ VBAT (3.0V–4.2V)
                          │
              ┌───────────▼────────────┐
              │  TI TPS7A02 LDO        │
              │  3.3V output, 200 mA   │
              │  IQ: 25 nA             │
              └───┬────────────────────┘
                  │ 3.3V (always on)
                  │
     ┌────────────┼──────────────────────────────────┐
     │            │                                   │
     │   ┌────────▼──────────┐              ┌────────▼──────────┐
     │   │  nRF52840 (MCU)   │              │  TI TPS22918      │
     │   │  + 32 MHz crystal │   P0.12 ──►  │  Load Switch      │
     │   │  + 32.768kHz LFXO │   (POWER_EN) │  2A, 1 µA IQ      │
     │   │  + BLE chip ant.  │              └────────┬───────────┘
     │   │  + Macronix QSPI  │                       │ 3.3V switched
     │   └───────────────────┘                       │
     │                                    ┌──────────┼──────────────┐
     │                                    │          │              │
     │                         ┌──────────▼──┐ ┌────▼─────┐ ┌─────▼──────────┐
     │                         │ Lambda62C-9S│ │ MAX-M10S │ │ Peripherals    │
     │                         │ (LoRa)      │ │ (GPS)    │ │                │
     │                         │ RF Solutions│ │ u-blox   │ │ Sharp LCD      │
     │                         │ Made in UK  │ │ Swiss    │ │ D-pad + Btns   │
     │                         │             │ │          │ │ Status LEDs    │
     │                         │ SPI0 to MCU │ │ I2C      │ │                │
     │                         │ +22 dBm     │ │          │ │                │
     │                         │ u.FL → SMA  │ │ Taoglas  │ │                │
     │                         │ TXEN/RXEN   │ │ GPS patch│ │                │
     │                         └─────────────┘ └──────────┘ └────────────────┘
     │
     └──► USB D+/D- to nRF52840 native USB (programming, debug, data)
```

---

## Pin Assignment Table (nRF52840 → All Peripherals)

Reference: LILYGO T-Echo variant.h + Lambda62C-9S datasheet + architecture review fixes.

### Lambda62C-9S LoRa Module (SPI0)

| Signal | nRF52840 Pin | Direction | Notes |
|--------|-------------|-----------|-------|
| SPI_SCK | P0.19 | OUT | SPI clock to Lambda62 |
| SPI_MOSI | P0.22 | OUT | SPI data to Lambda62 |
| SPI_MISO | P0.23 | IN | SPI data from Lambda62 |
| LORA_CS (NSS) | P0.24 | OUT | SPI chip select, active low |
| LORA_DIO1 | P0.20 | IN | Interrupt from SX1262 (TX/RX done) |
| LORA_BUSY | P0.17 | IN | SX1262 busy indicator |
| LORA_RESET | P0.25 | OUT | Hardware reset, active low |
| LORA_RXEN | P1.06 | OUT | Lambda62 RX_SWITCH (pin 4), active HIGH |
| LORA_TXEN | P1.07 | OUT | Lambda62 TX_SWITCH (pin 5), active HIGH |

**Critical notes — Lambda62 vs. bare SX1262:**
- The Lambda62C-9S contains the SX1262 + crystal + RF switch + matching network + harmonic filter inside a shielded module with u.FL connector
- DIO2 is NOT used as RF switch. The Lambda62 breaks out TX/RX switch control to two external pins (TXEN/RXEN). The nRF52840 must actively toggle these.
- DIO3 drives the internal TCXO at 1.8V — this is controlled via SPI register writes (`SX126X_DIO3_TCXO_VOLTAGE 1.8` in variant.h). DIO3 is NOT broken out to an external pin. Do not route P0.21 to the Lambda62 — P0.21 is now an unassigned free GPIO.
- `SX126X_DIO2_AS_RF_SWITCH` is REMOVED — replaced by `SX126X_RXEN` / `SX126X_TXEN`
- SPI clock: 8 MHz max
- FCC certified (FCC ID: P9OLAMBDA62) — inherit certification with approved antenna
- Runs on 3.3V from TPS7A02 LDO via TPS22918 load switch

### Sharp Memory LCD 1.3" LS013B7DH03 (SPI1)

| Signal | nRF52840 Pin | Direction | Notes |
|--------|-------------|-----------|-------|
| LCD_SCLK | P0.31 | OUT | SPI clock (separate SPI bus from LoRa) |
| LCD_MOSI (SI) | P0.29 | OUT | Serial data in to LCD |
| LCD_CS (SCS) | P0.30 | OUT | Chip select, active HIGH (unusual) |
| LCD_EXTCOMIN | P0.28 | OUT | COM inversion signal (toggle at 1 Hz) |
| LCD_DISP | P1.11 | OUT | Display on/off (tie HIGH to enable) |

**Critical notes:**
- Sharp Memory LCD uses active-HIGH chip select (opposite of most SPI devices)
- SPI Mode 0 (CPOL=0, CPHA=0), LSB first
- EXTCOMIN must toggle at ~1 Hz or the display will ghost — use a timer peripheral
- No MISO line — display is write-only. SPI1_MISO set to -1 in variant.h
- Connector: Molex 5051100892 (10-pin, 0.5mm pitch, ZIF FPC) — Molex, Lisle IL USA
- 96 x 96 pixels, monochrome, ultra-low power (~15 µW), sunlight readable
- variant.h defines: `HAS_SCREEN 1` and `USE_SHARP_MEMORY_DISPLAY`

### u-blox MAX-M10S GPS (I2C)

| Signal | nRF52840 Pin | Direction | Notes |
|--------|-------------|-----------|-------|
| GPS_SDA | P0.26 | I/O | I2C data (shared bus + external header) |
| GPS_SCL | P0.27 | I/O | I2C clock (shared bus + external header) |
| GPS_PPS | P1.04 | IN | 1 PPS timing pulse |
| GPS_RESET | P1.05 | OUT | Hardware reset |
| GPS_EXTINT | P1.02 | OUT | Wake from backup mode |

**Critical notes:**
- I2C address: 0x42 (fixed, all u-blox modules)
- Requires EXTERNAL 4.7 kΩ pull-ups on SDA/SCL to 3.3V — do NOT rely on nRF52840 internal pull-ups (~13 kΩ, too weak for 400 kHz). Disable internal pull-ups in firmware.
- Supports GPS, GLONASS, Galileo, BeiDou simultaneously
- Ultra-low power: 12 mW tracking, 27 mW acquisition
- **On-board GPS antenna:** Taoglas CGGBP.25.4.A.02 (25x25mm ceramic patch, Ireland)
- GPS patch placed on opposite end of PCB from LoRa SMA (1575 MHz vs 915 MHz isolation)
- Solid ground plane underneath GPS antenna on layer 2
- Repeater variant: optional u.FL footprint for external active GPS antenna on pole
- I2C has clock stretching — set nRF52840 TWIM to handle it

### I2C External Expansion Header

| Pin | Signal | Notes |
|-----|--------|-------|
| 1 | SDA | P0.26 — shared with GPS I2C bus |
| 2 | SCL | P0.27 — shared with GPS I2C bus |
| 3 | 3.3V | From TPS22918 switched rail (peripherals must be powered) |
| 4 | GND | Ground reference |

**Spec:** 4-pin, 2.54mm (0.1") pitch header. Through-hole, right-angle or vertical. Standard 0.1" pin header (Samtec TSW or equivalent).

**Purpose:** Future sensor expansion (temperature, humidity, air quality, etc.). Not populated on initial 30-unit run — deferred until business partners (Dave, Ken Kiernan) decide otherwise. Footprint must be on the PCB for future use. The 4.7 kΩ I2C pull-ups are shared with GPS and already present.

### BLE Antenna (nRF52840 2.4 GHz Radio)

| Signal | nRF52840 Pin | Direction | Notes |
|--------|-------------|-----------|-------|
| BLE_ANT | ANT pin (dedicated) | RF | 50 Ω microstrip to matching network → chip antenna |

**Components:**
- Chip antenna: Johanson 2450AT18D0100 (1.2x2.0mm, 0805) — Camarillo, CA USA
- Pi matching network: L ~3.9 nH + C ~0.8 pF + C ~0.5 pF (0402) — values per Nordic reference design Config-2, final tune with VNA on first prototype
- Ground plane keep-out zone: ~5 mm around chip antenna at board edge
- Place on opposite end of board from LoRa SMA antenna

### nRF52840 Clocks

| Signal | nRF52840 Pins | Notes |
|--------|--------------|-------|
| 32 MHz HFXO | XC1, XC2 | Abracon ABM8-32.000MHZ-B2-T (Spicewood, TX USA). MANDATORY. 2x 12 pF load caps. Place within 5 mm of XC1/XC2. Short symmetric traces. |
| 32.768 kHz LFXO | XL1, XL2 | Abracon ABS07-120-32.768KHZ-T (Spicewood, TX USA). For RTC / USE_LFXO. 2x 6 pF load caps. 3.2x1.5mm package. -40°C to +85°C. Place within 5 mm of XL1/XL2. |

### User Interface — D-Pad + A/B Buttons

| Signal | nRF52840 Pin | Direction | Notes |
|--------|-------------|-----------|-------|
| BTN_UP | P1.10 | IN | D-pad up (C&K PTS636) |
| BTN_DOWN | P0.18 | IN | D-pad down |
| BTN_LEFT | P0.11 | IN | D-pad left |
| BTN_RIGHT | P0.06 | IN | D-pad right |
| BTN_CENTER | P0.08 | IN | D-pad center press (confirm/select) |
| BTN_A | P1.00 | IN | A button (SOS / primary action) |
| BTN_B | P1.01 | IN | B button (back / cancel) |

**Critical notes:**
- All buttons: active LOW with internal pull-up enabled in firmware
- Add 100 nF hardware debounce capacitor on each button line
- BTN_A (P1.00) maps to Meshtastic `PIN_BUTTON1` (primary user button)
- BTN_B (P1.01) maps to Meshtastic `PIN_BUTTON2`
- D-pad navigates canned messages: `!police` `!fire` `!ems` `!help` `I am OK`
- All buttons: C&K PTS636 series (USA distributor, mil-temp rated -40°C to +85°C)

### Status LEDs

| Signal | nRF52840 Pin | Direction | Notes |
|--------|-------------|-----------|-------|
| LED_RED | P0.14 | OUT | Fault / SOS active |
| LED_GREEN | P0.13 | OUT | Mesh connected / heartbeat |
| LED_BLUE | P0.15 | OUT | BLE connected / pairing |

**Notes:** Use low-current LEDs (2 mA) with 680 Ω series resistors. All active HIGH.

### Physical Slide Switch — Hard Battery Disconnect

| Signal | Connection | Notes |
|--------|-----------|-------|
| SWITCH COM | Battery + terminal | Common pin connected to battery positive |
| SWITCH NO | System VBAT rail | Normally-open contact feeds the rest of the board |

**Component:** C&K JS102011SAQN (SPDT slide switch)
- Rated 300 mA @ 6V DC — handles peak TX current (118 mA)
- -40°C to +85°C operating temp (mil-spec range)
- Through-hole mount for mechanical durability
- **Security feature:** When OFF, battery is physically disconnected from all circuits. No firmware, no radio, no leakage. Cannot be bypassed in software.
- Place accessible on enclosure — all three enclosure variants expose the switch

### Power Management

| Signal | nRF52840 Pin | Direction | Notes |
|--------|-------------|-----------|-------|
| BATTERY_ADC | P0.04 (AIN2) | IN | Battery voltage via 1:2 divider (100k/100k) |
| POWER_EN | P0.12 | OUT | TPS22918 load switch enable (peripheral power rail) |
| BQ25504_VBAT_OK | P0.16 | IN | Battery good flag from BQ25504 |

### QSPI Flash — Macronix MX25R6435F (Taiwan)

| Signal | nRF52840 Pin | Direction | Notes |
|--------|-------------|-----------|-------|
| QSPI_SCK | P1.14 | OUT | QSPI clock — NOTE: shares with USB D+, see note |
| QSPI_CS | P1.15 | OUT | QSPI chip select |
| QSPI_IO0 | P1.12 | I/O | QSPI data 0 (MOSI) |
| QSPI_IO1 | P1.13 | I/O | QSPI data 1 (MISO) — NOTE: shares with USB D-, see note |
| QSPI_IO2 | P0.07 | I/O | QSPI data 2 (WP) |
| QSPI_IO3 | P0.05 | I/O | QSPI data 3 (HOLD) |

**Critical notes on QSPI/USB pin sharing:**
- P1.13 and P1.14 are shared between QSPI and USB D-/D+ on the nRF52840
- The nRF52840 hardware MUX handles this — QSPI and USB are mutually exclusive peripherals at the silicon level
- During USB operation (plugged in): QSPI is disabled, flash not accessible
- During normal operation (unplugged): QSPI active, flash available for OTA/DFU storage
- This is the same approach used by the T-Echo and other nRF52840 boards with QSPI
- Macronix MX25R6435F: 64 Mbit, 1.65-3.6V, ultra-low power (8 µA read, 0.01 µA deep sleep)

### Programming / Debug

| Signal | nRF52840 Pin | Direction | Notes |
|--------|-------------|-----------|-------|
| USB_D+ | P1.14 (dedicated) | I/O | Native USB (shared with QSPI_SCK) |
| USB_D- | P1.13 (dedicated) | I/O | Native USB (shared with QSPI_IO1) |
| SWDIO | SWDIO | I/O | SWD debug/program |
| SWCLK | SWDCLK | IN | SWD clock |
| UART_TX | P1.08 | OUT | Debug serial (optional header) |
| UART_RX | P1.09 | IN | Debug serial (optional header) |

### USB-C Connector & Charging

**Connector:** GCT USB4085-GF-A (USB 2.0 Type-C receptacle) — GCT, UK/USA

**ESD Protection:** TI TPD2E001DRLR — dual-channel TVS on D+/D- (Dallas, TX)

**CC Identification:** 2x 5.1 kΩ resistors (0402) — CC1 and CC2 to GND. Required by USB-C spec for device/sink identification. Without these, the cable won't supply power.

**USB Charge IC:** Microchip MCP73831T (Chandler, AZ USA)
- Single-cell Li-Ion/Li-Po charger
- 500 mA charge current (set by PROG resistor: 2 kΩ for 500 mA)
- Charge status output — can route to LED or GPIO
- VBUS (5V) in → regulated charge current → battery
- OR-ing Schottky diode (STMicroelectronics BAT54JFILM) between MCP73831 output and BQ25504 VBAT output prevents backfeed between solar and USB charge paths
- Both chargers can be connected simultaneously — the diode OR ensures no conflict

---

## Power Architecture

### Dual-Path Charging: Solar + USB → Battery → System

```
                    PHYSICAL SLIDE SWITCH (C&K JS102011SAQN)
                    ┌─────────────────────────┐
  Battery (+) ─────►│ COM ──── NO ──── NC     │
                    └──────────┬──────────────┘
                               │ Switched VBAT (OFF = dead, no bypass)
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                    │
           │    ┌──────────────▼─────────────────┐  │
           │    │    Panasonic NCR18650B          │  │
           │    │    3.7V, 3400 mAh protected     │  │
           │    │    Keystone 1042P battery holder │  │
           │    └──────────────┬─────────────────┘  │
           │                   │                    │
           │         ┌─────── ─┤                    │
           │         │         │                    │
    ┌──────▼─────┐   │   ┌────▼──────┐             │
    │ BQ25504     │   │   │ BAT54J    │             │
    │ Solar MPPT  │───┘   │ Schottky  │◄────────────┘
    │ VIN ◄ Solar │       │ OR-ing    │   MCP73831 USB charge path
    │ VBAT_OK→MCU │       │ (STMicro) │
    └─────────────┘       └───────────┘
           │ (Solar charges battery through BQ25504)
           │ (USB charges battery through MCP73831)
           │ (Diode OR prevents backfeed between paths)
           │
    ┌──────▼────────────────────────────────────┐
    │  VBAT rail (3.0V–4.2V)                    │
    │                                            │
    │  ┌────────────────────────────────────┐    │
    │  │  TI TPS7A02 LDO Regulator          │    │
    │  │  3.3V output, 200 mA max           │    │
    │  │  IQ: 25 nA                          │    │
    │  │  Dropout: 100 mV @ 100 mA           │    │
    │  │  PSRR: 62 dB @ 1 kHz               │    │
    │  │  Input cap: 1 µF ceramic            │    │
    │  │  Output cap: 1 µF ceramic           │    │
    │  └───────┬────────────────────────────┘    │
    │          │ 3.3V (always on)                 │
    │          │                                   │
    │   ┌──────┼──────────────────┐                │
    │   │      │                  │                │
    │   │  ┌───▼───┐    ┌────────▼────────┐       │
    │   │  │nRF52840│    │ TI TPS22918     │       │
    │   │  │ (MCU)  │    │ Load Switch     │       │
    │   │  │ always │    │ EN ← P0.12      │       │
    │   │  │ on     │    │ 2A max, 1µA IQ  │       │
    │   │  └────────┘    └────────┬────────┘       │
    │   │                         │ 3.3V switched   │
    │   │              ┌──────────┼────────────┐    │
    │   │              │          │            │    │
    │   │         ┌────▼───┐ ┌───▼──────┐ ┌───▼──┐│
    │   │         │Lambda62│ │ MAX-M10S │ │ LCD  ││
    │   │         │LoRa    │ │ GPS      │ │Sharp ││
    │   │         └────────┘ └──────────┘ └──────┘│
    └───┴──────────────────────────────────────────┘
```

### Power Budget (Worst Case Active)

| Component | Active | Sleep | Notes |
|-----------|--------|-------|-------|
| nRF52840 | 5.3 mA | 1.5 µA | System ON, 64 MHz |
| Lambda62C-9S TX (+22 dBm) | 118 mA | 0.6 µA (cold sleep) | TX burst only |
| Lambda62C-9S RX | 4.6 mA | — | Listening window |
| Sharp LCD | 0.015 mA | 0.005 mA | Static display, no backlight |
| MAX-M10S GPS | 8.2 mA | 0.015 mA | Tracking / backup |
| MX25R6435F QSPI | 8 µA (read) | 0.01 µA | Deep power-down |
| BQ25504 | 0.330 µA | 0.330 µA | Always on, manages solar charging |
| MCP73831 | ~1.5 mA | — | Only active when USB VBUS present |
| TPS7A02 LDO | 0.025 µA | 0.025 µA | Always on |
| TPS22918 load switch | 1 µA | 0.01 µA | When ON / when OFF |
| LEDs (1 active) | 2 mA | 0 | Intermittent |
| **Total (active TX)** | **~138 mA** | — | Peak, momentary |
| **Total (mesh idle)** | **~10 mA** | — | RX windows + GPS tracking |
| **Total (deep sleep)** | — | **~2.5 µA** | Everything off except RTC + slide switch leakage (~0) |

**Battery life estimates (3400 mAh 18650):**
- Mesh idle (10 mA avg): ~14 days
- Mesh idle + solar (2.5W panel): effectively indefinite
- Deep sleep: ~155 years (theoretical)
- Slide switch OFF: zero drain (physically disconnected)

---

## Lambda62C-9S LoRa Module — Integration Notes

The Lambda62C-9S replaces the bare SX1262 and eliminates the entire RF matching/filter/balun design. This is the single biggest simplification from V1.

### What the Lambda62 contains internally
- Semtech SX1262 die
- TCXO crystal
- TX/RX RF switch (SKY13373 or similar)
- Impedance matching network (50 Ω at 915 MHz)
- Harmonic filter (2nd/3rd harmonic rejection)
- Metal shield can
- u.FL antenna connector

### What it removes from our BOM
- SX1262IMLTRT bare chip
- Standalone TCXO 32 MHz (for SX1262 — we still need the nRF52840 32 MHz crystal)
- DC-DC inductor 4.7 µH (SX1262 internal regulator)
- ~12 RF passive components (matching, balun, filter caps/inductors)
- All 50 Ω microstrip trace routing for LoRa
- Via stitching around LoRa RF section
- FCC certification testing (~$5K-$10K saved — we inherit Lambda62's FCC cert)

### PCB Layout for Lambda62
- Module footprint: 23 x 20 mm with castellated edge pads
- Place near board edge for short u.FL pigtail run to SMA bulkhead
- No special RF layout rules needed — the module handles all RF internally
- Standard digital traces from nRF52840 to module SPI/control pins
- Ground plane under module recommended but not critical (module has its own shield)
- u.FL to SMA pigtail cable connects to external antenna through enclosure

### RF Switch Control (TXEN/RXEN)
The Lambda62 requires the MCU to actively control TX/RX switching:
- Before TX: set TXEN HIGH, RXEN LOW
- Before RX: set RXEN HIGH, TXEN LOW
- Idle/Sleep: both LOW
- Meshtastic firmware supports this via `SX126X_RXEN` and `SX126X_TXEN` defines (same as RAK4631)

---

## BLE Antenna — Johanson 2450AT18D0100

The nRF52840's 2.4 GHz BLE radio needs its own antenna. Without this, users can't pair with the Meshtastic phone app.

### Layout requirements
- Chip antenna at board edge, opposite end from LoRa SMA connector
- Pi matching network (L ~3.9 nH, C ~0.8 pF, C ~0.5 pF) between nRF52840 ANT pin and antenna — values per Nordic reference design Config-2, final tune with VNA
- 50 Ω microstrip from ANT pin through matching to chip antenna
- Ground plane keep-out zone: ~5 mm around chip antenna
- No copper pour, traces, or components in the keep-out zone

---

## nRF52840 Decoupling — Complete Requirements

Per Nordic product specification, the nRF52840 QFN73 package requires specific decoupling on DEC pins (internal regulator outputs), not just VDD pins.

| Pin | Capacitor | Placement | Notes |
|-----|-----------|-----------|-------|
| Each VDD pin | 100 nF 0402 | Within 2 mm of pin | Standard bypass |
| VDD bulk | 1 µF 0402 | Near IC | Bulk bypass |
| VDDH | 4.7 µF 0402 | If using VDDH input | Battery direct to VDDH option |
| DEC1 | 100 nF 0402 | Within 2 mm, short GND trace | Internal 1.3V regulator — critical value |
| DEC4 | 1 µF 0402 | Within 2 mm, short GND trace | Internal regulator — critical value |
| DEC6 | 100 nF 0402 | Within 2 mm, short GND trace | Internal regulator |
| DECUSB | 4.7 µF + 100 nF | Near USB power pins | USB regulator (since we use USB) |

Wrong values or bad placement → internal regulators oscillate → random crashes, radio malfunction, excess current.

---

## BOM Summary

| Component | Part Number | Manufacturer | HQ / Origin | Notes |
|-----------|-------------|-------------|-------------|-------|
| MCU | nRF52840-QIAA | Nordic Semiconductor | Norway (NATO) | ARM Cortex-M4, BLE 5.0, CryptoCell-310, fab: TSMC Taiwan |
| LoRa Module | Lambda62C-9S | RF Solutions | West Sussex, UK (NATO) | SX1262 inside, +22 dBm, FCC cert, u.FL, Made in Britain |
| GPS | MAX-M10S-00B | u-blox | Switzerland (PfP) | I2C, multi-GNSS, ultra-low power |
| Display | LS013B7DH03 | Sharp | Sakai, Japan (Treaty) | 1.3" 96x96, memory LCD, 15 µW |
| LCD Connector | 5051100892 | Molex | Lisle, IL USA | 10-pin, 0.5mm pitch, ZIF FPC |
| Solar Charger | BQ25504RGTR | Texas Instruments | Dallas, TX USA | MPPT energy harvester, 330 nA IQ |
| USB Charge IC | MCP73831T | Microchip | Chandler, AZ USA | Single-cell Li-Ion, 500 mA, PROG resistor set |
| LDO Regulator | TPS7A0233DBVR | Texas Instruments | Dallas, TX USA | 3.3V, 200 mA, 25 nA IQ |
| Load Switch | TPS22918DBVR | Texas Instruments | Dallas, TX USA | 2A, 1 µA IQ, SOT-23-5 |
| USB ESD | TPD2E001DRLR | Texas Instruments | Dallas, TX USA | Dual TVS for USB D+/D- |
| LoRa Antenna | TG.09.0113 | Taoglas | Ireland (NATO) | 915 MHz, SMA edge-mount |
| BLE Antenna | 2450AT18D0100 | Johanson Technology | Camarillo, CA USA | 2.4 GHz chip antenna, 0805 |
| GPS Antenna | CGGBP.25.4.A.02 | Taoglas | Ireland (NATO) | 25x25mm ceramic GPS patch |
| 32 MHz Crystal | ABM8-32.000MHZ-B2-T | Abracon | Spicewood, TX USA | nRF52840 HFXO, mandatory, 2x 12 pF load caps |
| 32.768 kHz Crystal | ABS07-120-32.768KHZ-T | Abracon | Spicewood, TX USA | nRF52840 LFXO/RTC, 2x 6 pF load caps, 3.2x1.5mm, -40/+85°C |
| QSPI Flash | MX25R6435F | Macronix | Taiwan (Treaty) | 64 Mbit, ultra-low power, for OTA/DFU |
| Battery | NCR18650B | Panasonic | Japan (Treaty) | 3.7V, 3400 mAh protected |
| Battery Holder | 1042P | Keystone Electronics | New Hyde Park, NY USA | SMT 18650 holder, phosphor bronze contacts |
| Slide Switch | JS102011SAQN | C&K | USA | SPDT, 300 mA, hard battery disconnect |
| Buttons (x7) | PTS636 series | C&K | USA | Tactile, mil-temp rated -40°C to +85°C |
| USB-C Connector | USB4085-GF-A | GCT | UK/USA | USB 2.0 Type-C receptacle |
| SMA Connector | CONSMA006.062 | TE Connectivity / Linx | Merlin, OR USA | SMA jack, edge-mount, 50 Ω, MIL-STD-202, -65/+165°C, brass/gold |
| Solar Connector | S2B-PH-K-S(LF)(SN) | JST | Japan (Treaty) | 2-pin JST-PH, 2mm pitch, THT right-angle, for solar panel input |
| OR-ing Diode | BAT54JFILM | STMicroelectronics | France (NATO) | Schottky, 40V 300mA, SOD-323, COO: France. Prevents backfeed between solar/USB charge paths |
| Passives | Various 0402/0603 | Various | — | Resistors, capacitors, decoupling, matching |

**Supply chain: Zero Chinese components. Zero Chinese assembly. 100% USA + NATO/Treaty Allied.**

---

## PCB Fabrication & Assembly

### OSH Park (Portland, OR) — PCB Fab

- 4-layer board
- 80 mm x 50 mm = ~6.2 sq in
- IPC-4552 ENIG surface finish (mil-spec gold plating)
- FR4, Tg 170+ (industrial temperature grade)
- 6/6 mil trace/space standard
- Controlled impedance available on request (for BLE 50 Ω trace)
- Turnaround: ~12 business days

### MacroFab (Houston, TX) — Assembly

- Upload KiCad Gerbers + BOM + pick-and-place file
- Mixed SMD + through-hole supported (slide switch, SMA, JST-PH, battery holder are TH)
- Low-volume friendly: 30 units is within their sweet spot
- Component sourcing through DigiKey/Mouser partnerships
- DFM check included in quoting process
- VNA tuning for BLE matching network available on first prototype

---

## Mechanical / Enclosure

| Parameter | Spec |
|-----------|------|
| PCB footprint | 80 mm x 50 mm |
| Enclosure | 3D printed (PETG or ASA for outdoor) |
| IP rating target | IP65 (weatherproof for repeater nodes) |
| Mounting | M2.5 standoffs, 4 corners |
| LoRa Antenna | SMA bulkhead through enclosure wall |
| GPS Antenna | On-board ceramic patch — position enclosure lid with GPS-transparent window (clear PETG or no metal above patch) |
| Battery access | Slide-out tray or snap-fit lid |
| Slide switch access | Exposed on enclosure side panel (all variants) |
| Button access | Silicone membrane over tactile switches |
| Display window | Clear PETG or polycarbonate cutout |
| Label | Mindtech Mesh Networks branding |
| Printing location | NJ (local 3D printer) |

### Enclosure Variants (Same PCB — Different Case + Power + Antenna)

1. **Handheld (citizen)**: Pocket-sized, D-pad + screen visible, slide switch on side, lanyard hole, rubber duck 915 MHz antenna on SMA, battery powered
2. **Repeater (solar)**: Weatherproof box, SMA pigtail to external directional/omni antenna, solar panel JST-PH input, optional u.FL for external active GPS, slide switch accessible through sealed port, pole/mast mount
3. **Anchor (hub)**: Indoor, USB-C powered (charges battery as backup), connects to The Operator SFF box, slide switch on back, desktop or wall mount

---

## Firmware — Multi-Protocol Support

The Freedom Unit is a protocol-agnostic platform. The SX1262 transmits on 915 MHz CSS regardless of which protocol stack runs on the nRF52840. Firmware is flashed via USB-C.

### Supported Protocols

| Protocol | Topology | Use Case | Status |
|----------|----------|----------|--------|
| Meshtastic | P2P flood mesh | Default. SOS dispatch, citizen mesh, GPS tracking | Primary — variant.h ready |
| LoRaWAN | Star (gateway) | Sensor backhaul, municipal IoT, ChirpStack self-hosted | Planned — same SX1262 driver |
| Reticulum | Encrypted mesh | Voice via Codec2, cryptographic identity, private comms | Planned — nRF52840 capable |
| MeshCore | Route-aware mesh | Efficient routing, large/dense deployments, MIT licensed | Planned — same SX1262 driver |

**Key constraint:** One radio = one protocol at a time. A 30-node network can mix (e.g., 20 Meshtastic + 5 Reticulum + 5 LoRaWAN) but each individual unit runs one firmware.

### Meshtastic variant.h (Default Firmware)

See companion file: `Freedom-Unit-variant-v3.h`

Key defines for the Freedom Unit V3:
- `#define PRIVATE_HW` (custom hardware flag)
- `#define USE_SX1262`
- `#define SX126X_RXEN` / `#define SX126X_TXEN` (Lambda62 RF switch control)
- `#define SX126X_DIO3_TCXO_VOLTAGE 1.8` (SPI register config — no GPIO pin)
- `#define HAS_GPS 1`
- `#define GPS_UBLOX`
- `#define HAS_SCREEN 1`
- `#define USE_SHARP_MEMORY_DISPLAY`
- `#define PIN_BUTTON1` → BTN_A (P1.00), `#define PIN_BUTTON2` → BTN_B (P1.01)
- `#define EXTERNAL_FLASH_DEVICES MX25R6435F`
- `#define EXTERNAL_FLASH_USE_QSPI`
- Battery ADC on AIN2 with voltage divider calibration
- NFC pins disabled via `CONFIG_NFCT_PINS_AS_GPIOS=y` in prj.conf
- External 4.7 kΩ I2C pull-ups (disable internal pull-ups)
- 4 unassigned GPIO: P0.09, P0.10, P0.21, P1.03

### LoRaWAN Notes
- ChirpStack (self-hosted) recommended over TTN for Liberty Mesh
- Potential gateway hardware: MultiTech Conduit (American-made, Mounds View, MN)
- Same SX1262 SPI interface — LoRaWAN MAC stack replaces Meshtastic mesh stack
- Device classes A/B/C all supported by SX1262 hardware

### Reticulum Notes
- Cryptographic identity per node (Ed25519 keypairs)
- Voice over LoRa via Codec2 at 1200 bps — nRF52840 has sufficient CPU for software vocoder
- Reference implementation: github.com/dudmuck/lora_codec2 (STM32F4 + SX1262)
- No central server dependency

### MeshCore Notes
- MIT-licensed, route-aware mesh (nodes learn topology vs. flood)
- Lower airtime than Meshtastic in dense networks
- Same SX1262 SPI driver, different routing logic
- github.com/ripplebiz/MeshCore

---

## KiCad Project Setup

### Getting Started

1. Install KiCad 8 (free, open source): https://www.kicad.org/download/
2. Create new project: `FreedomUnit_V2`
3. Set design rules:
   - Min trace width: 0.15 mm (6 mil)
   - Min clearance: 0.15 mm (6 mil)
   - Via size: 0.6 mm pad, 0.3 mm drill
   - BLE RF trace: 0.3 mm width (calculate for 50 Ω on your stackup)
4. Import component libraries:
   - nRF52840: Nordic's official KiCad library (GitHub: NordicSemiconductor/nRF-KiCad-Lib)
   - Lambda62C-9S: Custom footprint from RF Solutions datasheet (23x20mm castellated pads)
   - BQ25504: TI symbols from Ultra Librarian
   - MCP73831: Microchip symbols from Ultra Librarian
   - TPS22918: TI symbols from Ultra Librarian
   - MAX-M10S: u-blox footprint from SnapEDA
   - Sharp LCD: Molex 5051100892 FPC connector footprint from Molex
   - Johanson 2450AT18D0100: Footprint from Johanson Technology or SnapEDA
   - C&K JS102011SAQN: Footprint from C&K datasheet
   - GCT USB4085-GF-A: Footprint from GCT or SnapEDA
   - Keystone 1042P: Footprint from Keystone datasheet or SnapEDA
   - TE/Linx CONSMA006.062: Footprint from TE Connectivity datasheet
   - JST S2B-PH-K-S: Footprint from JST datasheet
   - Abracon ABS07: Footprint from Abracon datasheet (3.2x1.5mm, 4-pad)

### Schematic Sheets (Recommended Organization)

1. **Sheet 1 — MCU**: nRF52840, all decoupling (including DEC pins), 32 MHz crystal + load caps, 32.768 kHz crystal + load caps, BLE matching network + chip antenna
2. **Sheet 2 — LoRa**: Lambda62C-9S module, SPI connections, TXEN/RXEN, u.FL connector, SMA pigtail
3. **Sheet 3 — Power**: Slide switch, BQ25504 solar harvester, MCP73831 USB charger, BAT54JFILM OR-ing Schottky diode, TPS7A02 LDO, TPS22918 load switch, Keystone 1042P battery holder, JST-PH solar connector, voltage divider
4. **Sheet 4 — USB**: USB-C connector (GCT), CC resistors, TPD2E001 ESD protection, VBUS detection for MCP73831
5. **Sheet 5 — Peripherals**: Sharp LCD FPC connector, MAX-M10S GPS + I2C, GPS patch antenna, I2C expansion header, buttons (x7 C&K PTS636), LEDs, QSPI flash (Macronix)

### PCB Layout Priority Order

1. Place Lambda62C-9S module near board edge (for short u.FL cable to SMA bulkhead)
2. Place nRF52840 + all decoupling + 32 MHz crystal + 32.768 kHz crystal centrally
3. Route BLE 50 Ω antenna trace from nRF52840 ANT → matching → Johanson chip antenna at opposite board edge from LoRa SMA
4. Place GPS patch antenna (25x25mm) on opposite end from LoRa SMA, with solid GND pour underneath
5. Place BQ25504 + MCP73831 + BAT54JFILM OR-ing diode + TPS7A02 + TPS22918 in power section (away from both antennas)
6. Place slide switch at board edge (accessible through enclosure)
7. Place USB-C connector + ESD + CC resistors at board edge
8. Place Keystone 1042P battery holder + JST-PH solar connector in power section
9. Place buttons along one edge for ergonomic access
10. Place LCD FPC connector centered on the top edge
11. Place I2C expansion header near board edge (accessible through enclosure)
12. Place QSPI flash near nRF52840 (short QSPI traces)
13. Fill remaining copper with stitched ground pour

---

## Design Checklist

### MCU — nRF52840
- [ ] 100 nF on every VDD pin, within 2 mm
- [ ] 1 µF bulk near IC
- [ ] DEC1: 100 nF, within 2 mm, short GND trace
- [ ] DEC4: 1 µF, within 2 mm, short GND trace
- [ ] DEC6: 100 nF, within 2 mm, short GND trace
- [ ] DECUSB: 4.7 µF + 100 nF (USB regulator)
- [ ] VDDH: 4.7 µF if routing battery direct to VDDH
- [ ] 32 MHz crystal (Abracon ABM8) within 5 mm of XC1/XC2, symmetric traces
- [ ] 2x 12 pF load caps for 32 MHz crystal
- [ ] 32.768 kHz crystal (Abracon ABS07) within 5 mm of XL1/XL2
- [ ] 2x 6 pF load caps for 32.768 kHz crystal
- [ ] CONFIG_NFCT_PINS_AS_GPIOS=y set in prj.conf (frees P0.09/P0.10)

### BLE Radio
- [ ] Johanson chip antenna at board edge, ground keep-out ~5 mm
- [ ] Pi matching network (L + 2C) between ANT pin and chip antenna
- [ ] 50 Ω microstrip trace, verified with stackup calculator
- [ ] No copper pour in antenna keep-out zone

### LoRa — Lambda62C-9S
- [ ] Module footprint matches RF Solutions datasheet (castellated pads)
- [ ] SPI0 routed: SCK, MOSI, MISO, CS
- [ ] TXEN (P1.07) and RXEN (P1.06) routed to module pins 4 and 5
- [ ] DIO1, BUSY, RESET routed
- [ ] u.FL connector at board edge
- [ ] P0.21 is NOT routed to Lambda62 (DIO3 is internal, no external pin)
- [ ] No `SX126X_DIO2_AS_RF_SWITCH` in firmware

### GPS
- [ ] Taoglas GPS patch (25x25mm) on opposite end from LoRa SMA
- [ ] Solid ground plane under GPS patch on layer 2
- [ ] No digital traces routed under GPS antenna
- [ ] I2C EXTERNAL pull-ups: 4.7 kΩ to 3.3V on SDA/SCL (do NOT use internal pull-ups)

### I2C Expansion
- [ ] 4-pin header footprint (SDA/SCL/3.3V/GND) placed on PCB
- [ ] Connected to same I2C bus as GPS (P0.26/P0.27)
- [ ] 3.3V from TPS22918 switched rail
- [ ] Not populated on initial 30-unit run

### Power
- [ ] Slide switch (C&K JS102011SAQN) between battery + and system VBAT rail
- [ ] Keystone 1042P battery holder — verify SMT footprint matches datasheet
- [ ] BQ25504 thermal pad soldered to ground plane
- [ ] BQ25504 programming resistors: OV=4.2V, UV=3.0V
- [ ] JST S2B-PH-K-S solar connector — THT right-angle, 2-pin, 2mm pitch
- [ ] MCP73831 PROG resistor: 2 kΩ for 500 mA charge current
- [ ] BAT54JFILM Schottky OR-ing diode between BQ25504 VBAT and MCP73831 output
- [ ] TPS7A02 input/output caps: 1 µF ceramic each
- [ ] TPS22918 input/output caps: 100 nF each
- [ ] Battery voltage divider: 2x 100 kΩ, center tap to AIN2 (P0.04)

### USB
- [ ] GCT USB4085-GF-A connector at board edge
- [ ] TPD2E001 ESD protection close to connector, before traces to MCU
- [ ] CC1 → 5.1 kΩ → GND, CC2 → 5.1 kΩ → GND (close to connector)
- [ ] VBUS routed to MCP73831 input

### RF Connectors
- [ ] TE/Linx CONSMA006.062 SMA jack — edge-mount, 50 Ω
- [ ] SMA connector at board edge near Lambda62 module (short u.FL pigtail)

### UI
- [ ] Button debounce caps: 100 nF each (x7)
- [ ] LED series resistors: 680 Ω each (x3)
- [ ] BTN_A (P1.00) = PIN_BUTTON1, BTN_B (P1.01) = PIN_BUTTON2 (verify in variant.h)

### General
- [ ] All power traces: minimum 0.3 mm (12 mil), wider for high-current paths
- [ ] SWD header: 10-pin Cortex debug connector or 2x5 0.05" pitch
- [ ] Test points: VBAT, 3.3V, GND, UART TX/RX, SWD
- [ ] QSPI traces short and matched length
- [ ] Silkscreen: Component references, Mindtech logo, "Freedom Unit V2", "Made in USA"
- [ ] Ground pour stitched everywhere except antenna keep-out zones
- [ ] P0.21 left unrouted (free GPIO, not connected to Lambda62)

---

## GPIO Summary — Unassigned Pins

| Pin | Status | Notes |
|-----|--------|-------|
| P0.09 | Free (with NFC disabled) | Requires CONFIG_NFCT_PINS_AS_GPIOS=y in prj.conf |
| P0.10 | Free (with NFC disabled) | Requires CONFIG_NFCT_PINS_AS_GPIOS=y in prj.conf |
| P0.21 | Free | Was incorrectly assigned to DIO3 in V2. DIO3 is internal to Lambda62. |
| P1.03 | Free (reserve) | Unassigned general-purpose GPIO |

**Total free pins: 4** (with NFC disabled via prj.conf)

---

## Development Sequence

| Week | Task | Deliverable |
|------|------|-------------|
| 1–2 | KiCad schematic entry, all 5 sheets | `.kicad_sch` files |
| 3 | Component footprint verification, BOM in DigiKey | BOM spreadsheet |
| 4 | Order Lambda62C-9S samples from RF Solutions for eval | Lambda62 eval units |
| 5–6 | PCB layout, BLE trace routing, DRC/ERC clean | `.kicad_pcb` file |
| 7 | Generate Gerbers, submit to OSH Park | Gerber ZIP |
| 8–9 | Boards arrive, hand-solder 1 prototype | Working proto |
| 10 | VNA tune BLE matching network on prototype | Tuned values |
| 11 | Flash Meshtastic with Freedom Unit variant.h V3, range test | Firmware verified, test report |
| 12 | Power measurement, charge path validation (solar + USB) | Power test report |
| 13–14 | Submit BOM + Gerbers + CPL to MacroFab for 30-unit run | PO placed |
| 15–16 | 3D print enclosures (3 variants), assemble full kits | 30 Freedom Units ready |

---

## Reference Documents

- Lambda62C-9S datasheet: https://www.rfsolutions.co.uk/content/download-files/LAMBDA-62-6-DATASHEET.pdf
- Lambda62 product page: https://www.rfsolutions.co.uk/radio-modules/lambda-62-lora-transceiver-module-20km-featuring-semtech-sx1262/
- RF Solutions "Made in Britain": https://www.madeinbritain.org/members/rf-solutions-ltd
- Nordic nRF52840 product spec: https://infocenter.nordicsemi.com/pdf/nRF52840_PS_v1.8.pdf
- Semtech SX1262 datasheet: https://cdn.sparkfun.com/assets/6/b/5/1/4/SX1262_datasheet.pdf
- TI BQ25504 datasheet: https://www.ti.com/lit/ds/symlink/bq25504.pdf
- Microchip MCP73831 datasheet: https://ww1.microchip.com/downloads/en/DeviceDoc/MCP73831-Family-Data-Sheet-DS20001984H.pdf
- TI TPS22918 datasheet: https://www.ti.com/lit/ds/symlink/tps22918.pdf
- TI TPD2E001 datasheet: https://www.ti.com/lit/ds/symlink/tpd2e001.pdf
- u-blox MAX-M10S integration manual: https://www.u-blox.com/sites/default/files/MAX-M10S_IntegrationManual_UBX-20053088.pdf
- Sharp LS013B7DH03 datasheet: https://www.mouser.com/datasheet/2/365/LS013B7DH03%20SPEC_SMA-224806.pdf
- Johanson 2450AT18D0100 datasheet: https://www.johansontechnology.com/datasheets/antenna/2450AT18D0100.pdf
- Macronix MX25R6435F datasheet: https://www.macronix.com/Lists/Datasheet/Attachments/8729/MX25R6435F,%20Wide%20Range,%2064Mb,%20v1.6.pdf
- Abracon ABS07 datasheet: https://abracon.com/datasheets/ABS07-120-32.768KHZ-T.pdf
- Keystone 1042P datasheet: https://www.keyelco.com/product.cfm/product_id/918
- STMicroelectronics BAT54 datasheet: https://www.st.com/en/diodes-and-rectifiers/bat54.html
- TE/Linx CONSMA006.062 datasheet: https://www.te.com/en/product-L9000271-01.html
- JST PH connector: https://www.jst.com/products/crimp-style-connectors-wire-to-board-type/ph-connector/
- Meshtastic custom hardware guide: https://meshtastic.org/docs/development/firmware/build/
- T-Echo variant.h (reference): https://github.com/meshtastic/firmware/tree/master/variants/nrf52840/t-echo
- KiCad download: https://www.kicad.org/download/
- OSH Park specs: https://docs.oshpark.com/services/four-layer/
- MacroFab quoting: https://macrofab.com/
