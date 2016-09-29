import os
#import cryptomatte_utilities
import sys

import nuke
# import nkFinalLayout as nkFinalLayout
# reload(nkFinalLayout)

import nkU as nkU
reload(nkU)


# zombRootPath = os.environ["ZOMB_ROOT_PATH"]
# user_name = os.environ["USER_NAME"] #davos user name

# os.environ["ZOMB_ASSET_PATH"] = zombRootPath+"/zomb/asset"
# os.environ["ZOMB_SHOT_PATH"] = zombRootPath+"/zomb/shot"
# os.environ["ZOMB_OUTPUT_PATH"] = zombRootPath+"/zomb/output"
# os.environ["ZOMB_MISC_PATH"] = zombRootPath+"/zomb/misc"
# os.environ["ZOMB_TOOL_PATH"] = zombRootPath+"/zomb/tool"

# os.environ["ZOMB_SHOT_LOC"] = zombRootPath+"/private/"+user_name+"/zomb/shot"

nuke.addOnScriptLoad(nkU.initNukeShot)
nuke.addBeforeRender(nkU.createWriteDir)


#sys.path.append(os.path.join(zombRootPath+"/zomb/tool",r"z2k-pipeline-toolkit\python\davos-dev"))
#sys.path.append(os.path.join(zombRootPath+"/zomb/tool",r"z2k-pipeline-toolkit\python\pypeline-tool-devkit"))

#cryptomatte_utilities.setup_cryptomatte()

# userName = os.environ["USERNAME"] #windows user name
# userPath = 'C:/Users/' + userName + '/zombillenium/z2k-pipeline-toolkit/nuke/gizmos'
# if os.path.isdir( userPath ):
#     nuke.pluginAddPath( userPath )

