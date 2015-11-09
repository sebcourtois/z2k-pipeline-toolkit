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

import dminutes.Z2K_ReleaseTool.modules.Z2K_Previz_PROP_checks as Z2K_Pcheck_PROP
reload(Z2K_Pcheck_PROP)
import dminutes.Z2K_ReleaseTool.modules.Z2K_Previz_CHAR_checks as Z2K_Pcheck_CHAR
reload(Z2K_Pcheck_CHAR)
import dminutes.Z2K_ReleaseTool.modules.Z2K_Previz_SET_checks as Z2K_Pcheck_SET
reload(Z2K_Pcheck_SET)


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

        # create releaseTool windows
        if not "Ref" in infoDict["assetType"][-3:] :
            Z2K_ReleaseTool_GuiI.createWin()
        else:

            raise Exception("THIS IS ALLREADY A REF FILE : THIS SCENE IS NOT RELEASABLE!")

        # insert le bon module de check dans l'interface
        Z2K_Pcheck="NADA"
        print 'infoDict["assetCat"]=',infoDict["assetCat"]
        # THIS IS FOR NOW ONLY OK FOR THE PREVIZ, IT DOESN'T TEST infoDict["assetType"] but only infoDict["assetCat"]
        if  infoDict["assetCat"] in ["chr"]:
            print "It' is a CHAR test"
            Z2K_Pcheck = Z2K_Pcheck_CHAR
        if  infoDict["assetCat"] in ["prp","vhl","c2d"]:
            print "It' is a PROP test"
            Z2K_Pcheck = Z2K_Pcheck_PROP
        if  infoDict["assetCat"] in ["set"]:
            print "It' is a SET test"
            Z2K_Pcheck = Z2K_Pcheck_SET

        if Z2K_Pcheck in ["NADA"]:
            raise Exception("PAS DE MODULE DE CHECK POUR CET ASSET")
        else:
            print "Z2K_Pcheck=", Z2K_Pcheck
            Z2K_Pcheck = Z2K_Pcheck.checkModule(GUI=True, parent=Z2K_ReleaseTool_GuiI.layoutImportModule )

    else:
        raise Exception("THIS SCENE IS NOT RELEASABLE! ")


RELEAZE_ALADIN()