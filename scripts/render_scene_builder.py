
import sys
import os
import os.path as osp
from itertools import izip
import shutil
import time
from datetime import datetime
import argparse
import subprocess

from pytd.util.sysutils import grouper, inDevMode, toStr
from pytd.util.logutils import confirmMessage
from pytd.util.fsutils import pathJoin, pathSuffixed, jsonWrite

from zomblib import damutils
from zomblib.mayabatch import MayaBatch
#from zomblib.damutils import playbackTimesFromShot
from davos.core.utils import mkVersionSuffix
from pprint import pprint

LAUNCH_TIME = None

def launch(shotNames=None, dryRun=False, timestamp=None, dialogParent=None):

    global LAUNCH_TIME

    proj = damutils.initProject()

    sgShots = None
    bPrompt = True
    bWriteCmd = False
    bOk = True
    if not shotNames:
        bOk, sgShots = damutils.shotsFromShotgun(project=proj, dialogParent=dialogParent)
        shotNames = tuple(d["code"] for d in sgShots)
        bWriteCmd = True
        bPrompt = False

    if not bOk:
        sys.exit()

    LAUNCH_TIME = timestamp if timestamp else time.time()

    if bWriteCmd:
        sCmd = os.environ.get("Z2K_LAUNCHER_CMD")
        cmdArgs = sCmd.split()
        print cmdArgs
        if cmdArgs:

            if dryRun and ("--dry" not in cmdArgs):
                cmdArgs.append("--dry")

            if "--time" not in cmdArgs:
                cmdArgs += ["--time", str(int(LAUNCH_TIME))]

            if shotNames and ("--shots" not in cmdArgs):
                cmdArgs += ["--shots"]
                print shotNames
                cmdArgs.extend(shotNames)

            sCmd = subprocess.list2cmdline(cmdArgs)
            print sCmd

            sBatFilePath = makeOutputPath("re_build.bat", timestamp=LAUNCH_TIME)
            with open(sBatFilePath, "w") as f:
                f.writelines(("REM {}\n".format(s) for s in shotNames))
                f.write(sCmd)

    sTitle = "RENDER SCENE BUILDER"
    print "\n", sTitle.center(len(sTitle) + 2).center(120, "#")

    damShotList = list(proj.getShot(s) for s in shotNames)
    build(damShotList, dryRun=dryRun, prompt=bPrompt, sgShots=sgShots)

def build(damShotList, dryRun=False, prompt=True, sgShots=None,
          sSrcRcName="finalLayout_scene", sDstRcName="rendering_scene"):

    proj = damShotList[0].project
    mayaBatch = MayaBatch()
    sgShotDct = {} if sgShots is None else dict((d["code"], d) for d in sgShots)

    sErrorList = []
    pubScnDct = {}
    validShotList = damShotList[:]
    for i, damShot in enumerate(damShotList):
        for sRcName in (sSrcRcName, sDstRcName):
            pubScn = None
            try:
                pubScn = damShot.getRcFile("public", sRcName,
                                            fail=True, dbNode=False)
            except Exception as e:
                sErrorList.append("{} - {}".format(damShot, toStr(e)))
            else:
                if not pubScn:
                    sErrorList.append("{} - {}".format(damShot, "Could not get public {}"
                                                       .format(sRcName.replace("_", " "))))

            pubScnDct.setdefault(sRcName, []).append(pubScn)

    #validShotList = list(o for o in validShotList if o)
    srcScnList = pubScnDct[sSrcRcName]
    dstScnList = pubScnDct[sDstRcName]

    loadDbNodes(proj, srcScnList + dstScnList)

    for i, pubScn in enumerate(srcScnList):
        latestFile = None
        if pubScn:
            try:
                latestFile = _assertedLatestVersion(pubScn, refresh=False)
            except Exception as e:
                sErrorList.append(toStr(e))
            else:
                if not latestFile:
                    sMsg = "Could not get latest version of '{}'".format(pubScn.name)
                    sErrorList.append("{} - {}".format(damShot, sMsg))

        #print pubScn, latestFile
        if not latestFile:
            validShotList[i] = None
            srcScnList[i] = None
        else:
            sVersSuffix = mkVersionSuffix(latestFile.versionFromName())
            sSuffix = "".join((sVersSuffix, '-', "toRenderScene"))
            privScn, _ = pubScn.copyToPrivateSpace(suffix=sSuffix, existing="replace",
                                                     sourceFile=latestFile)
            srcScnList[i] = privScn

    validShotList = list(o for o in validShotList if o)
    srcScnList = list(o for o in srcScnList if o)
    if len(validShotList) != len(srcScnList):
        raise RuntimeError("number of shots and '{}' scenes NOT the same."
                           .format(sSrcRcName.replace("_scene", "")))

    if sgShotDct:
        sNoSgShotList = tuple(sh.name for sh in validShotList if sh.name not in sgShotDct)
    else:
        sNoSgShotList = tuple(sh.name for sh in validShotList)

    if sNoSgShotList:
        sgShotList = proj.listAllSgShots(moreFilters=[["code", "in", sNoSgShotList]],
                                         includeOmitted=inDevMode())
        sgShotDct.update((d["code"], d) for d in sgShotList)

    #print sNoSgShotList, sgShotDct

    numValidShots = len(validShotList)

    if sErrorList:
        sSep = "\nWARNING: "
        sErrMsg = sSep + sSep.join(sErrorList)
        print sErrMsg, '\n'
        prompt = True

    numInShots = len(damShotList)
    if not validShotList:
        sMsg = "None of the {} selected shots can be built.".format(numInShots)
        confirmMessage("SORRY !", sMsg, ["OK"])
        return

    if numValidShots != numInShots:
        sMsg = ("Only {}/{} shots will be built.\n\nContinue to build anyway ?\n\n"
                .format(numValidShots, numInShots))
        prompt = True
    else:
        sMsg = "Build these {} shots ?\n\n".format(numValidShots)

    for grp in grouper(6, (o.name for o in validShotList)):
        sMsg += ("\n" + " ".join(s for s in grp if s is not None))

    if prompt:
        res = confirmMessage("DO YOU WANT TO...", sMsg, ["Yes", "No"])
        if res == "No":
            raise RuntimeWarning("Canceled !")

    sCode = """
from zomblib import damutils;reload(damutils);damutils.initProject()
"""
    jobList = [{"title":"Batch initialization", "py_lines":[sCode], "fail":True}]

