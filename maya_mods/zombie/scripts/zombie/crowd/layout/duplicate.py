
import maya.cmds as mc
import pymel.core as pm

from pytd.util.strutils import padded
#from pytaya.util import apiutils as myapi

from dminutes import geocaching
reload(geocaching)

def duplicate():
    sGeoGrpList, _ = geocaching._confirmProcessing("Duplicate", selected=True, confirm=True,
                                                   regexp="^cwp_", fromShapes=False)
    #sGeoGrpList = tuple(s for s in sGeoGrpList if mc.referenceQuery(s, isNodeReferenced=True))

    if not sGeoGrpList:
        mc.warning("No crowd to duplicate.")
        return

    sDupGeoGrpList = []
    #oRefList = []
    for sOriGeoGrp in sGeoGrpList:

        bIsRef = mc.referenceQuery(sOriGeoGrp, isNodeReferenced=True)
        if bIsRef:
            oOriRef = pm.FileReference(mc.referenceQuery(sOriGeoGrp, referenceNode=True))
            #oRefList.append(oOriRef)
            sOriNmspc = oOriRef.namespace
            oDupRef = pm.createReference(oOriRef.unresolvedPath(), ns=sOriNmspc)
            sDupNmspc = oDupRef.namespace
        else:
            sOriNmspc = geocaching.getNamespace(sOriGeoGrp)
            sAstName, incr = sOriNmspc.rsplit("_", 1)
            iPadd = len(incr)
            sDupNmspc = sOriNmspc
            while mc.namespace(exists=sDupNmspc):
                incr = int(incr) + 1
                incr = padded(incr, iPadd)
                sDupNmspc = sAstName + "_" + incr

            mc.namespace(add=sDupNmspc, parent=":")
            mc.namespace(set=sDupNmspc)
            try:
                mc.duplicate(sOriNmspc + ":asset", instanceLeaf=False, rr=True)
            finally:
                mc.namespace(set=":")

        sDupGeoGrp = sOriGeoGrp.replace(sOriNmspc + ":", sDupNmspc + ":")
        sDupGeoGrpList.append(sDupGeoGrp)

        if not bIsRef:
            for sOriMeshPath in mc.ls(sOriGeoGrp, dag=True, type="mesh"):
#                srcDagPath = myapi.getDagPath(sMeshPath)
#                if srcDagPath.isInstanced():
#                    n = srcDagPath.instanceNumber()
#                    print sMeshPath, n
                sDupMeshPath = geocaching.getNode(sOriMeshPath.replace(sOriNmspc + ":", sDupNmspc + ":"))
                if not sDupMeshPath:
                    continue

                sOutAttrList = mc.listConnections(sOriMeshPath, s=False, d=True, plugs=True, type="tripleShadingSwitch")
                if not sOutAttrList:
                    continue

                for sOutAttr in sOutAttrList:
                    if not sOutAttr.endswith(".inShape"):
                        continue

                    sSwitchNode = sOutAttr.split(".", 1)[0]
                    ids = mc.getAttr(sSwitchNode + ".input", multiIndices=True)
                    idx = (ids[-1] + 1) if ids else 0
                    sDupSwitchAttr = sSwitchNode + ".input[{}]".format(idx)
                    #print sDupMeshPath + ".instObjGroups[0]", sDupSwitchAttr + ".inShape"
                    mc.connectAttr(sDupMeshPath + ".instObjGroups[0]", sDupSwitchAttr + ".inShape")

                    sOriTripleAttr = sOutAttr.rsplit(".", 1)[0] + ".inTriple"
                    sInList = mc.listConnections(sOriTripleAttr, s=True, d=False, plugs=True)
                    if sInList:
                        #print sInList[0], sDupSwitchAttr + ".inTriple"
                        mc.connectAttr(sInList[0], sDupSwitchAttr + ".inTriple")

        astToAbcXfmItems = geocaching.getTransformMapping(sDupNmspc + ":asset", sOriNmspc, longName=True)
        geocaching.transferXfmAttrs(astToAbcXfmItems, dryRun=False, values=True,
                                    inConnections=False, keepSourceConnections=False)

        sOriAbcNodeList = mc.ls(sOriNmspc + ":*", type="AlembicNode")
        for sOriAbcNode in sOriAbcNodeList:

            sDupAbcNode = sOriAbcNode.replace(sOriNmspc + ":", sDupNmspc + ":")
            sDupAbcNode = geocaching.getNode(sDupAbcNode)
            if not sDupAbcNode:
                continue

            mc.copyAttr(sOriAbcNode, sDupAbcNode, values=True,
                        inConnections=False, keepSourceConnections=False)

    mc.select(sDupGeoGrpList)

duplicate()
