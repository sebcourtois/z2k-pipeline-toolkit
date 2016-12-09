
import os.path as osp
import re
from pprint import pprint

import maya.cmds as mc
import pymel.core as pm

from pytd.util.fsutils import pathJoin

from davos_maya.tool.general import infosFromScene

from dminutes import geocaching
from dminutes.maya_scene_operations import getMayaCacheDir

reload(geocaching)


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

        sLyrTexNode = createSharedNode("layeredTexture", "_".join((sBaseName, "layeredTexture")))
        sExprNode = createSharedNode("expression", "_".join((sBaseName, "expression")))
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
        sEnumList = tuple("{}={}".format(j["choice_label"], j["choice_index"]) for j in jobList)
        mc.addAttr("grp_geo", ln="animationChoice", at="enum",
                   en=":".join(sEnumList), defaultValue=jobList[0]["choice_index"])
        mc.setAttr("grp_geo.animationChoice", e=True, keyable=True)

    for sChoiceNode in importData["grp_geo"]["choice_nodes"]:
        mc.connectAttr("grp_geo.animationChoice", sChoiceNode + ".selector")

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

def createSharedNode(sNodeType, sNodeName):
    sNewNode = mc.createNode(sNodeType, n=sNodeName, shared=True)
    return sNewNode if sNewNode else sNodeName

def connectAttr(*args, **kwargs):
    if not mc.isConnected(*args, ignoreUnitConversion=True):
        return mc.connectAttr(*args, **kwargs)
