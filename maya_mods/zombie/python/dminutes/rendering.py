import maya.cmds as mc
#from mtoa.aovs import AOVInterface
from mtoa import aovs
from mtoa.core import createOptions

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
from dminutes import layerManager
reload (layerManager)

#createOptions()

if pm.window("unifiedRenderGlobalsWindow", exists=True):
    pm.deleteUI("unifiedRenderGlobalsWindow")

if pm.window("hyperShadePanel1Window", exists=True):
    pm.deleteUI("hyperShadePanel1Window")

def setArnoldRenderOption(outputFormat, renderMode=""):

    """
    this scripts sets the Arnold render options for production
    it also gets the rendering camera, and set the aovs
    sting --> "outputFormat": define the frame rendering format, only "png" and "exr" accepted.
                                "exr" also activate the AOVss
    """

    print ""
    print "#### {:>7}: runing rendering.setArnoldRenderOption(outputFormat = {})".format("info" , outputFormat)
    aspectRatio = 1.85

    if renderMode == "":
        if mc.ls("|shot") and (mc.file(q=True, sn=True).split("/")[-4]) == "shot":
            renderMode = "render"

            print "#### info: Lighting mode render options"
        else:
            renderMode = "shading"
            print "#### info: Shading mode render options"

    #TEMPORAIRE
    mc.workspace(fileRule=["images", "images"])

    mmToIncheFactor = 0.0393700787401575
    camApertureInche = 35 * mmToIncheFactor

    #get the "cam_" camera, stops if nothing found
    # if the camera has  an "aspectRatio" extra attribute sets the camera according to it
    # make the camera renderable
    if renderMode != "shading":
        myCamName = mc.ls('*:cam_shot_default*', type="camera")
    else:
        myCamName = mc.ls('*:cam_*', type="camera")

    if myCamName :
        if len(myCamName) > 1:
            print "#### warning: several 'cam_*' have been found, proceeding with: " + myCamName[0]
        else :
            print "#### info: one camera found, proceeding with: " + myCamName[0]
        myCamName = myCamName[0]
        if mc.attributeQuery ("aspectRatio", node=myCamName , exists=True):
            aspectRatio = mc.getAttr (myCamName + ".aspectRatio")
            mc.camera(myCamName, e=True, horizontalFilmAperture=camApertureInche, verticalFilmAperture=camApertureInche / aspectRatio)
        else:
            aspectRatio = mc.camera(myCamName, q=True, aspectRatio=True)

        allCam = mc.ls(type="camera")
        for eachCam in allCam:
            if eachCam != myCamName:
                mc.setAttr (eachCam + ".renderable", 0)
            else:
                #mc.setAttr (myCamName + ".renderable", 1)
                pass

    else:
        print "#### error: no '*:cam_*' camera could be found in the scene"




    ### Maya settings
    mc.setAttr("defaultResolution.pixelAspect", 1)
    mc.setAttr("defaultResolution.deviceAspectRatio", aspectRatio)
    if aspectRatio != 1:
        if renderMode == "render":
            mc.setAttr("defaultResolution.width", 2048)
            mc.setAttr("defaultResolution.height", 2048 / aspectRatio)
        else:
            mc.setAttr("defaultResolution.width", 1920)
            mc.setAttr("defaultResolution.height", 1920 / aspectRatio)
    else:
        mc.setAttr("defaultResolution.width", 1080)
        mc.setAttr("defaultResolution.height", 1080)
    mc.colorManagementPrefs(e=True, cmEnabled=False)

    animationStartTime = mc.playbackOptions(animationStartTime=True , q=True)
    animationEndTime = mc.playbackOptions(animationEndTime=True , q=True)

    mc.setAttr("defaultRenderGlobals.startFrame", animationStartTime)
    mc.setAttr("defaultRenderGlobals.endFrame", animationEndTime)
    mc.setAttr("defaultRenderGlobals.byFrameStep", 1)
    mc.setAttr("defaultRenderGlobals.outFormatControl", 0)
    mc.setAttr("defaultRenderGlobals.animation", 1)
    mc.setAttr("defaultRenderGlobals.putFrameBeforeExt", 1)
    mc.setAttr("defaultRenderGlobals.extensionPadding", 4)
    mc.setAttr("defaultRenderGlobals.currentRenderer", "arnold", type="string")

    maya.mel.eval('setMayaSoftwareFrameExt(3,0)')

    #arnold Settings

    #Image output settings
    mc.setAttr("defaultArnoldDriver.aiTranslator", "png", type="string")
    mc.setAttr("defaultArnoldDriver.pngFormat", 0)

    mc.setAttr("defaultArnoldDriver.aiTranslator", "exr", type="string")
    mc.setAttr("defaultArnoldDriver.exrCompression", 3)#zip
    mc.setAttr("defaultArnoldDriver.halfPrecision", 1)
    mc.setAttr("defaultArnoldDriver.autocrop", 1)
    mc.setAttr("defaultArnoldDriver.mergeAOVs", 1)
    mc.setAttr("defaultArnoldRenderOptions.aovMode", 2)#batch only
    mc.setAttr("defaultArnoldRenderOptions.threads_autodetect", 0)
    mc.setAttr("defaultArnoldRenderOptions.threads", -1)

    mainFilePath = mc.file(q=True, sn=True)
    mainFilePathElem = mainFilePath.split("/")
    if mainFilePathElem[-4] == "asset" or mainFilePathElem[-5] == "shot":
        fileRadical = os.path.basename(mainFilePath).split("-")[0]
        imageNameS = fileRadical.replace("_" + fileRadical.split("_")[-1], "")
        mc.setAttr("defaultRenderGlobals.imageFilePrefix", imageNameS, type="string")

    createAovs(renderMode=renderMode)



    if outputFormat == "png":
        mc.setAttr("defaultArnoldDriver.aiTranslator", "png", type="string")
        mc.setAttr("defaultArnoldRenderOptions.aovMode", 0)
    elif  outputFormat == "jpg":
        mc.setAttr("defaultArnoldDriver.aiTranslator", "jpeg", type="string")
        mc.setAttr("defaultArnoldDysplayDriver.aiTranslator", "jpeg", type="string")
        mc.setAttr("defaultArnoldRenderOptions.aovMode", 0)
    elif  outputFormat == "exr":
        mc.setAttr("defaultArnoldDriver.aiTranslator", "exr", type="string")
        mc.setAttr("defaultArnoldDysplayDriver.aiTranslator", "exr", type="string")
        mc.setAttr("defaultArnoldRenderOptions.aovMode", 1)

    mc.setAttr("defaultArnoldRenderOptions.GIDiffuseSamples", 0)
    mc.setAttr("defaultArnoldRenderOptions.GIGlossySamples", 5)
    mc.setAttr("defaultArnoldRenderOptions.GIRefractionSamples", 0)
    mc.setAttr("defaultArnoldRenderOptions.GISssSamples", 0)
    mc.setAttr("defaultArnoldRenderOptions.GIVolumeSamples", 3)
    mc.setAttr("defaultArnoldRenderOptions.use_sample_clamp", 0)
    mc.setAttr("defaultArnoldRenderOptions.AASampleClamp", 0)
    mc.setAttr("defaultArnoldRenderOptions.use_sample_clamp_AOVs", 0)
    mc.setAttr("defaultArnoldRenderOptions.use_existing_tiled_textures", 1)
    mc.setAttr("defaultArnoldRenderOptions.skipLicenseCheck", 1)
    mc.setAttr("defaultArnoldRenderOptions.log_verbosity", 1)#warnig + info


    if renderMode == 'shading':
        mc.setAttr("defaultArnoldRenderOptions.AASamples", 4)
        mc.setAttr("defaultArnoldRenderOptions.motion_blur_enable", 0)
        mc.setAttr("defaultArnoldRenderOptions.force_texture_cache_flush_after_render", 1)
    elif renderMode == 'render':
        mc.setAttr("defaultArnoldRenderOptions.AASamples", 8)
        mc.setAttr("defaultArnoldRenderOptions.motion_blur_enable", 1)
        if mc.getAttr("defaultArnoldRenderOptions.motion_frames") > 0.25 :
            pass
        else:
            mc.setAttr("defaultArnoldRenderOptions.motion_frames", 0.25)

    elif renderMode == 'finalLayout':
        mc.setAttr("defaultArnoldRenderOptions.ignoreBump", 1)
        mc.setAttr("defaultArnoldRenderOptions.AASamples", 2)
        mc.setAttr("defaultArnoldRenderOptions.motion_blur_enable", 1)
        mc.setAttr("defaultArnoldRenderOptions.motion_frames", 0.25)
        mc.setAttr("defaultArnoldRenderOptions.GIGlossySamples", 2)
        mc.setAttr("defaultArnoldRenderOptions.aovMode", 1)

    mc.setAttr("defaultArnoldRenderOptions.GITotalDepth", 4)
    mc.setAttr("defaultArnoldRenderOptions.GIDiffuseDepth", 0)
    mc.setAttr("defaultArnoldRenderOptions.GIGlossyDepth", 1)
    mc.setAttr("defaultArnoldRenderOptions.GIDiffuseDepth", 0)
    mc.setAttr("defaultArnoldRenderOptions.GIRefractionDepth", 4)
    mc.setAttr("defaultArnoldRenderOptions.GIReflectionDepth", 2)
    mc.setAttr("defaultArnoldRenderOptions.GIVolumeDepth", 1)
    mc.setAttr("defaultArnoldRenderOptions.autoTransparencyDepth", 10)

    print "#### info: render options are now production ready"


