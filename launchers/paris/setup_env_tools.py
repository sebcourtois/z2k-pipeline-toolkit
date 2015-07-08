import os
import sys
import subprocess

#Common envs, may be different for each studio
ENVS = {
		"ZOMBI_TOOL_PATH":"\\\\Diskstation\\z2k\\05_3D\\zombillenium\\tool",
		"ZOMBI_ASSET_DIR":"\\\\Diskstation\\z2k\\05_3D\\zombillenium\\asset",
		"ZOMBI_SHOT_DIR":"\\\\Diskstation\\z2k\\05_3D\\zombillenium\\shot",
		"ZOMBI_OUTPUT_DIR":"\\\\Diskstation\\z2k\\05_3D\\zombillenium\\output",
		}


if len(sys.argv) < 3:
	raise Exception("At least 2 arguments expected : SetEnvironments('True'/'False'), UpdateToolkit('True'/'False'), Process path ! ({0} given)".format(len(sys.argv)-1))

setEnvs = False if sys.argv[1] != "True" else True
update = False if sys.argv[2] != "True" else True

print ""
dirname, filename = os.path.split(os.path.abspath(__file__))

toolFolder = "z2k-pipeline-toolkit"
TOOL_ROOT = os.path.join(dirname.split(toolFolder)[0], toolFolder)
isDev = os.path.isdir(os.path.join(TOOL_ROOT, ".git"))

if setEnvs:
	print "Tools repository"
	print " - path          : {0}".format(TOOL_ROOT)
	print " - configuration : {0}".format("Development" if isDev else "Production")
	print ""

	print "Set environments"
	for envKey in ENVS:
		print " - SET {0} = {1}".format(envKey, ENVS[envKey])
		os.environ[envKey] = ENVS[envKey]

	#Python path
	pythonPathAdd = os.path.join(TOOL_ROOT, "python")
	pythonPathOld = "" if not "PYTHONPATH" in os.environ else os.environ["PYTHONPATH"]
	pythonPathNew = pythonPathAdd if pythonPathOld=="" else ";".join([pythonPathOld, pythonPathAdd])

	print " - SET {0} = {1}".format("PYTHONPATH", pythonPathNew)
	os.environ["PYTHONPATH"] = pythonPathNew

	#Maya module path
	modulePathAdd = os.path.join(TOOL_ROOT, "maya_mods")
	modulePathOld = "" if not "MAYA_MODULE_PATH" in os.environ else os.environ["MAYA_MODULE_PATH"]
	modulePathNew = modulePathAdd if modulePathOld=="" else ";".join([modulePathOld, modulePathAdd])

	print " - SET {0} = {1}".format("MAYA_MODULE_PATH", modulePathNew)
	os.environ["MAYA_MODULE_PATH"] = modulePathNew

	print ""

if update:
	#tools update
	repo = os.path.join(ENVS["ZOMBI_TOOL_PATH"], toolFolder)

	if isDev:
		print "Tools update from development environment !"
		repo = TOOL_ROOT

	local_root = os.path.join(os.environ["USERPROFILE"], "zombillenium", toolFolder)

	if repo == local_root:
		print "Source == Destination !"
	else:
		print "Updating Zombie toolkit ! ({0}=>{1})".format(repo, local_root)

		oscarPath = os.path.join(repo, "maya_mods", "Toonkit_module", "Maya2016", "Standalones", "OSCAR")
		cmdLine = "robocopy /S /NFL /NDL /NJH /MIR *.* {0} {1} /XD {2} .git tests /XF {3}*.pyc .git* .*project".format(repo, local_root, oscarPath, "setup.bat " if not isDev else "")
		subprocess.call(cmdLine)

		print "Zombie toolkit updated, use your local to launch applications ! ({0})".format(os.path.join(local_root, "launchers"))

if len(sys.argv) > 3:
	subprocess.Popen(sys.argv[3])