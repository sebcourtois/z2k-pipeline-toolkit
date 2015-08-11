import os
import sys
import subprocess

# Common envs, may be different for each studio
ENVS = {
		"ZOMBI_PRIVATE_PATH":'\\\\Diskstation\\Projects\\private\\${DAM_USER}\\zomb',
		"ZOMBI_TOOL_PATH":"\\\\Diskstation\\Projects\\zomb\\tool",
		"ZOMBI_ASSET_DIR":"\\\\Diskstation\\Projects\\zomb\\asset",
		"ZOMBI_SHOT_DIR":"\\\\Diskstation\\Projects\\zomb\\shot",
		"ZOMBI_OUTPUT_DIR":"\\\\Diskstation\\Projects\\zomb\\output",
		}

sCurDirPath, _ = os.path.split(os.path.abspath(__file__))

sToolDirName = "z2k-pipeline-toolkit"
TOOL_ROOT = os.path.join(sCurDirPath.split(sToolDirName)[0], sToolDirName)
isDev = os.path.isdir(os.path.join(TOOL_ROOT, ".git"))

def loadEnviron():

	print "Tools repository"
	print " - path          : {0}".format(TOOL_ROOT)
	print " - configuration : {0}".format("Development" if isDev else "Production")
	print ""

	print "Set environments"
	for envKey in ENVS:
		print " - SET {0} = {1}".format(envKey, ENVS[envKey])
		os.environ[envKey] = ENVS[envKey]

	# Python path
	pythonPathAdd = os.path.join(TOOL_ROOT, "python")
	pythonPathOld = "" if not "PYTHONPATH" in os.environ else os.environ["PYTHONPATH"]
	pythonPathNew = pythonPathAdd if pythonPathOld == "" else os.pathsep.join([pythonPathOld, pythonPathAdd])

	print " - SET {0} = {1}".format("PYTHONPATH", pythonPathNew)
	os.environ["PYTHONPATH"] = pythonPathNew

	# Maya module path
	modulePathAdd = os.path.join(TOOL_ROOT, "maya_mods")
	modulePathOld = "" if not "MAYA_MODULE_PATH" in os.environ else os.environ["MAYA_MODULE_PATH"]
	modulePathNew = modulePathAdd if modulePathOld == "" else os.pathsep.join([modulePathOld, modulePathAdd])

	print " - SET {0} = {1}".format("MAYA_MODULE_PATH", modulePathNew)
	os.environ["MAYA_MODULE_PATH"] = modulePathNew
	os.environ["DEV_MODE_ENV"] = str(int(isDev))

	print ""

def updateLocalCopy():

	# tools update
	repo = os.path.join(ENVS["ZOMBI_TOOL_PATH"], sToolDirName)

	if isDev:
		print "Tools update from development environment !"
		repo = TOOL_ROOT

	local_root = os.path.join(os.environ["USERPROFILE"], "zombillenium", sToolDirName)

	if repo == local_root:
		print "Source == Destination !"
	else:
		print "Updating Zombie toolkit ! ({0}=>{1})".format(repo, local_root)

		oscarPath = os.path.join(repo, "maya_mods", "Toonkit_module", "Maya2016", "Standalones", "OSCAR")
		cmdLine = ("robocopy /S /NFL /NDL /NJH /MIR *.* {0} {1} /XD {2} .git tests /XF {3}*.pyc .git* .*project"
					.format(repo, local_root, oscarPath, "setup.bat " if not isDev else ""))
		subprocess.call(cmdLine)

		print "Zombie toolkit updated, use your local to launch applications ! ({0})".format(os.path.join(local_root, "launchers"))

def launch(bSetEnvs, bUpdate, sAppPath=""):

	if bSetEnvs:
		loadEnviron()

	if bUpdate and not isDev:
		updateLocalCopy()

	if sAppPath:
		subprocess.call(sAppPath, shell=isDev)


if __name__ == '__main__':

	if len(sys.argv) < 3:
		msg = """
At least 2 arguments expected : 
	- SetEnvironments('True'/'False'), 
	- UpdateToolkit('True'/'False'), 
	- Application path ! ({0} given)""".format(len(sys.argv) - 1)

		raise ValueError(msg)

	bSetEnvs = False if sys.argv[1] != "True" else True
	bUpdate = False if sys.argv[2] != "True" else True
	sAppPath = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""

	print ""
	launch(bSetEnvs, bUpdate, sAppPath)
