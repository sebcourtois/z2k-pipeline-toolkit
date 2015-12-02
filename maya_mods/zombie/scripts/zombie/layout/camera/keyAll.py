
import maya.cmds as mc

from dminutes import maya_scene_operations as mop
reload(mop)

def camKeyAll():
    dCamInfo = mop.getCameraRig()

    mc.setKeyframe(dCamInfo['Global'].longName(), dCamInfo['Local'].longName(),
                   dCamInfo['Dolly'].longName(), dCamInfo['Transform'].longName(),
                   attribute=['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ'])
    mc.setKeyframe(dCamInfo['Shape'].longName(), attribute=['focalLength'])

camKeyAll()