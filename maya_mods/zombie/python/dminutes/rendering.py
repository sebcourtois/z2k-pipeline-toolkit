import maya.cmds as mc
#from mtoa.aovs import AOVInterface
from mtoa import aovs

import miscUtils
import os
import re
import shutil
import maya.mel




def setArnoldRenderOption(outputFormat):

    """
    this scripts sets the Arnold render options for production
    it also gets the rendering camera, and set the aovs
    sting --> "outputFormat": define the frame rendering format, only "png" and "exr" accepted.
                                "exr" also activate the AOVss
    """

    print ""
    print "#### {:>7}: runing rendering.setArnoldRenderOption(outputFormat = {})".format("info" , outputFormat)



    if mc.ls("|asset") and (mc.file(q=True, list = True)[0].split("/")[-4]) == "asset":
        shadingMode = True
        print "#### info: Shading mode render options"
    else:
        shadingMode = False
        print "#### info: Lighting mode render options"       

    #TEMPORAIRE
    mc.workspace(fileRule=["images","images"])

    mmToIncheFactor = 0.0393700787401575
    camApertureInche = 35 * mmToIncheFactor 
    
    #get the "cam_" camera, stops if nothing found
    # if the camera has  an "aspectRatio" extra attribute sets the camera according to it
    # make the camera renderable  
    myCamName = mc.ls('*:cam_*',type = "camera")
    if myCamName :
        if len(myCamName)>1:
            print "#### warning: several 'cam_*' have been found, proceeding with: "+myCamName[0]
        else : 
            print "#### info: one camera found, proceeding with: "+myCamName[0]
        myCamName = myCamName[0]
        if mc.attributeQuery ("aspectRatio", node = myCamName , exists = True):
            aspectRatio = mc.getAttr (myCamName+".aspectRatio")
            mc.camera( myCamName, e=True, horizontalFilmAperture=camApertureInche, verticalFilmAperture = camApertureInche/aspectRatio )
        else:
            aspectRatio = mc.camera(myCamName, q=True, aspectRatio=True)
        
        allCam = mc.ls(type = "camera")
        for eachCam in allCam:
            if eachCam != myCamName:
                mc.setAttr (eachCam+".renderable", 0)
            else:
                mc.setAttr (myCamName+".renderable", 1)
        
    else:
        print "#### error: no '*:cam_*' camera could be found in the scene"
        return
    

  
    ### Maya settings 
    mc.setAttr("defaultResolution.pixelAspect",1)
    mc.setAttr("defaultResolution.deviceAspectRatio",aspectRatio)
    if aspectRatio != 1:
        mc.setAttr("defaultResolution.width",1920)
        mc.setAttr("defaultResolution.height",1920/aspectRatio)
    else:
        mc.setAttr("defaultResolution.width",1080)
        mc.setAttr("defaultResolution.height",1080)
    mc.colorManagementPrefs(e=True, cmEnabled=False)

    animationStartTime =  mc.playbackOptions( animationStartTime = True , q= True)
    animationEndTime =  mc.playbackOptions( animationEndTime = True , q= True)

    mc.setAttr("defaultRenderGlobals.startFrame",animationStartTime)
    mc.setAttr("defaultRenderGlobals.endFrame",animationEndTime)
    mc.setAttr("defaultRenderGlobals.byFrameStep",1)
    mc.setAttr("defaultRenderGlobals.outFormatControl",0)
    mc.setAttr("defaultRenderGlobals.animation",1)
    mc.setAttr("defaultRenderGlobals.putFrameBeforeExt",1)
    mc.setAttr("defaultRenderGlobals.extensionPadding",4)
    mc.setAttr("defaultRenderGlobals.currentRenderer","arnold", type = "string")

    maya.mel.eval('setMayaSoftwareFrameExt(3,0)')

    #arnold Settings

    #Image output settings
    mc.setAttr("defaultArnoldDriver.aiTranslator","png", type = "string")
    mc.setAttr("defaultArnoldDriver.pngFormat",0)

    mc.setAttr("defaultArnoldDriver.aiTranslator","exr", type = "string")    
    mc.setAttr("defaultArnoldDriver.exrCompression",3)#zip
    mc.setAttr("defaultArnoldDriver.halfPrecision",1)
    mc.setAttr("defaultArnoldDriver.autocrop",1)
    mc.setAttr("defaultArnoldDriver.mergeAOVs",1)
    mc.setAttr("defaultArnoldRenderOptions.aovMode",2)#batch only



    createAovs()

                
        
    if outputFormat == "png":
        mc.setAttr("defaultArnoldDriver.aiTranslator","png", type = "string")
        mc.setAttr("defaultArnoldRenderOptions.aovMode", 0)
    elif  outputFormat == "jpg":
        mc.setAttr("defaultArnoldDriver.aiTranslator","jpeg", type = "string")
        mc.setAttr("defaultArnoldRenderOptions.aovMode", 0)
        
    
    if shadingMode == True:
        mc.setAttr("defaultArnoldRenderOptions.AASamples",4)
        mc.setAttr("defaultArnoldRenderOptions.motion_blur_enable",0)
        mc.setAttr("defaultArnoldRenderOptions.force_texture_cache_flush_after_render",1)
    else:
        mc.setAttr("defaultArnoldRenderOptions.AASamples",8)
        mc.setAttr("defaultArnoldRenderOptions.motion_blur_enable",1)

    mc.setAttr("defaultArnoldRenderOptions.GIDiffuseSamples",0)
    mc.setAttr("defaultArnoldRenderOptions.GIGlossySamples",3)
    mc.setAttr("defaultArnoldRenderOptions.GIRefractionSamples",0)
    mc.setAttr("defaultArnoldRenderOptions.GISssSamples",0)
    mc.setAttr("defaultArnoldRenderOptions.use_sample_clamp",1)
    mc.setAttr("defaultArnoldRenderOptions.AASampleClamp",2.5)
    mc.setAttr("defaultArnoldRenderOptions.use_existing_tiled_textures",1)
    mc.setAttr("defaultArnoldRenderOptions.skipLicenseCheck",1)
    mc.setAttr("defaultArnoldRenderOptions.log_verbosity",1)#warnig + info


    mc.setAttr("defaultArnoldRenderOptions.GITotalDepth",10)
    mc.setAttr("defaultArnoldRenderOptions.GIDiffuseDepth",0)
    mc.setAttr("defaultArnoldRenderOptions.GIGlossyDepth",1)
    mc.setAttr("defaultArnoldRenderOptions.GIDiffuseDepth",0)
    mc.setAttr("defaultArnoldRenderOptions.GIRefractionDepth",8)
    mc.setAttr("defaultArnoldRenderOptions.GIReflectionDepth",10)
    mc.setAttr("defaultArnoldRenderOptions.GIVolumeDepth",0)
    mc.setAttr("defaultArnoldRenderOptions.autoTransparencyDepth",10)
    
    print "#### info: render options are now production ready"



