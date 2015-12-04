
#import os.path as osp
import pymel.core as pm

from pytaya.util.sysutils import withSelectionRestored
from pytaya.core.reference import processSelectedReferences
from pytd.util.fsutils import pathResolve, normCase
from itertools import izip
from davos_maya.tool.general import entityFromScene
from pytd.util.sysutils import toStr
from pytd.gui.dialogs import confirmDialog



@processSelectedReferences
def listMayaRcForSelectedRefs(oFileRef, project, **kwargs):

    sRefPath = pathResolve(oFileRef.path)
    asset = project.entityFromPath(sRefPath)

    mayaRcDct = dict()
    if asset:
        mayaRcDct = dict((rc, p if normCase(p) != normCase(sRefPath) else "current")
                                    for rc, p in asset.iterMayaRcItems(**kwargs))
    res = (asset, mayaRcDct)

    resultList = kwargs.pop("processResults")
    resultList.append(res)

@withSelectionRestored
def switchSelectedReferences(dryRun=False, **kwargs):

    damEntity = entityFromScene()
    proj = damEntity.project

    kwargs.update(confirm=False, allIfNoSelection=True, topReference=True)

    oSelRefList, assetRcList = listMayaRcForSelectedRefs(proj, **kwargs)

    assetList = tuple(ast for ast, _ in assetRcList if ast)
    if not assetList:
        pm.displayWarning("No Asset References selected !")
        return

    sRcNameSet = set()
    for _, rcDct in assetRcList:
        sRcNameSet.update(rcDct.iterkeys())

    if not sRcNameSet:
        pm.displayWarning("No available resources on which to switch !")

    sortedRcNames = sorted(sRcNameSet)

    numRefs = len(oSelRefList)
    sMsg = 'Switch {} Asset References to...'.format(numRefs)
    sChosenRcName = pm.confirmDialog(title="Hey, mon ami !",
                                     message=sMsg,
                                     button=sortedRcNames + ['Cancel'],
                                     defaultButton='Cancel',
                                     cancelButton='Cancel',
                                     dismissString='Cancel',
                                     icon="question")

    if sChosenRcName == 'Cancel':
        pm.warning("Canceled !")
        return

    i = 0
    nonSwitchedRefList = []
    for oFileRef, assetRc in izip(oSelRefList, assetRcList):

        asset = assetRc[0]
        rcDct = assetRc[1]

        i += 1
        print "Switching {}/{}: '{}' ...".format(i, numRefs, oFileRef.refNode.name())

        if not asset:
            sMsg = "Unknown asset: '{}'".format(oFileRef.path)
            nonSwitchedRefList.append((oFileRef, sMsg))
            print sMsg
            continue

        if not oFileRef.isLoaded():
            sMsg = "Reference not loaded"
            nonSwitchedRefList.append((oFileRef, sMsg))
            print sMsg
            continue

        sRcPath = rcDct.get(sChosenRcName)
        if not sRcPath:
            sMsg = "{} has no such resource: '{}'".format(asset, sChosenRcName)
            nonSwitchedRefList.append((oFileRef, sMsg))
            print sMsg
            continue

        if sRcPath == "current":
            sMsg = "Reference already switched as '{}'".format(sChosenRcName)
            nonSwitchedRefList.append((oFileRef, sMsg))
            print sMsg
            continue

        mrcFile = proj.entryFromPath(sRcPath, library=asset.getLibrary(), dbNode=False)
        if not mrcFile:
            sMsg = "File not found: '{}'".format(sRcPath)
            nonSwitchedRefList.append((oFileRef, sMsg))
            print sMsg
            continue

        cachedDbNode = mrcFile.getDbNode(fromDb=False)
        if cachedDbNode:
            mrcFile.refresh(simple=True)
        else:
            mrcFile.getDbNode(fromCache=False)

        if not mrcFile.currentVersion:
            sMsg = "No version created yet: '{}'".format(sRcPath)
            nonSwitchedRefList.append((oFileRef, sMsg))
            print sMsg
            continue

        if not mrcFile.isUpToDate(refresh=False):
            sMsg = "File is out of sync: '{}'".format(sRcPath)
            nonSwitchedRefList.append((oFileRef, sMsg))
            print sMsg
            continue

        if not dryRun:
            try:
                oFileRef.replaceWith(mrcFile.envPath())
            except Exception as e:
                sMsg = toStr(e)
                nonSwitchedRefList.append((oFileRef, sMsg))
                print sMsg
                continue

    if nonSwitchedRefList:

        w = len(max((r.refNode.name() for r, _ in nonSwitchedRefList), key=len))
        def f(r, m):
            return "{0:<{2}}: {1}".format(r.refNode.name(), m, w)

        numFails = len(nonSwitchedRefList)
        sSep = "\n- "
        sMsgHeader = " Failed to switch {}/{} references: ".format(numFails, numRefs)
        sMsgBody = sSep.join(f(r, m) for r, m in nonSwitchedRefList)
        sMsgEnd = "".center(100, "-")

        sMsg = '\n' + sMsgHeader.center(100, "-") + sSep + sMsgBody + '\n' + sMsgEnd
        print sMsg
        pm.displayWarning(sMsgHeader + "More details in Script Editor --" + (100 * ">"))

        #pm.mel.ScriptEditor()
    else:
        pm.displayInfo("Successfully switched {} references as '{}'"
                          .format(numRefs, sChosenRcName))
