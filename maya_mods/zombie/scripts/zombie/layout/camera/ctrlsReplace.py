
from dminutes import maya_scene_operations as mop
reload(mop)

def camCTRLReplace():
    dCamInfo = mop.getCameraRig()

    vCamT = dCamInfo['Transform'].getTranslation(space='world')
    vCamR = dCamInfo['Transform'].getRotation(space='world')
    #vCamS = dCamInfo['Transform'].getScale()

    dCamInfo['Global'].setTranslation([vCamT[0], 0, vCamT[2]], space='world')
    dCamInfo['Global'].setRotation([0, vCamR[1], 0], space='world')
    dCamInfo['Local'].setTranslation(vCamT, space='world')
    dCamInfo['Local'].setRotation([0, vCamR[1], 0], space='world')
    dCamInfo['Dolly'].setRotation(vCamR, space='world')
    dCamInfo['Dolly'].setTranslation([0, 0, 0], space='object')

    dCamInfo['Transform'].setTranslation([0, 0, 0], space='object')
    dCamInfo['Transform'].setRotation([0, 0, 0], space='object')
    dCamInfo['Transform'].setScale([1, 1, 1])

camCTRLReplace()