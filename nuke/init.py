import os
import sys

import nuke

import cryptomatte_utilities
cryptomatte_utilities.setup_cryptomatte()


userName = os.environ["USERNAME"] #windows user name

sNukePath = os.path.dirname(__file__)
gizmosPath = os.path.join(sNukePath, "gizmos").replace("\\", "/")
if os.path.isdir(gizmosPath):
    nuke.pluginAddPath(gizmosPath)

scriptsPath = os.path.join(sNukePath, "scripts").replace("\\", "/")
if os.path.isdir(scriptsPath):
    nuke.pluginAddPath(scriptsPath)

pythonPath = os.path.join(sNukePath, "python").replace("\\", "/")
if os.path.isdir(scriptsPath):
    nuke.pluginAddPath(pythonPath)

iconsPath = os.path.join(sNukePath, "icons").replace("\\", "/")
if os.path.isdir(scriptsPath):
    nuke.pluginAddPath(iconsPath)

NodePresetPath = os.path.join(sNukePath, "NodePreset").replace("\\", "/")
if os.path.isdir(scriptsPath):
    nuke.pluginAddPath(NodePresetPath)
#---------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------ToolBox from Compositing Angouleme----------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------#

# nuke.pluginAddPath( os.path.join(os.path.expanduser("~"), "zombillenium\\z2k-pipeline-toolkit\\nuke\\python"))
# nuke.pluginAddPath( os.path.join(os.path.expanduser("~"), "zombillenium\\z2k-pipeline-toolkit\\nuke\\icons"))
# nuke.pluginAddPath( os.path.join(os.path.expanduser("~"), "zombillenium\\z2k-pipeline-toolkit\\nuke\\NodePreset"))

import nkFinalLayout as nkFinalLayout
reload(nkFinalLayout)

import nkU as nkU
reload(nkU)

nuke.addOnScriptLoad(nkU.initNukeShot)
nuke.addBeforeRender(nkU.createWriteDir)

nuke.addOnScriptSave(nkU.createCompoBatchFiles)


#sys.path.append(os.path.join(zombRootPath+"/zomb/tool",r"z2k-pipeline-toolkit\python\davos-dev"))
#sys.path.append(os.path.join(zombRootPath+"/zomb/tool",r"z2k-pipeline-toolkit\python\pypeline-tool-devkit"))

#cryptomatte_utilities.setup_cryptomatte()

# userName = os.environ["USERNAME"] #windows user name
# userPath = 'C:/Users/' + userName + '/zombillenium/z2k-pipeline-toolkit/nuke/gizmos'
# if os.path.isdir( userPath ):
#     nuke.pluginAddPath( userPath )

