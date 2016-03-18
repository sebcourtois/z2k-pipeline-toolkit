import os
osp = os.path
import sys

sys.path.append(osp.join(osp.dirname(__file__), ".."))
from ztk_setup import Z2kToolkit

# Common envs, may be different for each studio
ENVS = {
        "ZOMB_ASSET_LOC":"\\\\lv7000_fileserver\\Zombidamas",
        "ZOMB_SHOT_LOC":"\\\\lv7000_fileserver\\Zombidamas",
        "ZOMB_OUTPUT_LOC":"\\\\lv7000_fileserver\\Zombidamas",
        "ZOMB_MISC_LOC":"\\\\lv7000_fileserver\\Zombidamas",
        "ZOMB_PRIVATE_LOC":"\\\\lv7000_fileserver\\Zombidamas",

        "ZOMB_TOOL_PATH":"\\\\lv7000_fileserver\\Zombidamas\\zomb\\tool",

        }

try:
    status = Z2kToolkit(ENVS).runFromCmd()
except:
    os.environ["PYTHONINSPECT"] = "1"
    raise
sys.exit(status)