def setArnoldRenderOptionShot(outputFormat="exr", renderMode='finalLayout', gui=True):

    """
    this scripts sets the Arnold render options for production
    it also gets the rendering camera, and set the aovs
    sting --> "outputFormat": define the frame rendering format, only "png" and "exr" accepted.
                                "exr" also activate the AOVss
    """
    log = miscUtils.LogBuilder(gui=gui, funcName="setArnoldRenderOptionShot")

    if renderMode == 'finalLayout':
        setRenderCamera(leftCam = False, rightCam = False)
    else:
        setRenderCamera(leftCam=True, rightCam=True)  #temprairement off on fait pour le moment encore les rendus avec la defaut cam
        #setRenderCamera(leftCam = False, rightCam = False)

    mc.colorManagementPrefs(e=True, cmEnabled=False)

    animationStartTime = mc.playbackOptions(animationStartTime=True , q=True)
    animationEndTime = mc.playbackOptions(animationEndTime=True , q=True)

    miscUtils.setAttrC("defaultRenderGlobals.startFrame", animationStartTime)
    miscUtils.setAttrC("defaultRenderGlobals.endFrame", animationEndTime)
    miscUtils.setAttrC("defaultRenderGlobals.byFrameStep", 1)
    miscUtils.setAttrC("defaultRenderGlobals.outFormatControl", 0)
    miscUtils.setAttrC("defaultRenderGlobals.animation", 1)
    miscUtils.setAttrC("defaultRenderGlobals.putFrameBeforeExt", 1)
    miscUtils.setAttrC("defaultRenderGlobals.extensionPadding", 4)
    miscUtils.setAttrC("defaultRenderGlobals.currentRenderer", "arnold", type="string")

    maya.mel.eval('setMayaSoftwareFrameExt(3,0)')

    deleteAovs(GUI=True)
    createAovs(renderMode=renderMode)

    #arnold Settings

    #Image output settings
    miscUtils.setAttrC("defaultArnoldDriver.aiTranslator", "png", type="string")
    miscUtils.setAttrC("defaultArnoldDriver.pngFormat", 0)

    miscUtils.setAttrC("defaultArnoldDriver.aiTranslator", "exr", type="string")
    miscUtils.setAttrC("defaultArnoldDriver.exrCompression", 3)#zip
    miscUtils.setAttrC("defaultArnoldDriver.halfPrecision", 1)
    miscUtils.setAttrC("defaultArnoldDriver.autocrop", 1)
    miscUtils.setAttrC("defaultArnoldDriver.mergeAOVs", 1)
    miscUtils.setAttrC("defaultArnoldRenderOptions.threads_autodetect", 0)
    miscUtils.setAttrC("defaultArnoldRenderOptions.threads", -1)
    miscUtils.setAttrC("defaultArnoldRenderOptions.aovMode", 1)

    if outputFormat == "png":
        miscUtils.setAttrC("defaultArnoldDriver.aiTranslator", "png", type="string")
        mc.setAttr("defaultArnoldDriver.mergeAOVs", 0)
    elif  outputFormat == "jpg":
        miscUtils.setAttrC("defaultArnoldDriver.aiTranslator", "jpeg", type="string")
        miscUtils.setAttrC("defaultArnoldDisplayDriver.aiTranslator", "jpeg", type="string")
        mc.setAttr("defaultArnoldDriver.mergeAOVs", 0)
    if outputFormat == "png":
        miscUtils.setAttrC("defaultArnoldDriver.aiTranslator", "png", type="string")
        mc.setAttr("defaultArnoldDriver.mergeAOVs", 0)
    elif  outputFormat == "exr":
        miscUtils.setAttrC("defaultArnoldDriver.aiTranslator", "exr", type="string")
        miscUtils.setAttrC("defaultArnoldDisplayDriver.aiTranslator", "exr", type="string")
        mc.setAttr("defaultArnoldDriver.mergeAOVs", 1)


    mainFilePath = mc.file(q=True, sn=True)
    mainFilePathElem = mainFilePath.split("/")
    if mainFilePathElem[-4] == "asset" or mainFilePathElem[-5] == "shot":
        fileRadical = os.path.basename(mainFilePath).split("-")[0]
        imageNameS = fileRadical.replace("_" + fileRadical.split("_")[-1], "")
        mc.setAttr("defaultRenderGlobals.imageFilePrefix", imageNameS, type="string")

    miscUtils.setAttrC("defaultArnoldRenderOptions.GIDiffuseSamples", 0)
    miscUtils.setAttrC("defaultArnoldRenderOptions.GIGlossySamples", 5)
    miscUtils.setAttrC("defaultArnoldRenderOptions.GIRefractionSamples", 0)
    miscUtils.setAttrC("defaultArnoldRenderOptions.GISssSamples", 0)
    miscUtils.setAttrC("defaultArnoldRenderOptions.GIVolumeSamples", 3)
    miscUtils.setAttrC("defaultArnoldRenderOptions.use_sample_clamp", 0)
    miscUtils.setAttrC("defaultArnoldRenderOptions.AASampleClamp", 0)
    miscUtils.setAttrC("defaultArnoldRenderOptions.use_sample_clamp_AOVs", 0)
    miscUtils.setAttrC("defaultArnoldRenderOptions.use_existing_tiled_textures", 1)
    miscUtils.setAttrC("defaultArnoldRenderOptions.skipLicenseCheck", 1)
    miscUtils.setAttrC("defaultArnoldRenderOptions.log_verbosity", 1)#warnig + info
    miscUtils.setAttrC("defaultArnoldRenderOptions.motion_blur_enable", 1)
    if mc.getAttr("defaultArnoldRenderOptions.motion_frames") > 0.25 :
        pass
    else:
        miscUtils.setAttrC("defaultArnoldRenderOptions.motion_frames", 0.25)


    if renderMode == 'render':
        miscUtils.setAttrC("defaultArnoldRenderOptions.AASamples", 8)
        miscUtils.setAttrC("defaultArnoldFilter.width",4)
        miscUtils.setAttrC("defaultArnoldFilter.aiTranslator","blackman_harris",type="string")

        resolution = 1998
    elif renderMode == 'finalLayout':
        miscUtils.setAttrC("defaultArnoldRenderOptions.AASamples", 2)
        miscUtils.setAttrC("defaultArnoldRenderOptions.GIGlossySamples", 2)
        resolution = 1920

    miscUtils.setAttrC("defaultArnoldRenderOptions.GITotalDepth", 4)
    miscUtils.setAttrC("defaultArnoldRenderOptions.GIDiffuseDepth", 0)
    miscUtils.setAttrC("defaultArnoldRenderOptions.GIGlossyDepth", 1)
    miscUtils.setAttrC("defaultArnoldRenderOptions.GIDiffuseDepth", 0)
    miscUtils.setAttrC("defaultArnoldRenderOptions.GIRefractionDepth", 4)
    miscUtils.setAttrC("defaultArnoldRenderOptions.GIReflectionDepth", 2)
    miscUtils.setAttrC("defaultArnoldRenderOptions.GIVolumeDepth", 1)
    miscUtils.setAttrC("defaultArnoldRenderOptions.autoTransparencyDepth", 10)

    aspectRatio = 1.85
    ### Maya settings
    miscUtils.setAttrC("defaultResolution.pixelAspect", 1)
    miscUtils.setAttrC("defaultResolution.deviceAspectRatio", aspectRatio)
    miscUtils.setAttrC("defaultResolution.width", resolution)
    miscUtils.setAttrC("defaultResolution.height", resolution / aspectRatio)

    txt = "#### info: render options are now production ready"
    log.printL("i", txt)



