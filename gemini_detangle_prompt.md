
================================================================================
GEMINI CODE ASSIST PROMPT — REPO DETANGLE: HARDWARE vs SOFTWARE
================================================================================

Copy everything below this line and paste it into Gemini Code Assist.

================================================================================

You are reorganizing the freedomUnit1 repository. The repo currently mixes 
KiCad PCB/schematic hardware files with Python software files in the root 
directory. Your job is to move ALL hardware files into a `hardware/` folder 
while preserving KiCad's internal relative path references.

## CURRENT ROOT-LEVEL HARDWARE FILES (move ALL of these)

KiCad project files:
- FreedomUnit_V2.kicad_pcb
- FreedomUnit_V2.kicad_pro
- FreedomUnit_V2.kicad_sch

KiCad hierarchical schematic sheets:
- Sheet1_MCU.kicad_sch
- Sheet2_LoRa.kicad_sch
- Sheet3_Power.kicad_sch
- Sheet4_USB.kicad_sch
- Sheet5_Peripherals.kicad_sch

KiCad library tables:
- fp-lib-table
- sym-lib-table

Hardware support directories (move entire directories):
- fab/          (fabrication outputs, Gerbers, BOM)
- libs/         (custom KiCad symbol/footprint libraries)

## TARGET STRUCTURE

```
freedomUnit1/
├── hardware/
│   ├── FreedomUnit_V2.kicad_pcb
│   ├── FreedomUnit_V2.kicad_pro
│   ├── FreedomUnit_V2.kicad_sch
│   ├── Sheet1_MCU.kicad_sch
│   ├── Sheet2_LoRa.kicad_sch
│   ├── Sheet3_Power.kicad_sch
│   ├── Sheet4_USB.kicad_sch
│   ├── Sheet5_Peripherals.kicad_sch
│   ├── fp-lib-table
│   ├── sym-lib-table
│   ├── fab/
│   │   └── (existing fab contents)
│   └── libs/
│       └── (existing libs contents)
├── huffman_mesh_poc.py          (SOFTWARE — stays in root)
├── huffman_codec.py             (SOFTWARE — stays in root)
├── mux_codec.py                 (SOFTWARE — stays in root)
├── ... (all other .py files stay in root)
├── codebooks/                   (SOFTWARE — stays in root)
├── logs/                        (SOFTWARE — stays in root)
├── experiment_f/                (SOFTWARE — stays in root)
├── docs/                        (stays in root)
├── scripts/                     (check contents — if hardware scripts, move)
├── archive/                     (stays in root)
└── README.md                    (stays in root)
```

## CRITICAL: FIX KICAD INTERNAL REFERENCES AFTER MOVE

KiCad files reference each other with relative paths. After moving files 
into hardware/, you MUST update these internal references:

### 1. FreedomUnit_V2.kicad_sch — Hierarchical sheet references
The root schematic references sub-sheets. Search for lines like:
```
(sheet (at ...) (size ...)
  (fields ...)
  (sheet_name "MCU")
  (file_name "Sheet1_MCU.kicad_sch")
)
```
These file_name values do NOT need changing because the sub-sheets are 
in the SAME directory as the root schematic after the move. All .kicad_sch 
files move together into hardware/, so relative paths between them are 
preserved.

### 2. FreedomUnit_V2.kicad_pro — Project file paths
Open the .kicad_pro file (it's JSON). Check for any paths referencing 
files that moved. Typically the project file uses relative paths to 
.kicad_sch and .kicad_pcb in the same directory, so these should be fine.

### 3. fp-lib-table and sym-lib-table — Library paths
These files contain paths to footprint and symbol libraries. Check for 
paths like:
```
(lib (name "custom_lib")(type "KiCad")(uri "${KIPRJMOD}/libs/custom.pretty")(options "")(descr ""))
```
${KIPRJMOD} resolves to the directory containing the .kicad_pro file.
Since libs/ moves INTO hardware/ alongside .kicad_pro, the relative 
path ${KIPRJMOD}/libs/ stays correct.

IF any lib table entries use ABSOLUTE paths or paths relative to the 
repo root (not ${KIPRJMOD}), those MUST be updated.

### 4. scripts/ directory — CHECK CONTENTS
Look at what's in scripts/. If it contains KiCad-related scripts 
(BOM generators, Gerber exporters, DRC runners), move them to 
hardware/scripts/. If it contains Python software scripts (test runners, 
build tools), leave in root.

## GIT COMMANDS (use git mv to preserve history)

```bash
# Create target directory
mkdir -p hardware

# Move KiCad project files
git mv FreedomUnit_V2.kicad_pcb hardware/
git mv FreedomUnit_V2.kicad_pro hardware/
git mv FreedomUnit_V2.kicad_sch hardware/

# Move hierarchical sheets
git mv Sheet1_MCU.kicad_sch hardware/
git mv Sheet2_LoRa.kicad_sch hardware/
git mv Sheet3_Power.kicad_sch hardware/
git mv Sheet4_USB.kicad_sch hardware/
git mv Sheet5_Peripherals.kicad_sch hardware/

# Move library tables
git mv fp-lib-table hardware/
git mv sym-lib-table hardware/

# Move support directories
git mv fab/ hardware/
git mv libs/ hardware/

# Check scripts/ contents first, then:
# git mv scripts/ hardware/   (if hardware-related)
# OR leave in place             (if software-related)

# Commit
git add -A
git commit -m "Repo reorg: Move all KiCad/hardware files into hardware/ directory"
```

## DO NOT MOVE (these are software files)

- Any .py file
- config.yaml
- codebooks/
- logs/
- experiment_f/
- docs/
- archive/
- __pycache__/
- english_unigram_freq.csv
- huffman_codebook_4k.csv
- mux_codebook.csv
- Any .md file in root
- .gitignore

## ALSO DO (cleanup while you're at it)

1. Delete __pycache__/ from the repo:
   ```bash
   git rm -r __pycache__/
   echo "__pycache__/" >> .gitignore
   ```
   __pycache__ should NEVER be committed. Add it to .gitignore.

2. After the move, verify KiCad can open the project:
   - Open KiCad
   - File → Open Project → navigate to hardware/FreedomUnit_V2.kicad_pro
   - Verify all 5 sub-sheets load in the schematic editor
   - Verify the PCB layout opens with all footprints resolved
   - Verify DRC and ERC pass (or at least show the same errors as before)

3. Update README.md repo structure section to reflect the new layout.

## SUMMARY

Move 12 files + 2 directories from root into hardware/.
All KiCad internal references should survive because all hardware files 
move together (relative paths preserved).
Use git mv for every move to preserve git history.
Delete __pycache__ and add it to .gitignore.
Verify KiCad project opens correctly after the move.
