
import sys
import os

import pymel.core as pm

from pytd.util.fsutils import pathResolve, pathSplitDirs, pathJoin

from davos.core.damproject import DamProject
from davos.core.damtypes import *

from pytaya.core import system as myasys

import dminutes.jipeLib_Z2K as jpZ
import dminutes.infoSetExp as infoE
from pytd.gui.itemviews.utils import toDisplayText
from itertools import groupby


def iterSeqDirPaths(shotLib, sSeqList):

    proj = shotLib.project

    for sSeqName in sSeqList:
        sAbsPath = proj.getPath("public", "shot_lib", "sequence_dir", dict(sequence=sSeqName))
        sDbPath = shotLib.absToDbPath(sAbsPath)
        #print sDbPath
        yield sDbPath

def launch(sSeqList=None, dryRun=True):

    sProject = os.environ.get("DAVOS_INIT_PROJECT")
    proj = DamProject(sProject)
    print ""
    print (" Project: '{}' ".format(sProject)).center(80, "-")


    if sSeqList is None:
        sSeqList = ()

    sComment = "fixed rotation values"

    shotLib = proj.getLibrary("public", "shot_lib")
    sSeqDirPaths = tuple(iterSeqDirPaths(shotLib, sSeqList))

    depth = len(pathSplitDirs(sSeqDirPaths[0]))

    sAlreadyFixedShots = set()
    dbNodeList = proj.findDbNodes("comment:/{}/".format(sComment.replace(" ", "\s")))
    dbNodeList.sort(key=lambda n: n.file)
    for dbNode in dbNodeList:

        sDbPath = dbNode.file
        if sSeqDirPaths:
            sSeqDir = pathJoin(*pathSplitDirs(sDbPath)[:depth])
            #print sSeqDir
            if sSeqDir not in sSeqDirPaths:
                continue

        drcFile = shotLib.entryFromDbPath(sDbPath, dbNode=False)
        if not drcFile.isVersionFile():
            continue

        drcFile = drcFile.getHeadFile(dbNode=False)

        damShot = drcFile.getEntity(fail=True)
        c = len(sAlreadyFixedShots)
        sAlreadyFixedShots.add(damShot.name)

        if (damShot.sequence in sSeqList) and len(sAlreadyFixedShots) > c:
            print "already fixed infoSet on '{}'".format(damShot.name)

    shotFilters = None
    bOmitted = False
    if sSeqList:
        shotFilters = [["sg_sequence.Sequence.code", "in", sSeqList]]
        bOmitted = True
    versFields = ["sg_source_file"]
    versFilters = [["sg_task.Task.step.Step.code", "in", ["previz 3d"]],
                   ]

    sgShotList = proj.listAllSgShots(includeOmitted=bOmitted, moreFilters=shotFilters)
    keyFnc = lambda d:d["sg_sequence"]["name"]
    sgShotList.sort(key=keyFnc)
    sgShotGrps = groupby(sgShotList, key=keyFnc)

    for sSeqCode, sgShotIter in sgShotGrps:

        print 3 * "\n", sSeqCode.center(100, "-")

        privFileList = []

        for sgShot in sgShotIter:

            sShotCode = sgShot["code"]

            if sShotCode in sAlreadyFixedShots:
                #print "already fixed infoSet on '{}'".format(sShotCode)
                continue

            sgVersList = proj.findSgVersions(sgShot, moreFilters=versFilters,
                                              moreFields=versFields, limit=1)

            for sgVers in sgVersList:

                sSgSrcPath = sgVers["sg_source_file"]
                if not sSgSrcPath:
                    print "no source file on '{}'".format(sgVers["code"])
                    continue

                versFile = shotLib.getEntry(pathResolve(sSgSrcPath), dbNode=True)

                pubFile = versFile#.getHeadFile(dbNode=False)

#                if not pubFile.isUpToDate():
#                    print pubFile, "out of sync"
#                    continue
#
#                if pubFile.getLockOwner(refresh=False):
#                    print pubFile, "locked"
#                    continue

                print "not process yet: '{}'".format(sShotCode)
                print "    ", pubFile.relPath(), toDisplayText(pubFile.dbMtime), "\n"
                if not dryRun:
                    privFile, _ = pubFile.copyToPrivateSpace(existing="keep")
                    privFileList.append(privFile)

        for privFile in privFileList:

            print 100 * "-"

            print "scene:", privFile.absPath()
            myasys.openScene(privFile.absPath(), force=True, fail=False, lrd="none")

            if not dryRun:
                for oFileRef in pm.listReferences(unloaded=True):
                    if oFileRef.namespace.startswith("set_"):
                        print repr(oFileRef)
                        oFileRef.load()

                pm.refresh()

            if not dryRun:
                infoSetExpI = infoE.infoSetExp()
                infoSetExpI.export(sceneName=jpZ.getShotName(), comment=sComment)

            print 100 * "-"

        print sSeqCode.center(100, "-")

if __name__ == "__main__":
    launch()

#python("import fix_infosets;reload(fix_infosets);fix_infosets.launch(['sq0160'],False)")
