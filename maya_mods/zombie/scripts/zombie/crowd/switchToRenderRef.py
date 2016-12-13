
import maya.cmds as mc

from davos_maya.tool import reference as myaref
reload(myaref)

def preSwitch(oFileRef):

    sLocalSrt = oFileRef.namespace + ":Local_SRT"
    if not mc.objExists(sLocalSrt):
        return

    return mc.xform(sLocalSrt, q=True, m=True, ws=True)

def postSwitch(oFileRef, mtx):

    sGeoGrp = oFileRef.namespace + ":grp_geo"
    if not mc.objExists(sGeoGrp):
        return

    mc.xform(sGeoGrp, m=mtx, ws=True)

myaref.switchSelectedAssetFiles(allIfNoSelection=False, filter="render_ref",
                                preSwitchCall=preSwitch, postSwitchCall=postSwitch)
