
import pymel.core as pm

from pytaya.core.transform import matchTransform
from davos_maya.tool.general import entityFromScene
from dminutes import maya_scene_operations as mop

def addMirrorCam():

    oSelList = pm.selected()

    damShot = entityFromScene()
    sCurShotCode = damShot.name

    oShotCam = mop.getShotCamera(sCurShotCode, fail=True)
    #print oShotCam

    proj = damShot.project
    mirCamFile = proj.getLibrary("public", "misc_lib").getEntry("layout/mirror_cam.ma")
    #print mirCamFile

    camAst = proj.getAsset("cam_shot_default")
    newCamFile = camAst.getResource("public", "scene")
    #print newCamFile

    sMirShotCode = ""
    result = pm.promptDialog(title='Please...',
                          message='mirror shot name: ',
                          button=['OK', 'Cancel'],
                          defaultButton='OK',
                          cancelButton='Cancel',
                          dismissString='Cancel',
                          text=sCurShotCode[:-1] + "b",
                          scrollableField=True)

    if result == 'Cancel':
        pm.displayWarning("Canceled !")
        return
    elif result == 'OK':
        sMirShotCode = pm.promptDialog(query=True, text=True)

    oMirShotCam = mop.getShotCamera(sMirShotCode, fail=False)
    if oMirShotCam:
        raise RuntimeError("Camera already exists: '{}'".format(oMirShotCam))

    sImpNs = "mirror_cam" + "_" + sMirShotCode
    oNewObjList = mirCamFile.mayaImportScene(returnNewNodes=True,
                                             ns=sImpNs)
    oNewObjList = pm.ls(oNewObjList, type="transform")
    sMirCamNs = oNewObjList[0].parentNamespace()
    oMirFtLoc = pm.PyNode(sMirCamNs + ":loc_cameraFront")
    oMirBkLoc = pm.PyNode(sMirCamNs + ":loc_cameraBack")
    oMirCamBk = pm.PyNode(sMirCamNs + ":camBack")
    oMirPlane = pm.PyNode(sMirCamNs + ":mirror_plane")

    sNewCamNs = mop.mkShotCamNamespace(sMirShotCode)
    newCamFile.mayaImportScene(ns=sNewCamNs)
    oMirShotCam = mop.getShotCamera(sMirShotCode, fail=True)
    oNewGlobal = pm.PyNode(sNewCamNs + ":Global_SRT")

    matchTransform(oMirFtLoc, oShotCam, atm="tr")
    matchTransform(oNewGlobal, oMirBkLoc, atm="tr")
    pm.rotate(oNewGlobal, (0, 180, 0), r=True, os=True, fo=True)
    pm.refresh()

    pm.parentConstraint(oShotCam, oMirFtLoc, maintainOffset=True)
    pm.parentConstraint(oMirBkLoc, oNewGlobal, maintainOffset=True)
    pm.parentConstraint(oMirShotCam, oMirCamBk, maintainOffset=True)

    oMirCamBk.getShape().setAttr("visibility", False)
    pm.copyAttr(oShotCam.getShape(), oMirShotCam.getShape(), values=True)

    if oSelList:
        matchTransform(oMirPlane, oSelList[0], atm="tr")

    pm.select(oMirPlane)

addMirrorCam()
