

import os
import os.path as osp
from itertools import izip

import maya.cmds as mc
import pymel.core as pm
import pymel.util as pmu

from pytd.util.fsutils import pathResolve, normCase
from davos.core.damproject import DamProject
from collections import OrderedDict

okValue = 'OK'
noneValue = 'MISSING'


def loadProject():

    bBatchMode = pm.about(batch=True)
    proj = DamProject(os.environ["DAVOS_INIT_PROJECT"], empty=bBatchMode)
    proj.loadEnviron()

def projectFromScene(scenePath=""):

    sCurScnPath = scenePath if scenePath else pm.sceneName()
    if not sCurScnPath:
        raise ValueError("Current scene is untitled.".format(sCurScnPath))

    return DamProject.fromPath(sCurScnPath, fail=True)

def entityFromScene(scenePath="", fail=True):

    sCurScnPath = scenePath if scenePath else pm.sceneName()
    if not sCurScnPath:
        raise ValueError("Current scene is untitled.".format(sCurScnPath))

    proj = DamProject.fromPath(sCurScnPath, fail=True)
    damEntity = proj.entityFromPath(sCurScnPath, fail=fail)

    return damEntity

def infosFromScene(scenePath="", fail=True):

    scnInfos = {}

    sCurScnPath = scenePath if scenePath else pm.sceneName()
    if not sCurScnPath:
        raise ValueError("Current scene is untitled.".format(sCurScnPath))

    proj = DamProject.fromPath(sCurScnPath, fail=True)
    ctxData = {}
    rcFile = proj.entryFromPath(sCurScnPath, fail=fail)
    if rcFile:
        ctxData = proj.contextFromPath(rcFile)
        scnInfos.update(ctxData)

    scnInfos.update(project=proj)

    return scnInfos

def assertSceneInfoMatches(scnInfos, sRcName, msg=""):

    if scnInfos.get("resource") != sRcName:
        sMsg = "Current scene is NOT a '{}'.".format(sRcName) if not msg else msg
        raise AssertionError(sMsg)

def setMayaProject(sProjName, sEnvVar):

    if not sProjName:
        raise ValueError("Invalid project name: '{}'".format(sProjName))

    if not sEnvVar:
        raise ValueError("Invalid env. variable: '{}'".format(sEnvVar))

    sMayaProjsLoc = osp.dirname(osp.normpath(mc.workspace(q=True, rd=True)))
    sMayaProjPath = osp.join(sMayaProjsLoc, sProjName)

    if not osp.exists(sMayaProjPath):
        os.mkdir(sMayaProjPath)

    mc.workspace(update=True)
    mc.workspace(sProjName, openWorkspace=True)

    if not mc.workspace(fileRuleEntry="movie"):
        mc.workspace(fileRule=("movie", "captures"))
        mc.workspace(saveWorkspace=True)

    if not mc.workspace(fileRuleEntry="alembicCache"):
        mc.workspace(fileRule=("alembicCache", "cache/alembic"))
        mc.workspace(saveWorkspace=True)

    pmu.putEnv(sEnvVar, sMayaProjPath.replace("\\", "/"))

    return sMayaProjPath

