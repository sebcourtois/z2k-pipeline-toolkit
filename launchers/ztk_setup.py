
import sys
import site
import os
import os.path as osp
import subprocess
import argparse
from shutil import make_archive, ignore_patterns
from datetime import datetime
import traceback
import webbrowser
from pprint import pprint
from collections import OrderedDict
import re

BASE_NAME = "z2k-pipeline-toolkit"
MASTER_NAME = BASE_NAME+"_master"

APPS_LOCATIONS = {
"Z2K_RV_LOC":(r"C:\Program Files\Shotgun\RV-7.0.0\bin",
              r"C:\Program Files\Shotgun\RV-7.0\bin",
              r"C:\Program Files\Shotgun\RV-6.2.8\bin",
              r"C:\Program Files\Shotgun\RV 6.2.6\bin",),
"Z2K_MAYA_LOC":(r"C:\Program Files\Autodesk\Maya2016\bin",),
}

APPS_INFOS = {
"rv":{"app_loc_var":"Z2K_RV_LOC",
      "app_bin_name":r"rv.exe",
      },
"rvpush":{"app_loc_var":"Z2K_RV_LOC",
          "app_bin_name":r"rvpush.exe",
          },
"maya":{"app_loc_var":"Z2K_MAYA_LOC",
        "app_bin_name":r"maya.exe",
        },
"mayabatch":{"app_loc_var":"Z2K_MAYA_LOC",
             "app_bin_name":r"mayabatch.exe",
             },
}

def getAppPath(sAppName):

    appInfos = APPS_INFOS[sAppName]

    sAppLocVar = appInfos["app_loc_var"]
    sAppLocPath = os.environ.get(sAppLocVar)
    if sAppLocPath:
        sLocPathList = (sAppLocPath,)
    else:
        sLocPathList = APPS_LOCATIONS[sAppLocVar]

    sNotFoundList = []
    for sLocPath in sLocPathList:

        sAppPath = osp.normpath(osp.join(sLocPath, appInfos["app_bin_name"]))
        if osp.isfile(sAppPath):
            sNotFoundList = []
            break
        sNotFoundList.append(sAppPath)

    numNotFound = len(sNotFoundList)
    if numNotFound == 1:
        raise EnvironmentError("'{}' application NOT found: '{}'"
                               .format(sAppName.capitalize(), sAppPath))
    elif numNotFound > 1:
        sSep = "\n    - "
        sMsg = "None of '{}' applications found:" + sSep + sSep.join(sNotFoundList)
        raise EnvironmentError(sMsg.format(sAppName.capitalize()))

    return sAppPath

def pathInUserProfile(sPath):
    sNormPath = addEndSlash(normAll(osp.expandvars(sPath)))
    sLocToolPath = addEndSlash(normAll(os.environ["USERPROFILE"]))
    return sNormPath.startswith(sLocToolPath)

def pathInPublicTools(sPath):
    sNormPath = addEndSlash(normAll(osp.expandvars(sPath)))
    sPubToolPath = addEndSlash(normAll(os.environ["ZOMB_TOOL_PATH"]))
    return sNormPath.startswith(sPubToolPath)

def mkReleasePath(sReleaseLoc, fail=True):

    if not sReleaseLoc:
        raise ValueError("invalid release location: '{}'".format(sReleaseLoc))

    if not osp.isdir(sReleaseLoc):
        if fail:
            raise EnvironmentError("No such release location: '{}'".format(sReleaseLoc))
        else:
            print "WARNING:", "No such release location: '{}'".format(sReleaseLoc)

    return pathJoin(sReleaseLoc, BASE_NAME)

def defaultInstallLocation():
    return osp.expandvars(pathJoin(os.environ["USERPROFILE"], "zombillenium"))

