import maya.cmds as cmds
import dminutes.jipeLib_Z2K as jpZ
reload(jpZ)
print jpZ.GetSel()
jpZ.resetCTR(inObjL=jpZ.GetSel(), userDefined=False, SRT=True, )