#    sExportFunc = "exportCaches(selected=False, frameRange={frameRange}, dryRun={dryRun}, publish={publish})"
#    jobArgsList = tuple(dict(scene=src.absPath(), dryRun=dryRun, frameRange=frm, publish=pub)
#                        for src, frm, pub in izip(srcScnList, frameRangeList, publishArgList))
#    jobList.extend(generMayaJobs(sExportFunc, jobArgsList))

    sJobFilePath = makeOutputPath("mayabatch.json", timestamp=LAUNCH_TIME)
    jsonWrite(sJobFilePath, jobList)

    sLogFilePath = makeOutputPath("mayabatch.log", timestamp=LAUNCH_TIME)

    return mayaBatch.launch(sJobFilePath, logTo=sLogFilePath)

def _assertedLatestVersion(scnFile, refresh=False):

    if not scnFile.currentVersion:
        raise AssertionError("{} - no version yet.".format(scnFile.name))
        #return None

    sLockOwner = scnFile.getLockOwner(refresh=refresh)
    if sLockOwner:
        raise AssertionError("{} - locked by '{}'."
                             .format(scnFile.name, sLockOwner))

    versFile = scnFile.assertLatestFile(refresh=refresh, returnVersion=True)

    return versFile

def generMayaJobs(sExportFunc, jobArgsList):

    sCodeFmt = """
import maya.cmds as mc
from pytaya.core import system as myasys
from dminutes import geocaching

myasys.openScene('{scene}', force=True, fail=False, {lrd})
mc.refresh()
geocaching.{func}
"""
    for kwargs in (d.copy() for d in jobArgsList):

        sAbsPath = kwargs.pop("scene")
        sLrd = kwargs.pop("lrd", "")
        if sLrd:
            sLrd = "lrd='{}'".format(sLrd)

        sFunc = sExportFunc.format(**kwargs)
        sTitle = "{} on '{}'".format(sFunc, osp.basename(sAbsPath))
        sCode = sCodeFmt.format(func=sFunc, scene=sAbsPath, lrd=sLrd)
        _ = compile(sCode, '<string>', 'exec')

        job = {"title":sTitle, "py_lines":sCode.strip().split('\n')}
        yield job

def makeOutputPath(sFileName, timestamp=None, save=True):

    #for sFileName in ("maya_jobs.json", "maya_batch.bat", "maya_batch.log"):
    sOutDirPath = pathJoin(os.environ["USERPROFILE"], "zombillenium",
                           osp.splitext(osp.basename(__file__))[0])

    sFilePath = pathJoin(sOutDirPath, sFileName)
    if timestamp:
        sDate = datetime.fromtimestamp(timestamp).strftime("_%Y%m%d-%H%M%S")
        sFilePath = pathSuffixed(sFilePath, sDate)
        save = False

    if not osp.isdir(sOutDirPath):
        os.makedirs(sOutDirPath)
    elif save and osp.isfile(sFilePath):
        st = os.stat(sFilePath)
        if st.st_size:
            sTimestamp = datetime.fromtimestamp(st.st_mtime).strftime("_%Y%m%d-%H%M%S")
            shutil.copy2(sFilePath, pathSuffixed(sFilePath, sTimestamp))

    return sFilePath

def loadDbNodes(proj, drcFileList):
    dbNodeList = proj.dbNodesFromEntries(drcFileList)
    for scnFile, dbNode in izip(drcFileList, dbNodeList):
        if not dbNode:
            scnFile.loadDbNode(fromCache=False)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    #parser.add_argument("resource")
    parser.add_argument("--dry", action="store_true")
    parser.add_argument("--time", type=int, default=None)
    parser.add_argument("--shots", nargs="*", default=None)

    try:
        ns = parser.parse_args()
        launch(shotNames=ns.shots, dryRun=ns.dry, timestamp=ns.time)
    except Exception as e:
        os.environ["PYTHONINSPECT"] = "1"
        if isinstance(e, Warning):
            print e.message
        else:
            raise
