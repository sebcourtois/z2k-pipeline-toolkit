
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
from collections import OrderedDict

LAUNCH_TIME = None

def launch(shots=None, dryRun=False, noPublish=False, timestamp=None, dialogParent=None):

    global LAUNCH_TIME

    proj = damutils.initProject()

    sgShots = None
    bPrompt = True
    bWriteCmd = False
    bOk = True
    if not shots:
        bOk, sgShots = damutils.shotsFromShotgun(project=proj, dialogParent=dialogParent)
        sShotList = tuple(d["code"] for d in sgShots)
        bWriteCmd = True
        bPrompt = False
    else:
        sShotList = shots

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

            if noPublish and ("--no-publish" not in cmdArgs):
                cmdArgs.append("--no-publish")

            if "--time" not in cmdArgs:
                cmdArgs += ["--time", str(int(LAUNCH_TIME))]

            if sShotList and ("--shots" not in cmdArgs):
                cmdArgs += ["--shots"]
                print sShotList
                cmdArgs.extend(sShotList)

            sCmd = subprocess.list2cmdline(cmdArgs)
            print sCmd

            sBatFilePath = makeOutputPath("re_build.bat", timestamp=LAUNCH_TIME)
            with open(sBatFilePath, "w") as f:
                f.writelines(("REM {}\n".format(s) for s in sShotList))
                f.write(sCmd)

    sTitle = "RENDER SCENE BUILDER"
    print "\n", sTitle.center(len(sTitle) + 2).center(120, "-")
    kwargs = dict(dryRun=dryRun, prompt=bPrompt, noPublish=noPublish)
    if inDevMode():
        pprint(kwargs)
    print ""

    damShotList = list(proj.getShot(s) for s in sShotList)
    build(damShotList, sgShots=sgShots, **kwargs)

