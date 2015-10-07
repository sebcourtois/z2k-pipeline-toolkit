
import sys
import os
import os.path as osp
import subprocess
import argparse
from shutil import make_archive, ignore_patterns
from datetime import datetime


class Z2kToolkit(object):

    def __init__(self, customEnvs):

        sBaseName = "z2k-pipeline-toolkit"
        sCurDirPath = normPath(osp.dirname(osp.abspath(__file__)))

        sRoot, sTail = sCurDirPath.split(sBaseName)
        sDirName = sBaseName + sTail.split("/", 1)[0]

        sRootPath = pathJoin(sRoot, sDirName)
        if not osp.isdir(sRootPath):
            raise EnvironmentError("No such directory: '{}'".format(sRootPath))

        self.isDev = osp.isdir(pathJoin(sRootPath, ".git"))
        self.rootPath = sRootPath
        #self.dirName = sDirName
        self.baseName = sBaseName
        self.pythonPath = pathJoin(sRootPath, "python")
        self.thirdPartyPath = pathJoin(sRootPath, "third-party")

        self.loadEnvs(customEnvs)

    def loadEnvs(self, customEnvs):

        print "Tools repository"
        print " - path          : {0}".format(self.rootPath)
        print " - configuration : {0}".format("Development" if self.isDev else "Production")
        print ""

        print "\nLoading site-defined environment:"

        for sVar, value in customEnvs.iteritems():
            updEnv(sVar, value, conflict="keep")


        print "\nLoading toolkit environment:"

        updEnv("PYTHONPATH", self.pythonPath, conflict="add")
        sys.path.append(self.pythonPath)

        sDavosPath = pathJoin(self.pythonPath, "davos-dev")
        updEnv("PYTHONPATH", sDavosPath, conflict="add")
        sys.path.append(sDavosPath)

        sPytdPath = pathJoin(self.pythonPath, "pypeline-tool-devkit")
        updEnv("PYTHONPATH", sPytdPath, conflict="add")
        sys.path.append(sPytdPath)

        updEnv("PYTHONPATH", self.thirdPartyPath, conflict="add")
        sys.path.append(self.thirdPartyPath)

        updEnv("DAVOS_CONF_PACKAGE", "zomblib.config", conflict="keep")
        updEnv("DAVOS_INIT_PROJECT", "zombillenium", conflict="keep")

        os.environ["DEV_MODE_ENV"] = str(int(self.isDev))

    def loadAppEnvs(self, sAppPath):

        sAppPath = sAppPath.lower()
        sAppName = osp.basename(sAppPath).rsplit(".", 1)[0]

        # initializing an empty DamProject to have project's environ loaded
        from davos.core.damproject import DamProject
        proj = DamProject(os.environ["DAVOS_INIT_PROJECT"], empty=True)
        proj.loadEnviron()

        if sAppName in ("maya", "mayabatch", "render", "mayapy"):

            print "\nLoading maya environment:"

            updEnv("MAYA_MODULE_PATH", pathJoin(self.rootPath, "maya_mods"),
                   conflict="add")

            if "maya2016" in sAppPath:

                updEnv("Z2K_PYTHON_SITES", pathJoin(self.thirdPartyPath, "mayapy2016-site"),
                       conflict="add")

            print ''

    def install(self):

        # tools update
        sReleasePath = self.releasePath()
        if self.isDev:
            print "Tools update from development environment !"
            sReleasePath = self.rootPath

        sInstallPath = pathJoin(os.environ["USERPROFILE"], "zombillenium", self.baseName)

        if sReleasePath == sInstallPath:
            print "Source == Destination !"
        else:

            sAction = "Installing"
            if osp.exists(sInstallPath):
                sAction = "Updating"
            else:
                os.makedirs(sInstallPath)

            print "\n{} Z2K Toolkit:\n'{}' -> '{}'".format(sAction, sReleasePath, sInstallPath)

            sOutput = self.makeCopy(sReleasePath, sInstallPath,
                                    dryRun=False, summary=False)

            if not sOutput.strip():
                print "\nNo changes !"
                return

            print "\n", sOutput

            cleanUpPyc(sInstallPath)

            print ("Zombie toolkit updated, use your local to launch applications ! ({0})"
                   .format(pathJoin(sInstallPath, "launchers")))

    def release(self, location="", archive=True):

        if not self.isDev:
            raise EnvironmentError("Sorry, you are not in DEV mode !")

        sDistroPath = self.releasePath(location)

        if osp.exists(sDistroPath):
            bUpdating = True
            sAction = "Updating"
        else:
            bUpdating = False
            sAction = "Creating"
            os.makedirs(sDistroPath)

        print "\n{} toolkit release:\n'{}' -> '{}'".format(sAction, self.rootPath, sDistroPath)

        if bUpdating:
            sOutput = self.makeCopy(self.rootPath, sDistroPath,
                                    dryRun=True, summary=False)
            if not sOutput.strip():
                print "\nNo changes !"
                return

            if archive:
                sDate = datetime.now().strftime("%Y%m%d-%H%M")
                sZipPath = pathJoin(sDistroPath + "_backups", self.baseName + "_" + sDate)

                cleanUpPyc(sDistroPath)

                logger = initLogger()
                make_archive(sZipPath , "zip",
                             root_dir=osp.dirname(sDistroPath),
                             base_dir=pathJoin('.', osp.basename(sDistroPath)),
                             logger=logger, dry_run=False)

        sOscarPath = pathJoin(sDistroPath, "maya_mods", "Toonkit_module",
                              "Maya2016", "Standalones", "OSCAR")

        if not os.path.exists(sOscarPath):
            os.makedirs(sOscarPath)

        print self.makeCopy(self.rootPath, sDistroPath, dryRun=False)

    def makeCopy(self, sSrcRepoPath, sDestPath, dryRun=False, summary=True):

        sMsg = ""
        for p in (sSrcRepoPath, sDestPath):
            if not osp.isdir(p):
                sMsg += "\n    No such directory: '{}'".format(p)

        if sMsg:
            sMsg = "Cannot launch robocopy:" + sMsg
            raise RuntimeError(sMsg)

        sOscarPath = pathJoin(sSrcRepoPath, "maya_mods", "Toonkit_module",
                              "Maya2016", "Standalones", "OSCAR")

        sDryRun = "/L" if dryRun else ""
        sNoSummary = "/NJS" if not summary else ""

        sExcludeFiles = ["*.pyc", ".git*", ".*project", "*.lic", "Thumbs.db",
                         "pull_all.bat"]
        if not self.isDev:
            sExcludeFiles += ["setup_*.bat"]
        sExcludeFiles = " ".join(sExcludeFiles)

        cmdLineFmt = "robocopy {} /S {} /NDL /NJH /MIR *.* {} {} /XD {} .git tests /XF {}"
        cmdLine = cmdLineFmt.format(sDryRun,
                                    sNoSummary,
                                    sSrcRepoPath,
                                    sDestPath,
                                    sOscarPath,
                                    sExcludeFiles)

