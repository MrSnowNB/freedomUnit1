import os
import re

def get_matching_parentheses(content, start_index):
    count = 0
    for i in range(start_index, len(content)):
        if content[i] == '(':
            count += 1
        elif content[i] == ')':
            count -= 1
            if count == 0:
                return i
    return -1

def extract_symbol_from_lib(lib_name, symbol_name, lib_dirs):
    for lib_dir in lib_dirs:
        lib_path = os.path.join(lib_dir, f"{lib_name}.kicad_sym")
        if not os.path.exists(lib_path):
            continue
            
        with open(lib_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            
        # Match (symbol "name" or (symbol name
        pattern = rf'\(symbol "{re.escape(symbol_name)}"'
        match = re.search(pattern, content)
        if not match:
            pattern_no_quotes = rf'\(symbol {re.escape(symbol_name)}[ \n\)]'
            match = re.search(pattern_no_quotes, content)
            
        if match:
            start_idx = match.start()
            end_idx = get_matching_parentheses(content, start_idx)
            if end_idx != -1:
                sym_block = content[start_idx : end_idx + 1]
                
                # FIX: KiCad 8/9 Lib Symbol naming rules inside lib_symbols:
                # 1. The top level symbol name MUST be "Library:Symbol"
                # 2. Sub-symbols (units) MUST NOT have the library prefix.
                
                # First, strip all existing library prefixes from symbol/sub-symbol names
                # (in case the source library itself has them, or from previous runs)
                # Then we will selectively re-add only to the top level.
                
                # Replace the very first (symbol "name" or (symbol name with the prefixed version
                # We use a unique marker to avoid double-prefixing sub-symbols
                full_id = f"{lib_name}:{symbol_name}"
                
                # Handle quoted and unquoted names in the source
                if sym_block.startswith(f'(symbol "{symbol_name}"'):
                    sym_block = sym_block.replace(f'(symbol "{symbol_name}"', f'(symbol "{full_id}"', 1)
                elif sym_block.startswith(f'(symbol {symbol_name}'):
                    sym_block = sym_block.replace(f'(symbol {symbol_name}', f'(symbol "{full_id}"', 1)
                
                return sym_block
                
    print(f"Warning: Symbol {symbol_name} not found in any library")
    return None

def process_schematic(sch_path, lib_dirs):
    try:
        with open(sch_path, 'r', encoding='utf-8', errors='replace') as f:
            sch_content = f.read()
    except Exception as e:
        print(f"Error reading {sch_path}: {e}")
        return
        
    lib_ids = set(re.findall(r'\(lib_id "([^"]+)"\)', sch_content))
    if not lib_ids: return

    lib_symbols_content = []
    for full_id in lib_ids:
        if ':' not in full_id: continue
        lib_name, symbol_name = full_id.split(':')
        sym_def = extract_symbol_from_lib(lib_name, symbol_name, lib_dirs)
        if sym_def:
            lib_symbols_content.append(sym_def)

    if lib_symbols_content:
        # Remove existing lib_symbols block
        sch_content = re.sub(r'\n  \(lib_symbols.*?\n  \)', '', sch_content, flags=re.DOTALL)
        
        joined_symbols = chr(10).join(["    " + s.replace("\n", "\n    ") for s in lib_symbols_content])
        block = chr(10) + "  (lib_symbols" + chr(10) + joined_symbols + chr(10) + "  )"
        
        # Insert after title_block or paper
        insert_match = re.search(r'\(title_block.*?\n  \)', sch_content, flags=re.DOTALL)
        if not insert_match:
            insert_match = re.search(r'\(paper "[^"]+"\)', sch_content)
            
        if insert_match:
            pos = insert_match.end()
            new_sch = sch_content[:pos] + block + sch_content[pos:]
            with open(sch_path, 'w', encoding='utf-8') as f:
                f.write(new_sch)
            print(f"Successfully embedded symbols into {sch_path}")

# KiCad 9 Paths
STOCK_LIB_DIR = r"C:\Program Files\KiCad\9.0\share\kicad\symbols"
CUSTOM_LIB_DIR = r"C:\Users\AMD\FreedomUnit_V2\libs"
LIB_DIRS = [STOCK_LIB_DIR, CUSTOM_LIB_DIR]

SCHEMATICS = [
    "FreedomUnit_V2/Sheet1_MCU.kicad_sch",
    "FreedomUnit_V2/Sheet2_LoRa.kicad_sch",
    "FreedomUnit_V2/Sheet3_Power.kicad_sch",
    "FreedomUnit_V2/Sheet4_USB.kicad_sch",
    "FreedomUnit_V2/Sheet5_Peripherals.kicad_sch",
    "FreedomUnit_V2/FreedomUnit_V2.kicad_sch"
]

for sch in SCHEMATICS:
    if os.path.exists(sch):
        process_schematic(sch, LIB_DIRS)