class Z2kToolkit(object):

    def __init__(self, customEnvs=None):

        sCurDirPath = normPath(osp.dirname(osp.abspath(__file__)))

        sRoot, sTail = sCurDirPath.split(BASE_NAME)
        sDirName = BASE_NAME + sTail.split("/", 1)[0]

        sRootPath = pathJoin(sRoot, sDirName)
        if not osp.isdir(sRootPath):
            raise EnvironmentError("No such directory: '{}'".format(sRootPath))

        self.isDev = osp.isdir(pathJoin(sRootPath, ".git"))# and (sDirName.lower() != MASTER_NAME)
        self.rootPath = sRootPath
        self.dirName = sDirName
        self.pythonPath = pathJoin(sRootPath, "python")
        self.thirdPartyPath = pathJoin(sRootPath, "third-party")

        self.envRecord = OrderedDict()
        self.customEnvs = customEnvs
        self.loadEnv(customEnvs)

    def loadEnv(self, customEnvs, replace=False):

        print "Tools repository"
        print " - path          : {0}".format(self.rootPath)
        print " - configuration : {0}".format("Development" if self.isDev else "Production")
        print ""

        sConflictMode = "replace" if replace else "keep"

        print "\nLoading site-defined environment:"

        for sVar, value in customEnvs.iteritems():
            self.updEnv(sVar, value, conflict=sConflictMode)

        print "\nLoading toolkit environment:"

        sPubToolPath = os.environ["ZOMB_TOOL_PATH"]
        sDefInstLoc = defaultInstallLocation()
        sNormCurLoc = normAll(osp.dirname(self.rootPath))

        if sNormCurLoc == normAll(sDefInstLoc):
            if not os.environ.get("Z2K_RELEASE_LOC"):
                self.updEnv("Z2K_RELEASE_LOC", sPubToolPath)
        elif sNormCurLoc == normAll(sPubToolPath):
            if not os.environ.get("Z2K_INSTALL_LOC"):
                self.updEnv("Z2K_INSTALL_LOC", sDefInstLoc)

        sZtkSetupLoc = osp.dirname(__file__)
        self.updEnv("PYTHONPATH", sZtkSetupLoc, conflict="add")
        sys.path.append(sZtkSetupLoc)

        self.updEnv("PYTHONPATH", self.pythonPath, conflict="add")
        sys.path.append(self.pythonPath)

        sDavosPath = pathJoin(self.pythonPath, "davos-dev")
        self.updEnv("PYTHONPATH", sDavosPath, conflict="add")
        sys.path.append(sDavosPath)

        sPytdPath = pathJoin(self.pythonPath, "pypeline-tool-devkit")
        self.updEnv("PYTHONPATH", sPytdPath, conflict="add")
        sys.path.append(sPytdPath)

        self.updEnv("PYTHONPATH", self.thirdPartyPath, conflict="add")
        sys.path.append(self.thirdPartyPath)

        #python site so PySide is found and DamProject can be instantiated
        sPy27SitePath = pathJoin(self.thirdPartyPath, "_python27_site")
        site.addsitedir(sPy27SitePath)

        self.updEnv("ZOMB_NUKE_PATH", pathJoin(self.rootPath, "nuke"),
                    conflict=sConflictMode)
        #self.updEnv("Z2K_ROOT_PATH", self.rootPath, conflict=sConflictMode)
        self.updEnv("DAVOS_CONF_PACKAGE", "zomblib.config", conflict=sConflictMode)
        self.updEnv("DAVOS_INIT_PROJECT", "zombillenium", conflict=sConflictMode)

        if "DEV_MODE_ENV" not in os.environ:
            self.updEnv("DEV_MODE_ENV", str(int(self.isDev)), conflict=sConflictMode)

    def loadAppEnv(self, sAppPath):

        sAppPath = sAppPath.lower()
        sAppName, _ = osp.splitext(osp.basename(sAppPath))

        #print "\n----------------", sAppPath

        # initializing an empty DamProject to have project's environ loaded
        from davos.core.damproject import DamProject
        proj = DamProject(os.environ["DAVOS_INIT_PROJECT"], empty=True)
        proj.loadEnviron(record=self.envRecord)

        if sAppName in ("maya", "mayabatch", "render", "mayapy"):

            print "\nLoading Maya environment:"

            self.updEnv("MAYA_MODULE_PATH", pathJoin(self.rootPath, "maya_mods"),
                   conflict="add")

            if "maya2016" in sAppPath:

                self.updEnv("Z2K_PYTHON_SITES", pathJoin(self.thirdPartyPath, "_mayapy2016_site"),
                       conflict="add")

        elif sAppName in ("rv", "rvpush"):

            print "\nLoading RV environment:"

            self.updEnv("MU_MODULE_PATH", pathJoin(self.rootPath, "RV", "Mu"),
                   conflict="add")

        elif sAppName in ("python", "pythonw", "eclipse", "splitall"):

            print "\nLoading {} environment:".format(sAppName.capitalize())

            self.updEnv("Z2K_PYTHON_SITES", pathJoin(self.thirdPartyPath, "_python27_site"),
                   conflict="add")

        elif sAppName.lower().startswith("nuke"):

            print "\nLoading {} environment:".format(sAppName.capitalize())

            self.updEnv("NUKE_PATH", pathJoin(self.rootPath, "nuke"), conflict="add")

        print ""

    def updEnv(self, sVar, in_value, **kwargs):
        return updEnv(sVar, in_value, record=self.envRecord, **kwargs)

    def installPath(self, location=""):

        if location:
            return pathJoin(location, BASE_NAME)

        return osp.expandvars(pathJoin(os.environ["Z2K_INSTALL_LOC"], BASE_NAME))

    def install(self, sInstallPath):

        return self._makeCopy(self.rootPath, sInstallPath)

    def update(self):
        
        if self.isDev:
            #print "Not able to update a dev toolkit."
            return False
        
        sReleasePath = osp.expandvars(pathJoin(os.environ["Z2K_RELEASE_LOC"], BASE_NAME))
        return self._makeCopy(sReleasePath, self.rootPath)

    def _makeCopy(self, sReleasePath, sInstallPath):

        bBeenUpdated = False

        if normAll(sReleasePath) == normAll(sInstallPath):
            raise EnvironmentError("Same source and destination path:\n    '{}' = '{}'\n"
                                   .format(sReleasePath, sInstallPath))

        bToPublicTool = pathInPublicTools(sInstallPath)
        if bToPublicTool:
            raise EnvironmentError("Not allowed to copy to '{}'\n".format(sInstallPath))

        sAction = "Installing"
        if osp.exists(sInstallPath):
            sAction = "Updating"
            bBeenUpdated = True
        else:
            os.makedirs(sInstallPath)

        sMsgFmt = "\n{} Z2K Toolkit:\n'{}' -> '{}'"
        print sMsgFmt.format(sAction, sReleasePath, sInstallPath)

        sOutput = self.roboCopy(sReleasePath, sInstallPath,
                                dryRun=True, summary=False)
        if not sOutput.strip():
            print " No changes ! ".center(120, "-"), "\n"
            return False

        if not pathInUserProfile(sInstallPath):
            res = raw_input("Continue ? (yes/no)")
            if res != "yes":
                return False

        self.roboCopy(sReleasePath, sInstallPath)

        cleanUpPyc(sInstallPath)

        print sMsgFmt.format(sAction.replace("ing", "ed"), sReleasePath, sInstallPath)

        return bBeenUpdated

    def release(self, sReleaseLoc, archive=None):

        if not self.isDev:
            raise EnvironmentError("Sorry, you are NOT in DEV environment !")

        sReleasePath = mkReleasePath(sReleaseLoc)
        bToPublicTool = pathInPublicTools(sReleaseLoc)
        if bToPublicTool:
            bReleaseOk = True if os.environ.get("Z2K_RELEASE_ALLOWED") else False
            if (not bReleaseOk):
                raise EnvironmentError("Not allowed to release.")

            if self.dirName != MASTER_NAME:
                raise EnvironmentError("Not allowed to release\nfrom '{}' to '{}'\n"
                                       .format(self.rootPath, sReleasePath))

        if osp.exists(sReleasePath):
            bUpdating = True
            sAction = "Updating"
        else:
            bUpdating = False
            sAction = "Creating"
            os.makedirs(sReleasePath)

        if bUpdating:
            sOutput = self.roboCopy(self.rootPath, sReleasePath, dryRun=True, summary=False)
            if not sOutput.strip():
                print " No changes ! ".center(120, "-"), "\n"
                return True

            print '\n', " Changes ".center(120, "-")
            print sOutput

            if archive is None:
                print ("\n{} toolkit release:\n'{}' -> '{}'\n"
                       .format(sAction, self.rootPath, sReleasePath))
                sChoiceList = ("yes", "no", "cancel")
                res = ""
                while res not in sChoiceList:
                    res = raw_input("Archive current release ? ({})".format('/'.join(sChoiceList)))
                    if res == "cancel":
                        return False
                archive = True if res == "yes" else False
            else:
                sNoArchive = "" if archive else " (no archiving)"
                print ("\n{} toolkit release{}:\n'{}' -> '{}'\n"
                       .format(sAction, sNoArchive, self.rootPath, sReleasePath))
                res = raw_input("Continue ? (ok/cancel)")
                if res != "ok":
                    return False

            if archive:
                sDate = datetime.now().strftime("%Y%m%d-%H%M")
                sZipPath = pathJoin(sReleasePath + "_backups", BASE_NAME + "_" + sDate)

                cleanUpPyc(sReleasePath)

                logger = initLogger()
                make_archive(sZipPath , "zip",
                             root_dir=osp.dirname(sReleasePath),
                             base_dir=pathJoin('.', osp.basename(sReleasePath)),
                             logger=logger, dry_run=False)

        sOscarPath = pathJoin(sReleasePath, "maya_mods", "Toonkit_module",
                              "Maya2016", "Standalones", "OSCAR")

        if not os.path.exists(sOscarPath):
            os.makedirs(sOscarPath)

        res = self.roboCopy(self.rootPath, sReleasePath)

        if bToPublicTool:
            enableToolSync()

        return res

    def roboCopy(self, sSrcRepoPath, sDestPath, dryRun=False, summary=True):

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
                         "pull_all.bat", "release.bat", "cifs*", ".DS_Store"]
        if not self.isDev:
            sExcludeFiles += ["setup_*.bat"]

        sExcludeFiles = '" "'.join(sExcludeFiles)

        cmdLineFmt = 'robocopy {0} /FFT /S {1} /NDL /NJH /MIR *.* "{2}" "{3}" /XD "{4}" .git tests /XF "{5}"'
        cmdLine = cmdLineFmt.format(sDryRun,
                                    sNoSummary,
                                    sSrcRepoPath,
                                    sDestPath,
                                    sOscarPath,
                                    sExcludeFiles)

        if (not dryRun) and self.isDev:
            print cmdLine

        return callCmd(cmdLine, catchStdout=dryRun)

    def writeEnv(self, sFilePath):

        if not self.envRecord:
            print "WARNING: No environment was recorded !"
            return

        with open(sFilePath, "w+") as f:

            f.write("\n")

            for k, v in self.envRecord.iteritems():

                bMultiLine = False
                if isinstance(v, basestring):

                    v = re.sub(r"\$(\w+)", r"%\1%", osp.normpath(v))

                    if "xgen" in k.lower():
                        v = v.replace("\\", "/")

                    if os.pathsep in v:
                        bMultiLine = True
                        sSep = ';^\n'
                        v = sSep.join(v.split(os.pathsep))

                if bMultiLine:
                    sLine = '\nset ^"{}=^\n{}^"\n\n'.format(k, v)
                else:
                    sLine = 'set "{}={}"\n'.format(k, v)

                f.write(sLine)

    def _resolvedArgs(self, appArgs):

        appArgs = list(osp.expandvars(a) for a in appArgs)

        sAppPath = osp.normpath(appArgs[0])

        if ("/" in sAppPath) or ("\\" in sAppPath):
            sAppPath = osp.expandvars(sAppPath)
            if not osp.isfile(sAppPath):
                raise EnvironmentError("No such application found: '{}'".format(sAppPath))

        elif sAppPath.startswith("@"):
            sAppName = sAppPath.strip("@").lower()
            sAppPath = getAppPath(sAppName)
            appArgs[0] = sAppPath

        return appArgs

    def launchApp(self, appArgs):

        if self.isDev:
            print appArgs

        status = callCmd(appArgs)
        if status:
            print "Application failed with status {}:".format(status)
            pprint(appArgs)
        return status

    def runFromCmd(self):

        sSetupEnvToolPath = osp.normpath(sys.argv[0])
        self.updEnv("Z2K_LAUNCH_SCRIPT", osp.normpath(sys.argv[0]))

        launcherArgs = [sys.executable] + sys.argv
        self.updEnv("Z2K_LAUNCHER_CMD", subprocess.list2cmdline(launcherArgs))

        cmdArgs = sys.argv[1:]
        sAction = ""
        sActionList = ("install", "launch", "release", "envtofile")
        appArgs = []
        if len(sys.argv) > 2:
            sAction = sys.argv[1]
            if sAction in ("launch",):# "envtofile"):
                cmdArgs = sys.argv[1:2]
                c = 2
                for arg in sys.argv[2:]:
                    if ("/" in arg) or ("\\" in arg) or (arg.startswith("@")):
                        break
                    cmdArgs.append(arg)
                    c += 1

                appArgs = sys.argv[c:]

        parser = argparse.ArgumentParser()
        parser.add_argument("action", choices=sActionList)

        ns = parser.parse_args(cmdArgs if not sAction else [sAction])

        sAction = ns.action
        bLaunch = (sAction == "launch")
        bWriteEnv = (sAction == "envtofile")

        sNormRootPath = normAll(self.rootPath)
        if (not self.isDev) and (bLaunch or bWriteEnv):
            if not pathInUserProfile(sNormRootPath):
                raise EnvironmentError("Apps can NOT be LAUNCHED from '{}' !"
                                       .format(osp.normpath(self.rootPath)))

        if osp.normcase(self.dirName) == osp.normcase(MASTER_NAME):
            if sAction != "release":
                raise EnvironmentError("You can NOT {} from '{}'. Only 'release' action allowed."
                                       .format(sAction, self.rootPath))