#        if (not dryRun) and self.isDev:
#            print cmdLine

        return callCmd(cmdLine, catchStdout=True)

    def releasePath(self, location=""):

        if location:
            sReleaseLoc = location
        else:
            sReleaseLoc = os.environ["ZOMB_TOOL_PATH"]

        if not osp.isdir(sReleaseLoc):
            raise EnvironmentError("No such Release location: '{}'".format(sReleaseLoc))

        return pathJoin(sReleaseLoc, self.baseName)

    def launchCmd(self, cmdArgs, update=True):

        sAppPath = cmdArgs[0]
        sAppName = osp.basename(sAppPath)

        try:

            if (not self.isDev) and update:
                self.install()

            self.loadAppEnvs(sAppPath)

        except Exception, err:

            print ("\n\nFailed initializing '{}' environments: \n    {}"
                   .format(sAppName, err))

            res = ""
            while res not in ("yes", "no"):
                res = raw_input("\nContinue launching '{}' ? (yes/no)"
                                .format(sAppName))

            if res == "no":
                raise

#        startupinfo = subprocess.STARTUPINFO()
#        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
#        subprocess.call(cmdArgs, startupinfo=startupinfo)

        return callCmd(cmdArgs)

    def runFromCmd(self):

        updEnv("Z2K_LAUNCH_SCRIPT", osp.normpath(sys.argv[0]))

        parser = argparse.ArgumentParser()
        parser.add_argument("command", choices=("install", "launch", "release"))
        parser.add_argument("--update", "-upd", type=int, default=1)
        parser.add_argument("--archive", "-arc", type=int, default=1)
        parser.add_argument("--location", "-loc", type=str, default="")

        ns, cmdArgs = parser.parse_known_args()

        sCmd = ns.command
        if sCmd == "launch":
            self.launchCmd(cmdArgs, update=ns.update)
            return

        if sCmd == "install":
            self.install()
        elif sCmd == "release":
            self.release(location=ns.location, archive=ns.archive)

CREATE_NO_WINDOW = 0x8000000

