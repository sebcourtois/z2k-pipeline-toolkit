
import sys
import os
import os.path as osp

sys.path.append(osp.abspath(osp.join(osp.dirname(__file__), "..")))
from ztk_setup import Z2kToolkit

#Nouveau chemins:
#\\tatooine\zombidamas\zomb
#\\tatooine\zombidamas\private


# Common envs, may be different for each studio
ENVS = {
        "ZOMB_ASSET_LOC":"\\\\ZOMBILLENIUM\\ZOMBIDAMAS",
        "ZOMB_SHOT_LOC":"\\\\ZOMBILLENIUM\\ZOMBIDAMAS",
        "ZOMB_OUTPUT_LOC":"\\\\ZOMBILLENIUM\\ZOMBIDAMAS",
        "ZOMB_MISC_LOC":"\\\\ZOMBILLENIUM\\ZOMBIDAMAS",
        "ZOMB_PRIVATE_LOC":"\\\\ZOMBILLENIUM\\ZOMBIDAMAS",

        "ZOMB_OUTPUT_PATH_BIS":r"\\NEW_SERVER\output_bis",

        "ZOMB_TOOL_PATH":"\\\\ZOMBILLENIUM\\ZOMBIDAMAS\\zomb\\tool",
        "DAVOS_SITE":"dmn_angouleme",
		
        "XGEN_CONFIG_PATH":r"//ZOMBILLENIUM/ZOMBIDAMAS/zomb/tool/z2k-pipeline-toolkit/launchers/angouleme/xgen",
        "XGEN_PATH":r"//ZOMBILLENIUM/ZOMBIDAMAS/zomb/tool/xgen",
        }

try:
    status = Z2kToolkit(ENVS).runFromCmd()
except:
    os.environ["PYTHONINSPECT"] = "1"
    raise
sys.exit(status)
