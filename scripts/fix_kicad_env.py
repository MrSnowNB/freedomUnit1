import json
import os

config_path = r"C:\Users\AMD\AppData\Roaming\kicad\8.0\kicad_common.json"

with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

kicad_share = r"C:\Users\AMD\AppData\Local\Programs\KiCad\8.0\share\kicad"

if config.get("environment") is None:
    config["environment"] = {}

config["environment"]["vars"] = {
    "KICAD8_3DMODEL_DIR": os.path.join(kicad_share, "3dmodels"),
    "KICAD8_FOOTPRINT_DIR": os.path.join(kicad_share, "footprints"),
    "KICAD8_SYMBOL_DIR": os.path.join(kicad_share, "symbols"),
    "KICAD8_TEMPLATE_DIR": os.path.join(kicad_share, "template"),
    "KICAD_USER_TEMPLATE_DIR": r"C:\Users\AMD\Documents\KiCad\8.0	emplate"
}

with open(config_path, "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2)

print("Successfully updated kicad_common.json with KICAD8 environment variables.")