def build(in_damShotList, dryRun=False, prompt=True, sgShots=None, noPublish=False,
          sSrcRcName="finalLayout_scene", sDstRcName="rendering_scene"):

    damShotList = in_damShotList[:]
    proj = damShotList[0].project

    mayaBatch = MayaBatch()
    sgShotDct = {} if (sgShots is None) else dict((d["code"], d) for d in sgShots)

    errorDct = OrderedDict()
    pubScnDct = {}
    for damShot in damShotList:
        sErrorList = []
        for sRcName in (sSrcRcName, sDstRcName):
            pubScn = None
            try:
                pubScn = damShot.getRcFile("public", sRcName, fail=True, dbNode=False)
            except Exception as e:
                sErrorList.append("{}".format(toStr(e)))
            else:
                if not pubScn:
                    sMsg = "Could not get public {}".format(sRcName.replace("_", " "))
                    sErrorList.append("{}".format(sMsg))

            pubScnDct.setdefault(sRcName, []).append(pubScn)

        errorDct[damShot.name] = sErrorList

    srcScnList = pubScnDct[sSrcRcName]
    dstScnList = pubScnDct[sDstRcName]

    loadDbNodes(proj, tuple(scn for scn in  (srcScnList + dstScnList) if scn))

    for i, (damShot, dstScn) in enumerate(izip(damShotList, dstScnList)):

        if not dstScn:
            continue

        iDstVers = dstScn.currentVersion
        sCmnt = dstScn.comment.strip()
        if iDstVers and (not sCmnt.lower().startswith("built from ")):
            dstScnList[i] = None
            sMsg = ("'{}' already edited by '{}' (v{:03d}: '{}')."
                    .format(dstScn.name, dstScn.author, iDstVers, sCmnt))
            errorDct.setdefault(damShot.name, []).append(sMsg)
            continue

        sLockOwner = dstScn.getLockOwner(refresh=False)
        if sLockOwner:
            dstScnList[i] = None
            sMsg = ("'{}' is locked by '{}'.".format(dstScn.name, sLockOwner))
            errorDct.setdefault(damShot.name, []).append(sMsg)
            continue


    for i, (damShot, srcScn, dstScn) in enumerate(izip(damShotList, srcScnList, dstScnList)):
        latestVers = None
        if srcScn:# and dstScn:
            try:
                latestVers = _assertedLatestVersion(srcScn, refresh=False)
            except Exception as e:
                errorDct.setdefault(damShot.name, []).append(toStr(e))
            else:
                if not latestVers:
                    sMsg = "could not get latest version."
                    errorDct.setdefault(damShot.name, []).append("{} - {}".format(srcScn.name, sMsg))
        #print srcScn, latestVers
        srcScnList[i] = latestVers


    if sgShotDct:
        sNoSgShotList = tuple(sh.name for sh in damShotList if sh.name not in sgShotDct)
    else:
        sNoSgShotList = tuple(sh.name for sh in damShotList)

    if sNoSgShotList:
        sgShotList = proj.listAllSgShots(moreFilters=[["code", "in", sNoSgShotList]],
                                         includeOmitted=inDevMode())
        sgShotDct.update((d["code"], d) for d in sgShotList)

    #print sNoSgShotList, sgShotDct

    if len(damShotList) != len(srcScnList):
        raise RuntimeError("number of shots and '{}' scenes NOT the same."
                           .format(sSrcRcName.replace("_scene", "")))


    sStep = ""
    sTask = "final layout"

    filters = [["content", "is", sTask],
               ["entity.Shot.code", "in", sgShotDct.keys()]]
    fields = ["entity.Shot.code", "sg_status_list"]
    sgTaskList = proj._shotgundb.sg.find("Task", filters, fields)
    sgTaskDct = dict((d["entity.Shot.code"], d) for d in sgTaskList)

    for i, (damShot, dstScn) in enumerate(izip(damShotList, dstScnList)):

        if not dstScn:
            continue

        sShotName = damShot.name
        #sgShot = sgShotDct[sShotName]
        sgTask = sgTaskDct[sShotName]#damShot.getSgTask(sTask, sStep, sgEntity=sgShot, fail=True)

        if sgTask["sg_status_list"] != "fin":

            dstScnList[i] = None
            sMsg = ("Status of '{}' task NOT FINAL."
                    .format("|".join(s for s in (sStep, sTask) if s)))
            errorDct.setdefault(damShot.name, []).append(sMsg)

        elif noPublish:
            dstScnList[i] = None


    bPublish = (not noPublish)

    for i, (damShot, srcScn, dstScn) in enumerate(izip(damShotList, srcScnList, dstScnList)):

        sShotName = damShot.name

        if (bPublish and not (srcScn and dstScn)) or (not srcScn):
            damShot = srcScn = dstScn = None
            damShotList[i] = None
            srcScnList[i] = None
            dstScnList[i] = None

        sMsgList = []
        if srcScn:
            sMsg = "ok to build "
            if dstScn:
                sMsg += "and publish"
            sMsgList.append(sMsg)

        sErrorList = errorDct.get(sShotName, [])
        if sErrorList:
            prompt = True
            sMsgList.extend("ERROR: " + s for s in sErrorList)

        sSep = "\n" + (len(sShotName) * " ") + " - "
        print "{} - {}".format(sShotName, sSep.join(sMsgList))
        #print damShot, srcScn, dstScn

    dstScnList = list(dst for shot, src, dst in izip(damShotList, srcScnList, dstScnList) if shot and src)
    damShotList = list(shot for shot in damShotList if shot)
    srcScnList = list(src for src in srcScnList if src)

    if len(damShotList) != len(srcScnList):
        print len(damShotList), len(srcScnList), len(dstScnList)
        raise RuntimeError("number of valid shots and '{}' scenes NOT the same."
                           .format(sSrcRcName.replace("_scene", "")))

    numValidShots = len(damShotList)
    numInputShots = len(in_damShotList)

    if not damShotList:
        sMsg = "None of the {} selected shots can be built.".format(numInputShots)
        confirmMessage("SORRY !", sMsg, ["OK"])

    prompt = True
    if numValidShots != numInputShots:
        sMsg = ("Only {}/{} shots will be built.\n\nContinue to build anyway ?\n\n"
                .format(numValidShots, numInputShots))
        prompt = True
    else:
        sMsg = "Build these {} shots ?\n\n".format(numValidShots)

    for grp in grouper(6, (o.name for o in damShotList)):
        sMsg += ("\n" + " ".join(s for s in grp if s is not None))

    if prompt:
        res = confirmMessage("DO YOU WANT TO...", sMsg, ["Yes", "No", "Refresh"])
        if res == "No":
            sys.exit(0)
            #raise RuntimeWarning("Canceled !")
        elif res == "Refresh":
            return build(in_damShotList, dryRun=dryRun, prompt=prompt, sgShots=sgShots, noPublish=noPublish)

    sCode = """
from zomblib import damutils;reload(damutils);damutils.initProject()
"""
    jobList = [{"title":"Batch initialization", "py_lines":[sCode], "fail":True}]

    jobArgsList = tuple(dict(shot=shot.name, src_scene=src.absPath(),
                             publish=True if dst else False, dryRun=dryRun)
                        for shot, src, dst in izip(damShotList, srcScnList, dstScnList))
    jobList.extend(generMayaJobs(jobArgsList))

    sJobFilePath = makeOutputPath("mayabatch.json", timestamp=LAUNCH_TIME)
    jsonWrite(sJobFilePath, jobList)

    sLogFilePath = makeOutputPath("mayabatch.log", timestamp=LAUNCH_TIME)

    return mayaBatch.launch(sJobFilePath, logTo=sLogFilePath)

def _assertedLatestVersion(scnFile, refresh=False):

    if not scnFile.currentVersion:
        raise AssertionError("'{}' has no version yet.".format(scnFile.name))
        #return None

    sLockOwner = scnFile.getLockOwner(refresh=refresh)
    if sLockOwner:
        raise AssertionError("'{}' is locked by '{}'.".format(scnFile.name, sLockOwner))

    versFile = scnFile.assertLatestFile(refresh=refresh, returnVersion=True)

    return versFile

def generMayaJobs(jobArgsList):

    sCodeFmt = """
from dminutes import batchprocess
reload(batchprocess)

#print "{shot}", "{src_scene}", {publish}, {dryRun}
batchprocess.buildRenderScene("{src_scene}", publish={publish}, dryRun={dryRun})
"""
    for kwargs in (d.copy() for d in jobArgsList):

        sSrcScnPath = kwargs.get("src_scene")

        sFunc = "batchprocess.buildRenderScene()"
        sTitle = "{} on '{}'".format(sFunc, osp.basename(sSrcScnPath))

        sCode = sCodeFmt.format(**kwargs)
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
    parser.add_argument("--no-publish", action="store_true")
    parser.add_argument("--time", type=int, default=None)
    parser.add_argument("--shots", nargs="*", default=None)

    ns = parser.parse_args()

#    if inDevMode():
#        ns.no_publish = True

    try:
        launch(shots=ns.shots, dryRun=ns.dry, timestamp=ns.time, noPublish=ns.no_publish)
    except Exception as e:
        os.environ["PYTHONINSPECT"] = "1"
        if isinstance(e, Warning):
            print e.message
        else:
            raise
