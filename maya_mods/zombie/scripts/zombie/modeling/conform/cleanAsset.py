import maya.cmds as mc

from dminutes import modeling
reload(modeling)

from dminutes import assetconformation
reload(assetconformation)

from dminutes import rendering
reload (rendering)

from dminutes import miscUtils
reload (miscUtils)



# if mc.ls("|asset"):        
#     mainFilePath = mc.file(q=True, list = True)[0]
#     mainFilePathElem = mainFilePath.split("/")
#     if  mainFilePathElem[-4] == "asset":
#         privateMapdir = miscUtils.normPath(miscUtils.pathJoin("$PRIV_ZOMB_TEXTURE_PATH",mainFilePathElem[-3],mainFilePathElem[-2],"texture"))
#         privateMapdirExpand = miscUtils.normPath(os.path.expandvars(os.path.expandvars(privateMapdir)))
#         publicMapdir = miscUtils.normPath(miscUtils.pathJoin("$ZOMB_TEXTURE_PATH",mainFilePathElem[-3],mainFilePathElem[-2],"texture"))
#         publicMapdirExpand = miscUtils.normPath(os.path.expandvars(os.path.expandvars(publicMapdir)))
#     else:
#         raise ValueError("#### Error: you are not working in an 'asset' structure directory")
# else :
#     raise ValueError("#### Error: no '|asset' could be found in this scene")


# assetType = mainFilePathElem[-3]
# fileType = mainFilePathElem[-1].split("-")[0].split("_")[-1]

# possible file type exaustive list: ["anim", "modeling", "previz", "render", "master"]
# possible asset type exaustive list: ["c2d", "cam", "chr", "env", "fxp", "prp", "set", "vhl"]


answer =  mc.confirmDialog( title='Confirm', message="You are about to delete all the nodes that are not related to the asset structure, delete geometry history and clean the namespaces", button=['Proceed','Cancel'], defaultButton='Proceed', cancelButton='Cancel', dismissString='Cancel' )
if answer != "Cancel": 
	rendering.deleteAovs()
	#if fileType in ["anim", "modeling", "previz", "render", "master"] and assetType ["c2d", "cam", "chr", "env", "fxp", "prp", "set", "vhl"]:
	assetconformation.softClean()
	modeling.geoGroupDeleteHistory()
	modeling.makeAllMeshesUnique(inParent="|asset|grp_geo")
	modeling.meshShapeNameConform(inParent = "|asset|grp_geo")
	miscUtils.deleteUnknownNodes()