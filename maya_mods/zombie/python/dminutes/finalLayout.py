import maya.cmds as mc
#from mtoa.aovs import AOVInterface
from mtoa import aovs

import miscUtils
import os
import re
import shutil
import maya.mel
import pymel.core as pm

from dminutes import rendering
reload (rendering)
from davos.core.damproject import DamProject

from pprint import pprint

def layerOverrideFLCustomShader(dmnToonList=[], dmnInput = "dmnMask08", layerName = "lay_finalLayout_00",gui= True):
    log = miscUtils.LogBuilder(gui=gui, funcName ="layerOverrideFLCustomShader")

    if not dmnToonList:
        dmnToonList = mc.ls(type="dmnToon")

    preConnectedInputL = []
    failedDmnToonL = []
    SuccededDmnToonL = []



    for each in dmnToonList:

        # dmnInputConnection = mc.listConnections(each+'.'+dmnInput,connections = False, destination = False, source =True, plugs = True)
        # if dmnInputConnection:
        #     preConnectedInputL.append(each)
        
        aiUtilNode = mc.shadingNode("aiUtility", asShader=True, name = "mat_finalLayout_aiUtility")
        mc.setAttr(aiUtilNode+'.shadeMode', 2)
        mc.setAttr(aiUtilNode+'.colorMode', 21)
        aiAmbientOccNode = mc.shadingNode("aiAmbientOcclusion", asShader=True, name = "mat_finalLayout_aiAmbientOcclusion")
        mc.setAttr(aiAmbientOccNode+'.samples', 2)
        mc.setAttr(aiAmbientOccNode+'.spread', 0.8)
        mc.setAttr(aiAmbientOccNode+'.farClip', 10)
        mc.connectAttr(aiUtilNode+'.outColor', aiAmbientOccNode+'.white', force =True)

        try: 
            mc.editRenderLayerAdjustment(each+"."+dmnInput, layer=layerName)
            mc.connectAttr(aiAmbientOccNode+'.outColor', each+'.'+dmnInput, force =True)

            opacityConnection = mc.listConnections(each+'.opacity',connections = False, destination = False, source =True, plugs = True)
            opacityValue = mc.getAttr(each+'.opacity')
            if opacityConnection:
                opacityConnection = opacityConnection [0]
                mc.connectAttr(opacityConnection, aiAmbientOccNode+'.opacity', force =True)
            else:
                mc.setAttr(aiAmbientOccNode+'.opacity', opacityValue[0][0], opacityValue[0][1] ,opacityValue[0][2], type = "double3")
            SuccededDmnToonL.append(each)

        except Exception,err:
            log.printL("e", "{}".format(err))
            failedDmnToonL.append(each)

    # if preConnectedInputL:
    #     log.printL("i", "{} noded(s) skipped since '{}' input is already connected: '{}'".format( len(preConnectedInputL), dmnInput ,preConnectedInputL))
    if failedDmnToonL:
        log.printL("e", "{} noded(s) could not be proceeded : '{}'".format( len(failedDmnToonL), dmnInput ,failedDmnToonL))
    if SuccededDmnToonL:
        log.printL("i", "{} noded(s) proceeded: '{}'".format( len(SuccededDmnToonL) ,SuccededDmnToonL))



def importFinalLayoutLight( gui=True, lgtRig="lgt_finalLayout_directional01"):

    log = miscUtils.LogBuilder(gui=gui, funcName ="createFinalLayoutLight")

    if mc.ls("|shot"):        
        mainFilePath = pm.sceneName()
        mainFilePathElem = mainFilePath.split("/")
        assetName = mainFilePathElem[-2]
        assetType = mainFilePathElem[-3]
        assetFileType = mainFilePathElem[-1].split("-")[0].split("_")[-1]
        if  mainFilePathElem[-5] == "shot"or mainFilePathElem[-6] == "shot":
            lgtRigFilePath = miscUtils.normPath(miscUtils.pathJoin("$ZOMB_MISC_PATH","rendu","lightRig",lgtRig+".ma"))
            lgtRigFilePath_exp = miscUtils.normPath(os.path.expandvars(os.path.expandvars(lgtRigFilePath)))
        else:
            txt= "You are not working in a 'shot' structure directory"
            log.printL("e", txt, guiPopUp = True)
            raise ValueError(txt)
    else :
        log.printL("e", "No '|shot' could be found in this scene", guiPopUp = True)
        raise ValueError(txt)

    grpLgt =  mc.ls("grp_light*", l=True)
    if grpLgt: 
        mc.delete(grpLgt)


    mc.file( lgtRigFilePath_exp, i= True, type= "mayaAscii", ignoreVersion=True, preserveReferences= False )
    log.printL("i", "Importing '{}'".format(lgtRigFilePath_exp))

    finalLayLight = mc.ls("lgt_finalLayout*", type="light",l=True)    
    if finalLayLight:
        if len(finalLayLight)>1:
            txt= "several '|shot|grp_light|lgt_finalLayout*'found, proceeding with the first one: '{}'".format(finalLayLight),
            log.printL("w", txt)
        finalLayLight = mc.ls(finalLayLight[0].replace("|"+finalLayLight[0].split("|")[-1],""), type="transform")[-1]
        mc.group( finalLayLight, name="grp_light",parent="|shot")
        finalLayLight = mc.ls("|shot|grp_light|lgt_finalLayout*", l=True)[0]


        from davos_maya.tool.general import entityFromScene
        from dminutes import maya_scene_operations as mop
        damShot = entityFromScene()
        oShotCam = mop.getShotCamera(damShot.name)
        if oShotCam:                 
            shotCam = oShotCam.name() 
            mc.orientConstraint(shotCam , finalLayLight, name="cst_orientLightAsCAm")
        else: 
            txt= "could not find light: |shot|grp_light|"+lgtRig+"*"
            log.printL("e", txt)
    return dict(resultB=log.resultB, logL=log.logL)


