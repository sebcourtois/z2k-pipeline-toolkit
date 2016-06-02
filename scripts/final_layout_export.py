
import sys
import os
#import os.path as osp
from tempfile import NamedTemporaryFile
from itertools import izip
import json

from zomblib import damutils
from zomblib.mayabatch import MayaBatch
from pytd.gui.dialogs import confirmDialog

def launch(dryRun=True, dialogParent=None):

    proj = damutils.initProject()

    bOk, sgShots = damutils.shotsFromShotgun(project=proj, dialogParent=dialogParent)
    if not bOk:
        sys.exit()

    damShotList = list(proj.getShot(d["code"]) for d in sgShots)
    export(damShotList, dryRun=dryRun)

def export(damShotList, dryRun=False):

    proj = damShotList[0].project
    myabatch = MayaBatch()

    sErrorList = []
    animScnList = []
    animShotList = damShotList[:]
    for i, damShot in enumerate(damShotList):
        animScene = None
        try:
            animScene = damShot.getRcFile("public", "anim_scene",
                                          fail=True, dbNode=False)
        except Exception as e:
            sErrorList.append("{} - {}".format(damShot, e.message))

        if animScene:
            animScnList.append(animScene)
        else:
            animShotList[i] = None

    animShotList = list(o for o in animShotList if o)

    if len(animShotList) != len(animScnList):
        raise RuntimeError("number of shots and anim scenes must be the same.")

    loadDbNodes(proj, animScnList)

    for i, scnFile in enumerate(animScnList):
        latestFile = None
        try:
            latestFile = _assertedLatestVersion(scnFile, refresh=False)
        except Exception as e:
            sErrorList.append(e.message)

        animScnList[i] = latestFile
        if not latestFile:
            animShotList[i] = None

    animScnList = list(o for o in animScnList if o)
    animShotList = list(o for o in animShotList if o)
    if len(animShotList) != len(animScnList):
        raise RuntimeError("number of shots and anim scenes NOT the same.")

    layoutScnList = []
    for i, animShot in enumerate(animShotList):
        layInfoFile = animShot.getRcFile("public", "layoutInfo_file",
                                        weak=True, dbNode=False)
        if not layInfoFile.exists():
            try:
                layoutScene = animShot.getRcFile("public", "layout_scene",
                                                fail=True, dbNode=False)
            except Exception as e:
                sErrorList.append("{} - {}".format(animShot, e.message))
                continue

            print ("{} - layout infos file not found and will be exported first."
                   .format(animShot))
            layoutScnList.append(layoutScene)

    loadDbNodes(proj, layoutScnList)

    for i, scnFile in enumerate(layoutScnList):
        latestFile = None
        try:
            latestFile = _assertedLatestVersion(scnFile, refresh=False)
        except Exception as e:
            sErrorList.append(e.message)

        layoutScnList[i] = latestFile

    if sErrorList:
        sSep = "\nWARNING: "
        sErrMsg = sSep + sSep.join(sErrorList)
        print sErrMsg

        res = confirmDialog(title="DO YOU WANT TO...",
                            message="Continue despite these warnings ?",
                            button=["Yes", "No"],
                            defaultButton="No",
                            cancelButton="No",
                            dismissString="No",
                            icon="question")
        if res == "No":
            raise RuntimeWarning("Canceled !")

    sCode = "from zomblib import damutils;reload(damutils);damutils.initProject()"
    jobList = [{"title":"Batch initialization", "py_code":sCode, "fail":True}]

    sFunc = "exportLayoutInfo(publish=True,dryRun={})".format(dryRun)
    jobList.extend(generMayaJobs(layoutScnList, sFunc))

    sFunc = "exportCaches(selected=False,dryRun={})".format(dryRun)
    jobList.extend(generMayaJobs(animScnList, sFunc))

    with NamedTemporaryFile(suffix=".json", delete=False, prefix="mayajobs_") as fp:
        json.dump(jobList, fp, indent=2, encoding='utf-8')

    myabatch.launch(fp.name)

def _assertedLatestVersion(scnFile, refresh=False):

    if not scnFile.currentVersion:
        print ("{} - no version yet.".format(scnFile.name))
        return None

    sLockOwner = scnFile.getLockOwner(refresh=refresh)
    if sLockOwner:
        raise AssertionError("{} - locked by '{}'."
                             .format(scnFile.name, sLockOwner))

    versFile = scnFile.assertLatestFile(refresh=refresh, returnVersion=True)

    return versFile

def generMayaJobs(scnFileList, sFunc):

    sBaseCode = """
import maya.cmds as mc
from pytaya.core import system as myasys
from dminutes import geocaching
reload(myasys)
reload(geocaching)

myasys.openScene('{scene}', force=True, fail=False)
mc.refresh()
geocaching.{func}
"""
    for scnFile in scnFileList:
        sPath = scnFile.absPath()
        sTitle = "{} on '{}'".format(sFunc, scnFile.name)
        sCode = sBaseCode.format(scene=sPath, func=sFunc)
        _ = compile(sCode, '<string>', 'exec')
        job = {"title":sTitle, "py_code":sCode}
        yield job

def loadDbNodes(proj, drcFileList):
    dbNodeList = proj.dbNodesForResources(drcFileList)
    for scnFile, dbNode in izip(drcFileList, dbNodeList):
        if not dbNode:
            scnFile.getDbNode(fromCache=False)

if __name__ == "__main__":

    try:
        launch()
    except:
        os.environ["PYTHONINSPECT"] = "1"
        raise
