

#import os
import os.path as osp
#import subprocess

import maya.cmds as mc
import pymel.core as pm

from pytd.util.fsutils import pathJoin

from davos_maya.tool.general import entityFromScene

from dminutes import maya_scene_operations as mop
from dminutes import gpucaching

reload(mop)
reload(gpucaching)

@mop.withParallelEval
def exportCaches():

    damShot = entityFromScene()

    sAbcDirPath = mop.getAlembicCacheDir(damShot)

    frameRange = (pm.playbackOptions(q=True, animationStartTime=True),
                 pm.playbackOptions(q=True, animationEndTime=True))

    sJobList = []
    for sGeoGrp in gpucaching.iterGeoGroups():
        sNmspc = sGeoGrp.rsplit("|", 1)[-1].rsplit(":", 1)[0]
        sAbcPath = pathJoin(sAbcDirPath, sNmspc + "_cache.abc")
        sJob = ("-noNormals -renderableOnly -uvWrite -writeVisibility -frameRange {range[0]} {range[1]} -root {root} -file {file}"
                .format(range=frameRange, root=sGeoGrp, file=sAbcPath))
        print sJob
        sJobList.append(sJob)

    mc.AbcExport(v=True, j=sJobList)

def connectAlembicToMeshes(sRefAbcNode, sTargetNamespace):

        sAbcMeshXfmList = mc.listConnections(sRefAbcNode, s=False, d=True, type="mesh")
#        sAbcMeshXfmList = tuple(s.rsplit("|", 1)[0] for s in mc.ls(sNewNodeList, type="mesh", long=True, ni=True))

        if not sAbcMeshXfmList:
            pm.displayInfo("No meshes has been cached !")
            return

        print len(sAbcMeshXfmList), "cached meshes."

        sDupAbcNode = mc.duplicate(sRefAbcNode, ic=True)[0]

#        sAbcMeshXfmList = mc.ls(sAbcMeshXfmList, long=False)# just to convert long to short names.
#        sAbcNmspc = sAbcMeshXfmList[0].rsplit("|", 1)[-1].rsplit(":", 1)[0]

        for sAbcMeshXfm in sAbcMeshXfmList:

            sRndMeshXfm = sAbcMeshXfm.rsplit("|", 1)[-1].rsplit(":", 1)[-1]
            sRndMeshXfm = sTargetNamespace + ":" + sRndMeshXfm

            sFoundList = mc.ls(sRndMeshXfm, type="transform")
            if not sFoundList:
                pm.displayWarning("No such object named '{}'".format(sRndMeshXfm))
                continue
            elif len(sFoundList) > 1:
                pm.displayWarning("Multiple objects named '{}'".format(sRndMeshXfm))
                continue

            sFoundList = mc.listRelatives(sRndMeshXfm, c=True, type="mesh", path=True, ni=True)
            if not sFoundList:
                pm.displayWarning("No mesh shape found under '{}'.".format(sRndMeshXfm))
                continue
            elif len(sFoundList) > 1:
                pm.displayWarning("Multiple mesh shapes found under '{}'.".format(sRndMeshXfm))
                continue

            #sMeshShape = sFoundList[0]

            sAbcMeshShape = mc.listRelatives(sAbcMeshXfm, c=True, type="mesh", path=True, ni=True)[0]

            abcStat = mc.polyEvaluate(sAbcMeshXfm, v=True, f=True)
            rndStat = mc.polyEvaluate(sRndMeshXfm, v=True, f=True)

            if abcStat != rndStat:
                if abcStat["vertex"] != rndStat["vertex"]:
                    sMsg = "Number of vertices differs:"
                    sMsg += "\n    - '{}': {} verts".format(sAbcMeshXfm, abcStat["vertex"])
                    sMsg += "\n    - '{}': {} verts".format(sRndMeshXfm, rndStat["vertex"])
                    pm.displayWarning(sMsg)
                    continue
                elif abcStat["face"] != rndStat["face"]:
                    sMsg = "Number of faces differs:"
                    sMsg += "\n    - '{}': {} faces".format(sAbcMeshXfm, abcStat["face"])
                    sMsg += "\n    - '{}': {} faces".format(sRndMeshXfm, rndStat["face"])
                    pm.displayInfo(sMsg)

            sTransfNode = mc.polyTransfer(sRndMeshXfm, ao=sAbcMeshXfm,
                                          uv=False, v=True, vc=False, ch=True)[0]
            sAbcOutAttr = mc.listConnections(sAbcMeshShape, s=True, d=False,
                                             type="AlembicNode", plugs=True)[0]

            sAbcOutAttr = sAbcOutAttr.replace(sRefAbcNode, sDupAbcNode)
            mc.connectAttr(sAbcOutAttr, sTransfNode + ".otherPoly", f=True)

            mc.hide(sAbcMeshXfm)

def importCaches():

    damShot = entityFromScene()
    sAbcDirPath = mop.getAlembicCacheDir(damShot)

    oFileRefList = []

    try:
        for sGeoGrp in gpucaching.iterGeoGroups():

            sAstNmspc = sGeoGrp.rsplit("|", 1)[-1].rsplit(":", 1)[0]
            sBaseName = sAstNmspc + "_cache"
            sAbcPath = pathJoin(sAbcDirPath, sBaseName + ".abc")

            if not osp.isfile(sAbcPath):
                pm.displayWarning("No such alembic file: '{}'".format(sAbcPath))
                continue

            print "\nImporting caches from '{}'".format(sAbcPath)

            sNewNodeList = mc.file(sAbcPath, type="Alembic", r=True, ns=sBaseName,
                                   rnn=True, mergeNamespacesOnClash=False, gl=True)

            oFileRef = pm.PyNode(sNewNodeList[0]).referenceFile()
            oFileRefList.append(oFileRef)

            sFoundList = mc.ls(sNewNodeList, type="AlembicNode")
            if not sFoundList:
                pm.displayInfo("No Alembic Node imported !")
                continue

            sRefAbcNode = sFoundList[0]

            connectAlembicToMeshes(sRefAbcNode, sAstNmspc)
    finally:
        for oFileRef in oFileRefList:
            oFileRef.remove()