#        elif (sNormRootPath == normAll(mkReleasePath(fail=False)) or
#              normAll("/zomb/tool/" + BASE_NAME) in sNormRootPath):
#            if sAction != "install":
#                raise EnvironmentError("You can NOT {} from '{}'. Only 'install' action allowed."
#                                       .format(sAction, self.rootPath))

        if (bLaunch or bWriteEnv):
            if bWriteEnv:
                parser.add_argument("filename", type=str)
                parser.add_argument("--application", "-app", type=str)

            parser.add_argument("--update", "-u", type=int, default=1)
            parser.add_argument("--renew", "-r", type=int, default=0)
            ns = parser.parse_args(cmdArgs, ns)

            if bWriteEnv and ns.application:
                appArgs.append(ns.application)

            if ns.update:
                bUpdated = False
                try:
                    bUpdated = self.update()
                except Exception as err:
                    print ("\n\n!!!!!!! Failed updating toolkit: {}".format(err))
                    if raw_input("\nPress enter to continue...") == "raise": raise

                #print "bUpdated", bUpdated
                if bUpdated and bLaunch:
                    sMsg = """
#===============================================================================
# Tools updated so let's relaunch...
#===============================================================================
                        """
                    relaunchArgs = ([sys.executable] + sys.argv[:c] +
                                    ["--update", "0", "--renew", "1"] + appArgs)
                    print sMsg
