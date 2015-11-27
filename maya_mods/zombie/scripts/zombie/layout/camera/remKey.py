
import maya.cmds as mc

from dminutes import maya_scene_operations as mop
reload(mop)


def camRemKey():
    dCamInfo = mop.getCameraRig()

    mc.cutKey(dCamInfo['Global'].longName(), dCamInfo['Local'].longName(),
              dCamInfo['Dolly'].longName(), dCamInfo['Transform'].longName(),
              attribute=['translateX', 'translateY', 'translateZ', 'rotateX',
                         'rotateY', 'rotateZ', 'scaleX', 'scaleY', 'scaleZ', 'visibility'])
    mc.cutKey(dCamInfo['Shape'].longName(), attribute=['focalLength'])

camRemKey()