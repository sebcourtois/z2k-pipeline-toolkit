import maya.cmds as mc
import os

from dminutes import miscUtils
reload (miscUtils)
from dminutes import rendering
reload (rendering)
from dminutes import modeling
reload (modeling)
from dminutes import assetconformation
reload (assetconformation)
from dminutes import shading
reload (shading)

def cleanAsset (GUI = True):
    resultB = True
    logL = []

    if mc.ls("|asset"):        
        mainFilePath = mc.file(q=True, list = True)[0]
        mainFilePathElem = mainFilePath.split("/")
        if  mainFilePathElem[-4] == "asset" or mainFilePathElem[-5] == "asset":
            privateMapdir = miscUtils.normPath(miscUtils.pathJoin("$PRIV_ZOMB_TEXTURE_PATH",mainFilePathElem[-3],mainFilePathElem[-2],"texture"))
            privateMapdirExpand = miscUtils.normPath(os.path.expandvars(os.path.expandvars(privateMapdir)))
            publicMapdir = miscUtils.normPath(miscUtils.pathJoin("$ZOMB_TEXTURE_PATH",mainFilePathElem[-3],mainFilePathElem[-2],"texture"))
            publicMapdirExpand = miscUtils.normPath(os.path.expandvars(os.path.expandvars(publicMapdir)))
        else:
            raise ValueError("#### Error: you are not working in an 'asset' structure directory")
    else :
        raise ValueError("#### Error: no '|asset' could be found in this scene")


    assetType = mainFilePathElem[-3]
    fileType = mainFilePathElem[-1].split("-")[0].split("_")[-1]

    #possible file type exaustive list: ["anim", "modeling", "previz", "render", "master"]
    #possible asset type exaustive list: ["c2d", "cam", "chr", "env", "fxp", "prp", "set", "vhl"]


    baseMessageS="cleaning prosses will:\n    - delete AOVs,\n    - delete unknown nodes,\n    - fix materialInfo nodes,\n    - delete all color sets,"
    baseMessage2S ="cleaning prosses will:\n    - delete unknown nodes,\n    - fix materialInfo nodes,\n    - delete all color sets,"
    if GUI == False: answer = "Proceed"


    if fileType == "previz":
        if assetType in ["chr", "prp", "vhl"] :
            if GUI == True: answer =  mc.confirmDialog( title='clean '+fileType+' '+assetType+' asset', message=baseMessageS, button=['Proceed','Cancel'], defaultButton='Proceed', cancelButton='Cancel', dismissString='Cancel' )
            if answer != "Cancel": 
                rendering.deleteAovs()
                miscUtils.deleteUnknownNodes()
                assetconformation.fixMaterialInfo()
                miscUtils.deleteAllColorSet()
        elif assetType == "set":
            if GUI == True: answer =  mc.confirmDialog( title='clean '+fileType+' '+assetType+' asset', message=baseMessageS+"\n    - delete geo history,\n    - convert branch instanced to leaf instances,\n    - make all mesh unique,\n    - conform mesh shapes names, \n    - delete all unused nodes (not connected to an asset dag node)", button=['Proceed','Cancel'], defaultButton='Proceed', cancelButton='Cancel', dismissString='Cancel' )
            if answer != "Cancel":
                rendering.deleteAovs()
                miscUtils.deleteUnknownNodes()
                assetconformation.fixMaterialInfo()
                miscUtils.deleteAllColorSet()
                modeling.geoGroupDeleteHistory()
                modeling.convertBranchToLeafInstance(inParent ="grp_geo", GUI = True, mode = "convToLeaf" )
                modeling.makeAllMeshesUnique(inParent="|asset|grp_geo")
                modeling.meshShapeNameConform(inParent = "|asset|grp_geo")
                assetconformation.softClean(keepRenderLayers = False)
        elif assetType in ["c2d", "env", "fpx", "cwp"]:
            if GUI == True: answer =  mc.confirmDialog( title='clean '+fileType+' '+assetType+' asset', message=baseMessageS+"\n    - make all mesh unique,\n    - conform mesh shapes names, \n    - delete all unused nodes (not connected to an asset dag node)", button=['Proceed','Cancel'], defaultButton='Proceed', cancelButton='Cancel', dismissString='Cancel' )
            if answer != "Cancel":
                rendering.deleteAovs()
                miscUtils.deleteUnknownNodes()
                assetconformation.fixMaterialInfo()
                miscUtils.deleteAllColorSet()
                modeling.makeAllMeshesUnique(inParent="|asset|grp_geo")
                modeling.meshShapeNameConform(inParent = "|asset|grp_geo")
                assetconformation.softClean(keepRenderLayers = False)


    elif fileType == "modeling":
        if assetType == "chr" :
            if GUI == True: answer =  mc.confirmDialog( title='clean '+fileType+' '+assetType+' asset', message=baseMessageS+"\n    - delete geo history,\n    - make all mesh unique,\n    - conform mesh shapes names, \n    - delete all unused nodes (not connected to an asset dag node), render layers will not be removed", button=['Proceed','Cancel'], defaultButton='Proceed', cancelButton='Cancel', dismissString='Cancel' )
            if answer != "Cancel":
                rendering.deleteAovs()
                miscUtils.deleteUnknownNodes()
                assetconformation.fixMaterialInfo()
                miscUtils.deleteAllColorSet()
                modeling.geoGroupDeleteHistory()
                modeling.makeAllMeshesUnique(inParent="|asset|grp_geo")
                modeling.meshShapeNameConform(inParent = "|asset|grp_geo")
                assetconformation.softClean(keepRenderLayers = True)
        else:
            if GUI == True: answer =  mc.confirmDialog( title='clean '+fileType+' '+assetType+' asset', message=baseMessageS+"\n    - delete geo history,\n    - make all mesh unique,\n    - conform mesh shapes names, \n    - delete all unused nodes (not connected to an asset dag node)", button=['Proceed','Cancel'], defaultButton='Proceed', cancelButton='Cancel', dismissString='Cancel' )
            if answer != "Cancel":
                rendering.deleteAovs()
                miscUtils.deleteUnknownNodes()
                assetconformation.fixMaterialInfo()
                miscUtils.deleteAllColorSet()
                modeling.geoGroupDeleteHistory()
                modeling.makeAllMeshesUnique(inParent="|asset|grp_geo")
                modeling.meshShapeNameConform(inParent = "|asset|grp_geo")
                assetconformation.softClean(keepRenderLayers = False)


    elif fileType == "anim":
            if GUI == True: answer =  mc.confirmDialog( title='clean '+fileType+' '+assetType+' asset', message=baseMessageS, button=['Proceed','Cancel'], defaultButton='Proceed', cancelButton='Cancel', dismissString='Cancel' )
            if answer != "Cancel": 
                rendering.deleteAovs()
                miscUtils.deleteUnknownNodes()
                assetconformation.fixMaterialInfo()
                miscUtils.deleteAllColorSet()
                assetconformation.setSubdiv()



    elif fileType == "master":
            if GUI == True:
                msgS = baseMessage2S+"""
    - delete geo history,\n    - convert branch instanced to leaf instances,\n    - make all mesh unique,\n    - conform mesh shapes names,\n    - create set subdiv,\n    - apply set subdiv,    
    - delete all unused nodes (unconnected to an asset dag node), except render layers,\n    - conform all shaders names"""
                answer =  mc.confirmDialog( title='clean '+fileType+' '+assetType+' asset', message=msgS, button=['Proceed','Cancel'], defaultButton='Proceed', cancelButton='Cancel', dismissString='Cancel' )
            if answer != "Cancel":
                #rendering.deleteAovs()
                miscUtils.deleteUnknownNodes()
                assetconformation.fixMaterialInfo()
                miscUtils.deleteAllColorSet()
                modeling.geoGroupDeleteHistory()
                modeling.convertBranchToLeafInstance(inParent ="grp_geo", GUI = True, mode = "convToLeaf" )
                modeling.makeAllMeshesUnique(inParent="|asset|grp_geo")
                modeling.meshShapeNameConform(inParent = "|asset|grp_geo")
                assetconformation.softClean(keepRenderLayers = False,nameSpaceToKeepL = ["lgtRig"])
                assetconformation.createSubdivSets()
                assetconformation.setSubdiv()
                shading.conformShaderNameNew( GUI = True )

    elif fileType == "render":
            if GUI == True: 
                msgS = baseMessage2S+"""
    - delete geo history,\n    - make all mesh unique,\n    - conform mesh shapes names,\n    - create set subdiv,\n    - apply set subdiv,\n    - create 'set_meshCache',   
    - delete all unused nodes (unconnected to an asset dag node), except render layers,\n    - conform all shaders names"""
                answer =  mc.confirmDialog( title='clean '+fileType+' '+assetType+' asset', message=msgS, button=['Proceed','Cancel'], defaultButton='Proceed', cancelButton='Cancel', dismissString='Cancel' )
            if answer != "Cancel":
                miscUtils.deleteUnknownNodes()
                assetconformation.fixMaterialInfo()
                miscUtils.deleteAllColorSet()
                modeling.geoGroupDeleteHistory()
                modeling.makeAllMeshesUnique(inParent="|asset|grp_geo")
                modeling.meshShapeNameConform(inParent = "|asset|grp_geo")
                assetconformation.softClean(keepRenderLayers = False,nameSpaceToKeepL = ["lgtRig"])
                assetconformation.setSubdiv()
                assetconformation.createSubdivSets()
                assetconformation.createSetMeshCache()
                shading.conformShaderNameNew( GUI = True )

    return resultB, logL
