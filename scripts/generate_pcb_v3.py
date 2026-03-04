import pcbnew
from pcbnew import *
import os
import shutil

def nm(mm):
    return int(mm * 1000000)

def place_footprint(board, lib_id_str, reference, pos_mm, angle=0):
    lib_name, fp_name = lib_id_str.split(':')
    stock_base = "C:/Program Files/KiCad/9.0/share/kicad/footprints"
    custom_base = "C:/Users/AMD/Desktop/FreedomUnit_V2/libs"
    lib_path = ""
    if os.path.exists(os.path.join(stock_base, f"{lib_name}.pretty")):
        lib_path = os.path.join(stock_base, f"{lib_name}.pretty")
    elif os.path.exists(os.path.join(custom_base, f"{lib_name}.pretty")):
        lib_path = os.path.join(custom_base, f"{lib_name}.pretty")
    if not lib_path: return None
    fp = pcbnew.FootprintLoad(lib_path, fp_name)
    if not fp: return None
    lib_id = pcbnew.LIB_ID(lib_name, fp_name)
    fp.SetFPID(lib_id)
    fp.SetReference(reference)
    fp.SetPosition(pcbnew.VECTOR2I(nm(pos_mm[0]), nm(pos_mm[1])))
    fp.SetOrientation(pcbnew.EDA_ANGLE(angle, pcbnew.DEGREES_T))
    board.Add(fp)
    return fp

def create_board_from_template():
    demo_path = "C:/Program Files/KiCad/9.0/share/kicad/demos/complex_hierarchy/complex_hierarchy.kicad_pcb"
    pcb_path = "C:/Users/AMD/Desktop/FreedomUnit_V2/FreedomUnit_V2.kicad_pcb"
    
    shutil.copy(demo_path, pcb_path)
    board = pcbnew.LoadBoard(pcb_path)
    
    # Safe removal
    for item in list(board.GetDrawings()): board.Remove(item)
    for item in list(board.GetFootprints()): board.Remove(item)
    for item in list(board.GetTracks()): board.Remove(item)
    for item in list(board.Zones()): board.Remove(item)
    
    width = 80
    height = 50
    edge_cuts = board.GetLayerID("Edge.Cuts")
    rect = [(0, 0), (width, 0), (width, height), (0, height), (0, 0)]
    for i in range(len(rect) - 1):
        start = pcbnew.VECTOR2I(nm(rect[i][0]), nm(rect[i][1]))
        end = pcbnew.VECTOR2I(nm(rect[i+1][0]), nm(rect[i+1][1]))
        segment = pcbnew.PCB_SHAPE(board)
        segment.SetShape(pcbnew.SHAPE_T_SEGMENT)
        segment.SetStart(start)
        segment.SetEnd(end)
        segment.SetLayer(edge_cuts)
        segment.SetWidth(nm(0.1))
        board.Add(segment)
        
    place_footprint(board, "FreedomUnit:Lambda62C-9S", "M1", (width-15, 15))
    place_footprint(board, "Package_DFN_QFN:Nordic_AQFN-73-1EP_7x7mm_P0.5mm", "U1", (width/2, height/2))
    place_footprint(board, "FreedomUnit:Taoglas_CGGBP.25.4.A.02", "AE2", (15, height-15))
    place_footprint(board, "FreedomUnit:Johanson_2450AT18D0100", "AE1", (15, 10))
    place_footprint(board, "Connector_USB:USB_C_Receptacle_GCT_USB4085", "J4", (width/2, height), 180)
    place_footprint(board, "FreedomUnit:CONSMA006.062", "J3", (width, 10), 90)
    place_footprint(board, "Connector_FFC-FPC:Molex_54548-1071_1x10-1MP_P0.5mm_Horizontal", "J5", (width/2, 5))
    place_footprint(board, "Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.1x1.1mm", "U2", (width-15, height/2 - 10))
    place_footprint(board, "Package_TO_SOT_SMD:SOT-23-5", "U3", (width-15, height/2))
    place_footprint(board, "Package_TO_SOT_SMD:SOT-23-5", "U4", (width-15, height/2 + 5))
    place_footprint(board, "Package_TO_SOT_SMD:SOT-23-5", "U5", (width-15, height/2 + 10))
    for i in range(7):
        place_footprint(board, "Button_Switch_SMD:SW_Tactile_SPST_NO_Straight_CK_PTS636Sx25SMTRLFS", f"SW{i+2}", (5, 10 + i*5))
    for i, pos in enumerate([(3, 3), (width-3, 3), (width-3, height-3), (3, height-3)]):
        place_footprint(board, "MountingHole:MountingHole_2.7mm_M2.5", f"H{i+1}", pos)

    board.Save(pcb_path)
    print(f"PCB updated from template at {pcb_path}")

if __name__ == "__main__":
    create_board_from_template()