def setRenderCamera(leftCam = True, rightCam = True, updateStereoCam = False , gui = True):
    log = miscUtils.LogBuilder(gui=gui, funcName ="setRenderCamera")

    defaultCamS = ""
    leftCamS =""
    rightCamS=""

    damShot = entityFromScene()
    oShotCam = mop.getShotCamera(damShot.name)




    if oShotCam:
        defaultCamNameS = oShotCam.name()
        leftCamNameS = defaultCamNameS.replace('cam_shot_default', 'cam_left').replace('cam_sq', 'stereo_cam_sq')
        rightCamNameS = defaultCamNameS.replace('cam_shot_default', 'cam_right').replace('cam_sq', 'stereo_cam_sq')
        stereoCamNameS = defaultCamNameS.replace('cam_shot_default', 'cam_stereo').replace('cam_sq', 'stereo_cam_sq')
        leftCamNameS = "stereo_rig:cam_left"
        rightCamNameS = "stereo_rig:cam_right"
        stereoCamNameS = "stereo_rig:cam_stereo"

        if leftCam or rightCam:
            if not mc.ls("stereo_rig:cam_stereo", type = "stereoRigTransform") or updateStereoCam:
                log.printL("i", "importing stereo camera")
                mop.loadStereoCam(infosFromScene()["dam_entity"])
                #mc.setAttr (defaultCamS + ".farClipPlane", 100000)


        allCam = mc.ls(type="camera")     
        for eachCam in allCam:
            eachCam = eachCam.replace("Shape", "")
            if eachCam == leftCamNameS:
                leftCamS = eachCam
            elif eachCam == rightCamNameS and rightCam:
                rightCamS = eachCam
            elif eachCam == defaultCamNameS:
                defaultCamS = eachCam
            elif eachCam == stereoCamNameS:
                stereoCam = eachCam
            else:
                try:
                    mc.setAttr (eachCam + ".renderable", 0)
                except:
                    pass

        if leftCam:
            if leftCamS: 
                mc.setAttr (leftCamS + ".renderable", 0)
                mc.setAttr (stereoCam + ".renderable", 0)
                mc.renderSettings(camera=stereoCam)
                if defaultCamS:
                    mc.setAttr (defaultCamS + ".renderable", 0)
                log.printL("i", "render camera: '{}'".format(leftCamS))
            else:
                log.printL("e", "could not found 'stereo_cam_sqxxxx_shxxxxa:cam_reft'")
                try:
                    mc.setAttr (leftCamS + ".renderable", 0)
                except:
                    pass

                if defaultCamS:
                    log.printL("i", "render camera: '{}'".format(defaultCamS))
                    mc.setAttr (defaultCamS + ".renderable", 0)
                else:
                    log.printL("e", "could not found 'cam_sqxxxx_shxxxxa:cam_shot_default'")
                    mc.setAttr (defaultCamS + ".renderable", 0)
        else:
            try:
                mc.setAttr (leftCamS + ".renderable", 0)
            except:
                pass

        if rightCam:
            if rightCamS: 
                mc.setAttr (rightCamS + ".renderable", 0)
                mc.setAttr (stereoCam + ".renderable", 0)
                mc.renderSettings(camera=stereoCam)
                log.printL("i", "render camera: '{}'".format(rightCamS))
            else:
                try:
                    mc.setAttr (rightCamS + ".renderable", 0)
                    log.printL("e", "could not found 'stereo_cam_sqxxxx_shxxxxa:cam_right'")
                except:
                    pass

        if not rightCam and not leftCam:
            if defaultCamS:
                log.printL("i", "render camera: '{}'".format(defaultCamS))
                mc.setAttr (defaultCamS + ".renderable", 1)
            else:
                log.printL("e", "could not found 'cam_sqxxxx_shxxxxa:cam_shot_default'")
                mc.setAttr (defaultCamS + ".renderable", 1)
    else:
        log.printL("e", "could not found 'cam_sqxxxx_shxxxxa:cam_shot_default'")

    return dict(resultB=log.resultB, logL=log.logL)



