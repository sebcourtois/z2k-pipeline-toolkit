
import os.path as osp
import re
from functools import partial
from pprint import pprint

from PySide import QtGui
from PySide.QtCore import Qt
from PySide.QtGui import QTreeWidgetItemIterator

import maya.cmds as mc
import pymel.core as pm

from pytd.util.fsutils import pathJoin, pathEqual

from davos_maya.tool.general import infosFromScene

from davos.core.damproject import DamProject

from dminutes import geocaching
from dminutes.maya_scene_operations import getMayaCacheDir
from random import randint
from pytaya.core.transform import matchTransform

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from pytd.gui.widgets import QuickTree
from pytd.util.strutils import labelify
from pytaya.util.sysutils import withSelectionRestored
from pytd.util.sysutils import toStr

reload(geocaching)


def delete(sGeoGrpList):

    for sGeoGrp in sGeoGrpList:

        bIsRef = mc.referenceQuery(sGeoGrp, isNodeReferenced=True)
        if bIsRef:
            oRef = pm.FileReference(mc.referenceQuery(sGeoGrp, referenceNode=True))
            oRef.remove()
#            sNmspc = oRef.fullNamespace
#            oRef.importContents()
        else:
            sNmspc = geocaching.getNamespace(sGeoGrp)

            sDelList = mc.ls(sNmspc + ":*")
            mc.delete(sDelList)
            try:
                mc.namespace(rm=sNmspc)
            except RuntimeError as e:
                pm.displayWarning(toStr(e))

def createPreviewSwitch():

    sSwitchExpr = """
    int $sel = .I[0];
    int $viz[];
    for ($i = 0; $i < 10; $i++) $viz[$i] = ($sel == $i) ? 1 : 0;
    
    .O[0] = $viz[0];
    .O[1] = $viz[1];
    .O[2] = $viz[2];
    .O[3] = $viz[3];
    .O[4] = $viz[4];
    .O[5] = $viz[5];
    .O[6] = $viz[6];
    .O[7] = $viz[7];
    .O[8] = $viz[8];
    .O[9] = $viz[9];
    """

    for sSgNode in mc.ls("sgr_*", type="shadingEngine"):

        sHistList = mc.listHistory(sSgNode, ac=True, pdo=True)
        if sHistList:
            sHistList = mc.ls(sHistList, type=("choice", "alSwitchColor", "lambert"))

        if not sHistList:
            continue

        #print sSgNode, sHistList

        try:
            sLamberNode = mc.ls(sHistList, type="lambert")[0]
        except IndexError:
            pm.displayInfo("preview 'lambert' node not found for '{}'".format(sSgNode))
            continue

        try:
            sSwicthNode = mc.ls(sHistList, type="alSwitchColor")[0]
        except IndexError:
            pm.displayInfo("'alSwitchColor' node not found for '{}'".format(sSgNode))
            continue

        try:
            sChoiceNode = mc.ls(sHistList, type="choice")[0]
        except IndexError:
            sChoiceNode = ""

        sBaseName = re.sub("^sgr_", "pre_", sSgNode)

        sLyrTexNode = getOrCreateNode("layeredTexture", "_".join((sBaseName, "layeredTexture")))
        sExprNode = getOrCreateNode("expression", "_".join((sBaseName, "expression")))
        mc.expression(sExprNode, e=True, alwaysEvaluate=False, string=sSwitchExpr)
        for i in xrange(10):
            connectAttr(sExprNode + ".output[{}]".format(i), sLyrTexNode + ".inputs[{}].isVisible".format(i), f=True)

        connectAttr("grp_geo.variationChoice", sExprNode + ".input[0]", f=True)

        for i, sLetter in enumerate("ABCDEFGHIJ"):
            sInList = mc.listConnections(sSwicthNode + ".input" + sLetter, s=True, d=False, p=True)
            if not sInList:
                continue
            sInAttr = sInList[0]
            connectAttr(sInAttr, sLyrTexNode + ".inputs[{}].color".format(i), f=True)

        if sChoiceNode:
            sOutList = mc.listConnections(sChoiceNode + ".output", s=False, d=True, p=True)
            for sOutAttr in sOutList:
                connectAttr(sLyrTexNode + ".outColor", sOutAttr, f=True)

            mc.delete(sChoiceNode)
        else:
            connectAttr(sLyrTexNode + ".outColor", sLamberNode + ".color", f=True)