def getRenderOutput(gui = True):

    outputImageName = ""

    #creates a workspace named as the davos user en the maya project path and set it
    #miscUtils.createUserWorkspace()

    mainFilePath = mc.file(q=True, list = True)[0]
    mainFilePathElem = mainFilePath.split("/")

    try:
        davosUser = os.environ["DAVOS_USER"]
    except:
        myMessage = "#### {:>7}: DAVOS_USER environement variable is not defined, please log to davos".format("Error")
        if gui == True:
            mc.confirmDialog( title='$DAVOS_USER not defined', message=myMessage, button=['Ok'], defaultButton='Ok' )
            return
        else:
            raise ValueError(myMessage)

    #define output directoy
    if mc.ls("|asset"):        
        if  mainFilePathElem[-4] == "asset":
            departement =  mainFilePathElem[-1].split("_")[-1].split(".")[0].split("-")[0]
            #version =  mainFilePathElem[-1].split("_")[-1].split(".")[0].split("-")[1]
            version =  mainFilePathElem[-1].split("-")[1][:4]
            if departement not in ["modeling","anim","previz","render","master"]:
                myMessage = "#### {:>7}: '{}' is not a valid scene name, file type '{}' is not valid and cannot be used to define the render path".format("Error",mainFilePathElem[-1], departement)
                if gui == True:
                    mc.confirmDialog( title='Shader structure Error', message=myMessage, button=['Ok'], defaultButton='Ok' )
                else:
                    print myMessage
                departement = "undefined"
            if not re.match('^v[0-9]{3}$', version):
                myMessage = "#### {:>7}: '{}' is not a valid scene name, version '{}' is not valid and cannot be used to define the render path".format("Error",mainFilePathElem[-1], version)
                if gui == True:
                    mc.confirmDialog( title='Shader structure Error', message=myMessage, button=['Ok'], defaultButton='Ok' )
                else:
                    print myMessage
                version = "vxxx"
            outputFilePath = miscUtils.pathJoin("$PRIV_ZOMB_ASSET_PATH",mainFilePathElem[-3],mainFilePathElem[-2],"review",departement+"-"+version)
            outputFilePath_exp = miscUtils.normPath(os.path.expandvars(os.path.expandvars(outputFilePath)))
            outputImageName = mainFilePathElem[-2]

            print "#### Info: Set render path: {}".format( outputFilePath)
            print "#### Info: Set image name:  {}".format( outputImageName)
            #mc.workspace(fileRule=["images",outputFilePath_exp])
            #mc.workspace(fileRule=["images","images"])
            #mc.workspace( saveWorkspace = True)
            #mc.setAttr("defaultRenderGlobals.imageFilePrefix",outputImageName ,type = "string")
            #mc.setAttr("defaultRenderGlobals.imageFilePrefix",outputFilePath_exp ,type = "string")
            #mc.file(save = True)
        else:
            print "#### Warning: you are not working in an 'asset' structure directory, output image name and path cannot not be automaticaly set"
    elif mc.ls("|shot"):
        print "#### Warning: this tool hass not been tested yet"
        if  mainFilePathElem[-4] == "shot":
            outputFilePath = miscUtils.pathJoin("$PRIV_ZOMB_OUTPUT_PATH",mainFilePathElem[-3],mainFilePathElem[-2],mainFilePathElem[-1],"render")
            outputFilePath_exp = miscUtils.normPath(os.path.expandvars(os.path.expandvars(outputFilePath)))
            outputImageName = mainFilePathElem[-2]
            print "#### Info: Set render path: {}".format( outputFilePath_exp)
            print "#### Info: Set image name:  {}".format( outputImageName)
            #mc.workspace(fileRule=["images",outputFilePath_exp])
            #mc.workspace( saveWorkspace = True)
            #mc.setAttr("defaultRenderGlobals.imageFilePrefix",outputImageName ,type = "string")
            #mc.file(save = True)
        else:
            print "#### Warning: you are not working in an 'shot' structure directory, output image name and path cannot not be automaticaly set"
    else:
        print "#### Warning: no '|asset'or '|shot' group could be found in this scene, output image name and path cannot be automaticaly set"
    return outputFilePath_exp, outputImageName
    
    
