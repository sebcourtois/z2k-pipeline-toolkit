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
