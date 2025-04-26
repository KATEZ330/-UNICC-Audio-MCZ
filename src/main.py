import tkinter as tk
import logging
import traceback
from gui.media_analyzer_gui import MediaAnalyzerGUI

def main():
    try:
        root = tk.Tk()
        app = MediaAnalyzerGUI(root)
        root.title("UNICC Audio MCZ")
        root.mainloop()
    except Exception as e:
        logging.critical(f"Program startup failed: {str(e)}")
        logging.critical(traceback.format_exc())
        print(f"Program startup failed: {str(e)}")

if __name__ == "__main__":
    main()   