def createRenderLayerLegacy(layerName="lay_finalLayout_00", setMeshCacheL=[],lightL=["lgt_finalLayout_directional"], gui= True):
    log = miscUtils.LogBuilder(gui=gui, funcName ="createFinalLayoutLayer")
    layerItemL=[]
   
    if not mc.ls(layerName, type = "renderLayer"):
        mc.createRenderLayer(name=layerName, empty=True)
        txt= "New '{}' empty render layer created".format(layerName)
        log.printL("i", txt)

    if not setMeshCacheL:
        objectSetL = mc.ls(exactType = "objectSet")
        for each in objectSetL:
            if "set_meshCache" in each:
                setMeshCacheL.append(each)
                layerItemL.extend(mc.sets(each, q=True ))
    else:
        for each in setMeshCacheL:
            layerItemL.extend(mc.sets(each, q=True ))

    mc.setAttr("defaultRenderLayer.renderable", 0)
    mc.editRenderLayerGlobals( currentRenderLayer=layerName )
    mc.editRenderLayerMembers(layerName,layerItemL)
    mc.editRenderLayerMembers(layerName,lightL)
    mc.setAttr(layerName+".renderable", 1)

    txt= "Added '{:>3}' object(s) to '{}' render layer. Content of following 'set_meshCache': '{}' ".format(len(layerItemL), layerName,setMeshCacheL)
    log.printL("i", txt)
    txt= "Added '{:>3}' light(s) to '{}' render layer: '{}' ".format(len(lightL), layerName,lightL)
    log.printL("i", txt)




def layerOverrideToonWeightOff(dmnToonList=[], layerName = "lay_finalLayout_00", gui= True):
    log = miscUtils.LogBuilder(gui=gui, funcName ="dmnToonOverrideToonWeightOff")

    if not dmnToonList:
        dmnToonList = mc.ls(type="dmnToon")

    overidedDmnToonL = []

    for each in dmnToonList:
        dmnInputConnection = mc.listConnections(each+'.selfShadows',connections = False, destination = False, source =True, plugs = True)
        if mc.getAttr(each+".selfShadows") !=1 or dmnInputConnection:
            mc.editRenderLayerAdjustment(each+".toonWeight", layer=layerName)
            mc.setAttr (each+".toonWeight",0)
            overidedDmnToonL.append(each)

    if overidedDmnToonL:
        log.printL("i", "Toon weight overrided to 0 for layer '{}' on '{}'' dmntoon noded(s): '{}'".format(layerName, len(overidedDmnToonL), overidedDmnToonL))


def createNukeBatch(gui=True):
    """
    this  script creates a renderbatch.bat file in the private maya working dir, all the variable are set properly
    a 'renderBatch_help.txt' is also created to help on addind render options to the render command

    """
