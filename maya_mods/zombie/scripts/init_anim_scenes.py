
import os
from itertools import groupby

import pymel.core as pm

#from pytd.util.fsutils import pathResolve, pathSplitDirs, pathJoin

from davos.core.damproject import DamProject
#from davos.core.damtypes import *

from pytaya.core import system as myasys

from pytd.gui.itemviews.utils import toDisplayText
from pytd.util.sysutils import inDevMode, toStr
from dminutes.miscUtils import deleteUnknownNodes


def iterSeqDirPaths(shotLib, sSeqList):

    proj = shotLib.project

    for sSeqName in sSeqList:
        sAbsPath = proj.getPath("public", "shot_lib", "sequence_dir", dict(sequence=sSeqName))
        sDbPath = shotLib.absToDbPath(sAbsPath)
        #print sDbPath
        yield sDbPath

def launch(shots=None, sequences=None, dryRun=True):

    if not (shots or sequences):
        raise TypeError("Neither list of shots nor sequences was given.")

    sProject = os.environ.get("DAVOS_INIT_PROJECT")
    proj = DamProject(sProject)
    print ""
    print (" Project: '{}' ".format(sProject)).center(80, "-")

    shotLib = proj.getLibrary("public", "shot_lib")

    if sequences:
        sSeqList = tuple(s.lower() for s in sequences)

        for sSeq in sSeqList:
            sQuery = "file:/{}_sh\d{{4}}._anim\.ma$/i".format(sSeq)
            for dbNode in proj.findDbNodes(sQuery):
                shotLib._addDbNodeToCache(dbNode)

        shotFilters = [["sg_sequence.Sequence.code", "in", sSeqList]]

    elif shots:
        sShotList = tuple(s.lower() for s in shots)

        for sShot in sShotList:
            sQuery = "file:/{}_anim\.ma$/i".format(sShot)
            for dbNode in proj.findDbNodes(sQuery):
                shotLib._addDbNodeToCache(dbNode)

        shotFilters = [["code", "in", sShotList]]

    bOmitted = False#inDevMode()

    sgShotList = proj.listAllSgShots(includeOmitted=bOmitted, moreFilters=shotFilters)

    keyFnc = lambda d:d["sg_sequence"]["name"]
    sgShotList.sort(key=keyFnc)
    sgShotGrps = groupby(sgShotList, key=keyFnc)

    for sSeqCode, sgShotIter in sgShotGrps:

        print 3 * "\n", sSeqCode.center(100, "#")

        layToAnimItems = []

        for sgShot in sgShotIter:

            sShotCode = sgShot["code"]
            damShot = proj.getShot(sShotCode)

            try:
                pubAnimScn = damShot.getResource("public", "anim_scene", dbNode=False, fail=True)
                v = pubAnimScn.currentVersion
                if v:
                    raise AssertionError("{} - anim scene already published (v{})."
                                         .format(damShot, v))

                pubLayoutScn = damShot.getResource("public", "layout_scene", dbNode=False, fail=True)
                sLockOwner = pubLayoutScn.getLockOwner(refresh=True)
                if sLockOwner:
                    raise AssertionError("{} - layout scene locked by '{}'".format(damShot, sLockOwner))

                pubLayoutScn = pubLayoutScn.latestVersionFile(refresh=False)
                if not pubLayoutScn:
                    raise AssertionError("{} - No layout version found".format(damShot))

            except Exception as e:
                pm.displayWarning(toStr(e))
                continue

            print "not processed yet: '{}'".format(sShotCode)
            print "    ", pubLayoutScn.relPath(), toDisplayText(pubLayoutScn.dbMtime), "\n"
            #if not dryRun:
            privLayoutScn, _ = pubLayoutScn.copyToPrivateSpace(existing="keep")
            layToAnimItems.append((privLayoutScn, pubAnimScn))

        for privLayoutScn, pubAnimScn in layToAnimItems:

            print 100 * "-"

            print "scene:".upper(), privLayoutScn.absPath(), '\n'
            if not dryRun:
                myasys.openScene(privLayoutScn.absPath(), force=True, fail=False, lrd="none")

                try:
                    deleteUnknownNodes()
                except Exception as e:
                    pm.displayWarning(e)
                pm.refresh()

                print "\nsave as:".upper(), pubAnimScn.absPath()
                pm.saveAs(pubAnimScn.absPath(), force=True)

            print (100 * "-") + "\n"

        print sSeqCode.center(100, "#")
