import os
osp = os.path
import sys
import subprocess

# Common envs, may be different for each studio
ENVS = {
		"ZOMB_PRIVATE_PATH":'\\\\Diskstation\\Projects\\private\\${DAVOS_USER}\\zomb',
		"ZOMB_TOOL_PATH":"\\\\Diskstation\\Projects\\zomb\\tool",
		"ZOMB_ASSET_PATH":"\\\\Diskstation\\Projects\\zomb\\asset",
		"ZOMB_SHOT_PATH":"\\\\Diskstation\\Projects\\zomb\\shot",
		"ZOMB_OUTPUT_PATH":"\\\\Diskstation\\Projects\\zomb\\output",
		}

print "Set environments"
for k, v in ENVS.iteritems():
	print " - SET {0} = {1}".format(k, v)
	os.environ[k] = v

sScriptPath = osp.join(osp.dirname(__file__), "..", "ztk_setup.py")
cmdArgs = [sys.executable, sScriptPath] + sys.argv[1:]
subprocess.call(cmdArgs)
