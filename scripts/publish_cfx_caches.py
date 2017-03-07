

import sys
import os
import os.path as osp
from itertools import izip
import shutil
import time
from datetime import datetime
#import argparse
#import subprocess
#from pprint import pprint
from itertools import groupby

from tabulate import tabulate

from pytd.util.systypes import MemSize
#from pytd.gui.itemviews.utils import toDisplayText

#from pytd.util.sysutils import grouper, inDevMode, toStr
from pytd.util.logutils import confirmMessage, logMsg
from pytd.util.fsutils import pathJoin, pathSuffixed, jsonWrite

from zomblib import damutils
from zomblib.mayabatch import MayaBatch
#from zomblib.damutils import playbackTimesFromShot
#from collections import OrderedDict

LAUNCH_TIME = None

def launch():

    global LAUNCH_TIME

    proj = damutils.initProject()
    mayaBatch = MayaBatch()

    sCurUser = proj.loggedUser().loginName

#    damShotList = []
    srcScnList = []

#    sTask = "charfx"
#
#    sSeqList = [#"sq6660",
#                #"sq0690",
#                #"sq0645",
#                #"sq0360",
#                "sq0260",
#                #"sq0580",
#                #"sq0480",
#                ]
#
#    filters = [["content", "is", sTask],
#               ["entity.Shot.sg_sequence.Sequence.code", "in", sSeqList ],
#               ["entity.Shot.sg_sequence.Sequence.sg_status_list", "is_not", "omt" ],
#               ["sg_status_list", "is", "fin"],
#               #["entity.Shot.sg_sequence.Sequence.sg_status_list", "is", "omt"],
#               ["entity.Shot.sg_status_list", "is_not", "omt"]]
#
#    fields = ["content", "sg_status_list",
#              "entity.Shot.code",
#              "entity.Shot.sg_status_list",
#              #"entity.Shot.sg_sequence.Sequence.sg_status_list",
#              ]
#
#    sgTaskList = proj._shotgundb.sg.find("Task", filters, fields)
#
#
#    sSrcRcName = "charFx_scene"
#
#    for sgTask in sgTaskList:
#
#        sShotName = sgTask["entity.Shot.code"]
#        damShot = proj.getShot(sShotName)
#
#        srcScn = damShot.getResource("public", sSrcRcName, dbNode=False)
#        if not srcScn:
#            continue
#
#        srcScnList.append(srcScn)
#        damShotList.append(damShot)
#
#    loadDbNodes(proj, srcScnList)

    query = {
    "file":r"REGEX_/zomb/shot/.+/sq\d{4}_sh\d{4}[a-z]_(charFx|charFx-v\d{3})\.ma",
    "origin":"dmn_paris",
    "comment":{"$exists":True, "$ne":"BATCH: published caches"}
    }
    foundNodeList = proj._db.findNodes(query)

    library = proj.getLibrary("public", "shot_lib")

    headNodeList = sorted((n for n in foundNodeList if ("#parent" not in n._data)), key=lambda n:n.id_)
    sHeadIdList = tuple(n.id_ for n in headNodeList)
    # for each head file, its latest version needs to be updated too
    sortKey = lambda n: n._data["#parent"] + "_" + n.name
    dbVersIter = (n for n in foundNodeList if ("#parent" in n._data) and (n._data["#parent"] in sHeadIdList))
    dbVersList = sorted(dbVersIter, key=sortKey, reverse=True)
    grpIter = groupby(dbVersList, key=lambda n: n._data["#parent"])

    versNodeList = list(next(g) for _, g in grpIter)
    versNodeList.sort(key=lambda n:n._data["#parent"])

    if len(headNodeList) != len(versNodeList):
        raise AssertionError("number of head and version nodes does not match.")

    sErrorList = []

    bothNodeList = sorted(izip(headNodeList, versNodeList), key=lambda b:b[1].time)

    for i, (headNode, versNode) in enumerate(bothNodeList):

