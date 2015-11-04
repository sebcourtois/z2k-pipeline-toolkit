#!/usr/bin/python
# -*- coding: utf-8 -*-
# A base de PREVIZ_PROP pour le moment
import os
import dminutes.Z2K_ReleaseTool.Z2K_ReleaseTool as z2kR
reload (z2kR)

import dminutes.Z2K_ReleaseTool.modules.Z2K_Previz_PROP_checks as Z2K_PcheckD
reload(Z2K_PcheckD)


# get zomb project
curproj = os.environ.get("DAVOS_INIT_PROJECT")
print curproj

Z2K_ReleaseTool_GuiI = z2kR.Z2K_ReleaseTool_Gui(sourceAsset="chr_aurelien_manteau", SourceAssetType="anim_scene", assetCat = "chr",
                        destinationAsset="chr_aurelien_manteau", destinationAssetType= "anim_ref",
                        projConnectB= True, theProject=curproj,
                        theComment= "auto rock the casbah release !",
                        debug=False,
                        )
Z2K_ReleaseTool_GuiI.createWin()

Z2K_Pcheck = Z2K_PcheckD.checkModule(GUI=True, parent=Z2K_ReleaseTool_GuiI.layoutImportModule )