#                    print sys.argv[:c]
#                    print appArgs
                    print relaunchArgs

                    if bLaunch:
                        return subprocess.call(relaunchArgs, shell=True)

            if ns.renew:
                self.envRecord.clear()
                self.loadEnv(self.customEnvs, replace=True)

            if bLaunch or (bWriteEnv and len(appArgs)):
                appArgs = self._resolvedArgs(appArgs)

                sAppPath = appArgs[0]
                try:
                    self.loadAppEnv(sAppPath)
                except Exception as e:
                    sAppName = osp.basename(sAppPath).rsplit(".", 1)[0]
                    print ("\n\n!!!!!!! Failed loading '{}' environments: {}"
                           .format(sAppName, e))
                    traceback.print_exc()
                    if raw_input("\nPress enter to continue anyway...") == "raise": raise

            if bLaunch:
                return self.launchApp(appArgs)
            elif bWriteEnv:
                return self.writeEnv(ns.filename)

        elif sAction == "install":
            parser.add_argument("--location", "-l", type=str, default="")
            ns = parser.parse_args(cmdArgs, ns)

            sInstallPath = self.installPath(location=ns.location)
            self.install(sInstallPath)

            if (not self.isDev) and sys.stdin.isatty() and sys.stdout.isatty():
                p = normPath(sInstallPath + sSetupEnvToolPath.split(BASE_NAME, 1)[1])
                showPathInExplorer(p, isFile=True, select=True)

        elif sAction == "release":
            parser.add_argument("location", type=str)
            parser.add_argument("--archive", "-a", type=int, default=None)
            ns = parser.parse_args(cmdArgs, ns)

            sReleaseLoc = osp.expandvars(ns.location)
            self.release(sReleaseLoc, archive=ns.archive)