def UVSetCount(gui = True):
    log = miscUtils.LogBuilder(gui=gui, funcName ="UVSetCount")
    multiUVmapObjL=[]

    meshList, instanceList = miscUtils.getAllTransfomMeshes(inParent = "|asset|grp_geo")

    for each in meshList:
        uvMapList = mc.polyUVSet(each, query=True, allUVSets=True )
        if "uvSet_display" in uvMapList:
            uvMapList.remove("uvSet_display")
        if len(uvMapList)>1:
            multiUVmapObjL.append(each)

    if multiUVmapObjL :
        txt = "{} meshes has several uv maps, please clean: '{}': ".format(len(multiUVmapObjL), multiUVmapObjL)
        log.printL("e", txt)

    return dict(resultB=log.resultB, logL=log.logL)




def getRenderOutput(gui=True):

    outputImageName = ""

    #creates a workspace named as the davos user en the maya project path and set it
    #miscUtils.createUserWorkspace()

    mainFilePath = mc.file(q=True, sn=True)
    mainFilePathElem = mainFilePath.split("/")

    try:
        davosUser = os.environ["DAVOS_USER"]
    except:
        myMessage = "#### {:>7}: DAVOS_USER environement variable is not defined, please log to davos".format("Error")
        if gui == True:
            mc.confirmDialog(title='$DAVOS_USER not defined', message=myMessage, button=['Ok'], defaultButton='Ok')
            return
        else:
            raise ValueError(myMessage)

    #define output directoy
    if mc.ls("|asset"):
        if  mainFilePathElem[-4] == "asset" or mainFilePathElem[-5] == "asset":
            departement = mainFilePathElem[-1].split("_")[-1].split(".")[0].split("-")[0]
            #version =  mainFilePathElem[-1].split("_")[-1].split(".")[0].split("-")[1]
            version = mainFilePathElem[-1].split("-")[1][:4]
            if departement not in ["modeling", "anim", "previz", "render", "master"]:
                myMessage = "#### {:>7}: '{}' is not a valid scene name, file type '{}' is not valid and cannot be used to define the render path".format("Error", mainFilePathElem[-1], departement)
                if gui == True:
                    mc.confirmDialog(title='Shader structure Error', message=myMessage, button=['Ok'], defaultButton='Ok')
                else:
                    print myMessage
                departement = "undefined"
            if not re.match('^v[0-9]{3}$', version):
                myMessage = "#### {:>7}: '{}' is not a valid scene name, version '{}' is not valid and cannot be used to define the render path".format("Error", mainFilePathElem[-1], version)
                if gui == True:
                    mc.confirmDialog(title='Shader structure Error', message=myMessage, button=['Ok'], defaultButton='Ok')
                else:
                    print myMessage
                version = "vxxx"
            outputFilePath = miscUtils.pathJoin("$PRIV_ZOMB_ASSET_PATH", mainFilePathElem[-3], mainFilePathElem[-2], "review", departement + "-" + version)
            outputFilePath_exp = miscUtils.normPath(os.path.expandvars(os.path.expandvars(outputFilePath)))
            outputImageName = mainFilePathElem[-2]

            print "#### Info: Set render path: {}".format(outputFilePath)
            print "#### Info: Set image name:  {}".format(outputImageName)

        else:
            print "#### Warning: you are not working in an 'asset' structure directory, output image name and path cannot not be automaticaly set"
    elif mc.ls("|shot"):
        if  mainFilePathElem[-5] == "shot":
            vertionNumber = mainFilePathElem[-1].split("-")[1].split(".")[0]
            outputFilePath = miscUtils.pathJoin("$PRIV_ZOMB_SHOT_PATH", mainFilePathElem[-4], mainFilePathElem[-3], mainFilePathElem[-2], "render-" + vertionNumber)
            outputFilePath_exp = miscUtils.normPath(os.path.expandvars(os.path.expandvars(outputFilePath)))
            outputImageName = mainFilePathElem[-3]
            print "#### Info: Set render path: {}".format(outputFilePath_exp)
            print "#### Info: Set image name:  {}".format(outputImageName)

        else:
            print "#### Warning: you are not working in an 'shot' structure directory, output image name and path cannot not be automaticaly set"
    else:
        print "#### Warning: no '|asset'or '|shot' group could be found in this scene, output image name and path cannot be automaticaly set"
    return outputFilePath_exp, outputImageName


