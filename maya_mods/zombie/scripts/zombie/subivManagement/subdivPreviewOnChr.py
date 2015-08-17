import maya.cmds as mc

from dminutes import assetconformation
reload(assetconformation)

assetconformation.previewSubdiv(enable = True, filter = "chr_")