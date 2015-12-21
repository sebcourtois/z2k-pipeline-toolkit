
################################################################



import os
import maya.cmds as cmds
import dminutes.jipeLib_Z2K as jpZ
reload(jpZ)

import dminutes.Z2K_BS_Tertiaire_Check_mayaFile as BS_check
reload(BS_check)

BS_check.checkDialog()
