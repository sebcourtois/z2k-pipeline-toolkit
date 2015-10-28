import os
osp = os.path
import sys


sys.path.append(osp.join(osp.dirname(__file__), ".."))
from ztk_setup import Z2kToolkit

# Common envs, may be different for each studio
ENVS = {
        "ZOMB_ASSET_LOC":"\\\\ZOMBIWALK\\Projects",
        "ZOMB_SHOT_LOC":"\\\\ZOMBIWALK\\Projects",
        "ZOMB_OUTPUT_LOC":"\\\\ZOMBIWALK\\Projects",
        "ZOMB_MISC_LOC":"\\\\ZOMBIWALK\\Projects",
        "ZOMB_PRIVATE_LOC":"\\\\ZOMBIWALK\\Projects",

        "ZOMB_TOOL_PATH":"\\\\ZOMBIWALK\\Projects\\zomb\\tool",

        "MAYA_MODULE_PATH":r"\\ZOMBIWALK\Z2K_RnD\maya_mods"

        }

try:
    Z2kToolkit(ENVS).runFromCmd()
except:
    os.environ["PYTHONINSPECT"] = "1"
    raise
