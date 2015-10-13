#!/usr/bin/python
# -*- coding: utf-8 -*-

import os

import dminutes.Z2K_ReleaseTool.modules.Z2K_ASSET_replacer as Z2K_replace
reload(Z2K_replace)

# get zomb project
curproj = os.environ.get("DAVOS_INIT_PROJECT")
print curproj


Z2K_replaceI = Z2K_replace.Z2K_ASSET_replacer_GUI(theProject=curproj,sourceSceneP="", replacingSceneP="")
Z2K_replaceI.insertLayout( parent="")



