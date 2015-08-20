
import os
import os.path as osp
import subprocess
import argparse
import logging
from shutil import make_archive
from datetime import datetime

CREATE_NO_WINDOW = 0x8000000

def runCmd(cmd, shell=False, catchOutput=True, noCmdWindow=False):

    iCreationFlags = CREATE_NO_WINDOW if noCmdWindow else 0

    pipe = subprocess.Popen(cmd, shell=shell,
                            stdout=subprocess.PIPE if catchOutput else None,
                            stderr=subprocess.STDOUT if catchOutput else None,
                            creationflags=iCreationFlags)

    stdOut = pipe.communicate()[0]

    return stdOut

def getLogger():

    # create logger
    logger = logging.getLogger('simple_example')
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # add ch to logger
    logger.addHandler(ch)

    return logger

class Z2kToolkit(object):

    def __init__(self):

        sDirName = "z2k-pipeline-toolkit"
        sCurDirPath = osp.dirname(osp.abspath(__file__))
        sRootPath = osp.join(sCurDirPath.split(sDirName)[0], sDirName)

        self.isDev = osp.isdir(osp.join(sRootPath, ".git"))
        self.rootPath = sRootPath
        self.dirName = sDirName

    def loadEnvs(self):

        print "Tools repository"
        print " - path          : {0}".format(self.rootPath)
        print " - configuration : {0}".format("Development" if self.isDev else "Production")
        print ""

        # Python path
        pythonPathAdd = osp.join(self.rootPath, "python")
        pythonPathOld = "" if not "PYTHONPATH" in os.environ else os.environ["PYTHONPATH"]
        pythonPathNew = pythonPathAdd if pythonPathOld == "" else os.pathsep.join([pythonPathOld, pythonPathAdd])

        print " - SET {0} = {1}".format("PYTHONPATH", pythonPathNew)
        os.environ["PYTHONPATH"] = pythonPathNew

        sEnvKey = "DAVOS_CONF_PACKAGE"
        if sEnvKey not in os.environ:
            value = "zomblib.config"
            print " - SET {0} = {1}".format(sEnvKey, value)
            os.environ[sEnvKey] = value

        # Maya module path
        modulePathAdd = osp.join(self.rootPath, "maya_mods")
        modulePathOld = "" if not "MAYA_MODULE_PATH" in os.environ else os.environ["MAYA_MODULE_PATH"]
        modulePathNew = modulePathAdd if modulePathOld == "" else os.pathsep.join([modulePathOld, modulePathAdd])

        print " - SET {0} = {1}".format("MAYA_MODULE_PATH", modulePathNew)
        os.environ["MAYA_MODULE_PATH"] = modulePathNew
        os.environ["DEV_MODE_ENV"] = str(int(self.isDev))

        print ""

    def install(self):

        # tools update
        repo = self.releasePath()
        if self.isDev:
            print "Tools update from development environment !"
            repo = self.rootPath

        local_root = osp.join(os.environ["USERPROFILE"], "zombillenium", self.dirName)

        if repo == local_root:
            print "Source == Destination !"
        else:

            print self.makeCopy(repo, local_root)

            print "Zombie toolkit updated, use your local to launch applications ! ({0})".format(osp.join(local_root, "launchers"))

    def release(self):

        if not self.isDev:
            raise EnvironmentError("Sorry, you are not in DEV mode !")

        sDistroPath = self.releasePath()
        sOutput = self.makeCopy(self.rootPath, sDistroPath, dryRun=True).strip()
        if not sOutput:
            print "No changes !"
            return

        if osp.exists(sDistroPath):
            sDate = datetime.now().strftime("%Y%m%d-%H%M")
            sZipPath = osp.join(sDistroPath + "_backups", self.dirName + "_" + sDate)

            logger = getLogger()
            make_archive(sZipPath , "zip",
                         root_dir=osp.dirname(sDistroPath),
                         base_dir=osp.join('.', osp.basename(sDistroPath)),
                         logger=logger, dry_run=False)

        print self.makeCopy(self.rootPath, sDistroPath, dryRun=False)

    def makeCopy(self, sSrcRepoPath, sDestPath, dryRun=False):

        print "Updating Zombie toolkit: \n'{0}' -> '{1}'".format(sSrcRepoPath, sDestPath)

        oscarPath = osp.join(sSrcRepoPath, "maya_mods", "Toonkit_module", "Maya2016", "Standalones", "OSCAR")

        sDryRun = "/L /NJS" if dryRun else ""
        cmdLine = ("robocopy {} /S /NFL /NDL /NJH /MIR *.* {} {} /XD {} .git tests /XF {} *.pyc .git* .*project"
                    .format(sDryRun, sSrcRepoPath, sDestPath, oscarPath,
                            "setup_*.bat" if not self.isDev else ""))
        return runCmd(cmdLine)

    def releasePath(self):
        return osp.join(os.environ["ZOMB_TOOL_PATH"], self.dirName)

    def callCmd(self, args, update=True):

        self.loadEnvs()

        if (not self.isDev) and update:
            self.install()

        subprocess.call(args, shell=self.isDev)

    def runFromCmd(self):

        parser = argparse.ArgumentParser()
        parser.add_argument("command", choices=("install", "call", "release"))
        parser.add_argument("--update", "-u", type=int, default=1)

        ns, args = parser.parse_known_args()

        sCmd = ns.command
        if sCmd == "call":
            self.callCmd(args, update=ns.update)
            return

        if sCmd == "install":
            self.install()
        elif sCmd == "release":
            self.release()

if __name__ == "__main__":
    try:
        Z2kToolkit().runFromCmd()
    except:
        os.environ["PYTHONINSPECT"] = "1"
        raise