def loadAssetAnimations(space="public"):

    scnInfos = infosFromScene()

    sCurAstType = scnInfos.get("assetType")
    if sCurAstType != "cwp":
        raise EnvironmentError("Crowd setup does NOT apply to asset of type: '{}'."
                               .format(sCurAstType))

    sScnRcName = scnInfos["resource"]
    if sScnRcName != "render_scene":
        sMsg = ("Crowd setup can only be applied on a 'render_scene'. Current is a '{}'"
                .format(sScnRcName))
        raise EnvironmentError(sMsg)

    damAst = scnInfos["dam_entity"]
    proj = damAst.project
    sAstName = damAst.name


    #just to check if needed objects exist
    for sObj in ("grp_geo", "grp_local"):
        pm.PyNode(sObj)

    jobList = listCacheImportJobs(proj, space, sAstName)

    if not jobList:
        raise RuntimeError("No animation to import !")

    pprint(jobList)

    importData = importAnimCaches(jobList)

    clearAnimSwith()
    setupAnimSwitch(jobList, importData)

    mc.select("grp_geo")

def clearAssetAnimations():
    clearAnimSwith()
    geocaching.clearConnectedCaches(["grp_geo"])

def clearAnimSwith():

    for sAttr in ("coveredDistance", "endFrame", "startFrame", "offset", "speed"):
        sNodeName = "_".join(("choice", sAttr))
        if mc.objExists(sNodeName):
            sOutExprList = mc.listConnections(sNodeName, s=False, d=True, type="expression")
            mc.delete(sNodeName)
            if sOutExprList:
                mc.delete(sOutExprList)

    if mc.objExists("grp_geo.animationChoice"):
        mc.deleteAttr("grp_geo.animationChoice")

    mc.setAttr("grp_local.translateZ", 0)

def setupAnimSwitch(jobList, importData):

    sExprFmt = """
    if ({coveredDistance}.output)
    {{
        float $cycleLen = ({endFrame}.output - {startFrame}.output);
        float $distPerFrame = {coveredDistance}.output / $cycleLen * {speed}.output;
        grp_local.translateZ = ((frame - {startFrame}.output)*$distPerFrame)-({offset}.output*$distPerFrame);
    }}
    else grp_local.translateZ = 0;"""

    if not mc.objExists("grp_geo.animationChoice"):
        sEnumList = list("{}={}".format(j["choice_label"], j["choice_index"]) for j in jobList)
        sEnumList.insert(0, "None=0")
        mc.addAttr("grp_geo", ln="animationChoice", at="enum",
                   en=":".join(sEnumList), defaultValue=0)
        mc.setAttr("grp_geo.animationChoice", e=True, keyable=True)

    for sChoiceNode in importData["grp_geo"]["choice_nodes"]:
        mc.connectAttr("grp_geo.animationChoice", sChoiceNode + ".selector")
        sPolyTrans = mc.listConnections(sChoiceNode + ".output", s=False, d=True)[0]
        sMeshOrigAttr = mc.listConnections(sPolyTrans + ".inputPolymesh", s=True, d=False, plugs=True)[0]
        mc.connectAttr(sMeshOrigAttr, sChoiceNode + ".input[0]")

    sAbcNodeList = importData["grp_geo"]["alembic_nodes"]

    for i, sNode in enumerate(sAbcNodeList):
        mc.setAttr(sNode + ".cycleType", 1)#Loop
        mc.addAttr(sNode, ln="coveredDistance", at="double", dv=0, min=0)
        mc.setAttr(sNode + ".coveredDistance", e=True, cb=True)
        mc.setAttr(sNode + ".coveredDistance", jobList[i]["covered_dist"])

    sChoiceNodeDct = {}
    for sAttr in ("coveredDistance", "endFrame", "startFrame", "offset", "speed"):

        sNodeName = "_".join(("choice", sAttr))
        sChoiceNode = mc.createNode("choice", n=sNodeName)
        sChoiceNodeDct[sAttr] = sChoiceNode
        for i, sAbcNode in enumerate(sAbcNodeList):

            if i == 0:
                dv = mc.attributeQuery(sAttr, node=sAbcNode, listDefault=True)[0]
                mc.setAttr(sChoiceNode + ".input[0]", dv)

            sInAttr = sChoiceNode + ".input[{}]".format(jobList[i]["choice_index"])
            mc.connectAttr(sAbcNode + "." + sAttr, sInAttr)

    for sChoiceNode in sChoiceNodeDct.itervalues():
        mc.connectAttr("grp_geo.animationChoice", sChoiceNode + ".selector")

    sExprCode = sExprFmt.format(**sChoiceNodeDct)
    sExprNode = mc.expression(s=sExprCode, ae=True, uc="all")

