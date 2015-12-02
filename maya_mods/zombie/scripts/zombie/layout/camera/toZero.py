
from dminutes import maya_scene_operations as mop
reload(mop)

def camToZero():
    dCamInfo = mop.getCameraRig()

    vCamT = dCamInfo['Transform'].getTranslation(space='world')
    vCamR = dCamInfo['Transform'].getRotation(space='world')
    #vCamS = dCamInfo['Transform'].getScale()

    dCamInfo['Global'].setTranslation([0, 0, 0], space='world')
    dCamInfo['Global'].setRotation([0, 0, 0], space='world')
    dCamInfo['Local'].setTranslation([0, 0, 0], space='world')
    dCamInfo['Local'].setRotation([0, 0, 0], space='world')
    dCamInfo['Dolly'].setRotation([0, 0, 0], space='world')
    dCamInfo['Dolly'].setTranslation([0, 0, 0], space='world')

    dCamInfo['Transform'].setTranslation(vCamT, space='world')
    dCamInfo['Transform'].setRotation(vCamR, space='world')
    dCamInfo['Transform'].setScale([1, 1, 1])

camToZero()