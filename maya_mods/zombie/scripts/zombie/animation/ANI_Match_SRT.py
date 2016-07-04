import dminutes.jipeLib_Z2K as jpm
reload(jpm)
import maya.cmds as cmds


cursel = cmds.ls(os=True)
jpm.matchByXformMatrix(cursel=cursel, mode="first")