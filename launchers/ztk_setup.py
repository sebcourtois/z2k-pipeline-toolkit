
import os
import os.path as osp
import subprocess
import argparse

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
        repo = osp.join(os.environ["ZOMBI_TOOL_PATH"], self.dirName)
        if self.isDev:
            print "Tools update from development environment !"
            repo = self.rootPath

        local_root = osp.join(os.environ["USERPROFILE"], "zombillenium", self.dirName)

        if repo == local_root:
            print "Source == Destination !"
        else:
            print "Updating Zombie toolkit ! ({0}=>{1})".format(repo, local_root)

            oscarPath = osp.join(repo, "maya_mods", "Toonkit_module", "Maya2016", "Standalones", "OSCAR")

            cmdLine = ("robocopy /S /NFL /NDL /NJH /MIR *.* {0} {1} /XD {2} .git tests /XF {3} *.pyc .git* .*project"
                        .format(repo, local_root, oscarPath, "setup_*.bat" if not self.isDev else ""))
            subprocess.call(cmdLine)

            print "Zombie toolkit updated, use your local to launch applications ! ({0})".format(osp.join(local_root, "launchers"))

    def callCmd(self, args, update=True):

        self.loadEnvs()

        if (not self.isDev) and update:
            self.install()

        subprocess.call(args, shell=self.isDev)

    def runFromCmd(self):

        parser = argparse.ArgumentParser()
        parser.add_argument("command", choices=("install", "call"))
        parser.add_argument("--update", "-u", type=int, default=1)

        ns, args = parser.parse_known_args()

        sCmd = ns.command
        if sCmd == "call":
            self.callCmd(args, update=ns.update)
            return

        if sCmd == "install":
            self.install()

if __name__ == "__main__":
    try:
        Z2kToolkit().runFromCmd()
    except:
        os.environ["PYTHONINSPECT"] = "1"
        raise

