# Freedom Unit V2 - KiCad Project

Welcome to the Freedom Unit V2 KiCad project! This repository contains the hardware design files for a 4-layer 80x50mm LoRa mesh node PCB, designed as a protocol-agnostic platform supporting Meshtastic, LoRaWAN, Reticulum, and MeshCore.

## AI-First Workflow Manual

This repository is designed to be interacted with and managed by an AI Agent (like the Gemini CLI) to generate and modify KiCad 8 project files. If you are an AI assistant tasked with replicating or modifying this workflow, strictly adhere to the following steps and rules.

### 1. Read the Specifications
Before generating or modifying any files, you **MUST** read the full design specification and project mandates:
*   **`Freedom-Unit-Board-Layout-v2.2.md`**: Contains the comprehensive board layout design, BOM, architecture, and pin assignments.
*   **`GEMINI.md`**: Contains the critical technical mandates, constraints, and the absolute source of truth for Pin Assignments.

### 2. Understand the Tech Stack
*   **KiCad 8**: The target EDA tool.
*   **Formats**: Project files (`.kicad_pro`) must be JSON. Schematic files (`.kicad_sch`) and PCB files (`.kicad_pcb`) must use the S-expression format.
*   **Encoding**: All files must be UTF-8.

### 3. File Generation Workflow
When generating or modifying schematic sheets or the PCB layout:
1.  **Work iteratively**: Generate one schematic sheet at a time.
2.  **Verify against the Pin Table**: Never hallucinate pin assignments. Only use the table provided in `GEMINI.md`.
3.  **Ensure Connectivity**: Every component must have Nets or Labels. Use Hierarchical Labels for inter-sheet busing (e.g., SPI, I2C).
4.  **Enforce Passives**: Never omit decoupling capacitors (100nF/1uF per VDD/DEC pin), I2C pull-ups (4.7k), or button debouncing (100nF).

### 4. Validation and Export (CI/CD Equivalent)
After generating or modifying files, you must validate them using the KiCad CLI:

*   **Schematic Validation (ERC)**:
    ```bash
    kicad-cli sch erc <file.kicad_sch>
    ```
*   **PCB Validation (DRC)**:
    ```bash
    kicad-cli pcb drc <file.kicad_pcb>
    ```

### 5. Fabrication Outputs
When the design is complete and validates cleanly, use `kicad-cli` to generate outputs for MacroFab (Houston, TX) and OSH Park:
*   Gerber RS-274X (No X2).
*   Separate PTH/NPTH drill files.
*   Ensure the XYRS origin is set to the bottom-left of the board bounding box.
*   Ensure all symbols have an `mpn` (Manufacturer Part Number) property matching the BOM exactly.
