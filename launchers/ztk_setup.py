
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

BASE_NAME = "z2k-pipeline-toolkit"

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

class Z2kToolkit(object):

    def __init__(self, customEnvs=None):

        sCurDirPath = normPath(osp.dirname(osp.abspath(__file__)))

        sRoot, sTail = sCurDirPath.split(BASE_NAME)
        sDirName = BASE_NAME + sTail.split("/", 1)[0]

        sRootPath = pathJoin(sRoot, sDirName)
        if not osp.isdir(sRootPath):
            raise EnvironmentError("No such directory: '{}'".format(sRootPath))

        self.isDev = osp.isdir(pathJoin(sRootPath, ".git"))
        self.rootPath = sRootPath
        self.dirName = sDirName
        self.pythonPath = pathJoin(sRootPath, "python")
        self.thirdPartyPath = pathJoin(sRootPath, "third-party")

        self.customEnvs = customEnvs
        if customEnvs:
            self.loadEnvs(customEnvs)

    def loadEnvs(self, customEnvs, replace=False):

        print "Tools repository"
        print " - path          : {0}".format(self.rootPath)
        print " - configuration : {0}".format("Development" if self.isDev else "Production")
        print ""

        print "\nLoading site-defined environment:"

        sConflictMode = "replace" if replace else "keep"

        for sVar, value in customEnvs.iteritems():
            updEnv(sVar, value, conflict=sConflictMode)

        print "\nLoading toolkit environment:"

        sZtkSetupLoc = osp.dirname(__file__)
        updEnv("PYTHONPATH", sZtkSetupLoc, conflict="add")
        sys.path.append(sZtkSetupLoc)

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

        #python site so PySide is found and DamProject can be instantiated
        sPy27SitePath = pathJoin(self.thirdPartyPath, "_python27_site")
        site.addsitedir(sPy27SitePath)

        updEnv("DAVOS_CONF_PACKAGE", "zomblib.config", conflict=sConflictMode)
        updEnv("DAVOS_INIT_PROJECT", "zombillenium", conflict=sConflictMode)

        if "DEV_MODE_ENV" not in os.environ:
            os.environ["DEV_MODE_ENV"] = str(int(self.isDev))

    def loadAppEnvs(self, sAppPath):

        sAppPath = sAppPath.lower()
        sAppName, _ = osp.splitext(osp.basename(sAppPath))

        #print "\n----------------", sAppPath

        # initializing an empty DamProject to have project's environ loaded
        from davos.core.damproject import DamProject
        proj = DamProject(os.environ["DAVOS_INIT_PROJECT"], empty=True)
        proj.loadEnviron()

        if sAppName in ("maya", "mayabatch", "render", "mayapy"):

            print "\nLoading Maya environment:"

            updEnv("MAYA_MODULE_PATH", pathJoin(self.rootPath, "maya_mods"),
                   conflict="add")

            if "maya2016" in sAppPath:

                updEnv("Z2K_PYTHON_SITES", pathJoin(self.thirdPartyPath, "_mayapy2016_site"),
                       conflict="add")

        elif sAppName in ("rv", "rvpush"):

            print "\nLoading RV environment:"

            updEnv("MU_MODULE_PATH", pathJoin(self.rootPath, "RV", "Mu"),
                   conflict="add")

        elif sAppName in ("python", "pythonw", "eclipse", "splitall"):

            print "\nLoading {} environment:".format(sAppName.capitalize())

            updEnv("Z2K_PYTHON_SITES", pathJoin(self.thirdPartyPath, "_python27_site"),
                   conflict="add")