def createBatchRender(arnoldLic="on"):
    """
    this  script creates a renderbatch.bat file in the private maya working dir, all the variable are set properly
    a 'renderBatch_help.txt' is also created to help on addind render options to the render command

    """
    try:
        davosUser = os.environ["DAVOS_USER"]
    except:
        raise ValueError("#### Error: DAVOS_USER environement variable is not defined, please log to davos")


    workingFile = mc.file(q=True, sn=True)
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


def toggleCameraAspectRatio(cameraPatternS='cam_shading_*:*'):

    shadingCamL = mc.ls(cameraPatternS, type='camera')
    initAspectRatio = mc.getAttr(shadingCamL[0] + ".aspectRatio")

    if initAspectRatio == 1:
        aspectRatio = 1.85
    else:
        aspectRatio = 1

    for each in shadingCamL:
        mc.setAttr(each + ".aspectRatio", aspectRatio)

    #change render options
    mc.setAttr("defaultResolution.pixelAspect", 1)
    mc.setAttr("defaultResolution.deviceAspectRatio", aspectRatio)
    if aspectRatio != 1:
        mc.setAttr("defaultResolution.width", 1920)
        mc.setAttr("defaultResolution.height", 1920 / aspectRatio)
    else:
        mc.setAttr("defaultResolution.width", 1080)
        mc.setAttr("defaultResolution.height", 1080)

    print "#### Info: 'toggleCameraAspectRatio' aspect ratio changed from {} to {} on following cameras: {}".format(initAspectRatio, aspectRatio, shadingCamL)


