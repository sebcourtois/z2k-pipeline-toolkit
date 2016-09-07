import maya.cmds as cmds

try:
    cmds.select("chr*:set_control")
except:
	cmds.select("*set_control")
