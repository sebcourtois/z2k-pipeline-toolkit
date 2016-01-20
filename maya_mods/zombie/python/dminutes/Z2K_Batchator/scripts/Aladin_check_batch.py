
import os
import maya.cmds as cmds
import dminutes.jipeLib_Z2K as jpZ
reload(jpZ)

import dminutes.Z2K_ReleaseTool.Z2K_ReleaseTool_batchable as z2kR
reload (z2kR)




# get zomb project
curproj = os.environ.get("DAVOS_INIT_PROJECT")
print curproj




def RELEAZE_ALADIN_BATCH():
    result = False
    # extract interesting info: AssetType - assetCat - current file version -
    infoDict = jpZ.infosFromMayaScene()
    print "infoDict=", infoDict 
    if infoDict and not "Ref" in infoDict["assetType"][-3:] :

        # intanciate relaseClass
        Z2K_ReleaseToolI = z2kR.Z2K_ReleaseTool(sourceAsset=infoDict["assetName"], sourceAssetType=infoDict["assetType"]+"_scene", assetCat = infoDict["assetCat"],
                            destinationAsset=infoDict["assetName"], destinationAssetType= infoDict["assetType"]+"_ref",
                            projConnectB= True, theProject=curproj,
                            theComment= "released From " + infoDict["version"] ,
                            debug=False,
                            )

        # lauch the auto check swith function from daddy class
        Z2K_Pcheck,theDebugFile = Z2K_ReleaseToolI.Aladin_CheckSwitch()
        # parent the new good one
        print "STEP01"
        if Z2K_Pcheck in ["NADA"]:
            raise Exception("PAS DE MODULE DE CHECK POUR CET ASSET")
        else:
            print "Z2K_Pcheck=", Z2K_Pcheck
            Z2K_PcheckI = Z2K_Pcheck.checkModule(GUI=False, parent="", debugFile = theDebugFile )
            result = Z2K_PcheckI.btn_cleanAll()

            print "## ALADIN RESULT=", result


        # # instanciate releaze tool with the right parameters
        # Z2K_ReleaseTool_GuiI = z2kR.Z2K_ReleaseTool_Gui(sourceAsset=infoDict["assetName"], SourceAssetType=infoDict["assetType"]+"_scene", assetCat = infoDict["assetCat"],
        #                     destinationAsset=infoDict["assetName"], destinationAssetType= infoDict["assetType"]+"_ref",
        #                     projConnectB= True, theProject=curproj,
        #                     theComment= "released From " + infoDict["version"] ,
        #                     debug=False,
        #                     )


        # Z2K_ReleaseTool_GuiI.createWin()


    else:
        raise Exception("THIS SCENE IS NOT RELEASABLE! ")

    # output the result here
    return result

result = RELEAZE_ALADIN_BATCH()


