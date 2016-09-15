#  Select all controls of selected asset
import maya.cmds as cmds
import dminutes.jipeLib_Z2K as jpZ
reload(jpZ)
jpZ.selAll_asset_Ctr(setN="set_control")