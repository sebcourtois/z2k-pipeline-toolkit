
import sys
import os
import os.path as osp
#import subprocess

from pytd.util.sysutils import inDevMode
from pytd.util.fsutils import copyFile

from davos.core.damproject import DamProject
from davos.core.damtypes import DamShot

from zomblib.editing import parseEdl, convertTcToSeconds, convertTcToSecondsTc
from zomblib.editing import FPS


if inDevMode():
    SHOT_FOLDER = "C:\\Users\\sebcourtois\\zombillenium\\shot\\"
else:
    SHOT_FOLDER = "\\\\Zombiwalk\\Projects\\zomb\\shot\\"

SHOT_TEMPLATE = "{sequence}\\{sequence}_{shot}\\00_data"

def getShotFolder(in_sSequence, in_sShot):
    return SHOT_FOLDER + SHOT_TEMPLATE.format(sequence=in_sSequence, shot=in_sShot)

def splitMovie(in_sSourcePath, in_sEdlPath, in_sSeqFilter=None, in_sSeqOverrideName=None,
                doSplit=True, exportCsv=True, in_sShotSuffix="", in_bExportInShotFolders=True):

    bDryRun = (not doSplit)

    proj = DamProject(os.environ.get("DAVOS_INIT_PROJECT"))
    shotLib = proj.getLibrary("public", "shot_lib")

    dirname, _ = osp.split(osp.abspath(__file__))
    batchFile = osp.join(dirname, "split.bat")

    print "splitMovie({0}, {1}, {2}, {3})".format(in_sSourcePath, in_sEdlPath, in_sSeqFilter, in_sSeqOverrideName)

    shots = parseEdl(in_sEdlPath)

    if shots is None:
        print "Cannot read Edl correctly (see above) !"
        return

    csv = ("{0},{1},{2},{3},{4},{5}\n".format("Shot Code",
                                              "Cut In",
                                              "Cut Out",
                                              "Cut Duration",
                                              "Scn In",
                                              "Scn Out"))

    lenShots = len(shots)
    counter = 1
    for shot in shots:

        sequenceCode = shot["sequence"].replace("SQ", "sq")
        shotCode = shot["shot"].replace("P", "sh").replace("A", "a") + in_sShotSuffix
        startseconds = convertTcToSeconds(shot["start"], in_iHoursOffset=-1)
        endseconds = convertTcToSeconds(shot["end"], in_iHoursOffset=-1, in_iFramesOffset=-1)

        if in_sSeqFilter == None or shot["sequence"] == in_sSeqFilter:

            if in_sSeqFilter != None and in_sSeqOverrideName != None:
                sequenceCode = in_sSeqOverrideName

            damShot = DamShot(proj, name=sequenceCode + "_" + shotCode)
            sPrivMoviePath = osp.normpath(damShot.getPath("private", "animatic_capture"))
            sPrivOutDirPath, sFilename = osp.split(sPrivMoviePath)

            fmtFields = (batchFile, "{0}".format(in_sSourcePath),
                         convertTcToSecondsTc(shot["start"], in_iHoursOffset=-1),
                         convertTcToSecondsTc(shot["end"], in_iHoursOffset=-1, in_iFramesOffset=0),
                         sFilename)
            cmdLine = "{0} {1} {2} {3} {4}".format(*fmtFields)

            if in_bExportInShotFolders:
                if not osp.exists(sPrivOutDirPath):
                    os.makedirs(sPrivOutDirPath)
                cmdLine += " {0}\\".format(sPrivOutDirPath)

            if doSplit:
                os.system(cmdLine)
            else:
                print cmdLine

            if in_bExportInShotFolders:

                sPubMoviePath = damShot.getPath("public", "animatic_capture")
                sPubOutDirPath = osp.dirname(sPubMoviePath)
                pubOutDir = shotLib._weakDir(sPubOutDirPath, dbNode=False)
                if not osp.exists(sPubOutDirPath):
                    os.makedirs(sPubOutDirPath)
                    sSyncRuleList = pubOutDir.getParam("default_sync_rules", None)
                    if sSyncRuleList:
                        pubOutDir.setSyncRules(sSyncRuleList, applyRules=False)

                _, versionFile = pubOutDir.publishFile(sPrivMoviePath,
                                                       autoLock=True,
                                                       autoUnlock=True,
                                                       saveChecksum=True,
                                                       dryRun=bDryRun)
                if versionFile:
                    sgVersion = versionFile.shotgunVersion
                    proj.updateSgEntity(sgVersion, sg_path_to_movie=versionFile.envPath())
                    if sgVersion:
                        print " Uploading to Shotgun... ".center(100, "-")
                        proj.uploadSgVersion(sgVersion, versionFile.absPath())

                    sPrivSoundPath = damShot.getPath("private", "animatic_sound")
                    sPubSoundPath = damShot.getPath("public", "animatic_sound")
                    copyFile(sPrivSoundPath, sPubSoundPath, dry_run=bDryRun)

            percent = counter * 100 / lenShots
            bar = ["-" for _ in range(int(percent * .5))]
            print ("\nShot {0:04d}/{1:04d} {2:.0f}% |{3:<50}|"
                    .format(counter, lenShots, percent, "".join(bar)))
            counter += 1

        fmtFields = (sequenceCode + "_" + shotCode,
                     startseconds * FPS,
                     endseconds * FPS,
                     (endseconds - startseconds) * FPS + 1,
                     101,
                     101 + (endseconds - startseconds) * FPS)
        csv += "{0},{1:.0f},{2:.0f},{3:.0f},{4:.0f},{5:.0f}\n".format(*fmtFields)

    if exportCsv:
        outPath = in_sEdlPath.replace('.edl', '.csv')
        with open(outPath, 'w') as f:
            print outPath
            f.write(csv)
    else:
        print csv

if __name__ == "__main__":

    if len(sys.argv) < 3:
        print "Two arguments must be given (Source_video_path, edl_path) !"
    else:
        args = list(sys.argv)
        args.pop(0)
        print "splitMovie:\n    " + "\n    ".join(args)
        splitMovie(*args)
