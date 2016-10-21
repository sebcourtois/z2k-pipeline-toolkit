import maya.cmds as mc
#from mtoa.aovs import AOVInterface
from mtoa import aovs

from davos_maya.tool.general import infosFromScene
from davos_maya.tool.general import entityFromScene
from dminutes import maya_scene_operations as mop
reload(mop)

import os
import re
import shutil
import maya.mel
import pymel.core as pm

from dminutes import miscUtils
reload (miscUtils)

def createFxBatchRender(arnoldLic="on"):
    """
    this  script creates a renderbatch.bat file in the private maya working dir, all the variable are set properly
    a 'renderBatch_help.txt' is also created to help on addind render options to the render command

    """
    try:
        davosUser = os.environ["DAVOS_USER"]
    except:
        raise ValueError("#### Error: DAVOS_USER environement variable is not defined, please log to davos")


    workingFile = mc.file(q=True, list=True)[0]
    workingDir = os.path.dirname(workingFile)
    renderBatchHelp_src = miscUtils.normPath(os.path.join(os.environ["ZOMB_TOOL_PATH"], "z2k-pipeline-toolkit", "maya_mods", "zombie", "python", "dminutes", "renderBatch_help.txt"))
    renderBatchHelp_trg = miscUtils.normPath(os.path.join(workingDir, "renderBatch_help.txt"))
    renderBatch_src = miscUtils.normPath(os.path.join(os.environ["ZOMB_TOOL_PATH"], "z2k-pipeline-toolkit", "maya_mods", "zombie", "python", "dminutes", "renderBatch.bat"))
    renderBatch_trg = miscUtils.normPath(os.path.join(workingDir, "renderBatch.bat"))
    setupEnvTools = os.path.normpath(os.path.join(os.environ["Z2K_LAUNCH_SCRIPT"]))
    #location = miscUtils.normPath(setupEnvTools).split("/")[-2]
    #setupEnvToolsNetwork = os.path.join(os.environ["ZOMB_TOOL_PATH"],"z2k-pipeline-toolkit","launchers",location,"setup_env_tools.py")
    #setupEnvToolsNetwork = os.path.join('%USERPROFILE%'+'"',"DEVSPACE","git","z2k-pipeline-toolkit","launchers",location,"setup_env_tools.py")
    userprofile = os.path.normpath(os.path.join(os.environ["USERPROFILE"]))
    setupEnvToolsNetwork = setupEnvTools.replace(userprofile, '%USERPROFILE%')
    renderDesc = os.environ["MAYA_RENDER_DESC_PATH"]
    mayaPlugInPath = os.environ["MAYA_PLUG_IN_PATH"]
    arnoldPluginPath = os.environ["ARNOLD_PLUGIN_PATH"]


    outputFilePath, outputImageName = getRenderOutput()

    zombToolsPath = os.environ["ZOMB_TOOL_PATH"]
    #arnoldToolPath = os.path.normpath(zombToolsPath+"/z2k-pipeline-toolkit/maya_mods/solidangle/mtoadeploy/2016")
    #arnoldToolPath = os.path.normpath('%USERPROFILE%'+"/DEVSPACE/git/z2k-pipeline-toolkit/maya_mods/solidangle/mtoadeploy/2016")
    arnoldToolPath = os.path.normpath(setupEnvToolsNetwork.split("z2k-pipeline-toolkit")[0] + "z2k-pipeline-toolkit/maya_mods/solidangle/mtoadeploy/2016")

    renderCmd = os.path.normpath(os.path.join(os.environ["MAYA_LOCATION"], "bin", "Render.exe"))
    renderCmd = '"{}"'.format(renderCmd)
    if os.path.isfile(renderBatch_trg):
        if os.path.isfile(renderBatch_trg + ".bak"): os.remove(renderBatch_trg + ".bak")
        print "#### Info: old renderBatch.bat backuped: {}.bak".format(os.path.normpath(renderBatch_trg))
        os.rename(renderBatch_trg, renderBatch_trg + ".bak")
    if not os.path.isfile(renderBatchHelp_trg):
        shutil.copyfile(renderBatchHelp_src, renderBatchHelp_trg)
        print "#### Info: renderBatch_help.txt created: {}".format(os.path.normpath(renderBatchHelp_trg))

    shutil.copyfile(renderBatch_src, renderBatch_trg)

    renderBatch_obj = open(renderBatch_trg, "w")
    renderBatch_obj.write("rem #### User Info ####\n")
    renderBatch_obj.write("rem set MAYA_RENDER_DESC_PATH=" + renderDesc + "\n")
    renderBatch_obj.write("rem set ARNOLD_PLUGIN_PATH=" + arnoldPluginPath + "\n")
    renderBatch_obj.write("rem set MAYA_PLUG_IN_PATH=" + mayaPlugInPath + "\n")
    renderBatch_obj.write("rem ###################\n\n")

    renderBatch_obj.write("set render=" + renderCmd + "\n")
    renderBatch_obj.write("set MAYA_RENDER_DESC_PATH=" + arnoldToolPath + "\n\n")

    renderBatch_obj.write("set DAVOS_USER=" + davosUser + "\n\n")

    renderBatch_obj.write('set option=-r arnold -lic ' + arnoldLic + ' -ai:threads 0\n')
    renderBatch_obj.write('set image=-im ' + outputImageName + '\n')
    renderBatch_obj.write('set path=-rd ' + os.path.normpath(outputFilePath) + '\n')
    workingFile = os.path.normpath(workingFile)
    renderBatch_obj.write("set scene=" + workingFile + "\n")
    setupEnvToolsNetwork = setupEnvToolsNetwork.replace('%USERPROFILE%', '%USERPROFILE%"')
    finalCommand = r'"C:\Python27\python.exe" ' + setupEnvToolsNetwork + '" launch %render% %option% %path% %image% %scene%'
    renderBatch_obj.write(finalCommand + "\n")
    renderBatch_obj.write("\n")
    renderBatch_obj.write("pause\n")
    renderBatch_obj.close()
    print "#### Info: renderBatch.bat created: {}".format(os.path.normpath(renderBatch_trg))