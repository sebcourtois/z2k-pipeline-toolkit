
import sys
import os
import os.path as osp

sys.path.append(osp.abspath(osp.join(osp.dirname(__file__), "..")))
from ztk_setup import Z2kToolkit

# Common envs, may be different for each studio
ENVS = {
        "ZOMB_ASSET_LOC":"\\\\lv7000_fileserver\\Zombidamas",
        "ZOMB_SHOT_LOC":"\\\\lv7000_fileserver\\Zombidamas",
        "ZOMB_OUTPUT_LOC":"\\\\lv7000_fileserver\\Zombidamas",
        "ZOMB_MISC_LOC":"\\\\lv7000_fileserver\\Zombidamas",
        "ZOMB_PRIVATE_LOC":"\\\\lv7000_fileserver\\Zombidamas",

        "ZOMB_TOOL_PATH":"\\\\lv7000_fileserver\\Zombidamas\\zomb\\tool",
        "DAVOS_SITE":"dream_wall",
		
		"XGEN_CONFIG_PATH":r"//lv7000_fileserver/Zombidamas/zomb/tool/z2k-pipeline-toolkit/launchers/dreamwall/xgen",
        "XGEN_PATH":r"//lv7000_fileserver/Zombidamas/zomb/tool/xgen",
		
        }

try:
    status = Z2kToolkit(ENVS).runFromCmd()
except:
    os.environ["PYTHONINSPECT"] = "1"
    raise
sys.exit(status)
