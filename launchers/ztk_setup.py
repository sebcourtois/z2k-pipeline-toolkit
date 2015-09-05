
import os
import os.path as osp
import subprocess
import argparse
from shutil import make_archive, ignore_patterns
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

    sPrivZombPath = os.environ["PRIV_ZOMB_PATH"]
    sDirName = osp.basename(sPublicPath)
    return osp.join(sPrivZombPath, sDirName)

def pathNorm(p):
    return osp.normpath(p).replace("\\", "/")

def pathJoin(*args):
    try:
        p = osp.join(*args)
    except UnicodeDecodeError:
        p = osp.join(*tuple(toUnicode(arg) for arg in args))

    return pathNorm(p)

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



class Z2kToolkit(object):

    envsToPrivate = (
    "ZOMB_ASSET_PATH",
    "ZOMB_SHOT_PATH",
    "ZOMB_OUTPUT_PATH",
    "ZOMB_TEXTURE_PATH",
    )

    def __init__(self, customEnvs):

        sDirName = "z2k-pipeline-toolkit"
        sCurDirPath = osp.dirname(osp.abspath(__file__))
        sRootPath = osp.join(sCurDirPath.split(sDirName)[0], sDirName)

        self.isDev = osp.isdir(osp.join(sRootPath, ".git"))
        self.rootPath = sRootPath
        self.dirName = sDirName

        self.loadEnvs(customEnvs)

    def loadEnvs(self, customEnvs):

        print "Tools repository"
        print " - path          : {0}".format(self.rootPath)
        print " - configuration : {0}".format("Development" if self.isDev else "Production")
        print ""

        print "\nLoading user-defined environments:"

        for sVar, value in customEnvs.iteritems():
            updEnv(sVar, value, conflict="keep")

        print "\nLoading toolkit environments:"

        updEnv("PYTHONPATH", osp.join(self.rootPath, "python"), conflict="add")
        updEnv("MAYA_MODULE_PATH", osp.join(self.rootPath, "maya_mods"), conflict="add")
        updEnv("DAVOS_CONF_PACKAGE", "zomblib.config", conflict="keep")
        updEnv("DAVOS_INIT_PROJECT", "zombillenium", conflict="keep")

        for sVar in self.__class__.envsToPrivate:

            sPubPath = osp.expandvars(os.environ[sVar])
            sPrivPath = makePrivatePath(sPubPath)

            if osp.normcase(sPubPath) == osp.normcase(sPrivPath):
                raise EnvironmentError("Same public and private path: {}='{}'"
                                       .format(sVar, sPrivPath))

            updEnv("PRIV_" + sVar, sPrivPath, conflict="keep")

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
            sOutput = self.makeCopy(repo, local_root,
                                    dryRun=False, summary=False)

            if not sOutput.strip():
                print "\nNo changes !"
                return

            print "\n", sOutput

            cleanUpPyc(local_root)

            print ("Zombie toolkit updated, use your local to launch applications ! ({0})"
                   .format(osp.join(local_root, "launchers")))

    def release(self, location="", archive=True):

        if not self.isDev:
            raise EnvironmentError("Sorry, you are not in DEV mode !")

        sDistroPath = self.releasePath(location)
        sOutput = self.makeCopy(self.rootPath, sDistroPath,
                                dryRun=True, summary=False)
        if not sOutput.strip():
            print "\nNo changes !"
            return

        if archive and osp.exists(sDistroPath):
            sDate = datetime.now().strftime("%Y%m%d-%H%M")
            sZipPath = osp.join(sDistroPath + "_backups", self.dirName + "_" + sDate)

            cleanUpPyc(sDistroPath)

            logger = initLogger()
            make_archive(sZipPath , "zip",
                         root_dir=osp.dirname(sDistroPath),
                         base_dir=osp.join('.', osp.basename(sDistroPath)),
                         logger=logger, dry_run=False)

        sOscarPath = osp.join(sDistroPath, "maya_mods", "Toonkit_module",
                              "Maya2016", "Standalones", "OSCAR")

        if not os.path.exists(sOscarPath):
            os.makedirs(sOscarPath)

        print self.makeCopy(self.rootPath, sDistroPath, dryRun=False)

    def makeCopy(self, sSrcRepoPath, sDestPath, dryRun=False, summary=True):

        print "Updating Zombie toolkit: \n'{0}' -> '{1}'".format(sSrcRepoPath, sDestPath)


        sOscarPath = osp.join(sSrcRepoPath, "maya_mods", "Toonkit_module",
                              "Maya2016", "Standalones", "OSCAR")

        sDryRun = "/L" if dryRun else ""
        sNoSummary = "/NJS" if not summary else ""

        cmdLineFmt = "robocopy {} /S {} /NDL /NJH /MIR *.* {} {} /XD {} .git tests /XF {} *.pyc .git* .*project *.lic Thumbs.db"
        cmdLine = cmdLineFmt.format(sDryRun,
                                    sNoSummary,
                                    sSrcRepoPath,
                                    sDestPath,
                                    sOscarPath,
                                    "setup_*.bat" if not self.isDev else "")
        #print cmdLine
        return runCmd(cmdLine)

    def releasePath(self, location=""):

        if location:
            sReleaseLoc = location
        else:
            sReleaseLoc = os.environ["ZOMB_TOOL_PATH"]

        return osp.join(sReleaseLoc, self.dirName)

    def launchCmd(self, args, update=True):

        if (not self.isDev) and update:
            self.install()

#        startupinfo = subprocess.STARTUPINFO()
#        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
#        subprocess.call(args, startupinfo=startupinfo)

        subprocess.call(args)#shell=self.isDev)

    def runFromCmd(self):

        parser = argparse.ArgumentParser()
        parser.add_argument("command", choices=("install", "launch", "release"))
        parser.add_argument("--update", "-upd", type=int, default=1)
        parser.add_argument("--archive", "-arc", type=int, default=1)
        parser.add_argument("--location", "-loc", type=str, default="")

        ns, args = parser.parse_known_args()

        sCmd = ns.command
        if sCmd == "launch":
            self.launchCmd(args, update=ns.update)
            return

        if sCmd == "install":
            self.install()
        elif sCmd == "release":
            self.release(location=ns.location, archive=ns.archive)

#if __name__ == "__main__":
#    try:
#        Z2kToolkit().runFromCmd()
#    except:
#        os.environ["PYTHONINSPECT"] = "1"
#        raise

