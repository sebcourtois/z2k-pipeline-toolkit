#!/usr/bin/python
# -*- coding: utf-8 -*-
# RELEAZE ALADIN ----> rub the lamp and wait the genius to show the right asset check style!
# WIP
# show and set the good GUI depending on context (the scene path)

#!/usr/bin/python
# -*- coding: utf-8 -*-
################################################################
# Name    : Z2K_ReleaseTool_ALADIN_LAMP
# Version : 001
# Description : rub the lamp and wait the genius to show the right asset check style!
#               show and set the good check GUI depending on context (the scene path)
# Author : Jean-Philippe Descoins
# Date : 2014-04-01
# Comment : WIP
# To Do:
# - allow releaseTool to show up if no specifique check_GUI match the case
# - Force it to refresh when the scene is closed-opened-saved- maybe close it when released
# - handle the problem of from version: (when read-only: ok, when edit-> publish or make version= version-1) 
################################################################
#    ! Toute utilisation de ce se script sans autorisation     #
#                         est interdite !                      #
#    ! All use of this script without authorization is         #
#                           forbidden !                        #
#                                                              #
#                                                              #
#                 © Jean-Philippe Descoins                     #
################################################################



import os
import maya.cmds as cmds
import dminutes.jipeLib_Z2K as jpZ
reload(jpZ)

import dminutes.Z2K_ReleaseTool.Z2K_ReleaseTool as z2kR
reload (z2kR)




# get zomb project
curproj = os.environ.get("DAVOS_INIT_PROJECT")
print curproj


def RELEAZE_ALADIN():
    # extract interesting info: AssetType - assetCat - current file version -
    infoDict = jpZ.infosFromMayaScene()
    print "infoDict=", infoDict 
    if infoDict:
        # instanciate releaze tool with the right parameters
        Z2K_ReleaseTool_GuiI = z2kR.Z2K_ReleaseTool_Gui(sourceAsset=infoDict["assetName"], SourceAssetType=infoDict["assetType"]+"_scene", assetCat = infoDict["assetCat"],
                            destinationAsset=infoDict["assetName"], destinationAssetType= infoDict["assetType"]+"_ref",
                            projConnectB= True, theProject=curproj,
                            theComment= "released From " + infoDict["version"] ,
                            debug=False,
                            )


        Z2K_ReleaseTool_GuiI.createWin()


    else:
        raise Exception("THIS SCENE IS NOT RELEASABLE! ")


RELEAZE_ALADIN()