#        if bNeedPy27Site:
#            updEnv("Z2K_PYTHON_SITES", pathJoin(self.thirdPartyPath, "_python27_site"),
#                   conflict="add")
        print ""

    def install(self):

        bBeenUpdated = False

        # tools update
        sReleasePath = self.releasePath()
        if self.isDev:
            print "Tools update from development environment !"
            sReleasePath = self.rootPath

        sInstallPath = pathJoin(os.environ["USERPROFILE"], "zombillenium", BASE_NAME)

        if sReleasePath == sInstallPath:
            print "Source == Destination !"
        else:
            sAction = "Installing"
            if osp.exists(sInstallPath):
                sAction = "Updating"
                bBeenUpdated = True
            else:
                os.makedirs(sInstallPath)

            print "\n{} Z2K Toolkit:\n'{}' -> '{}'".format(sAction, sReleasePath, sInstallPath)

            sOutput = self.makeCopy(sReleasePath, sInstallPath,
                                    dryRun=True, summary=False)
            if not sOutput.strip():
                print "\nNo changes !"
                return False

            self.makeCopy(sReleasePath, sInstallPath)

            cleanUpPyc(sInstallPath)

            print ("Zombie toolkit updated, use your local to launch applications ! ({0})"
                   .format(pathJoin(sInstallPath, "launchers")))

        return bBeenUpdated

    def release(self, location="", archive=None):

        if not self.isDev:
            raise EnvironmentError("Sorry, you are not in DEV mode !")

        sDistroPath = self.releasePath(location)

        bReleaseOk = True if os.environ.get("ZTK_RELEASE_ALLOWED") else False
        if (not location) and (not bReleaseOk):
            raise EnvironmentError("Release of '{}' NOT allowed."
                                   .format(BASE_NAME))

        if osp.exists(sDistroPath):
            bUpdating = True
            sAction = "Updating"
        else:
            bUpdating = False
            sAction = "Creating"
            os.makedirs(sDistroPath)

        if bUpdating:
            sOutput = self.makeCopy(self.rootPath, sDistroPath,
                                    dryRun=True, summary=False)
            if not sOutput.strip():
                print "\nNo changes !"
                return True

            print '\n', " changes ".center(120, "-")
            print sOutput

            if archive is None:
                print ("\n{} toolkit release:\n'{}' -> '{}'\n"
                       .format(sAction, self.rootPath, sDistroPath))
                sChoiceList = ("yes", "no", "cancel")
                res = ""
                while res not in sChoiceList:
                    res = raw_input("Archive current release ? ({})".format('/'.join(sChoiceList)))
                    if res == "cancel":
                        return False
                archive = True if res == "yes" else False
            else:
                sNoArchive = "" if archive else " (without archive)"
                print ("\n{} toolkit release{}:\n'{}' -> '{}'\n"
                       .format(sAction, sNoArchive, self.rootPath, sDistroPath))
                res = raw_input("Continue ? (yes/no)")
                if res != "yes":
                    return False

            if archive:
                sDate = datetime.now().strftime("%Y%m%d-%H%M")
                sZipPath = pathJoin(sDistroPath + "_backups", BASE_NAME + "_" + sDate)

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

        res = self.makeCopy(self.rootPath, sDistroPath)

        enableToolSync()

        return res

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

    def releasePath(self, location="", fail=True):

        if location:
            sReleaseLoc = location
        else:
            sReleaseLoc = os.environ["ZOMB_TOOL_PATH"]

        if not osp.isdir(sReleaseLoc):
            if fail:
                raise EnvironmentError("No such release location: '{}'".format(sReleaseLoc))
            else:
                print "WARNING:", "No such release location: '{}'".format(sReleaseLoc)

        return pathJoin(sReleaseLoc, BASE_NAME)

    def launchApp(self, appArgs, launch=True):

        if (not launch) and not appArgs:
            return

        sAppPath = osp.normpath(appArgs[0])

        if ("/" in sAppPath) or ("\\" in sAppPath):
            sAppPath = osp.expandvars(sAppPath)
            sAppName = osp.basename(sAppPath).rsplit(".", 1)[0]
            if not osp.isfile(sAppPath):
                raise EnvironmentError("No such application found: '{}'".format(sAppPath))

        elif sAppPath.startswith("@"):
            sAppName = sAppPath.strip("@").lower()
            sAppPath = getAppPath(sAppName)
            appArgs[0] = sAppPath

        try:
            self.loadAppEnvs(sAppPath)
        except Exception as e:
            print ("\n\n!!!!!!! Failed loading '{}' environments: {}"
                   .format(sAppName, e))
            traceback.print_exc()
            if raw_input("\nPress enter to continue anyway...") == "raise": raise

