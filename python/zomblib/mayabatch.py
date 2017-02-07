
import os
import os.path as osp
import subprocess
import traceback
from collections import OrderedDict

from pytd.util.fsutils import jsonRead, pathNorm
from pytd.util.sysutils import timer

@timer
def execJob(lines):
    exec("\n".join(lines), {})

@timer
def processJobsFromFile(sJobFilePath):

    jobList = jsonRead(sJobFilePath)

    numErrors = 0
    numJobs = len(jobList)
    errorDct = OrderedDict()

    exec("import maya.cmds as mc")

    for i, job in enumerate(jobList):

        sTitle = job["title"]

        sMsg = "#### STARTING {}/{} JOB: {}".format(i + 1, numJobs, sTitle)
        sSepLine = 120 * "#"
        print "\n", "\n".join((sSepLine, sMsg, "###"))

        lines = job["py_lines"]
        if not isinstance(lines, list):
            raise TypeError("'py_lines' value must be a {}, got {}."
                            .format(list, type(lines)))
        try:
            execJob(lines)#exec("\n".join(lines), {})
        except Warning as w:
            print "WARNING: " + w.message
        except StandardError as e:
            if job.get("fail", False):
                raise
            lines = [""] + traceback.format_exc().splitlines(True)
            print "!ERROR! ".join(lines)
            numErrors += 1
            errorDct[sTitle] = e.message

        sMsg = "##### DONE WITH {}/{} JOB: {}".format(i + 1, numJobs, sTitle)
        #sSepLine = max(len(sMsg), 120) * "#"
        print "\n".join(("####", sMsg, sSepLine)), "\n"

    if numErrors:
        sMsg = " {}/{} JOBS FAILED ".format(numErrors, len(jobList)).center(120, "!")
        print sMsg
        w = len(max(errorDct.iterkeys(), key=len))
        for k, v in errorDct.iteritems():
            print "- {k:<{w}}: {v}".format(k=k, v=v, w=w)
        print sMsg
        exec("mc.file(new=True, f=True)")
    else:
        exec("mc.quit(f=True)")

    return True if numErrors else None

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

        self.commandArgs = [osp.normpath(sPython27Path),
                            osp.normpath(sZ2kEnvScript),
                            "launch", "--update", "0", #"--renew", "1",
                            osp.normpath(sBatchAppPath)]

    def launch(self, sJobFilePath, logTo="", writeCmdTo=""):

        sJobFilePath = pathNorm(sJobFilePath)

        cmdArgs = self.commandArgs[:]
        if logTo:
            cmdArgs.extend(("-log", pathNorm(logTo)))

        sPyCmd = "from zomblib import mayabatch;reload(mayabatch);"
        sPyCmd += "mayabatch.processJobsFromFile('{}');".format(sJobFilePath)
        sMelCmd = "python(\"{}\");".format(sPyCmd)

        cmdArgs.extend(("-prompt", "-command", sMelCmd))

        if writeCmdTo:
            with open(writeCmdTo, "w") as f:
                f.write(subprocess.list2cmdline(cmdArgs))

        return subprocess.call(cmdArgs)
