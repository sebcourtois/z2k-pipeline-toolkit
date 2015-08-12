import maya.cmds as mc
from mtoa.aovs import AOVInterface




def setArnoldRenderOption(outputFormat):
    print ""
    print "------------running setArnoldRenderOption------------"

    """
    this scripts sets the Arnold render options for production
    it also gets the rendering camera, and set the aovs
    sting --> "outputFormat": define the frame rendering format, only "png" and "exr" accepted.
                                "exr" also activate the AOVss

    """
    mmToIncheFactor = 0.0393700787401575
    camApertureInche = 35 * mmToIncheFactor 
    
    #get the "cam_" camera, stops if nothing found
    # if the camera has  an "aspectRatio" extra attribute sets the camera according to it
    # make the camera renderable  
    myCamName = mc.ls('cam_*',type = "camera")
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
        print "#### error: no 'cam_*' camera could be found in the scene"
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
    #mc.setAttr("defaultRenderGlobals.imageFilePrefix","" ,type = "string")


    #arnold Settings
    
    if outputFormat == "png":
        mc.setAttr("defaultArnoldDriver.aiTranslator","png", type = "string")
        mc.setAttr("defaultArnoldRenderOptions.aovMode", 0)
        
    elif outputFormat == "exr":
        mc.setAttr("defaultArnoldDriver.aiTranslator","exr", type = "string")    
        mc.setAttr("defaultArnoldDriver.exrCompression",3)#zip
        mc.setAttr("defaultArnoldDriver.halfPrecision",1)
        mc.setAttr("defaultArnoldDriver.autocrop",1)
        mc.setAttr("defaultArnoldDriver.mergeAOVs",1)
        mc.setAttr("defaultArnoldRenderOptions.aovMode",1)

        myAOVs = AOVInterface()
        #create aovs, type = rgb
        aovNameList = ["dmn_incandescence","dmn_ambient", "dmn_diffuse", "dmn_lambert", "dmn_toon" ]
        for eachAovName in aovNameList: 
            if not mc.ls("aiAOV_"+eachAovName, type = "aiAOV"):
                myAOVs.addAOV( eachAovName, aovType=5)
        #create aovs, type = float   
        aovNameList = ["dmn_incidence","dmn_shadow_mask", "dmn_occlusion", "dmn_contour" ]
        for eachAovName in aovNameList: 
            if not mc.ls("aiAOV_"+eachAovName, type = "aiAOV"):
                #myAOVs.addAOV( eachAovName, aovType=4) # desactivated so everything in rgb for the moment
                myAOVs.addAOV( eachAovName, aovType=5)
        #create aovs, type = rgba
        aovNameList = ["dmn_mask00","dmn_mask01", "dmn_mask02", "dmn_mask03", "dmn_mask04" ]
        for eachAovName in aovNameList: 
            if not mc.ls("aiAOV_"+eachAovName, type = "aiAOV"):
                myAOVs.addAOV( eachAovName, aovType=6)
                
        
    
    mc.setAttr("defaultArnoldRenderOptions.AASamples",8)
    mc.setAttr("defaultArnoldRenderOptions.GIDiffuseSamples",0)
    mc.setAttr("defaultArnoldRenderOptions.GIGlossySamples",3)
    mc.setAttr("defaultArnoldRenderOptions.GIRefractionSamples",0)
    mc.setAttr("defaultArnoldRenderOptions.sssBssrdfSamples",0)
    mc.setAttr("defaultArnoldRenderOptions.use_sample_clamp",1)
    mc.setAttr("defaultArnoldRenderOptions.AASampleClamp",2.5)
    mc.setAttr("defaultArnoldRenderOptions.motion_blur_enable",0)
    mc.setAttr("defaultArnoldRenderOptions.use_existing_tiled_textures",1)
    

    print "#### info: render options are now production ready"
    
    