#        startupinfo = subprocess.STARTUPINFO()
#        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
#        subprocess.call(appArgs, startupinfo=startupinfo)

        if self.isDev:
            print appArgs

        if launch:
            return callCmd(appArgs)

    def runFromCmd(self):

        launcherArgs = [sys.executable] + sys.argv
        updEnv("Z2K_LAUNCHER_CMD", subprocess.list2cmdline(launcherArgs))
        updEnv("Z2K_LAUNCH_SCRIPT", osp.normpath(sys.argv[0]))

        cmdArgs = sys.argv[1:]
        sAction = ""
        sActionList = ("install", "launch", "release", "loadenv")
        launchArgs = []
        if len(sys.argv) > 2:
            sAction = sys.argv[1]
            if sAction in ("launch", "loadenv"):
                cmdArgs = sys.argv[1:2]
                c = 2
                for arg in sys.argv[2:]:
                    if ("/" in arg) or ("\\" in arg) or (arg.startswith("@")):
                        break
                    cmdArgs.append(arg)
                    c += 1

                launchArgs = sys.argv[c:]

        parser = argparse.ArgumentParser()
        parser.add_argument("action", choices=sActionList)

        ns = parser.parse_args(cmdArgs if not sAction else [sAction])

        sAction = ns.action

        if self.dirName.endswith("_master"):
            if sAction != "release":
                raise EnvironmentError("You can't {} from location: '{}'. Only 'release' action allowed."
                                       .format(sAction, self.rootPath))
        elif osp.normcase(self.rootPath) == osp.normcase(self.releasePath(fail=False)):
            if sAction != "install":
                raise EnvironmentError("You can't {} from location: '{}'. Only 'install' action allowed."
                                       .format(sAction, self.rootPath))

        if sAction in ("launch", "loadenv"):
            parser.add_argument("--update", "-u", type=int, default=1)
            parser.add_argument("--renew", "-r", type=int, default=0)
            ns = parser.parse_args(cmdArgs, ns)

            if ns.update:
                bBeenUpdated = False
                try:
                    if (not self.isDev):
                        bBeenUpdated = self.install()
                except Exception as err:
                    print ("\n\n!!!!!!! Failed updating toolkit: {}".format(err))
                    if raw_input("\nPress enter to continue...") == "raise": raise

                #print "bBeenUpdated", bBeenUpdated
                if bBeenUpdated and sAction == "launch":
                    sMsg = """
#===============================================================================
# Tools updated so let's relaunch...
#===============================================================================
                        """
                    relaunchArgs = ([sys.executable] + sys.argv[:c] +
                                    ["--update", "0", "--renew", "1"] + launchArgs)
                    print sMsg
#                    print sys.argv[:c]
#                    print launchArgs
                    print relaunchArgs

                    if sAction == "launch":
                        return subprocess.call(relaunchArgs, shell=True)

            if ns.renew:
                self.loadEnvs(self.customEnvs, replace=True)

            return self.launchApp(launchArgs, launch=(sAction == "launch"))

        if sAction == "install":
            self.install()

        elif sAction == "release":
            parser.add_argument("--archive", "-a", type=int, default=None)
            parser.add_argument("--location", "-l", type=str, default="")
            ns = parser.parse_args(cmdArgs, ns)

            self.release(location=ns.location, archive=ns.archive)

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
        if not (os.environ.get("ZTK_RELEASE_ALLOWED") and 
                normAll(sToolPath).endswith(sToolDbPath)):
            print "\n", "Sync can NOT be enabled on {}".format(sToolPath)
            return False

    from davos.core.damproject import DamProject
    proj = DamProject("zombillenium")
    
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

