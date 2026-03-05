import pcbnew
import sys

def touch_board(path):
    try:
        board = pcbnew.LoadBoard(path)
        board.Save(path)
        print(f"Board {path} touched and saved.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    touch_board("C:/Users/AMD/Desktop/FreedomUnit_V2/FreedomUnit_V2.kicad_pcb")