def createBatchRender():
    """
    this  script creates a renderbatch.bat file in the private maya working dir, all the variable are set properly
    a 'renderBatch_help.txt' is also created to help on addind render options to the render command

    """
    try:
        davosUser = os.environ["DAVOS_USER"]
    except:
        raise ValueError("#### Error: DAVOS_USER environement variable is not defined, please log to davos")


    workingFile = mc.file(q=True, list = True)[0]
    workingDir = os.path.dirname(workingFile)
    renderBatchHelp_src = miscUtils.normPath(os.path.join(os.environ["ZOMB_TOOL_PATH"],"z2k-pipeline-toolkit","maya_mods","zombie","python","dminutes","renderBatch_help.txt"))
    renderBatchHelp_trg = miscUtils.normPath(os.path.join(workingDir,"renderBatch_help.txt"))
    renderBatch_src = miscUtils.normPath(os.path.join(os.environ["ZOMB_TOOL_PATH"],"z2k-pipeline-toolkit","maya_mods","zombie","python","dminutes","renderBatch.bat"))
    renderBatch_trg = miscUtils.normPath(os.path.join(workingDir,"renderBatch.bat"))
    setupEnvTools = os.path.normpath(os.path.join(os.environ["Z2K_LAUNCH_SCRIPT"]))
    #location = miscUtils.normPath(setupEnvTools).split("/")[-2]
    #setupEnvToolsNetwork = os.path.join(os.environ["ZOMB_TOOL_PATH"],"z2k-pipeline-toolkit","launchers",location,"setup_env_tools.py")
    #setupEnvToolsNetwork = os.path.join('%USERPROFILE%'+'"',"DEVSPACE","git","z2k-pipeline-toolkit","launchers",location,"setup_env_tools.py")
    userprofile =  os.path.normpath(os.path.join(os.environ["USERPROFILE"]))
    setupEnvToolsNetwork = setupEnvTools.replace(userprofile,'%USERPROFILE%')
    renderDesc = os.environ["MAYA_RENDER_DESC_PATH"]
    mayaPlugInPath = os.environ["MAYA_PLUG_IN_PATH"]
    arnoldPluginPath = os.environ["ARNOLD_PLUGIN_PATH"]


    outputFilePath, outputImageName = getRenderOutput()

    zombToolsPath = os.environ["ZOMB_TOOL_PATH"]
    #arnoldToolPath = os.path.normpath(zombToolsPath+"/z2k-pipeline-toolkit/maya_mods/solidangle/mtoadeploy/2016")
    #arnoldToolPath = os.path.normpath('%USERPROFILE%'+"/DEVSPACE/git/z2k-pipeline-toolkit/maya_mods/solidangle/mtoadeploy/2016")
    arnoldToolPath = os.path.normpath(setupEnvToolsNetwork.split("z2k-pipeline-toolkit")[0]+"z2k-pipeline-toolkit/maya_mods/solidangle/mtoadeploy/2016")

    renderCmd = os.path.normpath(os.path.join(os.environ["MAYA_LOCATION"],"bin","Render.exe"))
    renderCmd = '"{}"'.format(renderCmd)
    if os.path.isfile(renderBatch_trg):
        if os.path.isfile(renderBatch_trg+".bak"): os.remove(renderBatch_trg+".bak")
        print "#### Info: old renderBatch.bat backuped: {}.bak".format(os.path.normpath(renderBatch_trg))
        os.rename(renderBatch_trg, renderBatch_trg+".bak")
    if not os.path.isfile(renderBatchHelp_trg):
        shutil.copyfile(renderBatchHelp_src, renderBatchHelp_trg)
        print "#### Info: renderBatch_help.txt created: {}".format(os.path.normpath(renderBatchHelp_trg))

    shutil.copyfile(renderBatch_src, renderBatch_trg)

    renderBatch_obj = open(renderBatch_trg, "w")
    renderBatch_obj.write("rem #### User Info ####\n")
    renderBatch_obj.write("rem set MAYA_RENDER_DESC_PATH="+renderDesc+"\n")
    renderBatch_obj.write("rem set ARNOLD_PLUGIN_PATH="+arnoldPluginPath+"\n")
    renderBatch_obj.write("rem set MAYA_PLUG_IN_PATH="+mayaPlugInPath+"\n")
    renderBatch_obj.write("rem ###################\n\n")

    renderBatch_obj.write("set render="+renderCmd+"\n")
    renderBatch_obj.write("set MAYA_RENDER_DESC_PATH="+arnoldToolPath+"\n\n")
    
    renderBatch_obj.write("set DAVOS_USER="+davosUser+"\n\n")

    renderBatch_obj.write('set option=-r arnold -lic on\n')
    renderBatch_obj.write('set image=-im '+outputImageName+'\n')
    renderBatch_obj.write('set path=-rd '+os.path.normpath(outputFilePath)+'\n')
    workingFile = os.path.normpath(workingFile)
    renderBatch_obj.write("set scene="+workingFile+"\n")
    setupEnvToolsNetwork = setupEnvToolsNetwork.replace('%USERPROFILE%','%USERPROFILE%"')
    finalCommand = r'"C:\Python27\python.exe" '+setupEnvToolsNetwork+'" launch %render% %option% %path% %image% %scene%'
    renderBatch_obj.write(finalCommand+"\n")
    renderBatch_obj.write("\n")
    renderBatch_obj.write("pause\n")
    renderBatch_obj.close()
    print "#### Info: renderBatch.bat created: {}".format(os.path.normpath(renderBatch_trg))


