import os
import sys

import cryptomatte_utilities
cryptomatte_utilities.setup_cryptomatte()

userName = os.environ["USERNAME"] #windows user name
gizmosPath = 'C:/Users/' + userName + '/zombillenium/z2k-pipeline-toolkit/nuke/gizmos'
if os.path.isdir( gizmosPath ):
    nuke.pluginAddPath( gizmosPath )
	
## Bypassed 30092016
# scriptsPath = 'C:/Users/' + userName + '/zombillenium/z2k-pipeline-toolkit/nuke/scripts'
# if os.path.isdir( scriptsPath ):
    # nuke.pluginAddPath( scriptsPath )
	 
## Bypassed 30092016
# import nuke
# import nkFinalLayout as nkFinalLayout
# reload(nkFinalLayout)

## Bypassed 30092016
# import nkU as nkU
# reload(nkU)


# zombRootPath = os.environ["ZOMB_ROOT_PATH"]
# user_name = os.environ["USER_NAME"] #davos user name

# os.environ["ZOMB_ASSET_PATH"] = zombRootPath+"/zomb/asset"
# os.environ["ZOMB_SHOT_PATH"] = zombRootPath+"/zomb/shot"
# os.environ["ZOMB_OUTPUT_PATH"] = zombRootPath+"/zomb/output"
# os.environ["ZOMB_MISC_PATH"] = zombRootPath+"/zomb/misc"
# os.environ["ZOMB_TOOL_PATH"] = zombRootPath+"/zomb/tool"

# os.environ["ZOMB_SHOT_LOC"] = zombRootPath+"/private/"+user_name+"/zomb/shot"

## Bypassed 30092016
# nuke.addOnScriptLoad(nkU.initNukeShot)
# nuke.addBeforeRender(nkU.createWriteDir)

#sys.path.append(os.path.join(zombRootPath+"/zomb/tool",r"z2k-pipeline-toolkit\python\davos-dev"))
#sys.path.append(os.path.join(zombRootPath+"/zomb/tool",r"z2k-pipeline-toolkit\python\pypeline-tool-devkit"))