CREATE_NO_WINDOW = 0x8000000

def callCmd(cmdArgs, catchStdout=False, shell=False, inData=None, noCmdWindow=False):

    iCreationFlags = CREATE_NO_WINDOW if noCmdWindow else 0

    startupinfo = subprocess.STARTUPINFO()
    #startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.dwXCountChars = 200
    startupinfo.dwYCountChars = 3000

    pipe = subprocess.Popen(cmdArgs, shell=shell,
                            stdout=subprocess.PIPE if catchStdout else None,
                            stderr=subprocess.STDOUT if catchStdout else None,
                            creationflags=iCreationFlags,
                            startupinfo=startupinfo)
    if catchStdout:
        outData, errData = pipe.communicate(inData)
        if errData and errData.strip():
            pprint(cmdArgs)
            raise subprocess.CalledProcessError(errData)
        return outData
    else:
        status = pipe.wait()
        return status

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

def updEnv(sVar, in_value, conflict='replace', usingFunc=None, record=None):

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
    if usingFunc:
        usingFunc(sVar, newValue)
    else:
        os.environ[sVar] = newValue

    if record is not None:
        record[sVar] = newValue

def makePrivatePath(sPublicPath):

    sPrivZombPath = os.environ["ZOMB_PRIVATE_LOC"]
    sDirName = osp.basename(sPublicPath)
    return pathJoin(sPrivZombPath, sDirName)