def toggleCameraAspectRatio(cameraPatternS = 'cam_shading_*:*'):
    
    shadingCamL = mc.ls(cameraPatternS,type='camera')
    initAspectRatio= mc.getAttr(shadingCamL[0]+".aspectRatio")
   
    if initAspectRatio == 1:
        aspectRatio = 1.85
    else:
        aspectRatio = 1

    for each in shadingCamL:
        mc.setAttr(each+".aspectRatio",aspectRatio)

    #change render options
    mc.setAttr("defaultResolution.pixelAspect",1)
    mc.setAttr("defaultResolution.deviceAspectRatio",aspectRatio)
    if aspectRatio != 1:
        mc.setAttr("defaultResolution.width",1920)
        mc.setAttr("defaultResolution.height",1920/aspectRatio)
    else:
        mc.setAttr("defaultResolution.width",1080)
        mc.setAttr("defaultResolution.height",1080)

    print "#### Info: 'toggleCameraAspectRatio' aspect ratio changed from {} to {} on following cameras: {}".format(initAspectRatio, aspectRatio, shadingCamL)


def deleteAovs():
    toReturn =True
    infoS =""
    if mc.ls("defaultArnoldRenderOptions"):
        myAOVs = aovs.AOVInterface()
        aovList = myAOVs.getAOVs()
        if aovList:
            myAOVs.removeAOVs(aovList)
            aovs.refreshAliases()
            infoS =  "#### {:>7}: 'deleteAovs' has deleted {} aovs".format("Info", len(aovList))
            print infoS
        else:
            infoS =  "#### {:>7}: 'deleteAovs' no AOVs to delete".format("Info")
            print infoS
    else:
        infoS =  "#### {:>7}: 'deleteAovs' no 'defaultArnoldRenderOptions' found in the scene cannot delete aovs".format("Info")
        print infoS
    return toReturn, infoS