#        if i > 9:
#            break

        if versNode.getField("#parent") != headNode.id_:
            sErrorList.append("head and version nodes do not match:\n    {}\n    {}"
                              .format(headNode.file, versNode.file))
            continue

        headFile = proj.entryFromDbNode(headNode, library)
        if not headFile:
            sErrorList.append("No head file found for {}".format(headNode.file))
            continue

        versFile = proj.entryFromDbNode(versNode, library)
        if not versFile:
            sErrorList.append("No version file found for {}".format(versNode.file))
            continue

        sLockOwner = headFile.getLockOwner(refresh=False)
        if sLockOwner and sLockOwner != sCurUser:
            sErrorList.append("'{}' is locked by '{}'.".format(headFile.name, sLockOwner))

        srcScnList.append(versFile)

    table = []
    totalSize = 0
    for srcScn in srcScnList:
        n = srcScn._dbnode
        #print n.dataRepr("file", "time", "sync_disabled", "source_size")
        sSize = ""
        if n.source_size:
            totalSize += n.source_size
            sSize = "{:.2cM}".format(MemSize(n.source_size))

        sTime = datetime.fromtimestamp(n.time / 1000).strftime("%Y-%m-%d %H:%M:%S")
        table.append((osp.basename(n.file), sSize, sTime, n.author, n.comment))
        #print n.dataRepr()
    headers = ["file", "size", "time", "author", "comment"]
    print tabulate(table, headers, tablefmt="simple")
    print "{} resources - {:.2cM}".format(len(versNodeList), (MemSize(totalSize)))

    if sErrorList:
        sSep = "\n" + "ERROR: "
        print sSep + sSep.join(sErrorList)

    sCode = """
from zomblib import damutils;reload(damutils);damutils.initProject()
"""
    jobList = [{"title":"Batch initialization", "py_lines":[sCode], "fail":True}]

    jobArgsList = tuple(dict(src_scene=src.absPath(), publish=True, dryRun=False)
                        for src in srcScnList)
    jobList.extend(generMayaJobs(jobArgsList))

    LAUNCH_TIME = LAUNCH_TIME if LAUNCH_TIME else time.time()

    sJobFilePath = makeOutputPath("mayabatch.json", timestamp=LAUNCH_TIME)
    jsonWrite(sJobFilePath, jobList)

    sLogFilePath = makeOutputPath("mayabatch.log", timestamp=LAUNCH_TIME)

    if len(jobList) > 1:
        print "\n".join(jobList[1]["py_lines"])

    res = confirmMessage("DO YOU WANT TO...", "proceed ?", ["Batch", "Quit"])
    if (res == "Quit"):
        sys.exit(0)

    return mayaBatch.launch(sJobFilePath, logTo=sLogFilePath)

def loadDbNodes(proj, drcFileList):
    dbNodeList = proj.dbNodesFromEntries(drcFileList)
    for scnFile, dbNode in izip(drcFileList, dbNodeList):
        if not dbNode:
            dbNode = scnFile.loadDbNode(fromCache=False)
            if dbNode:
                dbNodeList.append(dbNode)

    headIds = list(dbNode.id_ for dbNode in dbNodeList if not dbNode.hasField("#parent"))
    if headIds:
        #print len(headIds)
        for dbNode in proj._db.findNodes({"#parent":{"$in":headIds}}):
            rcLib = proj.libraryFromDbPath(dbNode.file)
            if rcLib:
                rcLib._addDbNodeToCache(dbNode)

def _assertedLatestVersion(scnFile, refresh=False):

    if not scnFile.currentVersion:
        raise AssertionError("'{}' has no version yet.".format(scnFile.name))
        #return None

#    sLockOwner = scnFile.getLockOwner(refresh=refresh)
#    if sLockOwner:
#        raise AssertionError("'{}' is locked by '{}'.".format(scnFile.name, sLockOwner))

    versFile = scnFile.assertLatestFile(refresh=refresh, returnVersion=True)

    return versFile

def generMayaJobs(jobArgsList):

    sCodeFmt = """
from dminutes import batchprocess;reload(batchprocess)
batchprocess.publishCfxCaches("{src_scene}", 
                              publish={publish}, 
                              dryRun={dryRun})
"""
    for kwargs in (d.copy() for d in jobArgsList):

        sSrcScnPath = kwargs.get("src_scene")

        sFunc = "batchprocess.publishCfxCaches()"
        sTitle = "{} on '{}'".format(sFunc, osp.basename(sSrcScnPath))

        sCode = sCodeFmt.format(**kwargs)
        _ = compile(sCode, '<string>', 'exec')

        job = {"title":sTitle, "py_lines":sCode.strip().split('\n')}
        yield job

def makeOutputPath(sFileName, timestamp=None, save=True):

    #for sFileName in ("maya_jobs.json", "maya_batch.bat", "maya_batch.log"):
    sOutDirPath = pathJoin(osp.dirname(os.environ["Z2K_TOOLKIT_PATH"]), "publish_cfx_caches")

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


if __name__ == "__main__":

    launch()

