
import sys
import os
from itertools import groupby

import pymel.core as pm

from pytd.util.fsutils import pathResolve, pathSplitDirs, pathJoin

from davos.core.damproject import DamProject
from davos.core.damtypes import *

from pytaya.core import system as myasys

from pytd.gui.itemviews.utils import toDisplayText
from pytd.util.sysutils import inDevMode, toStr


def iterSeqDirPaths(shotLib, sSeqList):

    proj = shotLib.project

    for sSeqName in sSeqList:
        sAbsPath = proj.getPath("public", "shot_lib", "sequence_dir", dict(sequence=sSeqName))
        sDbPath = shotLib.absToDbPath(sAbsPath)
        #print sDbPath
        yield sDbPath

def launch(sSeqList, dryRun=True):

    sProject = os.environ.get("DAVOS_INIT_PROJECT")
    proj = DamProject(sProject)
    print ""
    print (" Project: '{}' ".format(sProject)).center(80, "-")


    shotLib = proj.getLibrary("public", "shot_lib")
    sSeqDirPaths = tuple(iterSeqDirPaths(shotLib, sSeqList))

    depth = len(pathSplitDirs(sSeqDirPaths[0]))

    damShotDct = {}
    sAnimStartedShots = set()
    dbNodeList = proj.findDbNodes("file:/sq\d{4}_sh\d{4}._anim\.ma$/i")
    dbNodeList.sort(key=lambda n: n.file)
    for dbNode in dbNodeList:

        sDbPath = dbNode.file
        if sSeqDirPaths:
            sSeqDir = pathJoin(*pathSplitDirs(sDbPath)[:depth])
            #print sSeqDir
            if sSeqDir not in sSeqDirPaths:
                continue

        damShot = proj.entityFromPath(shotLib.dbToAbsPath(sDbPath), library=shotLib)
        if dbNode.version:
            print "anim already started on '{}'".format(damShot.name)
            sAnimStartedShots.add(damShot.name)
        else:
            damShotDct[damShot.name] = damShot

    bOmitted = False#inDevMode()
    shotFilters = [["sg_sequence.Sequence.code", "in", sSeqList]]

    sgShotList = proj.listAllSgShots(includeOmitted=bOmitted, moreFilters=shotFilters)

    keyFnc = lambda d:d["sg_sequence"]["name"]
    sgShotList.sort(key=keyFnc)
    sgShotGrps = groupby(sgShotList, key=keyFnc)

    for sSeqCode, sgShotIter in sgShotGrps:

        print 3 * "\n", sSeqCode.center(100, "#")

        layToAnimItems = []

        for sgShot in sgShotIter:

            sShotCode = sgShot["code"]

            if sShotCode in sAnimStartedShots:
                #print "already fixed infoSet on '{}'".format(sShotCode)
                continue

            damShot = damShotDct[sShotCode]

            try:
                layScn = damShot.getResource("public", "layout_scene", dbNode=True, fail=True)
                sLockOwner = layScn.getLockOwner(refresh=True)
                if sLockOwner:
                    raise RuntimeError("{} - layout scene locked by '{}'".format(damShot, sLockOwner))
                layScn = layScn.latestVersionFile(refresh=False)
                if not layScn:
                    raise RuntimeError("{} - No layout version found".format(damShot))
                animScn = damShot.getResource("public", "anim_scene", dbNode=False, fail=True)
            except RuntimeError as e:
                pm.displayWarning(toStr(e))
                continue

            print "not processed yet: '{}'".format(sShotCode)
            print "    ", layScn.relPath(), toDisplayText(layScn.dbMtime), "\n"
            #if not dryRun:
            privLayScn, _ = layScn.copyToPrivateSpace(existing="keep")
            layToAnimItems.append((privLayScn, animScn))

        for privLayScn, animScn in layToAnimItems:

            print 100 * "-"

            print "scene:".upper(), privLayScn.absPath(), '\n'
            myasys.openScene(privLayScn.absPath(), force=True, fail=False, lrd="none")
            pm.refresh()

            print "\nsave as:".upper(), animScn.absPath()
            if not dryRun:
                pm.saveAs(animScn.absPath(), force=True)

            print (100 * "-") + "\n"

        print sSeqCode.center(100, "#")
