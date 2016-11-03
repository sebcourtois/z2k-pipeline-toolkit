
import maya.cmds as mc

from davos_maya.tool.general import infosFromScene
from pytaya.core.general import lsNodes

damShot = infosFromScene()["dam_entity"]

sCurShotCamList = mc.ls("cam_{}?:cam_shot_default".format(damShot.name[:-1]))

for sOtherShotCam in lsNodes("cam_shot_default", r=True, nodeNames=True, not_rn=True):

    if sOtherShotCam in sCurShotCamList:
        continue

    sNmspc = sOtherShotCam.rsplit(":", 1)
    sCamRoot = sNmspc + ":asset"
    mc.lockNode(mc.ls(sCamRoot, dag=True), lock=False)
    print "deleting", sCamRoot
    mc.delete(sCamRoot)
