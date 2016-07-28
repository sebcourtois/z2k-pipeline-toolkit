
import argparse
import sys
import os
from pytd.util.fsutils import pathResolve
os.environ["PYTHONINSPECT"] = "1"

try:
    import davos_env
    davos_env.load()
except ImportError:pass

from davos.core.damproject import DamProject
from davos.core.damtypes import *

parser = argparse.ArgumentParser()
parser.add_argument("--project", "-p", default=os.environ.get("DAVOS_INIT_PROJECT"))
ns = parser.parse_args()

sProject = ns.project
if not sProject:
    sProject = raw_input("project: ")

proj = DamProject(sProject)
while not proj:
    sProject = raw_input("project: ")
    proj = DamProject(sProject)

print ""
print (" Project: '{}' ".format(sProject)).center(80, "-")

def iterPrevizStartedShots():

    shotLib = proj.getLibrary("public", "shot_lib")
    shotLib.loadChildDbNodes(recursive=True, noVersions=True)

    allSgShots = proj.listAllSgShots()

    for sgShot in allSgShots:

        damShot = DamShot(proj, name=sgShot["code"])

        previzScn = damShot.getResource("public", "previz_scene")

        if previzScn and previzScn.currentVersion:
            yield sgShot, damShot, previzScn

def logShotsWithoutExportedCamera():

    for _, damShot, previzScn in iterPrevizStartedShots():
        if previzScn and previzScn.currentVersion:

            camFile = damShot.getResource("public", "camera_scene")
            if camFile:
                pass#print camFile.currentVersion, previzScn.currentVersion
            else:
                print damShot.name

def updatePathsToMovie(dryRun=True):

    shotgundb = proj._shotgundb

    filters = [
        ["project", "is", shotgundb.getProjectInfo()],
        ["entity.Shot.id", "is_not", None],
        ["sg_source_file", "is_not", None],
    ]

    fields = ["code",
              #"sg_current_release_version",
              #"sg_task",
              "sg_source_file",
              "sg_path_to_movie",
              "entity.Shot.code",
              ]

    shotVersions = shotgundb.sg.find("Version", filters, fields,
                                     [{"field_name":"code", "direction":"asc"}],
                                     limit=0)

    count = len(shotVersions)
    for i, version in enumerate(shotVersions):
        #print version
        sMoviePath = os.path.splitext(version["sg_source_file"])[0] + ".mov"
        #print sMoviePath
        if not os.path.exists(pathResolve(sMoviePath)):
            sMoviePath = ""

        if sMoviePath == version["sg_path_to_movie"]:
            continue

        data = {"sg_path_to_movie":sMoviePath}
        print "updating version {}/{}: {}...".format(i + 1, count, version["code"]), data
        if not dryRun:
            print shotgundb.sg.update("Version", version["id"], data)

def listPrevizStartedSequences():

    return sorted(set(sh.sequence.upper() for _, sh, _ in iterPrevizStartedShots()))

def splitAnimatic(sSeqList, dryRun=True):

    sSplitterDirPath = r"C:\Users\sebcourtois\devspace\git\z2k-pipeline-toolkit\movSplitter"
    sys.path.append(sSplitterDirPath)

    from splitter import splitMovie

    sMovPath = r"Z:\01_PRODUCTION\ANIMATIQUE\ZB_BAB_NEW_VOICES_20151126.mov"
    sEdlPath = r"Z:\01_PRODUCTION\ANIMATIQUE\ZB_BAB_NEW_VOICES_20151126.edl"

    for sSeq in sSeqList:
        splitMovie(sMovPath, sEdlPath, sSeq, doSplit=not dryRun, exportCsv=False,
                   in_bExportInShotFolders=not dryRun)

    print sSeqList