def listRelatedAssets(damShot):
    """Compare Shotgun shot<=>assets linking and scene content"""

    proj = damShot.project
    astLib = proj.getLibrary("public", "asset_lib")

    initData = {'name':'',
                'sg_link':noneValue,
                'sg_asset_shot_conn':None,
                'resource':noneValue,
                'path':"",
                'maya_rcs':{},
                'file_refs':[],
                'occurences':0 }

    astShotConnList = damShot.getSgRelatedAssets()
    assetShotConnDct = dict((d['asset']['name'].lower(), d) for d in astShotConnList)

    assetDataList = []
    sSgAstList = []
    oFileRefDct = {}
    for oFileRef in pm.iterReferences():

        sRefPath = pathResolve(oFileRef.path)

        sRefNormPath = normCase(sRefPath)
        if sRefNormPath in oFileRefDct:
            oFileRefDct[sRefNormPath].append(oFileRef)
            continue
        else:
            oFileRefDct[sRefNormPath] = [oFileRef]

        pathData = proj.contextFromPath(sRefPath, library=astLib, warn=False)

        astData = initData.copy()
        astData.update(path=sRefPath, file_refs=oFileRefDct[sRefNormPath])

        astData.update(pathData)
        #print sorted(astData.iteritems(), key=lambda x:x[0])

        sAstKey = astData["name"].lower()
        if sAstKey in assetShotConnDct:
            astData.update(sg_link=okValue, sg_asset_shot_conn=assetShotConnDct[sAstKey])
            sSgAstList.append(sAstKey)

        assetDataList.append(astData)

    for sAstKey, astShotConn in assetShotConnDct.iteritems():
        if sAstKey not in sSgAstList:
            astData = initData.copy()
            astData.update(name=astShotConn['asset']['name'], sg_link=okValue,
                           sg_asset_shot_conn=astShotConn)
            assetDataList.append(astData)

    allMyaFileDct = {}
    allMyaFileList = []
    for astData in assetDataList:

        sAstName = astData['name']
        if not sAstName:
            continue

        damAst = astData.get("dam_entity")
        if not damAst:
            damAst = proj.getAsset(sAstName)

        entryFromPath = lambda p: proj.entryFromPath(p, library=astLib, dbNode=False)
        mayaRcIter = damAst.iterMayaRcItems(filter="*_ref")
        mayaFileDct = OrderedDict((n, entryFromPath(p)) for n, p in mayaRcIter)
        allMyaFileDct[sAstName] = mayaFileDct

        allMyaFileList.extend(f for _, f in mayaFileDct.iteritems() if f)

        sCurRcName = astData["resource"]
        if sCurRcName and (sCurRcName != noneValue) and (sCurRcName not in mayaFileDct):
            curRcFile = astData["rc_entry"]
            if curRcFile:
                allMyaFileList.append(curRcFile)

    dbNodeList = proj.dbNodesForResources(allMyaFileList)
    for mrcFile, dbNode in izip(allMyaFileList, dbNodeList):
        if not dbNode:
            mrcFile.getDbNode(fromCache=False)

    for astData in assetDataList:

        sAstName = astData['name']
        if not sAstName:
            continue

        mayaFileDct = allMyaFileDct[sAstName]

        astRcDct = {}
        for sRcName, mrcFile in mayaFileDct.iteritems():

            rcDct = {"drc_file":mrcFile, "status":okValue}
            astRcDct[sRcName] = rcDct

            if not mrcFile:
                rcDct["status"] = noneValue
                continue

            if not mrcFile.currentVersion:
                rcDct["status"] = "NO VERSION"
                continue

            rcDct["version"] = mrcFile.currentVersion

            mrcVersFile = None
            try:
                mrcVersFile = mrcFile.assertLatestFile(refresh=False, returnVersion=True)
            except AssertionError as e:
                pm.displayWarning(e.message)
                rcDct["status"] = "OUT OF SYNC"

            rcDct["version_file"] = mrcVersFile

        curVersFile = None
        curRcFile = astData.get("rc_entry")
        if curRcFile:
            if curRcFile.isVersionFile():
                curVersFile = curRcFile
            else:
                sCurRcName = astData["resource"]
                curVersFile = None
                if sCurRcName in astRcDct:
                    curVersFile = astRcDct[sCurRcName]["version_file"]
                else:
                    try:
                        curVersFile = curRcFile.assertLatestFile(refresh=False, returnVersion=True)
                    except AssertionError as e:
                        pm.displayWarning(e.message)

                iCurVers = curRcFile.currentVersion
                if (not curVersFile) and iCurVers > 1:
                    v = iCurVers - 1
                    while (not curVersFile) and v > 0:
                        curVersFile = curRcFile.getVersionFile(v, refresh=False, dbNode=False)
                        v = iCurVers - 1

        astData["version_file"] = curVersFile
        astData["maya_rcs"] = astRcDct
        astData["occurences"] = len(astData["file_refs"])

    return assetDataList

def iterGeoGroups(**kwargs):

    bSelected = kwargs.get("selected", kwargs.get("sl", False))
    sObjList = kwargs.get("among", None)
    sNmspcList = kwargs.get("namespaces", None)

    if sObjList:
        bSelected = False

    if bSelected:
        sObjList = mc.ls(sl=True, dag=True, type="shape", ni=True)
        sNmspcList = set(o.rsplit("|", 1)[-1].rsplit(":", 1)[0] for o in sObjList)
    elif sNmspcList is None:
        sNmspcList = mc.namespaceInfo(listOnlyNamespaces=True)

    for sNmspc in sNmspcList:

        if sNmspc.endswith("_cache"):
            continue

        sGeoGrp = sNmspc + ":grp_geo"
        if mc.objExists(sGeoGrp):
            yield sGeoGrp