def deleteAovs(GUI=True):
    toReturn = True
    infoS = ""
    if mc.ls("defaultArnoldRenderOptions"):
        myAOVs = aovs.AOVInterface()
        aovList = myAOVs.getAOVs()
        if aovList:
            myAOVs.removeAOVs(aovList)
            aiAOVL = mc.ls(type="aiAOV")
            if aiAOVL:
                mc.lockNode(aiAOVL, lock=False)
                try:
                    mc.delete(aiAOVL)
                except:
                    infoS = "#### {:>7}: 'deleteAovs' failed to delete somme AOVS nodes".format("Error")
                    if GUI: print infoS
                    toReturn = False
            aovs.refreshAliases()
            infoS = "#### {:>7}: 'deleteAovs' has deleted {} aovs".format("Info", len(aovList))
            if GUI: print infoS
        else:
            infoS = "#### {:>7}: 'deleteAovs' no AOVs to delete".format("Info")
            if GUI: print infoS
    else:
        infoS = "#### {:>7}: 'deleteAovs' no 'defaultArnoldRenderOptions' found in the scene cannot delete aovs".format("Info")
        if GUI: print infoS
    return toReturn, infoS

def createAovs(renderMode="render"):
    if mc.ls("defaultArnoldRenderOptions"):
        myAOVs = aovs.AOVInterface()
        #create aovs, type = rgb
        #unUsedAovDmnNameL = [ "dmn_lambert", "dmn_toon", "dmn_incidence","dmn_shadow_mask", "dmn_occlusion", "dmn_contour"  ],"dmn_rimToon_na1_na2"
        if renderMode == "finalLayout":
            aovDmnNameL = []
            aovCustomNameL = ["aiAOV_arlequin"]
        else:
            aovDmnNameL = ["dmn_ambient", "dmn_diffuse", "dmn_mask00", "dmn_mask01", "dmn_mask02", "dmn_mask03", "dmn_mask04", "dmn_mask05", "dmn_mask06", "dmn_mask07", "dmn_mask08", "dmn_mask09", "dmn_specular", "dmn_reflection", "dmn_refraction", "dmn_lambert_shdMsk_toon", "dmn_contour_inci_occ", "dmn_rimToon", "dmn_mask_transp", "dmn_lgtMask01", "dmn_lgtMask02"]
            aovCustomNameL = ["aiAOV_depth_aa", "aiAOV_Z", "aiAOV_P", "aiAOV_Pref", "aiAOV_crypto_object", "aiAOV_uvs"]


        for each in aovDmnNameL:
            if not mc.ls("aiAOV_" + each, type="aiAOV"):
                myAOVs.addAOV(each, aovType='rgb')

        for each in aovCustomNameL:
            if each == "aiAOV_arlequin" and not 'aiAOV_arlequin' in mc.ls(type="aiAOV"):
                resultD = createCustomShader(shaderName="arlequin", gui=True)
                arlequinNodeO = myAOVs.addAOV("arlequin", aovType='rgb')
                mc.connectAttr(resultD['rootNodeOutputS'], arlequinNodeO.node + '.defaultValue', force=True)
                aovCustomNameL.append("arlequin")
            elif each == "aiAOV_depth_aa" and not 'aiAOV_depth_aa' in mc.ls(type="aiAOV"):
                resultD = createCustomShader(shaderName="depthaa", gui=True)
                zaaNodeO = myAOVs.addAOV("depth_aa", aovType='rgb')
                mc.connectAttr(resultD['rootNodeOutputS'], zaaNodeO.node + '.defaultValue', force=True)
            elif each == "aiAOV_Z" and not 'aiAOV_Z' in mc.ls(type="aiAOV"):
                myAOVs.addAOV("Z", aovType='float')
            elif each == "aiAOV_P" and not 'aiAOV_P' in mc.ls(type="aiAOV"):
                myAOVs.addAOV("P", aovType='point')
            elif each == "aiAOV_Pref" and not 'aiAOV_Pref' in mc.ls(type="aiAOV"):
                myAOVs.addAOV("Pref", aovType='point')
            elif each == "aiAOV_crypto_object" and not 'aiAOV_crypto_object' in mc.ls(type="aiAOV"):
                myAOVs.addAOV("crypto_object", aovType='rgb')
            elif each == "aiAOV_uvs" and not 'aiAOV_uvs' in mc.ls(type="aiAOV"):
                myAOVs.addAOV("uvs", aovType='rgb')
                #changeAovFilter(aovName = "Z", filterName = "default")

        aovs.refreshAliases()
        print "#### {:>7}: 'createAovs' has created {} aovs".format("Info", len(aovDmnNameL) + len(aovCustomNameL))
    else:
        print "#### {:>7}: 'createAovs' no 'defaultArnoldRenderOptions' found in the scene cannot create aovs".format("Info")


