import maya.cmds as mc

from dminutes import miscUtils
reload (miscUtils)



def orientAssetLightAsCam(shotCamL=[],gui=True):

    log = miscUtils.LogBuilder(gui=gui, funcName ="orientAssetLightAsCam")
    shotCamL = mc.ls(shotCamL,type="camera", l=True)

    if not shotCamL:
        shotCamL = mc.ls("*:cam_shot_defaultShape",type="camera", l=True)
        if not shotCamL:
            txt= "no '*:cam_shot_defaultShape' camera could be found in the scene".format()
            log.printL("e", txt, guiPopUp = True)
            return

    if len(shotCamL)> 1:
        txt= "'{}' camera found, proceeding with the first one: {}".format( len(shotCamL), shotCamL[0])
        log.printL("e", txt, guiPopUp = True)

    orientAsCamL = mc.ls("*:grp_orientAsCam",type="transform")
    
    i=1
    for each in orientAsCamL:
        mc.delete( mc.listRelatives(each,children=True, type="orientConstraint"))
        shotCamTransS = mc.listRelatives(shotCamL[0],parent=True, type="transform")
        mc.orientConstraint( shotCamTransS,each, maintainOffset = False, name = "orientAsCamera_constraint"+str(i))
        txt= "{:^48} --> constrained to --> {}".format(each, shotCamL[0].split("|")[-1])
        log.printL("i", txt)
        i+=1

    return dict(resultB=log.resultB, logL=log.logL)


#---WIP
def importGrpLgt(assetL=[], lgtRig = "lgtRig_character", gui=True, hideLgt = False):

    log = miscUtils.LogBuilder(gui=gui, funcName ="importGrpLgt")

    if mc.ls("|shot"):        
        mainFilePath = mc.file(q=True, list = True)[0]
        mainFilePathElem = mainFilePath.split("/")
        assetFileType = mainFilePathElem[-1].split("-")[0].split("_")[-1]
        if  mainFilePathElem[-5] == "shot"or mainFilePathElem[-6] == "shot":
            lgtRigFilePath = miscUtils.normPath(miscUtils.pathJoin("$ZOMB_MISC_PATH","shading","lightRigs",lgtRig+".ma"))
            lgtRigFilePath_exp = miscUtils.normPath(os.path.expandvars(os.path.expandvars(lgtRigFilePath)))
        else:
            txt= "You are not working in a 'shot' structure directory"
            log.printL("e", txt, guiPopUp = True)
            raise ValueError(txt)
    else :
        log.printL("e", "No '|shot' could be found in this scene", guiPopUp = True)
        raise ValueError(txt)

    if not assetL:
        refNodeList = mc.ls(type = "reference")
        for each in refNodeList:
            if re.match('^chr_{0,1}[a-zA-Z0-9_]{0,128}RN$', each) :
                assetL.append(each)


    grpLgt =  mc.ls("shot|grp_light", l=True)[0]
    #mc.delete(grpLgt)

    log.printL("i", "Importing '{}'".format(lgtRigFilePath_exp))
    myImport = mc.file( lgtRigFilePath_exp, i= True, type= "mayaAscii", ignoreVersion=True, preserveReferences= True )
    

    for each in assetL:
        mc.file( lgtRigFilePath_exp, i= True, type= "mayaAscii", ignoreVersion=True, namespace=each, preserveReferences= False )
        mc.parent(each+":light","shot|grp_light")



    lgtDefault =  mc.ls("lgt_default*", l=True, type = "light")
    if len(lgtDefault)!=1:
        txt= "'{}' 'lgt_default' light has been found".format( len(lgtDefault))
        log.printL("e", txt, guiPopUp = True)
        raise ValueError(txt)

    lgtDefault = lgtDefault[0]    

    shadingEngineList =  mc.ls("*",type = "shadingEngine")
    shadingEngine2LinkList = []
    for each in shadingEngineList:
        if each == "initialParticleSE" or each == "initialShadingGroup":
            continue
        elif not re.match('^sgr_[a-zA-Z0-9]{1,24}$', each):
                log.printL("w", "Skipping '{}' light linking, since it does not match naming convention 'sgr_materialName'".format(each))
                continue
        else:
            shadingEngine2LinkList.append(each)

    mc.lightlink( light=lgtDefault, object=shadingEngine2LinkList )
    log.printL("i", "'{}' light linked  to '{}' shaders".format(lgtDefault, len(shadingEngine2LinkList)))
    if hideLgt:
        mc.hide("|asset|grp_light")


    return dict(resultB=log.resultB, logL=log.logL)