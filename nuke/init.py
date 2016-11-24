import os
import sys

import nuke

import cryptomatte_utilities
cryptomatte_utilities.setup_cryptomatte()


userName = os.environ["USERNAME"] #windows user name

sNukePath = os.environ["ZOMB_NUKE_PATH"]
gizmosPath = os.path.join(sNukePath, "gizmos").replace("\\", "/")
if os.path.isdir(gizmosPath):
    nuke.pluginAddPath(gizmosPath)

scriptsPath = os.path.join(sNukePath, "scripts").replace("\\", "/")
if os.path.isdir(scriptsPath):
    nuke.pluginAddPath(scriptsPath)

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

