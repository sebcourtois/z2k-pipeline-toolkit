import os
osp = os.path
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

print "Set environments"
for k, v in ENVS.iteritems():
	print " - SET {0} = {1}".format(k, v)
	os.environ[k] = v

sScriptPath = osp.join(osp.dirname(__file__), "..", "ztk_setup.py")
cmdArgs = [sys.executable, sScriptPath] + sys.argv[1:]
subprocess.call(cmdArgs)
