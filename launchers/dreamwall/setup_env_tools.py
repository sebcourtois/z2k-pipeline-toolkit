import os
osp = os.path
import sys
import subprocess

sys.path.append(osp.join(osp.dirname(__file__), ".."))
from ztk_setup import Z2kToolkit

# Common envs, may be different for each studio
ENVS = {
        "ZOMB_ASSET_PATH":"\\\\Diskstation\\Projects\\zomb\\asset",
        "ZOMB_SHOT_PATH":"\\\\Diskstation\\Projects\\zomb\\shot",
        "ZOMB_OUTPUT_PATH":"\\\\Diskstation\\Projects\\zomb\\output",
        "ZOMB_TOOL_PATH":"Z:\\3D\\Z2K\\MOD\\04_Tools_Soft\\tool"
        "ZOMB_TEXTURE_PATH":"$ZOMB_ASSET_PATH",

        "PRIV_ZOMB_PATH":'\\\\Diskstation\\Projects\\private\\$DAVOS_USER\\zomb',
        }

try:
    Z2kToolkit(ENVS).runFromCmd()
except:
    os.environ["PYTHONINSPECT"] = "1"
    raise
