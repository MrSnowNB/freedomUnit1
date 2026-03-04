import os

pretty_path = "C:/Users/AMD/Desktop/FreedomUnit_V2/libs/FreedomUnit.pretty"
if not os.path.exists(pretty_path):
    os.makedirs(pretty_path)

def create_placeholder_mod(name, description, width=10, height=10):
    content = f"""(footprint "{name}" (version 20240108) (generator "Gemini CLI")
  (descr "{description}")
  (attr smd)
  (fp_text reference "REF**" (at 0 -{height/2 + 1}) (layer "F.SilkS")
    (effects (font (size 1 1) (thickness 0.15)))
  )
  (fp_text value "{name}" (at 0 {height/2 + 1}) (layer "F.Fab")
    (effects (font (size 1 1) (thickness 0.15)))
  )
  (fp_rect (start -{width/2} -{height/2}) (end {width/2} {height/2}) (layer "F.Cuts") (stroke (width 0.1) (type default)) (fill none))
  (pad "1" smd rect (at 0 0) (size 2 2) (layers "F.Cu" "F.Paste" "F.Mask"))
)
"""
    with open(os.path.join(pretty_path, f"{name}.kicad_mod"), "w", encoding="utf-8") as f:
        f.write(content)

create_placeholder_mod("Lambda62C-9S", "LoRa Module Placeholder", 23, 20)
create_placeholder_mod("CONSMA006.062", "SMA Edge Mount Placeholder", 10, 10)
create_placeholder_mod("Taoglas_CGGBP.25.4.A.02", "GPS Patch Placeholder", 25, 25)
create_placeholder_mod("Johanson_2450AT18D0100", "BLE Chip Antenna Placeholder", 3.2, 1.6)

print("Created placeholder footprints in libs/FreedomUnit.pretty")