#    sShotName = "sq6660_sh0050a"
    sShotName = mc.getAttr('defaultRenderGlobals.imageFilePrefix')
    proj = DamProject("zombillenium", user="rrender", password="arn0ld&r0yal")
    #shotgundb = proj._shotgundb
    damShot = proj.getShot(sShotName)
    sgTaskList = damShot.listSgTasks(moreFilters=[["content", "in", ("FL_Art", "Anim_MeshCache")]])
    pprint(sgTaskList[0])
    if sgTaskList[0]['sg_status_list'] == "vwd" or sgTaskList[0]['sg_status_list'] == "rtk" or sgTaskList[0]['sg_status_list'] == "fin" :
        #print sgTaskList[1]['sg_status_list']
        sNewStatus = "clc"
        proj.updateSgEntity(sgTaskList[1], sg_status_list=sNewStatus)
    else:
        sNewStatus = "clc"
        proj.updateSgEntity(sgTaskList[0], sg_status_list=sNewStatus)

    log = miscUtils.LogBuilder(gui=gui, funcName="createNukeBatch")

    zombToolsPath = os.environ["ZOMB_TOOL_PATH"]
    workingFile = mc.file(q=True, sn=True)
    workingDir = os.path.dirname(workingFile)
    renderBatchHelp_src = miscUtils.normPath(os.path.join(os.environ["ZOMB_TOOL_PATH"],"z2k-pipeline-toolkit","maya_mods","zombie","python","dminutes","nukeBatch_help.txt"))
    renderBatchHelp_trg = miscUtils.normPath(os.path.join(workingDir,"nukeBatch_help.txt"))
    renderBatch_src = miscUtils.normPath(os.path.join(os.environ["ZOMB_TOOL_PATH"],"z2k-pipeline-toolkit","maya_mods","zombie","python","dminutes","nukeBatch.bat"))
    renderBatch_trg = miscUtils.normPath(os.path.join(workingDir,"nukeBatch.bat"))

    try:
        versionNumber = os.path.basename(workingFile).split("-")[1]
        versionNumber = versionNumber.split(".")[0]
    except:
        versionNumber = "v000"
    renderDir = os.path.dirname(workingFile)+"/render-"+versionNumber


    if os.path.isfile(renderBatch_trg):
        if os.path.isfile(renderBatch_trg+".bak"): os.remove(renderBatch_trg+".bak")
        print "#### Info: old nukeBatch.bat backuped: {}.bak".format(os.path.normpath(renderBatch_trg))
        os.rename(renderBatch_trg, renderBatch_trg+".bak")
    if not os.path.isfile(renderBatchHelp_trg):
        shutil.copyfile(renderBatchHelp_src, renderBatchHelp_trg)
        print "#### Info: nukeBatch_help.txt created: {}".format(os.path.normpath(renderBatchHelp_trg))

    shutil.copyfile(renderBatch_src, renderBatch_trg)
    if os.environ["davos_site"] == "dmn_paris":
        licenceLocation=r"WS-041@4101"
        nukePath= r"\\Zombiwalk\z2k\06_PARTAGE\royalRenderShare\nuke\Nuke10.0.exe"
        nukePathLoc= r"rem C:\Program Files\Nuke10.0v1\Nuke10.0.exe"
    elif os.environ["davos_site"] == "dmn_paris":
        licenceLocation=r"???????"
        nukePath= r"rem merci de copier nuke sur le serveur et de donner le chemin a Alex"
        nukePathLoc= r"C:\Program Files\Nuke10.0v1\Nuke10.0.exe"
    else:
        licenceLocation=r"???????"
        nukePath= r"rem merci de copier nuke sur le serveur et de donner le chemin a Alex"
        nukePathLoc= r"C:\Program Files\Nuke10.0v1\Nuke10.0.exe"


    nukeScript = miscUtils.normPath(zombToolsPath + r"\template\nuke\finalLayoutTemplate.nk")
    renderBatch_obj = open(renderBatch_trg, "w")
    renderBatch_obj.write("set foundry_LICENSE="+licenceLocation+"\n")
    renderBatch_obj.write(r'''set "NUKE_PATH=C:\Users\%USERNAME%\zombillenium\z2k-pipeline-toolkit\nuke"'''+"\n")
    renderBatch_obj.write(r'''set "ZOMB_NUKE_PATH=C:\Users\%USERNAME%\zombillenium\z2k-pipeline-toolkit\nuke"''' + "\n")

    renderBatch_obj.write("set nuke="+nukePath+"\n")
    renderBatch_obj.write("rem set nuke="+nukePathLoc+"\n")
    renderBatch_obj.write("set nkscript="+nukeScript+"\n")
    renderBatch_obj.write("set argv0="+renderDir+"\n")

    #finalCommand = r'"C:\Python27\python.exe" "C:\users\%USERNAME%\zombillenium\z2k-pipeline-toolkit\launchers\paris\setup_env_tools.py" launch %nuke% -x %nkscript% %argva% %argv0%'
    finalCommand = r'%nuke% -x %nkscript% %argva% %argv0%'
    publish_movies = r'"C:\Python27\python.exe" "%USERPROFILE%\zombillenium\z2k-pipeline-toolkit\launchers\paris\setup_env_tools.py" launch "C:\Python27\python.exe" "%USERPROFILE%\zombillenium\z2k-pipeline-toolkit\scripts\FL_post_render.py" %argv0%'
    renderBatch_obj.write(finalCommand+"\n")
    renderBatch_obj.write(publish_movies + "\n")
    renderBatch_obj.write("\n")
    #renderBatch_obj.write("pause\n")
    renderBatch_obj.close()
    print "#### Info: nukeBatch.bat created: {}".format(os.path.normpath(renderBatch_trg))

    
