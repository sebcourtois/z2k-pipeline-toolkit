
import os
import os.path as osp
import subprocess
import traceback
from datetime import datetime

from pytd.util.fsutils import jsonRead, pathNorm, pathJoin, pathSuffixed
import shutil

def processJobsFromFile(sJobFilePath):

    jobList = jsonRead(sJobFilePath)

    numJobs = len(jobList)
    for i, job in enumerate(jobList):

        sTitle = job["title"]

        sMsg = "---- PROCESSING {}/{}: {}".format(i + 1, numJobs, sTitle)
        sSepLine = 120 * "-"
        print "\n", "\n".join((sSepLine, sSepLine, sMsg, "---"))

        try:
            exec(job["py_code"], {})
        except Warning as w:
            print "WARNING: " + w.message
        except StandardError:
            if job.get("fail", False):
                raise
            lines = [""] + traceback.format_exc().splitlines(True)
            print "!ERROR! ".join(lines)

        sMsg = "----- DONE WITH {}/{}: {}".format(i + 1, numJobs, sTitle)
        #sSepLine = max(len(sMsg), 120) * "-"
        print "\n".join(("----", sMsg, sSepLine, sSepLine)), "\n"

class MayaBatch(object):

    def __init__(self):

        sPython27Path = "C:/Python27/python.exe"
        if not osp.isfile(sPython27Path):
            raise EnvironmentError("'python.exe' NOT found: '{}'"
                                   .format(sPython27Path))
        try:
            sZ2kEnvScript = os.environ["Z2K_LAUNCH_SCRIPT"]
        except KeyError:
            raise EnvironmentError("Undefined environment variable: '{}'."
                                   .format("Z2K_LAUNCH_SCRIPT"))

        if not osp.isfile(sZ2kEnvScript):
            raise EnvironmentError("No such '{}': '{}'."
                                   .format("Z2K_LAUNCH_SCRIPT", sZ2kEnvScript))

        sMayaLocPath = "C:/Program Files/Autodesk/Maya2016"
        if not osp.isdir(sMayaLocPath):
            try:
                sMayaLocPath = os.environ["MAYA_LOCATION"]
            except KeyError:
                raise EnvironmentError("No such Maya location: '{}'."
                                       .format(sMayaLocPath))
            if not osp.isdir(sMayaLocPath):
                raise EnvironmentError("No such '{}': '{}'."
                                       .format("MAYA_LOCATION", sMayaLocPath))

        sBatchAppPath = osp.join(sMayaLocPath, "bin", "mayabatch.exe")
        if not osp.isfile(sBatchAppPath):
            raise EnvironmentError("'mayabatch.exe' NOT found: '{}'"
                                   .format(sBatchAppPath))

        sLogFilePath = pathJoin(os.environ["USERPROFILE"], "zombillenium",
                                "logs", "final_layout_export.log")
        sLogDirPath = osp.dirname(sLogFilePath)
        if not osp.isdir(sLogDirPath):
            os.makedirs(sLogDirPath)
        elif osp.isfile(sLogFilePath):
            st = os.stat(sLogFilePath)
            if st.st_size:
                sSufx = datetime.fromtimestamp(st.st_mtime).strftime("_%Y%m%d-%Hh%M")
                shutil.copy2(sLogFilePath, pathSuffixed(sLogFilePath, sSufx))

        self.commandArgs = [osp.normpath(sPython27Path),
                            osp.normpath(sZ2kEnvScript),
                            "launch", "--update", "0", #"--renew", "1",
                            osp.normpath(sBatchAppPath),
                            "-log", sLogFilePath]

    def launch(self, sJobFilePath):

        sJobFilePath = pathNorm(sJobFilePath)

        sPyCmd = "from zomblib import mayabatch;reload(mayabatch);"
        sPyCmd += "mayabatch.processJobsFromFile('{}');".format(sJobFilePath)
        sMelCmd = "python(\"{}\"); file -f -new; quit -f;".format(sPyCmd)

        cmdArgs = self.commandArgs
        cmdArgs.extend(("-prompt", "-command", sMelCmd))

        subprocess.call(cmdArgs)
