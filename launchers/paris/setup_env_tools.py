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
        "DAVOS_SITE":"dmn_paris",

        "MAYA_MODULE_PATH":r"\\ZOMBIWALK\Z2K_RnD\maya_mods",

        "XGEN_CONFIG_PATH":r"//ZOMBIWALK/Projects/zomb/tool/z2k-pipeline-toolkit/launchers/paris/xgen",
        "XGEN_PATH":r"//ZOMBIWALK/Projects/zomb/tool/xgen",
        }

try:
    status = Z2kToolkit(ENVS).runFromCmd()
except:
    os.environ["PYTHONINSPECT"] = "1"
    raise
sys.exit(status)
