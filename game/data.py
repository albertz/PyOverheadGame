
import os
import sys

MY_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.dirname(MY_DIR) + "/data"
GFX_DIR = DATA_DIR + "/gfx"

if sys.platform == "win32":
    UserDataDir = os.getenv("LOCALAPPDATA") + "/PyOverheadGame"
elif sys.platform == "darwin":
    UserDataDir = os.path.expanduser("~/Library/Application Support/PyOverheadGame")
else:
    UserDataDir = os.path.expanduser("~/.PyOverheadGame")