def importAnimCaches(jobList):

    geocaching.USE_LOGGING_SETS = False
    try:
        res = geocaching.importCaches(jobs=jobList, layoutViz=False, useCacheSet=False,
                                      dryRun=False, beforeHistory=True, removeRefs=True,
                                      showScriptEditor=False)
        pprint(res)
    finally:
        geocaching.USE_LOGGING_SETS = True

    return res

def listCacheImportJobs(proj, sSpace, sAstName):

    sgShotList = proj._shotgundb.find("Shot", [["sg_sequence", "name_is", "sq2000"],
                                              ["description", "contains", sAstName]],
                                      ["code", "description"],
                                      [{"field_name":"code", "direction":"asc"}])
    jobList = []
    for sgShot in sgShotList:

        damShot = proj.getShot(sgShot["code"])

        if sSpace == "local":
            sCacheDirPath = getMayaCacheDir(damShot)
        elif sSpace in ("public", "private"):
            sCacheDirPath = damShot.getPath(sSpace, "finalLayout_cache_dir")
        else:
            raise ValueError("Invalid space argument: '{}'".format(sSpace))

        sAbcPath = pathJoin(sCacheDirPath, sAstName + "_01_cache.abc")
        if not osp.isfile(sAbcPath):
            mc.warning("No such alembic file: {}".format(sAbcPath))
            continue

        iChoiceIdx = int(damShot.name.replace("sq2000_sh", "").strip("a")) % 100

        sDescList = tuple(s.strip() for s in sgShot["description"].split(","))
        sChoiceLabel = re.sub("\W", "_", sDescList[3])
        fDist = float(sDescList[4].rsplit(":")[-1])

        jobData = {"root":"grp_geo",
                   "file":sAbcPath,
                   "choice_index":iChoiceIdx,
                   "choice_label":sChoiceLabel,
                   "covered_dist":fDist,
                   }

        jobList.append(jobData)

    return jobList

def switchColors(sGeoGrpList):

    for sGeoGrp in sGeoGrpList:

        sVariaAttr = sGeoGrp + ".variationChoice"

        sVariaList = mc.addAttr(sVariaAttr, q=True, en=True)
        if not sVariaList:
            continue

        iCurVaria = mc.getAttr(sVariaAttr, asString=True)
        sCurVaria = mc.getAttr(sVariaAttr, asString=True)
        sCurFamily = sCurVaria.split("_", 1)[0]

        iVariaList = tuple(i for i, s in enumerate(sVariaList.split(":"))
                           if s.split("_", 1)[0] == sCurFamily)
        if not iVariaList:
            continue

        count = len(iVariaList)
        if count == 1:
            pm.displayWarning("Only one color available on '{}'".format(sCurFamily))
            continue

        v = iCurVaria
        while v == iCurVaria:
            v = iVariaList[randint(0, count - 1)]

        mc.setAttr(sVariaAttr, v)

