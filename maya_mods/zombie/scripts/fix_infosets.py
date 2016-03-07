
import sys
import os

import pymel.core as pm

from pytd.util.fsutils import pathResolve

from davos.core.damproject import DamProject
from davos.core.damtypes import *

from pytaya.core import system as myasys

import dminutes.jipeLib_Z2K as jpZ
import dminutes.infoSetExp as infoE

def launch(sSeqList=None, dryRun=True):

    sProject = os.environ.get("DAVOS_INIT_PROJECT")
    proj = DamProject(sProject)

    print ""
    print (" Project: '{}' ".format(sProject)).center(80, "-")

    sComment = "fixed rotation values"

    shotLib = proj.getLibrary("public", "shot_lib")

    sAlreadyFixedShots = set()
    for dbNode in proj.findDbNodes("comment:/{}/".format(sComment.replace(" ", "\s"))):

        drcFile = shotLib.entryFromDbPath(dbNode.file, dbNode=False)
        damShot = drcFile.getEntity()
#        c = len(sAlreadyFixedShots)
        sAlreadyFixedShots.add(damShot.name)
#        if len(sAlreadyFixedShots) > c:
#            print damShot

    shotFilters = None
    bOmitted = False
    if sSeqList:
        shotFilters = [["sg_sequence.Sequence.code", "in", sSeqList]]
        bOmitted = True
    versFields = ["sg_source_file"]
    versFilters = [["sg_task.Task.step.Step.code", "in", ["previz 3d"]],
                   ]

    privFileList = []

    for sgShot in proj.listAllSgShots(includeOmitted=bOmitted, moreFilters=shotFilters):

        sShotCode = sgShot["code"]

        if sShotCode in sAlreadyFixedShots:
            print "already fixed infoSet on '{}'".format(sShotCode)
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

#            if not pubFile.isUpToDate():
#                print pubFile, "out of sync"
#                continue
#
#            if pubFile.getLockOwner(refresh=False):
#                print pubFile, "locked"
#                continue

            privFile, _ = pubFile.copyToPrivateSpace(existing="keep")
            print "will be process: '{}'".format(privFile.absPath())
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

if __name__ == "__main__":
    launch()

#python("import fix_infosets;reload(fix_infosets);fix_infosets.launch(['sq0160'],False)")
