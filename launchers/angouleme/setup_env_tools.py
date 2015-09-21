import os
osp = os.path
import sys
import subprocess

sys.path.append(osp.join(osp.dirname(__file__), ".."))
from ztk_setup import Z2kToolkit

# Common envs, may be different for each studio
ENVS = {
        "ZOMB_ASSET_PATH":"\\\\ZOMBILLENIUM\\zomb\\PRE-PROD\\assets_3d",
        "ZOMB_SHOT_PATH":"\\\\ZOMBILLENIUM\\zomb\\PRE-PROD\\shot",
        "ZOMB_OUTPUT_PATH":"\\\\ZOMBILLENIUM\\zomb\\PRE-PROD\\output",
        "ZOMB_TOOL_PATH":"\\\\ZOMBILLENIUM\\zomb\\PRE-PROD\\tool",

        "PRIV_ZOMB_PATH":'\\\\ZOMBIWALK\\Projects\\private\\$DAVOS_USER\\zomb',
        }

try:
    Z2kToolkit(ENVS).runFromCmd()
except:
    os.environ["PYTHONINSPECT"] = "1"
    raise