def callCmd(cmdArgs, catchStdout=False, shell=False, inData=None, noCmdWindow=False):

    iCreationFlags = CREATE_NO_WINDOW if noCmdWindow else 0

    pipe = subprocess.Popen(cmdArgs, shell=shell,
                            stdout=subprocess.PIPE if catchStdout else None,
                            stderr=subprocess.STDOUT if catchStdout else None,
                            creationflags=iCreationFlags)
    if catchStdout:
        outData, errData = pipe.communicate(inData)
        if errData and errData.strip():
            print cmdArgs
            raise subprocess.CalledProcessError(errData)
        return outData
    else:
        return pipe.wait()

def initLogger():

    import logging

    # create logger
    logger = logging.getLogger('simple_example')
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # add ch to logger
    logger.addHandler(ch)

    return logger

def updEnv(sVar, in_value, conflict='replace'):

    opts = ('add', 'replace', 'keep', 'fail')
    if conflict not in opts:
        raise ValueError("Invalid value for 'conflict' arg: '{}'. Try {}"
                         .format(conflict, opts))

    newValue = in_value
    sMsgFmt = " - {} {} : '{}'"
    sAction = "set"
    if sVar in os.environ:
        if conflict == "keep":
            return
        elif conflict == "fail":
            raise EnvironmentError("Env. variable already defined: '{}'='{}'"
                                   .format(sVar, os.environ[sVar]))
        elif conflict == 'add':
            prevValue = os.environ[sVar]
            if in_value in prevValue:
                return
            newValue = os.pathsep.join((prevValue, in_value)) if prevValue else in_value
            sAction = "add"
        else:
            sAction = "upd"

    print sMsgFmt.format(sAction, sVar, in_value)
    os.environ[sVar] = newValue

def makePrivatePath(sPublicPath):

    sPrivZombPath = os.environ["ZOMB_PRIVATE_LOC"]
    sDirName = osp.basename(sPublicPath)
    return pathJoin(sPrivZombPath, sDirName)

def normPath(p):
    return osp.normpath(p).replace("\\", "/")

def normCase(p):
    return osp.normcase(p).replace("\\", "/")

def pathJoin(*args):
    return normPath(osp.join(*args))

def addEndSlash(sDirPath):
    return sDirPath if sDirPath.endswith("/") else sDirPath + "/"

def iterPaths(sRootDirPath, **kwargs):

    if not osp.isdir(sRootDirPath):
        raise ValueError, 'No such directory found: "{0}"'.format(sRootDirPath)

    bFiles = kwargs.pop("files", True)
    bDirs = kwargs.pop("dirs", True)
    bRecursive = kwargs.pop("recursive", True)

    ignoreDirsFunc = kwargs.get("ignoreDirs", None)
    ignoreFilesFunc = kwargs.get("ignoreFiles", None)

    filterFilesFunc = kwargs.get("filterFiles", None)

    for sDirPath, sDirNames, sFileNames in os.walk(sRootDirPath):

        if not bRecursive:
            del sDirNames[:] # don't walk further

        if ignoreDirsFunc is not None:
            sIgnoredDirs = ignoreDirsFunc(sDirPath, sDirNames)
            for sDir in sIgnoredDirs:
                try: sDirNames.remove(sDir)
                except ValueError: pass

        if bDirs:
            for sDir in sDirNames:
                yield addEndSlash(pathJoin(sDirPath, sDir))

        if bFiles:

            bFilter = False
            sFilterFiles = []
            if filterFilesFunc is not None:
                sFilterFiles = filterFilesFunc(sDirPath, sFileNames)
                #print "sFilterFiles", sFilterFiles, sFileNames
                bFilter = True

            sIgnoredFiles = []
            if ignoreFilesFunc is not None:
                sIgnoredFiles = ignoreFilesFunc(sDirPath, sFileNames)
                #print "sIgnoredFiles", sIgnoredFiles

            for sFileName in sFileNames:

                if bFilter and (sFileName not in sFilterFiles):
                    continue

                if sFileName in sIgnoredFiles:
                    continue

                yield pathJoin(sDirPath, sFileName)

def cleanUpPyc(sRootPath):

    pathIter = iterPaths(sRootPath, dirs=False, files=True,
                         filterFiles=ignore_patterns("*.pyc"),
                         ignoreDirs=ignore_patterns(".*"))
    n = 0
    for p in pathIter:
        if p.endswith(".pyc"):
            os.remove(p)
            n += 1

    print "Deleted {} '.pyc' files".format(n)


#if __name__ == "__main__":
#    try:
#        Z2kToolkit().runFromCmd()
#    except:
#        os.environ["PYTHONINSPECT"] = "1"
#        raise