def normPath(p):
    return osp.normpath(p).replace("\\", "/")

def normCase(p):
    return osp.normcase(p).replace("\\", "/")

def normAll(p):
    return osp.normcase(osp.normpath(p)).replace("\\", "/")

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

def enableToolSync(dryRun=False):

    sToolDbPath = "/zomb/tool"

    if not dryRun:
        sToolPath = os.environ["ZOMB_TOOL_PATH"]
        if not (os.environ.get("Z2K_RELEASE_ALLOWED") and 
                normAll(sToolPath).endswith(sToolDbPath)):
            print "\n", "Sync can NOT be enabled on {}".format(sToolPath)
            return False

    from davos.core.damproject import DamProject
    proj = DamProject("zombillenium", shotgun=False, checkTemplates=False)
    
    dbnode = proj._db.findOne("file:{}".format(sToolDbPath))
    data = {}#dict(("synced_" + sSite, None) for sSite in proj.listAllSites())

    tmpNode = proj._db.createNode({"temp_node":1})
    try:
        data.update(tmpNode.getData("time", "author"))
        if not dryRun:
            dbnode.setData(data)
            print dbnode.dataRepr()
    finally:
        tmpNode.delete()

    sUrl = ("https://zombi.damas.io:8444/console#search={}".format(sToolDbPath))
    webbrowser.open(sUrl, new=2)#2 = new tab

    return True

def showPathInExplorer(p, isFile=False, select=False):

    p = osp.normpath(p)

    if not osp.exists(p):
        sPathType = "file" if isFile else "directory"
        raise EnvironmentError("No such {} found: {}".format(sPathType, p))

    sCmd = "explorer /select, {}" if isFile or select else "explorer {}"
    sCmd = sCmd.format(p)
    subprocess.Popen(sCmd, shell=True)

    return True
