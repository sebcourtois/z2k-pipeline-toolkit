
################################################################



import os
import maya.cmds as cmds
import dminutes.jipeLib_Z2K as jpZ
reload(jpZ)

import dminutes.Z2K_BS_Tertiaire_Connect as BS_connect
reload(BS_connect)

BS_connect.connectDialog()


