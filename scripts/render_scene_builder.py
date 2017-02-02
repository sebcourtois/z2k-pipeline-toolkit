
import sys
import os
import os.path as osp
from itertools import izip
import shutil
import time
from datetime import datetime
import argparse
import subprocess
from pprint import pprint

from pytd.util.sysutils import grouper, inDevMode, toStr
from pytd.util.logutils import confirmMessage
from pytd.util.fsutils import pathJoin, pathSuffixed, jsonWrite

from zomblib import damutils
from zomblib.mayabatch import MayaBatch
#from zomblib.damutils import playbackTimesFromShot
from davos.core.utils import mkVersionSuffix

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

def build(in_damShotList, dryRun=False, prompt=True, sgShots=None,
          sSrcRcName="finalLayout_scene", sDstRcName="rendering_scene"):

    damShotList = in_damShotList[:]
    proj = damShotList[0].project

    mayaBatch = MayaBatch()
    sgShotDct = {} if (sgShots is None) else dict((d["code"], d) for d in sgShots)

    sErrorList = []
    pubScnDct = {}
    for damShot in damShotList:
        for sRcName in (sSrcRcName, sDstRcName):
            pubScn = None
            try:
                pubScn = damShot.getRcFile("public", sRcName,
                                            fail=True, dbNode=False)
            except Exception as e:
                sErrorList.append("{} - {}".format(damShot, toStr(e)))
            else:
                if not pubScn:
                    sMsg = "Could not get public {}".format(sRcName.replace("_", " "))
                    sErrorList.append("{} - {}".format(damShot, sMsg))

            pubScnDct.setdefault(sRcName, []).append(pubScn)

    srcScnList = pubScnDct[sSrcRcName]
    dstScnList = pubScnDct[sDstRcName]

    loadDbNodes(proj, tuple(scn for scn in  (srcScnList + dstScnList) if scn))

    for i, dstScn in enumerate(dstScnList):
        if not dstScn:
            continue

        iDstVers = dstScn.currentVersion
        if iDstVers:
            dstScnList[i] = None
            sMsg = " {} already started (v{})".format(sRcName.replace("_", " "), iDstVers)
            sErrorList.append("{} - {}".format(dstScn.name, sMsg))
            continue

        sLockOwner = dstScn.getLockOwner(refresh=False)
        if sLockOwner:
            dstScnList[i] = None
            sErrorList.append("{} - locked by '{}'.".format(dstScn.name, sLockOwner))
            continue

    for i, (srcScn, dstScn) in enumerate(izip(srcScnList, dstScnList)):
        latestVers = None
        if srcScn and dstScn:
            try:
                latestVers = _assertedLatestVersion(srcScn, refresh=False)
            except Exception as e:
                sErrorList.append(toStr(e))
            else:
                if not latestVers:
                    sMsg = "could not get latest version."
                    sErrorList.append("{} - {}".format(srcScn.name, sMsg))
        #print srcScn, latestVers
        if not latestVers:
            srcScnList[i] = None
        else:
            sVersSuffix = mkVersionSuffix(latestVers.versionFromName())
            sSuffix = "".join((sVersSuffix, '-', "built4Render"))
            privScn, _ = srcScn.copyToPrivateSpace(suffix=sSuffix, existing="",
                                                   sourceFile=latestVers)
            srcScnList[i] = privScn


    if sgShotDct:
        sNoSgShotList = tuple(sh.name for sh in damShotList if sh.name not in sgShotDct)
    else:
        sNoSgShotList = tuple(sh.name for sh in damShotList)

    if sNoSgShotList:
        sgShotList = proj.listAllSgShots(moreFilters=[["code", "in", sNoSgShotList]],
                                         includeOmitted=inDevMode())
        sgShotDct.update((d["code"], d) for d in sgShotList)

    #print sNoSgShotList, sgShotDct

    sTask = "final layout"
    step = ""

    for i, (damShot, srcScn, dstScn) in enumerate(izip(damShotList, srcScnList, dstScnList)):

        if srcScn and dstScn:
            sgShot = sgShotDct[damShot.name]
            sgTask = damShot.getSgTask(sTask, step, sgEntity=sgShot, fail=True)
            if sgTask["sg_status_list"] != "fin":
                sMsg = ("Status of the {} task is not final yet."
                        .format("|".join(s for s in (step, sTask) if s)))
                sErrorList.append("{} - {}".format(damShot, sMsg))
            else:
                continue

        damShotList[i] = None
        srcScnList[i] = None
        dstScnList[i] = None

    damShotList = list(o for o in damShotList if o)
    srcScnList = list(o for o in srcScnList if o)
    dstScnList = list(o for o in dstScnList if o)

#    if len(validShotList) != len(srcScnList):
#        raise RuntimeError("number of shots and '{}' scenes NOT the same."
#                           .format(sSrcRcName.replace("_scene", "")))

    numValidShots = len(damShotList)

    if sErrorList:
        sSep = "\nWARNING: "
        sErrMsg = sSep + sSep.join(sErrorList)
        print sErrMsg, '\n'
        prompt = True

    numInputShots = len(in_damShotList)
    if not damShotList:
        sMsg = "None of the {} selected shots can be built.".format(numInputShots)
        confirmMessage("SORRY !", sMsg, ["OK"])
        return

    if numValidShots != numInputShots:
        sMsg = ("Only {}/{} shots will be built.\n\nContinue to build anyway ?\n\n"
                .format(numValidShots, numInputShots))
        prompt = True
    else:
        sMsg = "Build these {} shots ?\n\n".format(numValidShots)

    for grp in grouper(6, (o.name for o in damShotList)):
        sMsg += ("\n" + " ".join(s for s in grp if s is not None))

    if prompt:
        res = confirmMessage("DO YOU WANT TO...", sMsg, ["Yes", "No"])
        if res == "No":
            raise RuntimeWarning("Canceled !")

    sCode = """
from zomblib import damutils;reload(damutils);damutils.initProject()
"""
    jobList = [{"title":"Batch initialization", "py_lines":[sCode], "fail":True}]

    jobArgsList = tuple(dict(src_scene=src.absPath(), dst_scene=dst.absPath(), dryRun=dryRun, lrd="none")
                        for src, dst in izip(srcScnList, dstScnList))
    jobList.extend(generMayaJobs(jobArgsList))

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
        raise AssertionError("{} - locked by '{}'.".format(scnFile.name, sLockOwner))

    versFile = scnFile.assertLatestFile(refresh=refresh, returnVersion=True)

    return versFile

def generMayaJobs(jobArgsList):

    sCodeFmt = """
import maya.cmds as mc
from pytaya.core import system as myasys

myasys.openScene('{src_scene}', force=True, fail=False, {lrd})
mc.refresh()
print "{dst_scene}"
"""
    for kwargs in (d.copy() for d in jobArgsList):

        sAbsPath = kwargs.get("src_scene")
        sLrd = kwargs.pop("lrd", "")
        if sLrd:
            sLrd = "lrd='{}'".format(sLrd)

        sFunc = ""
        sTitle = "{} on '{}'".format(sFunc, osp.basename(sAbsPath))
        sCode = sCodeFmt.format(lrd=sLrd, **kwargs)
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
