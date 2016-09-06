import maya.cmds as cmds

try:
    cmds.select("chr*:set_meshCache")
except:
	cmds.select("*set_meshCache")