def importAssignedVariations(assignedItems):

    proj = DamProject("zombillenium")

    sGeoGrpList = []
    count = len(assignedItems)
    for i, (target, astVariation) in enumerate(assignedItems):

        sAstName, sVariaName = astVariation
        damAst = proj.getAsset(sAstName)
        astFile = damAst.getResource("public", "render_ref", dbNode=False)

        bSwitchRef = isinstance(target, pm.FileReference)

        if not bSwitchRef:

            print "\nImporting {}/{} crowds: {}".format(i + 1, count, astFile.dbPath())

            res = astFile.mayaImportScene(deferReference=False, returnNewNodes=True,)
                                            #sharedNodes=("displayLayers", "shadingNetworks", "renderLayersByName"))

            oFileRef = res[0].referenceFile()
            sGeoGrp = oFileRef.namespace + ":grp_geo"

            if target.startswith("|"):
                sName = "decomposeMatrix"
            else:
                sName = target.replace("|", "_") + "_decomposeMatrix"

            sDecompMtx = mc.createNode("decomposeMatrix", n=sName)
            mc.connectAttr(target + ".worldMatrix[0]", sDecompMtx + ".inputMatrix")
            mc.connectAttr(sDecompMtx + ".outputTranslate", sGeoGrp + ".translate")
            mc.connectAttr(sDecompMtx + ".outputRotate", sGeoGrp + ".rotate")
            mc.connectAttr(sDecompMtx + ".outputScale", sGeoGrp + ".scale")
            #matchTransform(sGeoGrp, target)

        else:
            print "\nChanging {}/{} crowds: {}".format(i + 1, count, astFile.dbPath())

            mtx = None
            if not pathEqual(target.path, astFile.absPath()):

                sTrgtNmspc = target.namespace
                sGeoGrp = sTrgtNmspc + ":grp_geo"
                mtx = mc.xform(sGeoGrp, q=True, m=True, ws=True)

                target.replaceWith(astFile.envPath())

                sPrevAstName = "_".join(sTrgtNmspc.split("_")[:3])

                sRefNode = target.refNode.name()
                mc.lockNode(sRefNode, lock=False)
                try:
                    sRefNode = mc.rename(sRefNode, sRefNode.replace(sPrevAstName, sAstName))
                finally:
                    mc.lockNode(sRefNode, lock=True)

                sNewNmspc = sTrgtNmspc.replace(sPrevAstName, sAstName)
                target.namespace = sNewNmspc

            sGeoGrp = target.namespace + ":grp_geo"
            if mtx:
                mc.xform(sGeoGrp, m=mtx, ws=True)

        sVariaList = mc.addAttr(sGeoGrp + ".variationChoice", q=True, en=True)
        sVariaList = sVariaList.split(":")
        mc.setAttr(sGeoGrp + ".variationChoice", sVariaList.index(sVariaName))

        sGeoGrpList.append(sGeoGrp)

    return sGeoGrpList

def assignVariations(variaList, sObjList):

    if not sObjList:
        raise ValueError("Empty target object list: {}".format(sObjList))

    sRefNodeList = []
    targetList = []
    for sObj in mc.ls(sObjList, type="transform"):
        if mc.referenceQuery(sObj, isNodeReferenced=True):
            sRefNode = mc.referenceQuery(sObj, referenceNode=True, topReference=True)
            if sRefNode not in sRefNodeList:
                targetList.append(pm.FileReference(sRefNode))
                sRefNodeList.append(sRefNode)
        else:
            targetList.append(sObj)

    numVaria = len(variaList)
    mappedItems = tuple((target, variaList[randint(0, numVaria - 1)]) for target in targetList)

    return mappedItems

def iterVariations(variaDct, families=None, assets=None):

    if not families:
        mainIter = variaDct.iteritems()
    else:
        mainIter = (itm for itm in variaDct.iteritems() if itm[0] in families)

    if assets:
        _cwped = lambda s: (("cwp_" + s) if not s.startswith("cwp_") else s)
        sAstList = tuple(_cwped(s.rsplit("_", 1)[0]) for s in assets)
    else:
        sAstList = None

    for _, astVariaDct in mainIter:

        for sAstName, sVariaList in astVariaDct.iteritems():

            if sAstList and sAstName.rsplit("_", 1)[0] not in sAstList:
                continue

            for sVaria in sVariaList:
                yield (sAstName, sVaria)

@withSelectionRestored
def variationsFromLineUp(keepLineUp=False):

    proj = DamProject("zombillenium")

    lineUpScn = proj.getLibrary("public", "misc_lib").getEntry("layout/crowd_lineup.ma", dbNode=False)
    lineUpScn.mayaImportScene()
    oLineUpRef = pm.FileReference(lineUpScn.absPath())

    variationDct = {}
    try:
        for oAstRef in pm.listReferences(parentReference=oLineUpRef):
    
            sGeoGrp = oAstRef.fullNamespace + ":grp_geo"
            sVariaList = mc.addAttr(sGeoGrp + ".variationChoice", q=True, en=True)
            if not sVariaList:
                continue
            sAstName = "_".join(oAstRef.namespace.split("_")[:3])
            sVariaList = sVariaList.split(":")
            for sVaria in sVariaList:
                sFamily = sVaria.split("_", 1)[0]
                variationDct.setdefault(sFamily, {}).setdefault(sAstName, []).append(sVaria)
    finally:
        if not keepLineUp:
            oLineUpRef.remove()

    return variationDct


