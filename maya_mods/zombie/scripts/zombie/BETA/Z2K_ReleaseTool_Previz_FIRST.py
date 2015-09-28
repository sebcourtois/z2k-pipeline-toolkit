#!/usr/bin/python
# -*- coding: utf-8 -*-

import dminutes.Z2K_ReleaseTool.Z2K_ReleaseTool as z2kR
reload (z2kR)

import dminutes.Z2K_ReleaseTool.modules.Z2K_Asset_Previz_checks as Z2K_PcheckD
reload(Z2K_PcheckD)

import dminutes.Z2K_ReleaseTool.modules.Z2K_replaceWithCustomFile as Z2K_replace
reload(Z2K_replace)


Z2K_ReleaseTool_GuiI = z2kR.Z2K_ReleaseTool_Gui(sourceAsset="chr_aurelien_manteau", SourceAssetType="previz_scene", assetCat = "chr",
                        destinationAsset="chr_aurelien_manteau", destinationAssetType= "previz_ref",
                        projConnectB= True, theProject="zombtest",
                        theComment= "auto rock the casbah release !",
                        debug=False )
Z2K_ReleaseTool_GuiI.createWin()


Z2K_replaceI = Z2K_replace.Z2K_replaceWithCustomFile_GUI()
Z2K_replaceI.insertLayout( parent=Z2K_ReleaseTool_GuiI.layoutImportModule )



Z2K_Pcheck = Z2K_PcheckD.checkModule()
Z2K_Pcheck.insertLayout( parent=Z2K_ReleaseTool_GuiI.layoutImportModule )


