import maya.cmds as mc
from mtoa.aovs import AOVInterface

import miscUtils
import os
import shutil




def setArnoldRenderOption(outputFormat):

    """
    this scripts sets the Arnold render options for production
    it also gets the rendering camera, and set the aovs
    sting --> "outputFormat": define the frame rendering format, only "png" and "exr" accepted.
                                "exr" also activate the AOVss
    """

    print ""
    print "#### {:>7}: runing shading.setArnoldRenderOption(outputFormat = {})".format("info" , outputFormat)



    if mc.ls("|asset") and (mc.file(q=True, list = True)[0].split("/")[-4]) == "asset":
        shadingMode = True
        print "#### info: Shading mode render options"
    else:
        shadingMode = False
        print "#### info: Lighting mode render options"       


    setRenderOutputDir()    


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
    mc.setAttr("defaultResolution.width",1920)
    mc.setAttr("defaultResolution.height",1920/aspectRatio)
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


    #arnold Settings

    #Image output settings
    mc.setAttr("defaultArnoldDriver.aiTranslator","exr", type = "string")    
    mc.setAttr("defaultArnoldDriver.exrCompression",3)#zip
    mc.setAttr("defaultArnoldDriver.halfPrecision",1)
    mc.setAttr("defaultArnoldDriver.autocrop",1)
    mc.setAttr("defaultArnoldDriver.mergeAOVs",1)
    mc.setAttr("defaultArnoldRenderOptions.aovMode",2)#batch only



    myAOVs = AOVInterface()
    #create aovs, type = rgb
    #unUsedAovNameList = [ "dmn_lambert", "dmn_toon", "dmn_incidence","dmn_shadow_mask", "dmn_occlusion", "dmn_contour"  ],"dmn_rimToon_na1_na2"
    aovNameList = ["dmn_ambient", "dmn_diffuse","dmn_mask00", "dmn_mask01", "dmn_mask02", "dmn_mask03", "dmn_mask04", "dmn_specular", "dmn_reflection", "dmn_refraction", "dmn_lambert_shdMsk_toon", "dmn_contour_inci_occ", "dmn_rimToon"]
    for eachAovName in aovNameList: 
        if not mc.ls("aiAOV_"+eachAovName, type = "aiAOV"):
            myAOVs.addAOV( eachAovName, aovType=5)

                
        
    if outputFormat == "png":
        mc.setAttr("defaultArnoldDriver.aiTranslator","png", type = "string")
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
    mc.setAttr("defaultArnoldRenderOptions.sssBssrdfSamples",0)
    mc.setAttr("defaultArnoldRenderOptions.use_sample_clamp",1)
    mc.setAttr("defaultArnoldRenderOptions.AASampleClamp",2.5)
    mc.setAttr("defaultArnoldRenderOptions.use_existing_tiled_textures",1)
    mc.setAttr("defaultArnoldRenderOptions.skipLicenseCheck",1)
    
    print "#### info: render options are now production ready"



def setRenderOutputDir():

    outputImageName = ""

    #creates a workspace named as the davos user en the maya project path and set it
    miscUtils.createUserWorkspace()

    mainFilePath = mc.file(q=True, list = True)[0]
    mainFilePathElem = mainFilePath.split("/")

    #define output directoy
    if mc.ls("|asset"):        
        if  mainFilePathElem[-4] == "asset":
            outputFilePath = miscUtils.pathJoin("$PRIV_ZOMB_ASSET_PATH",mainFilePathElem[-3],mainFilePathElem[-2],"review",mainFilePathElem[-2])
            outputFilePath_exp = miscUtils.normPath(os.path.expandvars(os.path.expandvars(outputFilePath)))
            outputImageName = mainFilePathElem[-2]
            print "#### Info: Set render path: {}".format( outputFilePath)
            #print "#### Info: Set image name:  {}".format( outputImageName)
            #mc.workspace(fileRule=["images",outputFilePath_exp])
            mc.setAttr("defaultRenderGlobals.imageFilePrefix",outputFilePath_exp ,type = "string")
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
            mc.workspace(fileRule=["images",outputFilePath_exp])
            mc.setAttr("defaultRenderGlobals.imageFilePrefix",outputImageName ,type = "string")
        else:
            print "#### Warning: you are not working in an 'shot' structure directory, output image name and path cannot not be automaticaly set"
    else:
        print "#### Warning: no '|asset'or '|shot' group could be found in this scene, output image name and path cannot be automaticaly set"
    
    
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
    renderBatch = miscUtils.normPath(os.path.join(workingDir,"renderBatch.bat"))
    location = os.path.split(os.getcwd())[-1]
    setupEnvTools = os.path.normpath(os.path.join(os.environ["ZOMB_TOOL_PATH"],"z2k-pipeline-toolkit","launchers", location,"setup_env_tools.py"))
    renderDesc = os.environ["MAYA_RENDER_DESC_PATH"]
    plugIn = os.environ["MAYA_PLUG_IN_PATH"]
    renderCmd = os.path.normpath(os.path.join(os.environ["MAYA_LOCATION"],"bin","Render.exe"))
    if os.path.isfile(renderBatch):
        if os.path.isfile(renderBatch+".bak"): os.remove(renderBatch+".bak")
        print "#### Info: old renderBatch.bat backuped: {}.bak".format(os.path.normpath(renderBatch))
        os.rename(renderBatch, renderBatch+".bak")

    renderBatch_obj = open(renderBatch, "w")
    renderBatch_obj.write("set MAYA_RENDER_DESC_PATH="+renderDesc+"\n")
    renderBatch_obj.write("set MAYA_PLUG_IN_PATH="+renderDesc+"\n")
    renderBatch_obj.write("set DAVOS_USER="+davosUser+"\n")
    renderBatch_obj.write("set render="+renderCmd+"\n")
    renderBatch_obj.write("\n")
    renderBatch_obj.write('set option=-r arnold\n')
    workingFile = os.path.normpath(workingFile)
    renderBatch_obj.write("set scene="+workingFile+"\n")
    finalCommand = r'"C:\Python27\python.exe" "'+setupEnvTools+'" launch %render% %option% %scene%'
    renderBatch_obj.write(finalCommand+"\n")
    renderBatch_obj.write("\n")
    renderBatch_obj.write("pause\n")
    renderBatch_obj.close()
    print "#### Info: renderBatch.bat created: {}".format(os.path.normpath(renderBatch))

    renderBatchHelp_src = miscUtils.normPath(os.path.join(os.environ["ZOMB_TOOL_PATH"],"z2k-pipeline-toolkit","maya_mods","zombie","python","dminutes","renderBatch_help.txt"))
    renderBatchHelp_trg = miscUtils.normPath(os.path.join(workingDir,"renderBatch_help.txt"))
    if not os.path.isfile(renderBatchHelp_trg):
        shutil.copyfile(renderBatchHelp_src, renderBatchHelp_trg)
        print "#### Info: renderBatch_help.txt created: {}".format(os.path.normpath(renderBatchHelp_trg))
