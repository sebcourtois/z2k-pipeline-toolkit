import os
osp = os.path
import sys
import subprocess

sys.path.append(osp.join(osp.dirname(__file__), ".."))
from ztk_setup import Z2kToolkit

# Common envs, may be different for each studio
ENVS = {
        "ZOMB_ASSET_PATH":"\\\\ZOMBIWALK\\Projects\\zomb\\asset",
        "ZOMB_SHOT_PATH":"\\\\ZOMBIWALK\\Projects\\zomb\\shot",
        "ZOMB_OUTPUT_PATH":"\\\\ZOMBIWALK\\Projects\\zomb\\output",
        "ZOMB_TOOL_PATH":"Z:\\3D\\Z2K\\MOD\\04_Tools_Soft\\tool",

        "PRIV_ZOMB_PATH":'\\\\ZOMBIWALK\\Projects\\private\\$DAVOS_USER\\zomb',
        }

try:
    Z2kToolkit(ENVS).runFromCmd()
except:
    os.environ["PYTHONINSPECT"] = "1"
    raise
