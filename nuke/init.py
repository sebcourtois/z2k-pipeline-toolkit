import os
import sys

import nuke

import cryptomatte_utilities
cryptomatte_utilities.setup_cryptomatte()



userName = os.environ["USERNAME"] #windows user name

if "DEVSPACE" in os.environ["NUKE_PATH"]:
	print  "devmode", os.environ["NUKE_PATH"]
	gizmosPath = 'C:/Users/' + userName + '/DEVSPACE/git/z2k-pipeline-toolkit/nuke/gizmos'
	if os.path.isdir( gizmosPath ):
	    nuke.pluginAddPath( gizmosPath )

	scriptsPath = 'C:/Users/' + userName + '/DEVSPACE/git/z2k-pipeline-toolkit/nuke/scripts'
	print scriptsPath
	if os.path.isdir( scriptsPath ):
	    nuke.pluginAddPath( scriptsPath )

else:
	gizmosPath = 'C:/Users/' + userName + '/zombillenium/z2k-pipeline-toolkit/nuke/gizmos'
	if os.path.isdir( gizmosPath ):
	    nuke.pluginAddPath( gizmosPath )

	scriptsPath = 'C:/Users/' + userName + '/zombillenium/z2k-pipeline-toolkit/nuke/scripts'
	print scriptsPath
	if os.path.isdir( scriptsPath ):
	    nuke.pluginAddPath( scriptsPath )


import nkFinalLayout as nkFinalLayout
reload(nkFinalLayout)

import nkU as nkU
reload(nkU)


nuke.addOnScriptLoad(nkU.initNukeShot)
nuke.addBeforeRender(nkU.createWriteDir)


#sys.path.append(os.path.join(zombRootPath+"/zomb/tool",r"z2k-pipeline-toolkit\python\davos-dev"))
#sys.path.append(os.path.join(zombRootPath+"/zomb/tool",r"z2k-pipeline-toolkit\python\pypeline-tool-devkit"))

#cryptomatte_utilities.setup_cryptomatte()

# userName = os.environ["USERNAME"] #windows user name
# userPath = 'C:/Users/' + userName + '/zombillenium/z2k-pipeline-toolkit/nuke/gizmos'
# if os.path.isdir( userPath ):
#     nuke.pluginAddPath( userPath )

