#!/usr/bin/python
# -*- coding: utf-8 -*-
################################################################
# Name    : Z2K_BS_Tertiaire_Tool
# Version : 001
# Description : Tool facilitant le travail de connexion des blendShapes sur les personnages tertiaires
# Author : Jean-Philippe Descoins
# Date : 2015-12-11
# Comment : WIP
################################################################
#    ! Toute utilisation de ce se script sans autorisation     #
#                         est interdite !                      #
#    ! All use of this script without authorization is         #
#                           forbidden !                        #
#                                                              #
#                                                              #
#                 © Jean-Philippe Descoins                     #
################################################################

import os,sys
from functools import partial
import maya.cmds as cmds
import dminutes.jipeLib_Z2K as jpZ
reload(jpZ)

import dminutes.Z2K_BS_Tertiaire_Connect as BS_connect
reload(BS_connect)

import dminutes.Z2K_BS_Tertiaire_Check_mayaFile as BS_check
reload(BS_check)


# BS_check.checkDialog()
# BS_connect.connectDialog()



class Z2K_BS_Tertiaire_Tool_GUI (object):
    WNAME = "Z2K_BS_Tertiaire_Tools"
    version = "001"
    def __init__(self,*args, **kwargs):
        print "GUI_init"


    def createWin(self,*args,**kwargs):
        if cmds.window(self.WNAME, exists=True):
            cmds.deleteUI(self.WNAME)
        #create the window
        cmds.window(self.WNAME, title=self.WNAME+" v"+str(self.version), w=50,h=20, sizeable=0, tlb=0, mnb=True)
        #create layout
        cmds.frameLayout(lv=0)
        cmds.separator(3)
        cmds.text(self.WNAME.replace("_"," ")+":",font="boldLabelFont")
        cmds.tabLayout(tabsVisible=0,borderStyle="full")
        cmds.columnLayout(adj=1,rs=2)
        cmds.button("BS_File    : Check Naming correspondance".ljust(50),c= partial(BS_check.checkDialog,True),  )
        cmds.button("Asset_file : Connect imported BS to current asset".ljust(50),c= BS_connect.connectDialog,  )
        cmds.text(" info: Browse for the corresponding '.bsd' file ",)
        # show Window
        cmds.showWindow()


Z2K_BS_Tertiaire_Tool_GUII=Z2K_BS_Tertiaire_Tool_GUI()
Z2K_BS_Tertiaire_Tool_GUII.createWin()