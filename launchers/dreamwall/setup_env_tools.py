import os
osp = os.path
import sys
import subprocess

sys.path.append(osp.join(osp.dirname(__file__), ".."))
from ztk_setup import Z2kToolkit

# Common envs, may be different for each studio
ENVS = {
        "ZOMB_ASSET_LOC":"\\\\ZOMBIWALK\\Projects",
        "ZOMB_SHOT_LOC":"\\\\ZOMBIWALK\\Projects",
        "ZOMB_OUTPUT_LOC":"\\\\ZOMBIWALK\\Projects",
        "ZOMB_PRIVATE_LOC":"\\\\ZOMBIWALK\\Projects",

        "ZOMB_TOOL_PATH":"Z:\\3D\\Z2K\\MOD\\04_Tools_Soft\\tool",

        }

try:
    Z2kToolkit(ENVS).runFromCmd()
except:
    os.environ["PYTHONINSPECT"] = "1"
    raise
