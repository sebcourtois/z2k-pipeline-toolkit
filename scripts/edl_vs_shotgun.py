
import os
import sys
from collections import OrderedDict
import csv

from zomblib.editing import parseEdl, convertTcToSeconds, FPS

#from pytd.util.sysutils import inDevMode
#from pytd.util.fsutils import copyFile

from davos.core.damproject import DamProject
#from davos.core.damtypes import DamShot

def launch():

    sEdlPath = ""
    sCsvPath = ""
    if len(sys.argv) == 2:
        sEdlPath = sys.argv[1]
        sPath, sExt = os.path.splitext(sEdlPath)
        if sExt.lower() == ".edl":
            sCsvPath = sPath + "_EDLvsSG.csv"

    if not (sCsvPath and sEdlPath):
        raise RuntimeError("Please, drag and drop an EDL file on me.")

    proj = DamProject(os.environ.get("DAVOS_INIT_PROJECT"))
    shotgundb = proj._shotgundb

    statusNameDct = dict((d["code"], d["name"]) for d in  shotgundb.sg.find("Status", [], ["code", "name"]))

    sSeqList = []
    edlShotDct = OrderedDict()

    print "Parsing EDL data..."
    for edlShot in parseEdl(sEdlPath):

        print edlShot

        sSeqCode = edlShot["sequence"].lower()
        sShotName = "sh" + edlShot["shot"].lstrip("P").lower()
        sShotCode = sSeqCode + "_" + sShotName

        startTime = convertTcToSeconds(edlShot["start"], in_iHoursOffset=-1)
        endTime = convertTcToSeconds(edlShot["end"], in_iHoursOffset=-1, in_iFramesOffset=-1)
        numFrames = ((endTime - startTime) * FPS) + 1
        edlShot["duration"] = numFrames

        sSeqList.append(sSeqCode)
        edlShotDct[sShotCode] = edlShot

    if not sSeqList:
        raise RuntimeError("No sequences found in '{}'.".format(sEdlPath))

    print "Retrieving Shotgun data..."
    filters = [["sg_sequence.Sequence.code", "in", sSeqList], ["code", "ends_with", "a"]]
    fields = ["sg_cut_duration"]
    sgShotDct = OrderedDict((d["code"], d) for d in proj.listAllSgShots(moreFilters=filters,
                                                                        moreFields=fields))

    filters = [["entity.Shot.code", "in", sgShotDct.keys()], ["content", "is", "previz 3D"]]
    fields = ["entity.Shot.code", "sg_status_list"]#, "content"]
    sgPrevizTaskDct = dict((d.pop("entity.Shot.code"), d) for d in shotgundb.find("Task", filters, fields))

    sAllShotList = sorted(set(edlShotDct.iterkeys()) | set(sgShotDct.iterkeys()))

    with open(sCsvPath, "wb") as csvFile:

        writer = csv.writer(csvFile, delimiter="|")

        header = ["Shot Code", "Report", "EDL Duration", "SG Duration", "Previz Status"]
        writer.writerow(header)

        sPrevSeqCode = ""
        numShots = len(sAllShotList)
        c = 0
        for sShotCode in sAllShotList:

            c += 1
            print "Processing {}/{} shot: '{}'...".format(c, numShots, sShotCode)

            sSeqCode = sShotCode.split("_", 1)[0]
            if sPrevSeqCode and sSeqCode != sPrevSeqCode:
                writer.writerow([])

            sPrevSeqCode = sSeqCode

            bSgShot = sShotCode in sgShotDct
            bEdlShot = sShotCode in edlShotDct

            sReportMsg = ""
            sEdlDuration = ""
            sSgDuration = ""
            sPrevizStatus = ""

            if bSgShot:
                sSgDuration = "{:.0f}".format(sgShotDct[sShotCode]["sg_cut_duration"])
                sPrevizStatus = statusNameDct[sgPrevizTaskDct[sShotCode]["sg_status_list"]]
                if not bEdlShot:
                    sReportMsg = "omitted shot"

            if bEdlShot:
                sEdlDuration = "{:.0f}".format(edlShotDct[sShotCode]["duration"])
                if not bSgShot:
                    sReportMsg = "added shot"#"not in shotgun"

            if bSgShot and bEdlShot:
                if sSgDuration != "1" and sEdlDuration != sSgDuration:
                    sReportMsg = "updated duration"

            row = [sShotCode, sReportMsg, sEdlDuration, sSgDuration, sPrevizStatus]
            writer.writerow(row)

    os.system(sCsvPath)

if __name__ == "__main__":
    try:
        launch()
    except:
        os.environ["PYTHONINSPECT"] = "1"
        raise