def changeAovFilter(aovName="Z", filterName="default", gui=True):
    log = miscUtils.LogBuilder(gui=gui, funcName="'changeAovFilter'")
    aovNode = pm.ls('aiAOV_' + aovName, type='aiAOV')
    if aovNode:
        aovNode = aovNode[0]
    else :
        txt = "no '{}'' aovs found".format(aovName)
        log.printL("e", txt)
        return dict(resultB=log.resultB, logL=log.logL)

    if filterName != "default":
        filterNode = pm.createNode('aiAOVFilter', skipSelect=True)
        filterNode.aiTranslator.set(filterName)
        filterAttr = filterNode.attr('message')

    else:
        filterAttr = 'defaultArnoldFilter.message'

    out = aovNode.attr('outputs')[0]
    pm.connectAttr(filterAttr, out.filter, force=True)
    aovs._aovOptionsChangedCallbacks._callbackQueue["aoveditor"][0]()

    return dict(resultB=log.resultB, logL=log.logL)


def createCustomShader(shaderName="arlequin", gui=True):
    log = miscUtils.LogBuilder(gui=gui, funcName="'createCustomShader'")

    if shaderName == "arlequin":
        aiUtilityNode = mc.shadingNode("aiUtility", asShader=True, name="mat_arlequin_aiUtility")
        mc.setAttr(aiUtilityNode + '.shadeMode', 2)
        mc.setAttr(aiUtilityNode + '.colorMode', 21)
        aiAmbientOccNode = mc.shadingNode("aiAmbientOcclusion", asShader=True, name="mat_arelequin_aiAmbientOcclusion")
        mc.setAttr(aiAmbientOccNode + '.samples', 2)
        mc.setAttr(aiAmbientOccNode + '.spread', 0.8)
        mc.setAttr(aiAmbientOccNode + '.farClip', 10)
        mc.connectAttr(aiUtilityNode + '.outColor', aiAmbientOccNode + '.white', force=True)
        rootNodeOutput = aiAmbientOccNode + ".outColor"
    elif shaderName == "depthaa":
        multDivNode = mc.shadingNode("multiplyDivide", asShader=True, name="mat_depthaa_multiplyDivide")
        mc.setAttr(multDivNode + '.input2Z', 1)
        mc.setAttr(multDivNode + '.input2Y', 0)
        mc.setAttr(multDivNode + '.input2X', 0)
        samplerInfoNode = mc.shadingNode("samplerInfo", asShader=True, name="mat_depthaa_samplerInfo")
        mc.connectAttr(samplerInfoNode + '.pointCamera.pointCameraZ', multDivNode + '.input1.input1Z', force=True)
        rootNodeOutput = multDivNode + ".output"

    return dict(resultB=log.resultB, logL=log.logL, rootNodeOutputS=rootNodeOutput)

