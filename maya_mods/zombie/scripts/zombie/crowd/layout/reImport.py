
from pprint import pprint

import maya.cmds as mc
import pymel.core as pm
import pymel.util as pmu

from pytd.util.qtutils import setWaitCursor


from dminutes import geocaching, crowd
from davos.core.damproject import DamProject
from pytaya.core.general import lsNodes

reload(geocaching)
reload(crowd)

@setWaitCursor
def reImportRef():

    sGeoGrpList, _ = geocaching._confirmProcessing("Re-reference crowd", selected=True, confirm=True,
                                                   regexp="^cwp_", fromShapes=False)

    if  not sGeoGrpList:
        mc.warning("No crowd to re-reference.")
        return

    proj = DamProject("zombillenium", empty=True)

    sDupGeoGrpList = []
    for sOriGeoGrp in sGeoGrpList:

        if mc.referenceQuery(sOriGeoGrp, isNodeReferenced=True):
            continue

        sOriNmspc = geocaching.getNamespace(sOriGeoGrp)
        sAstName = "_".join(sOriNmspc.split("_")[:3])

        damAst = proj.getAsset(sAstName)
        refFile = damAst.getResource("public", "render_ref", dbNode=False)
        oRef = refFile.mayaImportScene(returnNewNodes=False)

        sDupNmspc = oRef.fullNamespace

        sDupGeoGrp = sOriGeoGrp.replace(sOriNmspc + ":", sDupNmspc + ":")
        sDupGeoGrpList.append(sDupGeoGrp)

        astToAbcXfmItems = geocaching.getTransformMapping(sDupNmspc + ":asset", sOriNmspc, longName=True)
        geocaching.transferXfmAttrs(astToAbcXfmItems, dryRun=False, values=True, locked=True,
                                    inConnections=False, keepSourceConnections=False)

        sOriAbcNodeList = mc.ls(sOriNmspc + ":*", type="AlembicNode")
        for sOriAbcNode in sOriAbcNodeList:

            sDupAbcNode = sOriAbcNode.replace(sOriNmspc + ":", sDupNmspc + ":")
            sDupAbcNode = geocaching.getNode(sDupAbcNode)
            if not sDupAbcNode:
                continue

            mc.copyAttr(sOriAbcNode, sDupAbcNode, values=True,
                        inConnections=False, keepSourceConnections=False)

        crowd.delete([sOriGeoGrp])

    if sDupGeoGrpList:
        mc.select(sDupGeoGrpList)

    return

reImportRef()
