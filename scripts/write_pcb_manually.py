import uuid

def get_uuid():
    return str(uuid.uuid4())

def footprint(lib_id, reference, value, pos, angle=0):
    u = get_uuid()
    x, y = pos
    return f"""
  (footprint "{lib_id}"
    (layer "F.Cu")
    (uuid "{u}")
    (at {x} {y} {angle})
    (property "Reference" "{reference}"
      (at 0 -5 0)
      (layer "F.SilkS")
      (uuid "{get_uuid()}")
      (effects (font (size 1 1) (thickness 0.15)))
    )
    (property "Value" "{value}"
      (at 0 5 0)
      (layer "F.Fab")
      (uuid "{get_uuid()}")
      (effects (font (size 1 1) (thickness 0.15)))
    )
  )"""

def edge_cut(start, end):
    return f"""
  (gr_line (start {start[0]} {start[1]}) (end {end[0]} {end[1]})
    (stroke (width 0.1) (type default)) (layer "Edge.Cuts") (uuid "{get_uuid()}")
  )"""

def generate_pcb():
    width = 80
    height = 50
    
    content = f"""(kicad_pcb
  (version 20241229)
  (generator "Gemini CLI")
  (generator_version "9.0")
  (general
    (thickness 1.6)
  )
  (paper "A4")
  (layers
    (0 "F.Cu" signal)
    (2 "B.Cu" signal)
    (25 "Edge.Cuts" user)
  )
  (setup
    (stackup
      (layer "F.Cu" (type "signal") (thickness 0.035))
      (layer "In1.GND" (type "power") (thickness 0.0175))
      (layer "In2.Power" (type "power") (thickness 0.0175))
      (layer "B.Cu" (type "signal") (thickness 0.035))
    )
  )
{edge_cut((0,0), (width,0))}
{edge_cut((width,0), (width,height))}
{edge_cut((width,height), (0,height))}
{edge_cut((0,height), (0,0))}
{footprint("FreedomUnit:Lambda62C-9S", "M1", "Lambda62C-9S", (width-15, 15))}
{footprint("Package_DFN_QFN:Nordic_AQFN-73-1EP_7x7mm_P0.5mm", "U1", "nRF52840", (width/2, height/2))}
{footprint("FreedomUnit:Taoglas_CGGBP.25.4.A.02", "AE2", "GPS", (15, height-15))}
{footprint("FreedomUnit:Johanson_2450AT18D0100", "AE1", "BLE", (15, 10))}
{footprint("Connector_USB:USB_C_Receptacle_GCT_USB4085", "J4", "USB-C", (width/2, height), 180)}
{footprint("FreedomUnit:CONSMA006.062", "J3", "SMA", (width, 10), 90)}
{footprint("Connector_FFC-FPC:Molex_54548-1071_1x10-1MP_P0.5mm_Horizontal", "J5", "LCD", (width/2, 5))}
)"""
    with open("C:/Users/AMD/Desktop/FreedomUnit_V2/FreedomUnit_V2.kicad_pcb", "w", encoding="utf-8") as f:
        f.write(content)
    print("PCB written manually.")

if __name__ == "__main__":
    generate_pcb()
