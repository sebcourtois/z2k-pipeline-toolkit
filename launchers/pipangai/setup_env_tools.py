import os
osp = os.path
import sys

sys.path.append(osp.join(osp.dirname(__file__), ".."))
from ztk_setup import Z2kToolkit



# Common envs, may be different for each studio
ENVS = {
        "ZOMB_ASSET_LOC":"\\\\Servnas02\\zombidamas",
        "ZOMB_SHOT_LOC":"\\\\Servnas02\\zombidamas",
        "ZOMB_OUTPUT_LOC":"\\\\Servnas02\\zombidamas",
        "ZOMB_MISC_LOC":"\\\\Servnas02\\zombidamas",
        "ZOMB_PRIVATE_LOC":"\\\\Servnas02\\zombidamas",

        "ZOMB_TOOL_PATH":"\\\\Servnas02\\zombidamas\\ZOMB\\tool",
        "DAVOS_SITE":"pipangai",

        "MAYA_MODULE_PATH":"\\\\Servnas02\\z2k\\04_WG_PIPANGAI\\PythonTree\\maya_mod",
        "CUSTOM_CASHBAH": "\\\\Servnas02\\z2k\\04_WG_PIPANGAI\\PythonTree\\",
        }

try:
    status = Z2kToolkit(ENVS).runFromCmd()
except:
    os.environ["PYTHONINSPECT"] = "1"
    raise
sys.exit(status)


