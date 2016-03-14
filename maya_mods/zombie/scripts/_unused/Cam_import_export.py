import os
import maya.cmds
import dminutes.jipeLib_Z2K as jpZ
reload(jpZ)
import dminutes.camImpExp as camIE
reload(camIE)

camImpExpI = camIE.camImpExp()
camImpExpI.createWindow()