def importLineUp():

    proj = DamProject("zombillenium")

    sgAstList = proj.listAllSgAssets(moreFilters=[["sg_asset_type", "is", "crowd previz"]])

    spacing = 12
    lineLen = spacing * len(sgAstList)

    x = lineLen * -.5
    for i, sgAst in enumerate(sgAstList):

        sAstName = sgAst["code"]
        damAst = proj.getAsset(sAstName)

        astFile = damAst.getResource("public", "render_ref", dbNode=False)
        res = astFile.mayaImportScene()

        oFileRef = res[0].referenceFile()
        sGeoGrp = oFileRef.namespace + ":grp_geo"

        mc.setAttr(sGeoGrp + ".tx", x + (i * spacing))

def getOrCreateNode(sNodeType, sNodeName):

    if mc.objExists(sNodeName):
        #mc.delete(sNodeName)
        return sNodeName

    return mc.shadingNode(sNodeType, n=sNodeName, asUtility=True)

def connectAttr(*args, **kwargs):
    if not mc.isConnected(*args, ignoreUnitConversion=True):
        return mc.connectAttr(*args, **kwargs)

class FlavorDialog(MayaQWidgetDockableMixin, QtGui.QDialog):

    def __init__(self, parent=None):
        super(FlavorDialog, self).__init__(parent=parent)

        self.setObjectName("CrowdFlavorSelector")
        self.setWindowTitle(labelify(self.objectName()))
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.resize(380, 400)

        layout = QtGui.QVBoxLayout(self)

        treeWdg = QuickTree(self)
        layout.addWidget(treeWdg)
        layout.setSpacing(6)
        layout.setContentsMargins(4, 4, 4, 4)

        buttonBox = QtGui.QDialogButtonBox(self)
        buttonBox.setOrientation(Qt.Horizontal)
        buttonBox.setObjectName("buttonBox")

        btn = buttonBox.addButton("Check All", QtGui.QDialogButtonBox.ResetRole)
        btn.clicked.connect(partial(self.setAllCheckState, Qt.Checked))
        btn = buttonBox.addButton("Uncheck All", QtGui.QDialogButtonBox.ResetRole)
        btn.clicked.connect(partial(self.setAllCheckState, Qt.Unchecked))
        btn = buttonBox.addButton("Assign", QtGui.QDialogButtonBox.AcceptRole)
        btn.clicked.connect(self.proceed)
        btn = buttonBox.addButton("Close", QtGui.QDialogButtonBox.RejectRole)
        btn.clicked.connect(self.reject)
        layout.addWidget(buttonBox)

        variationDct = variationsFromLineUp()

        treeDataList = []
        for sFamily, astVariaDct in variationDct.iteritems():
            for sAstName in astVariaDct.iterkeys():
                sTreePath = pathJoin(sFamily, sAstName)
                roleData = {Qt.UserRole:(0, (sFamily, sAstName))}
                treeDataList.append({"path":sTreePath, "flags":None,
                                     "roles":roleData})

        treeWdg.headerItem().setHidden(True)
        treeWdg.itemDelegate().setItemMarginSize(2, 2)
        treeWdg.defaultFlags |= Qt.ItemIsTristate
        treeWdg.defaultRoles = {Qt.CheckStateRole:(0, Qt.Checked)}
        treeWdg.createTree(treeDataList)

        for i in xrange(treeWdg.topLevelItemCount()):
            treeWdg.topLevelItem(i).setExpanded(True)

        self.treeWdg = treeWdg
        self.allVariations = variationDct

    def proceed(self):

        flags = (QTreeWidgetItemIterator.Checked | QTreeWidgetItemIterator.Enabled)
        treeIter = QTreeWidgetItemIterator(self.treeWdg, flags)
        dataIter = (it.value().data(0, Qt.UserRole) for it in treeIter)
        dataList = tuple(d for d in dataIter if d)

        if not dataList:
            pm.displayWarning("No variation selected.")
            return

        families = tuple(f for f, _ in dataList)
        assets = tuple(a for _, a in dataList)

        variaList = tuple(iterVariations(self.allVariations, families, assets))
        assignedItems = assignVariations(variaList, mc.ls(sl=True, dag=False, tr=True))
        sGeoGrpList = importAssignedVariations(assignedItems)
        mc.select(sGeoGrpList)

    def setAllCheckState(self, qChecked):

        treeWdg = self.treeWdg
        for i in xrange(treeWdg.topLevelItemCount()):
            treeWdg.topLevelItem(i).setCheckState(0, qChecked)


