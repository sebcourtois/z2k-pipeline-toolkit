import os
osp = os.path
import sys
import subprocess

sys.path.append(osp.join(osp.dirname(__file__), ".."))
from ztk_setup import Z2kToolkit

# Common envs, may be different for each studio
ENVS = {
        "ZOMB_ASSET_LOC":"\\\\ZOMBILLENIUM\\ZOMBIDAMAS",
        "ZOMB_SHOT_LOC":"\\\\ZOMBILLENIUM\\ZOMBIDAMAS",
        "ZOMB_OUTPUT_LOC":"\\\\ZOMBILLENIUM\\ZOMBIDAMAS",
        "ZOMB_PRIVATE_LOC":"\\\\ZOMBILLENIUM\\ZOMBIDAMAS",

        "ZOMB_TOOL_PATH":"\\\\ZOMBILLENIUM\\ZOMBIDAMAS\\zomb\\tool",
        }

try:
    Z2kToolkit(ENVS).runFromCmd()
except:
    os.environ["PYTHONINSPECT"] = "1"
    raise
