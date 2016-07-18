import os

zombRootPath = os.environ["ZOMB_ROOT_PATH"]
userName = os.environ["USER_NAME"]

os.environ["ZOMB_ASSET_PATH"] = zombRootPath+"/zomb/asset"
os.environ["ZOMB_SHOT_PATH"] = zombRootPath+"/zomb/shot"
os.environ["ZOMB_OUTPUT_PATH"] = zombRootPath+"/zomb/output"
os.environ["ZOMB_MISC_PATH"] = zombRootPath+"/zomb/misc"
os.environ["ZOMB_TOOL_PATH"] = zombRootPath+"/zomb/tool"


os.environ["ZOMB_SHOT_LOC"] = zombRootPath+"/private/"+userName+"/zomb/shot"

import nkFinalLayout as nkFinalLayout
reload(nkFinalLayout)