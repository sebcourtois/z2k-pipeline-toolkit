import os
osp = os.path
import sys


sys.path.append(osp.join(osp.dirname(__file__), ".."))
from ztk_setup import Z2kToolkit

# Common envs, may be different for each studio
ENVS = {
		"ZOMB_ASSET_PATH":"\\\\Diskstation\\Projects\\zombtest\\asset",
		"ZOMB_SHOT_PATH":"\\\\Diskstation\\Projects\\zombtest\\shot",
		"ZOMB_OUTPUT_PATH":"\\\\Diskstation\\Projects\\zombtest\\output",
        "ZOMB_TOOL_PATH":"\\\\Diskstation\\Projects\\zomb\\tool",

		"PRIV_ZOMB_PATH":'\\\\Diskstation\\Projects\\private\\$DAVOS_USER\\zombtest',
		"DAVOS_INIT_PROJECT":"zombtest"
		}

try:
	Z2kToolkit(ENVS).runFromCmd()
except:
    os.environ["PYTHONINSPECT"] = "1"
    raise
