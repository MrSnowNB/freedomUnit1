#!/usr/bin/env python3
"""Create placeholder footprints for custom components.

Usage: python create_placeholders.py [libs_dir]
  libs_dir defaults to <repo_root>/libs/FreedomUnit.pretty
"""
import os
import sys


def create_placeholder_mod(pretty_path, name, description, width=10, height=10, num_pads=2):
    """Create a minimal placeholder .kicad_mod file."""
    w2, h2 = width / 2, height / 2
    pads = []
    if num_pads <= 4:
        positions = [(-w2 + 1, 0), (w2 - 1, 0), (0, -h2 + 1), (0, h2 - 1)]
    else:
        # Distribute pads along left and right edges
        positions = []
        per_side = num_pads // 2
        for i in range(per_side):
            y = -h2 + 1.5 + i * ((height - 3) / max(per_side - 1, 1))
            positions.append((-w2 + 0.5, y))
        for i in range(num_pads - per_side):
            y = -h2 + 1.5 + i * ((height - 3) / max(num_pads - per_side - 1, 1))
            positions.append((w2 - 0.5, y))

    for i, (px, py) in enumerate(positions[:num_pads]):
        pads.append(
            f'  (pad "{i+1}" smd rect (at {px:.2f} {py:.2f}) '
            f'(size 1.5 0.6) (layers "F.Cu" "F.Paste" "F.Mask"))'
        )

    content = f"""(footprint "{name}" (version 20240108) (generator "FreedomUnit_Generator")
  (descr "{description}")
  (attr smd)
  (fp_text reference "REF**" (at 0 {-h2 - 1.5}) (layer "F.SilkS")
    (effects (font (size 1 1) (thickness 0.15)))
  )
  (fp_text value "{name}" (at 0 {h2 + 1.5}) (layer "F.Fab")
    (effects (font (size 1 1) (thickness 0.15)))
  )
  (fp_rect (start {-w2} {-h2}) (end {w2} {h2}) (layer "F.CrtYd") (stroke (width 0.05) (type default)) (fill none))
  (fp_rect (start {-w2 + 0.1} {-h2 + 0.1}) (end {w2 - 0.1} {h2 - 0.1}) (layer "F.Fab") (stroke (width 0.1) (type default)) (fill none))
{chr(10).join(pads)}
)
"""
    filepath = os.path.join(pretty_path, f"{name}.kicad_mod")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  Created {filepath} ({num_pads} pads)")


def main():
    if len(sys.argv) > 1:
        pretty_path = sys.argv[1]
    else:
        pretty_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'libs', 'FreedomUnit.pretty')
        )

    os.makedirs(pretty_path, exist_ok=True)
    print(f"Creating placeholders in {pretty_path}")

    # Component: (name, description, width_mm, height_mm, num_pads)
    components = [
        ("Lambda62C-9S",              "LoRa Module Lambda62C-9S",       23,   20,  11),
        ("CONSMA006.062",             "SMA Edge-Mount Connector",       10,   10,   2),
        ("Taoglas_CGGBP.25.4.A.02",  "GPS Patch Antenna 25.4mm",       25.4, 25.4, 2),
        ("Johanson_2450AT18D0100",    "BLE Chip Antenna 2450MHz",       3.2,  1.6,  2),
    ]

    for name, desc, w, h, pads in components:
        create_placeholder_mod(pretty_path, name, desc, w, h, pads)

    print("Done.")


if __name__ == "__main__":
    main()