def createAovs():
    if mc.ls("defaultArnoldRenderOptions"):
        myAOVs = aovs.AOVInterface()
        #create aovs, type = rgb
        #unUsedAovNameList = [ "dmn_lambert", "dmn_toon", "dmn_incidence","dmn_shadow_mask", "dmn_occlusion", "dmn_contour"  ],"dmn_rimToon_na1_na2"
        aovNameList = ["dmn_ambient", "dmn_diffuse","dmn_mask00", "dmn_mask01", "dmn_mask02", "dmn_mask03", "dmn_mask04", "dmn_mask05", "dmn_mask06", "dmn_mask07", "dmn_mask08", "dmn_mask09", "dmn_specular", "dmn_reflection", "dmn_refraction", "dmn_lambert_shdMsk_toon", "dmn_contour_inci_occ", "dmn_rimToon","dmn_mask_transp"]
        for eachAovName in aovNameList: 
            if not mc.ls("aiAOV_"+eachAovName, type = "aiAOV"):
                myAOVs.addAOV( eachAovName, aovType='rgb')
        if not 'aiAOV_Z' in mc.ls( type = "aiAOV"):
            myAOVs.addAOV( "Z", aovType='float')
        aovs.refreshAliases()
        print "#### {:>7}: 'createAovs' has created {} aovs".format("Info",len(aovNameList))
    else:
        print "#### {:>7}: 'createAovs' no 'defaultArnoldRenderOptions' found in the scene cannot create aovs".format("Info")