def renderLeftCam():
    shotName = ''
    if not pm.sceneName() == '' :
        mainFilePathS = mc.file(q=True, sn=True)
        shotName = mainFilePathS.split('/')[-1].split('_')[0] + '_' + mainFilePathS.split('/')[-1].split('_')[1]
    imageFileName = pm.getAttr('defaultRenderGlobals.imageFilePrefix')
    if pm.window("unifiedRenderGlobalsWindow", exists=True):
        pm.deleteUI("unifiedRenderGlobalsWindow")
    if not '/left/<RenderLayer>/' in imageFileName or '/right/<RenderLayer>/' in imageFileName or len(imageFileName) == 14 :
        pm.setAttr('cam_' + shotName + ':cam_shot_default.renderable', 0)
        pm.setAttr('stereo_rig:cam_stereoShape.renderable', 0)
        pm.setAttr('stereo_rig:cam_stereoShape.farClipPlane', 100000)
        pm.setAttr('stereo_rig:cam_rightShape.renderable', 0)
        pm.setAttr('stereo_rig:cam_leftShape.renderable', 1)
        if (pm.getAttr('stereo_rig:cam_leftShape.renderable')) :
            pm.setAttr('defaultRenderGlobals.imageFilePrefix', '/left/<RenderLayer>/' + shotName, type='string')
            print (u'Ready pour le rendu cam gauche')
    else :
        print (u'Merci, cam gauche already set, nothing to do !!')
        pass

def renderRightCam():
    shotName = ''
    if not pm.sceneName() == '' :
        mainFilePathS = mc.file(q=True, sn=True)
        shotName = mainFilePathS.split('/')[-1].split('_')[0] + '_' + mainFilePathS.split('/')[-1].split('_')[1]
    imageFileName = pm.getAttr('defaultRenderGlobals.imageFilePrefix')
    if pm.window("unifiedRenderGlobalsWindow", exists=True):
        pm.deleteUI("unifiedRenderGlobalsWindow")
    if not '/right/<RenderLayer>/' in imageFileName or '/left/<RenderLayer>/' in imageFileName or len(imageFileName) == 14 :
        pm.setAttr('cam_' + shotName + ':cam_shot_default.renderable', 0)
        pm.setAttr('stereo_rig:cam_stereoShape.renderable', 0)
        pm.setAttr('stereo_rig:cam_stereoShape.farClipPlane', 100000)
        pm.setAttr('stereo_rig:cam_leftShape.renderable', 0)
        pm.setAttr('stereo_rig:cam_rightShape.renderable', 1)
        if (pm.getAttr('stereo_rig:cam_rightShape.renderable')) :
            pm.setAttr('defaultRenderGlobals.imageFilePrefix', '/right/<RenderLayer>/' + shotName, type='string')
            print (u'Ready pour le rendu cam droite')
    else :
        print (u'Merci, ok pour le rendu cam droite')
        pass
