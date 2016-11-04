import maya.cmds as mc
import pymel.core as pm
import maya.utils as mu
import re
import string
import os

from pytd.util.logutils import logMsg
from datetime import datetime

from davos_maya.tool.general import infosFromScene, assertSceneInfoMatches
from pytd.util.fsutils import jsonWrite, jsonRead

from dminutes import miscUtils
reload (miscUtils)


def onCheckInAsset():
    """
    lists of things to automaticaly do before doing a check-in on an asset
    """
    unknownNodes = ['mentalrayGlobals','mentalrayItemsList','miDefaultFramebuffer','miDefaultOptions']
    mc.delete (unknownNodes)



def checkGroupNamingConvention(printInfo = True, inParent = "*"):
    """
    get all the transform nodes that are not parent of a shape and make sure their name is conforme to the group naming convention 'grp_name_complement##' 
        - name and complement## together is a string of 16 alphanumeric characters
        - complement is optional
        - exceptions are authorised for 'assets' ... 
    printInfo (True/False) : manage the log information
    return list of groups names that are not conform 
    """
    wrongGroupNamingConvention = []
    groupNamingConventionExceptionLong = ["|asset", "|shot"]
    groupNamingConventionException = []
    allGroup = []
    

    allTransform = mc.listRelatives(inParent, allDescendents = True, fullPath = True, type = "transform")
    allTransform = mc.ls(allTransform,exactType = "transform", long = True)
    if allTransform is None: allTransform = []
    for eachTransform in allTransform:
        if mc.listRelatives(eachTransform, children = True, shapes = True) is None:
            allGroup.append(eachTransform)
    
    for each in allGroup:
        eachShort = each.split("|")[-1]
        if not (re.match('^grp_[a-zA-Z0-9]{1,16}$', eachShort) or re.match('^grp_[a-zA-Z0-9]{1,16}_[a-zA-Z0-9]{1,16}$', eachShort)) and each not in groupNamingConventionExceptionLong and eachShort not in groupNamingConventionException:
            wrongGroupNamingConvention.append(each)
    
    if printInfo == True:
        print ""
        if wrongGroupNamingConvention:
            print "#### warning: 'checkGroupNamingConvention': the following GROUP(S) do not match the mesh naming convention : 'grp_name_complement##'"
            print "#### warning: 'checkGroupNamingConvention':      - name and complement## together is a string of 16 alphanumeric characters"
            print "#### warning: 'checkGroupNamingConvention':      - complement is optional"
            for each in wrongGroupNamingConvention:
                print "#### warning: 'checkGroupNamingConvention': wrong group naming convention --> "+each
            mc.select(wrongGroupNamingConvention, r=True)
        else:
            print "#### info: 'checkGroupNamingConvention': GROUP naming convention is correct"                
            
    return wrongGroupNamingConvention   
    



def createSubdivSets(GUI = True, defaultSetSubdiv = "set_subdiv_init"):
    """
    This function creates a "set_subdiv_init" that gather all the "geo_*" objects found in the scene.
    and bunch of empty sets named "set_subdiv_X" (where X is a digit) are also created.
    All theses sets are liked to a partition named 'par_subdiv'. this prevent a "geo_*" objects to exists in 2 different "set_subdiv_*" sets.
    the user must afterward move the all the "geo_*" objects from the "set_subdiv_init" set to the "set_subdiv_X" depending the level of subdivision that is requiered.
    then, the setSubdiv() procedure must be executed to apply the subdivision to the objects through the shapes attributes  
    """
    returnB = True
    logL = []

    assetType = ""

    if mc.ls("|asset"):        
        mainFilePath = mc.file(q=True, list = True)[0]
        mainFilePathElem = mainFilePath.split("/")
        assetType = mainFilePathElem[-3]


    subdivSets = mc.ls("set_subdiv_*", type = "objectSet")
    subdivPartitions = mc.ls("par_*", type = "partition")
    setMeshcacheL = mc.ls("set_meshCache", type="objectSet")

    if setMeshcacheL and assetType == 'chr':
        existingGeo=mc.ls(mc.sets(setMeshcacheL[0], query = True),l=True)
    else:
        #existingGeo = mc.ls("geo_*", type = "transform",l=True)
        meshList, instanceList = miscUtils.getAllTransfomMeshes(inParent = "|asset|grp_geo")
        existingGeo = list(meshList)
        existingGeo.extend(instanceList)

    subdivSetsInitList = ["set_subdiv_init","set_subdiv_0","set_subdiv_1","set_subdiv_2","set_subdiv_3"]
    if not existingGeo:
        logMessage = "#### {:>7}: 'createSubdivSets' 'geo_*' object could be foud in the scene".format("Error")
        if GUI == True: raise ValueError(logMessage)
        logL.append(logMessage)
        returnB = False

    if "par_subdiv" not in subdivPartitions:
        mc.partition( name="par_subdiv")

    createdSetL=[]
    for eachSet in subdivSetsInitList:
        if eachSet not in subdivSets:
            mc.sets(name=eachSet, empty=True)
            mc.partition( eachSet, add="par_subdiv")
            createdSetL.append(eachSet)

    if createdSetL:
        logMessage = "#### {:>7}: 'createSubdivSets' Created {} new subdiv sets : {}".format("Info",len(createdSetL), createdSetL)
        if GUI == True: print logMessage
        logL.append(logMessage)

    geoInSet = mc.ls(mc.sets(subdivSets, query = True),l=True)
    if geoInSet == None: geoInSet = []

    addedGeoToInitSet = []
    for eachGeo in existingGeo:
        if eachGeo not in geoInSet:
            mc.sets(eachGeo, forceElement=defaultSetSubdiv)
            addedGeoToInitSet.append(eachGeo)

    if addedGeoToInitSet:
        logMessage = "#### {:>7}: 'createSubdivSets' {} geo added to '{}': {}".format("Info",len(addedGeoToInitSet),defaultSetSubdiv,addedGeoToInitSet)
        if GUI == True: print logMessage
        logL.append(logMessage)

    if not logL:
        logMessage = "#### {:>7}: 'createSubdivSets' Nothing done".format("Info")
        if GUI == True: print logMessage
        logL.append(logMessage)

    return dict(returnB=returnB, logL=logL)

     
def setSubdiv(GUI= False ):
    """
    creates 'smoothLevel1' and 'smoothLevel2' extra attributes on the 'grp_geo' 
    and connect them to the smoothLevel (preview subdiv level) of the geo shapes
    """
    returnB = True
    logL = []

    if not mc.ls("|asset|grp_geo", l = True):
        logMessage = "#### {:>7}: 'setSubdiv' No '|asset|grp_geo' found".format("Error")
        if GUI == True: raise ValueError(logMessage)
        print logMessage
        logL.append(logMessage)
        returnB = False


    userDefinedAttr =(mc.listAttr("|asset|grp_geo",userDefined=True))
    if userDefinedAttr:
        if "smoothLevel1" in userDefinedAttr:
            mc.deleteAttr ("|asset|grp_geo.smoothLevel1")            
        if "smoothLevel2" in userDefinedAttr:
            mc.deleteAttr ("|asset|grp_geo.smoothLevel2") 
    mc.addAttr("|asset|grp_geo",ln = "smoothLevel1", at = "long", min = 0, max = 1,dv = 0, keyable = True) 
    mc.addAttr("|asset|grp_geo",ln = "smoothLevel2", at = "long", min = 0, max = 2,dv = 0, keyable = True)

    subdivSets = mc.ls("set_subdiv_*", type = "objectSet")
    if not subdivSets:
        logMessage = "#### {:>7}: 'setSubdiv' No subdivision set could be found (set_subdiv_*). Please create them first".format("Error")
        if GUI == True: raise ValueError(logMessage)
        print logMessage
        logL.append(logMessage)
        returnB = False
    processedTransL =[]
    skippedTransL =[]
    nonManifoldObjL = []
    nonMeshObjectL = []
    for eachSetSubdiv in subdivSets:
        geoInSet = mc.ls(mc.sets(eachSetSubdiv, query = True),l=True)
        if not geoInSet: geoInSet = []       
        if eachSetSubdiv != "set_subdiv_init" and geoInSet:
            subdivLevel =  int(eachSetSubdiv.split("set_subdiv_")[1])
            previewSubdivLevel = subdivLevel    
            if  0 <= subdivLevel <=9 :
                for eachGeo in geoInSet:
                    nonManifoldEdgesL = mc.polyInfo( eachGeo,nme=True )
                    if nonManifoldEdgesL:
                        nonManifoldObjL.append(eachGeo)
                    if mc.nodeType(eachGeo)!="mesh":
                        eachGeoShape =  mc.listRelatives(eachGeo, noIntermediate=True, shapes=True, path=True)
                        if eachGeoShape:
                            eachGeoShape = eachGeoShape[0]
                        else:
                            nonMeshObjectL.append(eachGeo)
                            continue
                    else:
                        eachGeoShape = eachGeo

                    eachGeoParentL = mc.listRelatives(eachGeoShape, allParents = True, fullPath = True)
                    if not set(eachGeoParentL) & set(processedTransL):
                        miscUtils.setAttrC(eachGeoShape+".displaySmoothMesh",0)
                        miscUtils.setAttrC(eachGeoShape+".useSmoothPreviewForRender",0)
                        miscUtils.setAttrC(eachGeoShape+".renderSmoothLevel",0)
                        miscUtils.setAttrC(eachGeoShape+".useGlobalSmoothDrawType",1)
                        if not mc.getAttr(eachGeoShape+".smoothLevel", lock = True):
                            if previewSubdivLevel == 0:
                                miscUtils.setAttrC(eachGeoShape+".smoothLevel", 0)
                            if previewSubdivLevel == 1:
                                mc.connectAttr("|asset|grp_geo.smoothLevel1", eachGeoShape+".smoothLevel", f=True)
                            if previewSubdivLevel > 1:
                                mc.connectAttr("|asset|grp_geo.smoothLevel2", eachGeoShape+".smoothLevel",f=True)
                        if not mc.attributeQuery ("aiSubdivType", node = eachGeoShape , exists = True):
                                try:
                                    mc.loadPlugin("mtoa")
                                except Exception,err:
                                    print err
                                    miscUtils.setAttrC(eachGeoShape+".aiSubdivIterations",subdivLevel)
                                    if subdivLevel > 0:
                                        miscUtils.setAttrC(eachGeoShape+".aiSubdivType",1)
                                    else:
                                        miscUtils.setAttrC(eachGeoShape+".aiSubdivType",0)

                                if not mc.attributeQuery ("aiSubdivType", node = eachGeoShape , exists = True):
                                    logMessage = "#### {:>7}: 'setSubdiv' {}.aiSubdivType attribute coud not be found, please check if Arnold is properly installed on your computer".format("Error",eachGeoShape)
                                    if GUI == True: raise ValueError(logMessage)
                                    logL.append(logMessage)
                                    returnB = False
                        else:
                            miscUtils.setAttrC(eachGeoShape+".aiSubdivIterations",subdivLevel)
                            if subdivLevel > 0:
                                miscUtils.setAttrC(eachGeoShape+".aiSubdivType",1)
                            else:
                                miscUtils.setAttrC(eachGeoShape+".aiSubdivType",0)

                        processedTransL.append(eachGeo)
                    else:
                        skippedTransL.append(eachGeo)

    miscUtils.setAttrC("|asset|grp_geo.smoothLevel1", 1)
    miscUtils.setAttrC("|asset|grp_geo.smoothLevel2", 2)
    
    if processedTransL and not skippedTransL:
        logMessage = "#### {:>7}: 'setSubdiv' {} meshes processed".format("Info", len(processedTransL))
        print logMessage
        logL.append(logMessage)
    if processedTransL and skippedTransL:
        logMessage = "#### {:>7}: 'setSubdiv' {} meshes processed and {} instances skipped ".format("Info", len(processedTransL), len(skippedTransL))
        print logMessage
        logL.append(logMessage)

    if "set_subdiv_init" in subdivSets and mc.sets("set_subdiv_init", query = True) != None:
        logMessage = "#### {:>7}: 'setSubdiv' A geo object is still in the 'set_subdiv_init', please asssign it to a 'set_subdiv*'".format("Error")
        #if GUI == True: mc.confirmDialog( title='Error:', message=logMessage, button=['Ok'], defaultButton='Ok' )
        print logMessage
        logL.append(logMessage)
        returnB = False

    if nonManifoldObjL:
        logMessage = "#### {:>7}: 'setSubdiv' '{}' object as non manifold edges please please use the 'modeling --> mesh --> cleanup' maya tools to fix that: {}".format("Error", len(nonManifoldObjL), nonManifoldObjL)
        #if GUI == True: mc.confirmDialog( title='Error:', message=logMessage, button=['Ok'], defaultButton='Ok' )
        print logMessage
        logL.append(logMessage)
        returnB = False

    if nonMeshObjectL:
        logMessage = "#### {:>7}: 'setSubdiv' '{}' objects without shape: {}".format("Error", len(nonMeshObjectL), nonMeshObjectL)
        #if GUI == True: mc.confirmDialog( title='Error:', message=logMessage, button=['Ok'], defaultButton='Ok' )
        print logMessage
        logL.append(logMessage)
        returnB = False


    if not logL:
        logMessage = "#### {:>7}: 'setSubdiv' Donne properly".format("Info")
        print logMessage
        logL.append(logMessage)


    return dict(returnB=returnB, logL=logL)



def createSetMeshCache(inParent= "|asset|grp_geo", GUI = True):
    returnB = True
    logL = []

    meshList, instanceList = miscUtils.getAllTransfomMeshes(inParent = inParent)
    existingGeoL = list(meshList)
    existingGeoL.extend(instanceList)

    if not existingGeoL:
        logMessage = "#### {:>7}: 'createSetMeshCache' geometries could be foud under '{}'".format("Info", inParent)
        if GUI == True: raise ValueError(logMessage)
        logL.append(logMessage)
        returnB = False

    setMeshCacheL = mc.ls("set_meshCache*", type = "objectSet")
    if setMeshCacheL:
        mc.delete(setMeshCacheL)

    mc.sets(existingGeoL, name="set_meshCache")

    logMessage = "#### {:>7}: 'createSetMeshCache' updated 'set_meshCache', now includes {} geometries".format("Info",len(existingGeoL))
    if GUI == True: print logMessage
    logL.append(logMessage)

    return dict(returnB=returnB, logL=logL)



def previewSubdiv(enable = True, filter = ""):
    """
    set the  'smoothLevel1' and 'smoothLevel2' extra attributes to 1 and 2 'grp_geo' of assets
    """
    geoGroupList = mc.ls("*:grp_geo", l = True)+mc.ls("grp_geo", l = True)

    for eachGeoGroup in geoGroupList:
        if "" in eachGeoGroup:
            smoothLevelAttrList = mc.listAttr(eachGeoGroup,string = "smoothLevel*",userDefined=True)
            if smoothLevelAttrList:
                print "#### info: '"+eachGeoGroup.split("|")[-1]+"' subdiv preview --> "+ str(enable)
                for eachAttr in smoothLevelAttrList:
                    mc.setAttr(eachGeoGroup+"."+eachAttr, enable * int(eachAttr[-1]))

def setShadingMask(selectFailingNodes = False, gui = True):

    log = miscUtils.LogBuilder(gui=gui, funcName ="'setShadingMask'")

    dmnMask00_R = ["chr_"]
    dmnMask00_G = ["prp_"]
    dmnMask00_B = ["vhl_"]

    dmnMask01_R = ["set_"]
    dmnMask01_G = ["env_"]
    dmnMask01_B = ["c2d_"]

    dmnMask02_R = ["chr_aton_","chr_barman_","chr_gamin2_","chr_femmeFaty_"]
    dmnMask02_G = ["chr_aurelien_","chr_actionnaire1_","chr_jose_", "chr_gamin1_"]
    dmnMask02_B = ["chr_gretchen_","chr_actionnaire2_","chr_zombie1_","chr_gamin3_"]

    dmnMask03_R = ["chr_francis_","chr_actionnaire3_","chr_maitresse_"]
    dmnMask03_G = ["chr_chauvesouris_","chr_actionnaire5_","chr_dick_"]
    dmnMask03_B = ["chr_blaise_","chr_miranda_","chr_penelope_"]

    dmnMask04_R = ["chr_cerbere_","chr_cyclopette_","chr_sylvain_"]
    dmnMask04_G = ["chr_steven_","chr_dolores_","chr_ado18aine_"]
    dmnMask04_B = ["chr_sirius_","chr_femme_","chr_ado_","chr_gamine_"]

    dmnMask05_R = []# visages, gazons, herbes folles custom et vegetation
    dmnMask05_G = []# yeux, custom, xgen
    dmnMask05_B = []# bouches, custom

    dmnMask06_R = []# shading decor custom, gradient sourcil sur aurelien et francis, ombre orbites sirus
    dmnMask06_G = []# shading decor custom ,  cheveux Lucie
    dmnMask06_B = []# shading decor custom

    dmnMask07_R = []# lighting custom
    dmnMask07_G = []# lighting custom
    dmnMask07_B = []# lighting custom

    dmnMask08_R = []# lighting custom utility
    dmnMask08_G = []# lighting custom utility
    dmnMask08_B = []# lighting custom utility

    dmnMask09_R = []#  custom no transparency
    dmnMask09_G = []#  custom no transparency
    dmnMask09_B = []#  custom no transparency

    dmnMask00 = [0,0,0]
    dmnMask01 = [0,0,0]
    dmnMask02 = [0,0,0]
    dmnMask03 = [0,0,0]
    dmnMask04 = [0,0,0]

    failingNodes = []
    succedingNodes = []
    lockedNodes = []

    if mc.ls("|asset"):        
        mainFilePath = mc.file(q=True, list = True)[0]
        mainFilePathElem = mainFilePath.split("/")
        if  mainFilePathElem[-4] != "asset" and mainFilePathElem[-5] != "asset":
                txt= "You are not working in an 'asset' structure directory"
                log.printL("e", txt, guiPopUp = True)
                raise ValueError(txt)
    else :
        log.printL("e", "No '|asset' could be found in this scene", guiPopUp = True)
        raise ValueError(txt)


    assetName =  mainFilePathElem[-2]

    for each in dmnMask00_R:
        if each in assetName: dmnMask00[0]=1
    for each in dmnMask00_G:
        if each in assetName: dmnMask00[1]=1
    for each in dmnMask00_B:
        if each in assetName: dmnMask00[2]=1

    for each in dmnMask01_R:
        if each in assetName: dmnMask01[0]=1
    for each in dmnMask01_G:
        if each in assetName: dmnMask01[1]=1
    for each in dmnMask01_B:
        if each in assetName: dmnMask01[2]=1

    for each in dmnMask02_R:
        if each in assetName: dmnMask02[0]=1
    for each in dmnMask02_G:
        if each in assetName: dmnMask02[1]=1
    for each in dmnMask02_B:
        if each in assetName: dmnMask02[2]=1

    for each in dmnMask03_R:
        if each in assetName: dmnMask03[0]=1
    for each in dmnMask03_G:
        if each in assetName: dmnMask03[1]=1
    for each in dmnMask03_B:
        if each in assetName: dmnMask03[2]=1

    for each in dmnMask04_R:
        if each in assetName: dmnMask04[0]=1
    for each in dmnMask04_G:
        if each in assetName: dmnMask04[1]=1
    for each in dmnMask04_B:
        if each in assetName: dmnMask04[2]=1


    dmnToonList = mc.ls(type="dmnToon")

    #log.printL("i", "{} dmnToon nodes to process".format(len(dmnToonList)) )
    log.printL("i", "'dmnMask00' set to -->  {}".format(dmnMask00) )
    log.printL("i", "'dmnMask01' set to -->  {}".format(dmnMask01) )
    log.printL("i", "'dmnMask02' set to -->  {}".format(dmnMask02) )
    log.printL("i", "'dmnMask03' set to -->  {}".format(dmnMask03) )
    log.printL("i", "'dmnMask04' set to -->  {}".format(dmnMask04) )



    for each in dmnToonList:
        maskNumber = 5
        locked = False
        if not mc.listConnections(each+".dmnMask00",connections = True):
            if not miscUtils.setAttrC(each+".dmnMask00", dmnMask00[0], dmnMask00[1], dmnMask00[2], type="double3"):
                locked =True
            maskNumber = maskNumber - 1
        else:
            log.printL("e", "'{}.dmnMask00' is already connected, can't change value".format( each))

        if not mc.listConnections(each+".dmnMask01",connections = True):
            if not miscUtils.setAttrC(each+".dmnMask01", dmnMask01[0], dmnMask01[1], dmnMask01[2], type="double3"):
                locked =True
            maskNumber = maskNumber - 1
        else:
            log.printL("e", "'{}.dmnMask01' is already connected, can't change value".format( each))

        if not mc.listConnections(each+".dmnMask02",connections = True):
            if not miscUtils.setAttrC(each+".dmnMask02", dmnMask02[0], dmnMask02[1], dmnMask02[2], type="double3"):
                locked =True
            maskNumber = maskNumber - 1
        else:
            log.printL("e", "'{}.dmnMask02' is already connected, can't change value".format( each))

        if not mc.listConnections(each+".dmnMask03",connections = True):
            if not miscUtils.setAttrC(each+".dmnMask03", dmnMask03[0], dmnMask03[1], dmnMask03[2], type="double3"):
                locked =True
            maskNumber = maskNumber - 1
        else:
            log.printL("e", "'{}.dmnMask03' is already connected, can't change value".format( each))

        if not mc.listConnections(each+".dmnMask04",connections = True):
            if not miscUtils.setAttrC(each+".dmnMask04", dmnMask04[0], dmnMask04[1], dmnMask04[2], type="double3"):
                locked =True
            maskNumber = maskNumber - 1
        else:
            log.printL("e", "'{}.dmnMask04' is already connected, can't change value".format( each))

        if locked: 
            lockedNodes.append(each)

        if maskNumber == 0:
            succedingNodes.append(each)
        else:
            failingNodes.append(each)

    if len(lockedNodes) > 0 :
        log.printL("w", "{} dmnToon nodes has locked attibutes hence could not be set totaly: {}".format( len(lockedNodes), lockedNodes))

    if len(failingNodes) > 0 :
        if selectFailingNodes == True and gui: 
            mc.select(failingNodes)
        log.printL("e", "{} dmnToon nodes masks cannot be set: {}".format( len(failingNodes), failingNodes), guiPopUp = True)

    if len(succedingNodes) > 0 :
        log.printL("i", "{} dmnToon nodes masks have been set succesfully: {}".format( len(succedingNodes), succedingNodes))
            

    return dict(resultB=log.resultB, logL=log.logL)





class Asset_File_Conformer:
    def __init__(self, gui = True):
        if mc.ls("|asset"):        
            self.mainFilePath = mc.file(q=True, list = True)[0]
            self.mainFilePathElem = self.mainFilePath.split("/")
            self.gui=gui
            self.log = miscUtils.LogBuilder(gui=gui, logL = [], resultB = True)

            if self.mainFilePathElem[-2] != "ref":
                self.assetName = self.mainFilePathElem[-2]
                self.assetType = self.mainFilePathElem[-3]
            else:
                self.assetName = self.mainFilePathElem[-3]
                self.assetType = self.mainFilePathElem[-4]
            
            self.assetFileType = self.mainFilePathElem[-1].split("-")[0].split("_")[-1]
            self.sourceList =[]
            self.targetList =[]
            self.sourceTargetListMatch = False
            self.sourceTargetTopoMatch = False
            self.sourceFile = ""
        else :
            raise ValueError("#### Error: no '|asset' could be found in this scene")


    def loadFile(self,sourceFile = "renderRef", reference = True):
        # if self.gui == True:
        #     panelL = mc.getPanel( visiblePanels=True )
        #     panelToCloseL=["hyperShadePanel","polyTexturePlacementPanel"]
        #     for each in panelL:
        #         for eachPanel in panelToCloseL:
        #             if eachPanel in each:
        #                 mc.deleteUI(each, panel = True)
        #                 #mu.executeDeferred("mc.deleteUI(each, panel = True)")


        self.log.funcName ="'loadFile' "
        mc.refresh()

        if  not (self.mainFilePathElem[-4] == "asset" or self.mainFilePathElem[-5] == "asset"):
            txt= "you are not working in an 'asset' structure directory"
            self.log.printL("e", txt)
            raise ValueError(txt)

        if sourceFile in ["render","anim","modeling","previz"]:
            self.sourceFile = sourceFile
            self.renderFilePath = miscUtils.normPath(miscUtils.pathJoin("$ZOMB_TEXTURE_PATH",self.assetType,self.assetName,self.assetName+"_"+self.sourceFile+".ma"))
            self.renderFilePath_exp = miscUtils.normPath(os.path.expandvars(os.path.expandvars(self.renderFilePath)))
            fileType ="mayaAscii"

        elif sourceFile in ["renderRef", "animRef"]:
            self.sourceFile = sourceFile
            self.renderFilePath = miscUtils.normPath(miscUtils.pathJoin("$ZOMB_TEXTURE_PATH",self.assetType,self.assetName,"ref",self.assetName+"_"+self.sourceFile+".mb"))
            self.renderFilePath_exp = miscUtils.normPath(os.path.expandvars(os.path.expandvars(self.renderFilePath)))
            fileType ="mayaBinary"
            if not os.path.isfile(self.renderFilePath_exp):
                txt = "Could not find: '{}', ref file has not been released yet, let's do it: '{}'".format(self.sourceFile, self.sourceFile.replace("Ref",""))
                self.sourceFile = self.sourceFile.replace("Ref","")
                fileType ="mayaAscii"
                self.log.printL("w", txt)
                self.renderFilePath = miscUtils.normPath(miscUtils.pathJoin("$ZOMB_TEXTURE_PATH",self.assetType,self.assetName,self.assetName+"_"+self.sourceFile.replace("Ref","")+".ma"))
                self.renderFilePath_exp = miscUtils.normPath(os.path.expandvars(os.path.expandvars(self.renderFilePath)))
        else:
            txt= "The choosen sourceFile '{}' is not correct".format(sourceFile)
            self.log.printL("e", txt)
            raise ValueError(txt)

        fileLoadedB = False
        if reference:
            if os.path.isfile(self.renderFilePath_exp):
                if os.stat(self.renderFilePath_exp).st_size > 75000:
                    mc.file( self.renderFilePath_exp, type= fileType, ignoreVersion=True, namespace=self.sourceFile, preserveReferences= True, reference = True )
                    txt = "referencing: '{}'".format(self.renderFilePath_exp)
                    self.log.printL("i", txt)
                    fileLoadedB = True
        else:
            if os.path.isfile(self.renderFilePath_exp):
                if os.stat(self.renderFilePath_exp).st_size > 75000:
                    mc.file( self.renderFilePath_exp, i= True, type= fileType, ignoreVersion=True, namespace=self.sourceFile, preserveReferences= False )
                    txt = "importing: '{}'".format(self.renderFilePath_exp)
                    self.log.printL("i", txt)
                    fileLoadedB = True
        if not fileLoadedB:
            txt = "File is missing or empty: '{}'".format(self.renderFilePath_exp)
            self.log.printL("e", txt)
        mc.refresh()
        return dict(resultB=self.log.resultB, logL=self.log.logL, fileLoadedB=fileLoadedB)


    def cleanFile(self, verbose = False):
        toReturnB = True
        outLogL = []
        self.log.funcName ="'cleanFile' "
        mc.refresh()

        refNodeList = mc.ls(type = "reference")
        for each in refNodeList:
            if re.match('^render[0-9]{0,3}[:]{0,1}[a-zA-Z0-9_]{0,128}RN$', each) or re.match('^anim[0-9]{0,3}[:]{0,1}[a-zA-Z0-9_]{0,128}RN$', each) or re.match('^renderRef[0-9]{0,3}[:]{0,1}[a-zA-Z0-9_]{0,128}RN$', each) or re.match('^animRef[0-9]{0,3}[:]{0,1}[a-zA-Z0-9_]{0,128}RN$', each) or re.match('^modeling[0-9]{0,3}[:]{0,1}[a-zA-Z0-9_]{0,128}RN$', each) or re.match('^previz[0-9]{0,3}[:]{0,1}[a-zA-Z0-9_]{0,128}RN$', each):
                fileRef= pm.FileReference(each)
                #fileRef = mc.referenceQuery(each,filename=True)# other way to do it
                try:
                    txt = "removing reference '{}'".format(fileRef.path)
                    self.log.printL("i", txt)
                    fileRef.remove()
                except :
                    pass

        nameSpaceList = mc.namespaceInfo(listOnlyNamespaces=True,r=True)
        for each in nameSpaceList:
            if re.match('^render[0-9]{0,3}', each) or re.match('^anim[0-9]{0,3}', each) or re.match('^renderRef[0-9]{0,3}', each) or re.match('^animRef[0-9]{0,3}', each) or re.match('^modeling[0-9]{0,3}', each) or re.match('^previz[0-9]{0,3}', each):
                node2deleteList = mc.ls(each+":*")
                for node2delete in node2deleteList:
                    mc.lockNode(node2delete,lock = False)

        nameSpaceList = mc.namespaceInfo(listOnlyNamespaces=True)
        for each in nameSpaceList:
            if re.match('^render[0-9]{0,3}', each) or re.match('^anim[0-9]{0,3}', each) or re.match('^renderRef[0-9]{0,3}', each) or re.match('^animRef[0-9]{0,3}', each) or re.match('^modeling[0-9]{0,3}', each) or re.match('^previz[0-9]{0,3}', each):
                mc.namespace(removeNamespace=each, deleteNamespaceContent=True)
                txt = "removing namespace and its content: '{:<10}'".format(each)
                self.log.printL("i", txt)

        if not outLogL:
            txt = "Nothing to clean, no '_render', '_renderRef','_anim','_animRef', '_previz' or '_modeling' reference found"
            self.log.printL("i", txt)
        mc.refresh()

        return dict(resultB=self.log.resultB, logL=self.log.logL)


    def initSourceTargetList(self, sourceFile = "", targetObjects = "set_meshCache"):
        """
        targetObjects = "set_meshCache" "selection" or a given list
            - set_meshCache, or given list :  the method initiate the sourceList (prefixing targets obj with the name space) and targetList automaticaly
            - selection, (2 transforms expected) fisrt object selected is the source, the second is the target

        """
        self.log.funcName ="'initSourceTargetList' "
        self.sourceList =[]
        self.targetList =[]
        errorOnTarget = 0
        errorOnSource = 0
        if sourceFile == "":
            sourceFile = self.sourceFile



        if targetObjects == "set_meshCache" or isinstance(targetObjects, (list,tuple,set)):
            if targetObjects == "set_meshCache":
                if mc.ls("set_meshCache"):
                    targetObjects = mc.ls(mc.sets("set_meshCache",q=1),l=1)
                else:
                    self.log.printL("e", "No 'set_meshCache' could be found")
                    errorOnTarget = errorOnTarget + 1
                    targetObjects= []                   

            for eachTarget in targetObjects:
                if mc.ls(eachTarget):
                    if mc.nodeType (eachTarget)!= "transform":
                        txt = "'{}' target object has not the right type, only 'transform' nodes accepted".format(eachTarget)
                        self.log.printL("e", txt)
                        errorOnTarget = errorOnTarget + 1
                    else:
                        self.targetList.append(eachTarget)
                else:
                    txt = "No '{}' target object could be found".format(eachTarget)
                    self.log.printL("e", txt)
                    errorOnTarget = errorOnTarget + 1

            for eachTarget in self.targetList:
                #eachSource = sourceFile+":"+("|"+sourceFile+":").join(eachTarget.split("|"))
                if sourceFile != "root":
                    eachSource = ("|"+sourceFile+":").join(eachTarget.split("|"))
                else:
                    eachSource = eachTarget.replace("|"+self.sourceFile+":","|")

                if mc.ls(eachSource):
                    if mc.nodeType (eachSource)!= "transform":
                        txt = "No '{}' source object has not the right type, only 'transform' nodes accepted".format(eachSource)
                        self.log.printL("e", txt)
                        errorOnSource = errorOnSource + 1
                    else:
                        self.sourceList.append(eachSource)
                else:
                    errorOnSource = errorOnSource + 1
                    txt = "Target --> '{:<30}'  has no correspondig source --> '{}'".format(eachTarget, eachSource)
                    self.log.printL("e", txt)

            if errorOnTarget != 0: self.targetList =[]
            if errorOnSource != 0: self.sourceList =[]

        elif targetObjects == "selection":
            mySelection = mc.ls(selection=True)
            if len(mySelection)== 2:
                if mc.nodeType(mySelection[0]) == "transform":
                    self.sourceList = [mySelection[0]]
                else:
                    self.log.printL("e", "Selected source is not a 'transform' node")
                    errorOnSource = errorOnSource + 1

                if mc.nodeType(mySelection[1]) == "transform":
                    self.targetList = [mySelection[1]]
                else:
                    self.log.printL("e", "Selected target is not a 'transform' node")
                    errorOnTarget = errorOnTarget + 1
            else:
                self.log.printL("e", "2 objects must be selected, source first then target")
                self.log.printL("e", "Selection {}".format(mySelection))
    
        else:
            txt = "Can't recognize targetObjects: '{}' value, should be 'set_meshCache' or a list".format(targetObjects)
            self.log.printL("e", txt)
            raise ValueError(txt)

        if self.targetList and errorOnTarget == 0 and errorOnSource == 0:
            self.sourceTargetListMatch = True
            self.log.printL("i", "Target and source list are conform")
        else:
            self.sourceTargetListMatch = False
            self.log.printL("e", "Target list and source list not conform")

        return dict(resultB=self.log.resultB, logL=self.log.logL)


    def printSourceTarget(self):
        self.log.funcName ="'printSourceTarget' "
        if self.targetList and len(self.sourceList) == len(self.targetList):
            targetNb = len (self.targetList)
            i = 0
            while i<targetNb:
                print self.sourceList[i]+" --> "+self.targetList[i]
                i+=1
        else:
            self.log.printL("e", "Target list and source list not conform")
            self.log.printL("e", "Source {}".format( self.sourceList))
            self.log.printL("e", "Target {}".format( self.targetList))
        return dict(resultB=self.log.resultB, logL=self.log.logL)


    def checkSourceTargetTopoMatch(self):
        self.log.funcName ="'checkSourceTargetTopoMatch' "
        if self.sourceTargetListMatch == True:
            i = 0
            topoMismatch = 0
            while  i < len(self.targetList):
                sourceVrtxCnt = len(mc.getAttr(self.sourceList[i]+".vrts[:]"))
                targetVrtxCnt = len(mc.getAttr(self.targetList[i]+".vrts[:]"))
                polyCompareResultI = mc.polyCompare( self.sourceList[i], self.targetList[i], vertices=False, edges=True, colorSetIndices=False, colorSets=False,  faceDesc=True, userNormals=False, uvSetIndices=False, uvSets=False) 
                if (sourceVrtxCnt != targetVrtxCnt) or (polyCompareResultI == 4):
                    topoMismatch = topoMismatch + 1
                    if sourceVrtxCnt != targetVrtxCnt:
                        txt="Vertex number mismatch: '{}' vertex nb = {} -- '{}' vertex nb = {}".format(self.sourceList[i],sourceVrtxCnt, self.targetList[i],targetVrtxCnt)
                        self.log.printL("e", txt)
                    elif polyCompareResultI == 4:
                        txt="Face description (topologie/order) mismatch: '{}' different from '{}' ".format(self.sourceList[i], self.targetList[i])
                        self.log.printL("e", txt)                    
                    i+=1
                    continue
                if polyCompareResultI == 6:
                    txt="Edge mismatch: '{}' different from '{}' ".format(self.sourceList[i], self.targetList[i])
                    self.log.printL("w", txt)

                # sourceBBox =  mc.exactWorldBoundingBox(self.sourceList[i])
                # targetBBox =  mc.exactWorldBoundingBox(self.targetList[i])
                # if masterBBox != targetBBox:
                #     print ("#### {:>7}: Bounding box  mismatch: '{}' -- '{}'".format("Warning",self.sourceList[i], self.targetList[i]))
                

                areaTolF = 0.01 #percentage world area tolerance
                sourceWorldArea =  mc.polyEvaluate(self.sourceList[i], worldArea= True)
                targetWorldArea =  mc.polyEvaluate(self.targetList[i], worldArea= True)
                if sourceWorldArea == 0:
                    sourceWorldArea = 0.0000000001
                    txt="'{}' area = 0, assigning a tiny value to avoid 'division by 0' errors".format(self.sourceList[i])
                    self.log.printL("w", txt)
                if targetWorldArea == 0:
                    targetWorldArea = 0.0000000001
                    txt="'{}' area = 0, assigning a tiny value to avoid 'division by 0' errors".format(self.targetList[i])
                    self.log.printL("w", txt)

                if not isinstance(sourceWorldArea,float):
                    self.log.printL("e", "Cannot check topoligie, {} is not a valid mesh".format(self.sourceList[i]))
                    if sourceVrtxCnt == targetVrtxCnt:
                        topoMismatch +=1
                    i+=1
                    continue
                if not isinstance(targetWorldArea,float):
                    self.log.printL("e", "Cannot check topoligie, {} is not a valid mesh".format(self.targetList[i]))
                    if sourceVrtxCnt == targetVrtxCnt:
                        topoMismatch +=1
                    i+=1
                    continue
                areaDifF = abs(float(sourceWorldArea - targetWorldArea)/sourceWorldArea *100)
                if areaDifF > areaTolF:
                    txt="World area is {:.3f} percent different: '{}' -- '{}'".format(areaDifF, self.sourceList[i], self.targetList[i])
                    self.log.printL("w", txt)
                i+=1
            if topoMismatch == 0:
                self.sourceTargetTopoMatch = True
            else:
                self.sourceTargetTopoMatch = False
        else:
            self.log.printL("e", "Cannot check topoligie, target and source list mismatch")

        return dict(resultB=self.log.resultB, logL=self.log.logL)



    def transferUV(self, sampleSpace = 4):
        self.log.funcName ="'transferUV' "
        if self.sourceTargetListMatch == True:
            i = -1
            uvTransferFailed = 0
            while i < len(self.targetList)-1:
                i+=1
                shapeOrig = False
                sourceShapeList = mc.ls(mc.listRelatives(self.sourceList[i], allDescendents = True, fullPath = True, type = "mesh"), noIntermediate = True, l=True)
                if len(sourceShapeList)==0:
                    txt = "No shape coud be found under source transform: '{}'".format(self.sourceList[i])
                    self.log.printL("e", txt)
                    uvTransferFailed +=1
                    continue
                elif len(sourceShapeList)==1:
                    sourceShape = sourceShapeList[0]
                else:
                    txt = "Several 'shapes' were found under source transform: '{}' ".format(self.sourceList[i])
                    self.log.printL("e", txt)
                    uvTransferFailed +=1
                    continue

                targetShapeList = mc.ls(mc.listRelatives(self.targetList[i], allDescendents = True, fullPath = True, type = "mesh"), noIntermediate = False, l=True)
                if len(targetShapeList)==0:
                    txt="No shape coud be found under target transform: '{}'".format(self.targetList[i])
                    self.log.printL("e", txt)
                    uvTransferFailed +=1
                    continue
                elif len(targetShapeList)==1:
                    targetShape = targetShapeList[0]
                else:
                    shapeOrigList =[]
                    for each in targetShapeList:
                        if mc.getAttr(each+".intermediateObject") == 1 and not mc.listConnections( each+".inMesh",source=True) and "ShapeOrig" in each:
                            shapeOrigList.append(each)
                    if len(shapeOrigList) == 1:
                        targetShape = shapeOrigList[0]
                        shapeOrig = True
                    else:
                        txt = "several 'ShapeOrig' were found under target transform: '{}' ".format(self.targetList[i])
                        self.log.printL("e", txt)
                        uvTransferFailed +=1
                        continue

                #if target shape is connected to a 'pointOnPolyConstraint' (uses uvs) then we must keep the original uvs, otherwise to avoid loosing the constraint info
                # pntOnPolyConsL = mc.ls(mc.listHistory(self.targetList[i],future=True),type='pointOnPolyConstraint')
                # if pntOnPolyConsL:
                #     UVSetL = mc.polyUVSet( myShape,query=True, allUVSets=True )
                #     each = UVSetL[0]
                #     #mc.polyUVSet(myShape,rename=True, newUVSet='anim_'+each, uvSet= each)

                #     uvi=0
                #     while uvi<10:
                #         uvSetName = mc.getAttr(myShape+'.uvSet['+str(uvi)+'].uvSetName')
                #         print "uvSetName: ", uvSetName
                #         if uvSetName  == 'anim_'+each:
                #             break
                #         uvi+=1
                #     for eachCons in pntOnPolyConsL:
                #         mc.setAttr (eachCons+".nodeState", 2)
                #         #mc.connectAttr( myShape+".uvSet["+str(uvi)+"].uvSetName", eachCons+".target[0].targetUVSetName",force=True)
                #         mc.connectAttr(myShape+".uvSet["+str(uvi)+"].uvSetPoints[0]", eachCons+".target[0].targetUV",force=True)
                #         mc.setAttr (eachCons+".nodeState", 0)



                    # sampleSpace: Selects which space the attribute transfer is performed in. 
                    # 0 is world space, (default)
                    # 1 is model space, 
                    # 4 is component-based, 
                    # 5 is topology-based

                    #print ("#### {:>7}: 'transferUV' from '{}' --> {}".format("Drebug",sourceShape,targetShape))
                
                if shapeOrig == True: 
                    mc.setAttr(targetShape+".intermediateObject", 0)
                    mc.setAttr(targetShape+".visibility", 1)
                    mc.transferAttributes( sourceShape, targetShape, sampleSpace=sampleSpace, transferUVs=2 )
                    mc.delete(targetShape, constructionHistory = True)
                    mc.setAttr(targetShape+".intermediateObject", 1)
                else:
                    if mc.getAttr(targetShape+".visibility") == 0:
                        mc.setAttr(targetShape+".visibility", 1) 
                        mc.transferAttributes( sourceShape, targetShape, sampleSpace=sampleSpace, transferUVs=2 ) 
                        mc.delete(targetShape, constructionHistory = True)
                        mc.setAttr(targetShape+".visibility", 0) 
                    else:
                        mc.transferAttributes( sourceShape, targetShape, sampleSpace=sampleSpace, transferUVs=2 )
                        mc.delete(targetShape, constructionHistory = True)



            # targetShapeList = mc.ls(mc.listRelatives(self.targetList[i], allDescendents = True, fullPath = True, type = "mesh"), noIntermediate = False, l=True)
            # targetShapeList.remove(targetShape)
            # for each in targetShapeList:
            #     if mc.getAttr(each+".intermediateObject") == 1 and not mc.listConnections( each+".inMesh",source=True) and "ShapeOrig" in each:
            #         shapeOrigList.append(each)

            if uvTransferFailed ==0:
                txt="UVs has been transfered properly for all the {} object(s)".format(len(self.targetList))
                self.log.printL("i", txt)
            else:
                txt="UVs transfer failed for {} object(s)".format(uvTransferFailed)
                self.log.printL("e", txt)
        else:
            self.log.printL("e", "Cannot transfer uvs, target and source list mismatch")

        return dict(resultB=self.log.resultB, logL=self.log.logL)


    def transferSG(self):
        self.log.funcName ="'transferSG' "
        if self.sourceTargetListMatch == True:
            i = -1
            sgTransferFailed = 0
            while i < len(self.targetList)-1:
                i+=1
                sourceShapeList = mc.ls(mc.listRelatives(self.sourceList[i], allDescendents = True, fullPath = True, type = "mesh"), noIntermediate = True, l=False)
                if len(sourceShapeList)==0:
                    txt = "No shape coud be found under source transform : '{}'".format(self.sourceList[i])
                    self.log.printL("e", txt)
                    sgTransferFailed +=1
                    continue
                elif len(sourceShapeList)==1:
                    sourceShape = sourceShapeList[0]
                else:
                    txt="Several 'shapes' were found under source transform: '{}'".format(self.sourceList[i])
                    self.log.printL("e", txt)
                    sgTransferFailed +=1
                    continue

                targetShapeList = mc.ls(mc.listRelatives(self.targetList[i], allDescendents = True, fullPath = True, type = "mesh"), noIntermediate = True, l=False)
                if len(targetShapeList)==0:
                    txt= "No shape coud be found under target transform: '{}'".format(self.targetList[i])
                    self.log.printL("e", txt)
                    sgTransferFailed +=1
                    continue
                elif len(targetShapeList)==1:
                    targetShape = targetShapeList[0]
                else:
                    txt="Several 'shapes' were found under target transform: '{}'".format(self.targetList[i])
                    self.log.printL("e", txt)
                    sgTransferFailed +=1
                    continue

                #store uv linking
                uvLinkD={}
                mc.refresh()
                sourceShadEngList = mc.ls(mc.listHistory(sourceShape,future = True),type="shadingEngine")
                textureNodeL = []
                for each in sourceShadEngList:
                    preview_shader =  mc.listConnections(each+'.surfaceShader',connections = False)
                    render_shader =  mc.listConnections(each+'.aiSurfaceShader',connections = False)
                    if not preview_shader: preview_shader = []
                    if not render_shader: render_shader = []
                    shaderL = list(set(preview_shader) | set(render_shader))
                    eachTextureL  = mc.ls(mc.listHistory(shaderL),type="file")
                    if eachTextureL:
                        textureNodeL.extend(eachTextureL)
                #print "--"
                #print "source: {}  --> target: {}".format(sourceShape, targetShape)

                for each in textureNodeL:
                    uvLinkD[each] = mc.uvLink( query=True, texture=each )
                    #print "GET: each: {}, uvLinkD[each]: {}".format(each, uvLinkD[each])

                #print sourceShape+" --> "+targetShape
                if len(sourceShadEngList) == 1:
                    mc.sets(targetShape,e=True, forceElement=sourceShadEngList[0])
                elif len(sourceShadEngList) > 0:
                    mc.transferShadingSets(sourceShape,targetShape, sampleSpace=0, searchMethod=3)
                else:
                    txt="No 'shader' found on source transform: '{}'".format(sourceShape)
                    self.log.printL("e", txt)
                    sgTransferFailed +=1

                #linkBack UVs
                mc.refresh()
                for each in textureNodeL:
                    if isinstance(uvLinkD[each], (list,tuple,set)):
                        for eachUVSet in uvLinkD[each]:
                            mc.uvLink( make=True, texture=each, uvSet= eachUVSet.replace(sourceShape,targetShape) )
                            #print "-> SET: textureNode: {}, uvLinkD[each]: {}".format(each, eachUVSet)
                    else:
                        mc.uvLink( make=True, texture=each, uvSet= uvLinkD[each].replace(sourceShape,targetShape) )                            
                        #print "-> SET: textureNode: {}, uvLinkD[each]: {}".format(each, uvLinkD[each])

            if sgTransferFailed ==0:
                txt="Materials have been transfered properly for all the {} object(s)".format(len(self.targetList))
                self.log.printL("i", txt)
            else:
                txt="Materials transfer failed for {} object(s)".format(sgTransferFailed)
                self.log.printL("e", txt)

        else:
            self.log.printL("e", "Cannot transfer materials, target and source list mismatch")

        return dict(resultB=self.log.resultB, logL=self.log.logL)


    def removeNameSpaceFromShadNodes(self, objectList = [], verbose = False):
        self.log.funcName ="'removeNameSpaceFromShadNodes' "
        shadEngList = []
        shapeList = miscUtils.getShape(objectList, failIfNoShape = False)
        renamedShadNodeNb = 0
        for eachShape in shapeList:
            eachSEList = mc.ls(mc.listHistory(eachShape,future = True),type="shadingEngine", l = True)
            shadEngList = list(set(eachSEList))
            for shadEng in shadEngList:
                try:
                    surfaceBranchShdNodeL = mc.ls(mc.listHistory(mc.listConnections(shadEng+'.surfaceShader',connections = False)),l=True)
                except:
                    surfaceBranchShdNodeL=[]

                try: 
                    aiSurfaceBranchShdNodeL = mc.ls(mc.listHistory(mc.listConnections(shadEng+'.aiSurfaceShader',connections = False)),l=True)
                except:
                    aiSurfaceBranchShdNodeL=[]
                nodeList = surfaceBranchShdNodeL + aiSurfaceBranchShdNodeL + [shadEng]
                nodeList = list(set(nodeList))
                for each in nodeList:
                    if ":"in each:
                        mc.lockNode(each, lock=False)
                        newEach= mc.rename(each,each.split(":")[-1],ignoreShape=True)
                        renamedShadNodeNb += 1
                        if verbose:
                            txt="Remove from any namespace:  '{}' --> '{}' ".format(each,newEach)
                            self.log.printL("i", txt)
        txt= "Name space removed from {} shading nodes(s)".format(renamedShadNodeNb)
        self.log.printL("i", txt)
        mc.refresh()
        return dict(resultB=self.log.resultB, logL=self.log.logL)


    def disconnectAiMaterials(self):
        """
        not finished yet, we finaly decided to keep arnold shaders in animation files
        """
        self.log.funcName ="'disconnectAiMaterials' "
        mc.refresh()
        shadEngineList = mc.ls("*",type = "shadingEngine")
        shadEngineList.remove("initialParticleSE")
        shadEngineList.remove("initialShadingGroup")
        if not shadEngineList :
            self.log.printL("e", "No shading engine")
            return
        for each in shadEngineList:
            matShadNode =  mc.listConnections(each+'.aiSurfaceShader',connections = True, plugs=True)
            mc.disconnectAttr(matShadNode[1],matShadNode[0])


    def smoothPolyDisplay(self, inMeshList = [], verbose = False, shapeOrigOnly = True):
        self.log.funcName ="'smoothPolyDisplay' "
        intSel = mc.ls(selection=True)
        for each in inMeshList:
                #if target shape is connected to a 'pointOnPolyConstraint' (uses uvs) then we must keep the original uvs, otherwise to avoid loosing the constraint info
                pntOnPolyConsL = mc.ls(mc.listHistory(each,future=True),type='pointOnPolyConstraint')
                if pntOnPolyConsL:
                    txt = "'skipping {}' a 'pointOnPolyConstraint' is using a uvSet ".format(each)
                    self.log.printL("w", txt)
                    continue

                shapeOrigL = miscUtils.getShapeOrig(TransformS = each)
                if len(shapeOrigL)==0:
                    if shapeOrigOnly:
                        txt="No shapeOrig found under '{}' skipping operation on this mesh ".format(each)
                        self.log.printL("w", txt)
                        continue
                    else:
                        target = each
                elif len(shapeOrigL)==1:
                    target = shapeOrigL[0]
                elif len(shapeOrigL)>1: 
                    target = shapeOrigL[0]
                    txt="{} shapeOrig found under '{}', proceeding with the first one: '{}'".format(len(shapeOrigL),each, target)
                    self.log.printL("w", txt)

                mc.polySoftEdge (target, angle=180, constructionHistory=True)
                mc.bakePartialHistory(target, prePostDeformers=True)
                if verbose == True:
                    txt="Done on '{:^30}'".format(each)
                    self.log.printL("i", txt)
        txt="Done on {} object(s)".format(len(inMeshList))
        self.log.printL("i", txt)
        mc.select(intSel, replace=True)

        return dict(resultB=self.log.resultB, logL=self.log.logL)



    def transferRenderAttr(self, transferArnoldAttr =  True):
        self.log.funcName ="'transferRenderAttr' "
        shapeAttrList = ["boundaryRule", "continuity", "smoothUVs", "propagateEdgeHardness", "keepMapBorders", "keepBorder", "keepHardEdge",
                        "castsShadows", "receiveShadows", "holdOut", "motionBlur", "primaryVisibility",
                        "smoothShading", "visibleInReflections", "visibleInRefractions", "doubleSided", "opposite"]
        shapeArnoldAttrList = ["aiSelfShadows", "aiOpaque", "aiVisibleInDiffuse", "aiVisibleInGlossy", "aiMatte", "aiSubdivUvSmoothing", "aiSubdivSmoothDerivs"]
        shapeTransferFailed = 0
        attrTransferFailed = 0

        if transferArnoldAttr ==  True:
            shapeAttrList = shapeAttrList + shapeArnoldAttrList

        if self.sourceTargetListMatch == True:
            i = 0
            while i < len(self.targetList):
                sourceShapeLn = mc.ls(mc.listRelatives(self.sourceList[i], allDescendents = True, fullPath = True, type = "mesh"), noIntermediate = True, l=False)
                targetShapeLn = mc.ls(mc.listRelatives(self.targetList[i], allDescendents = True, fullPath = True, type = "mesh"), noIntermediate = True, l=False)
                if len(sourceShapeLn) != 1 or len(targetShapeLn) != 1:
                    if len(sourceShapeLn) != 1:
                        txt= "{} shape(s) found under transform: '{}'".format(len(sourceShapeLn), self.sourceList[i])
                        self.log.printL("e", txt)
                    if len(targetShapeLn) != 1:
                        txt="{} shape(s) found under transform: '{}'".format(len(targetShapeLn), self.targetList[i])
                        self.log.printL("e", txt)
                    shapeTransferFailed += 1
                else:
                    for each in shapeAttrList:
                        attrValue = mc.getAttr(sourceShapeLn[0]+"."+each)
                        attrTransfOk = miscUtils.setAttrC(targetShapeLn[0]+"."+each,attrValue)
                        if attrTransfOk == False:
                            attrTransferFailed += 1
                i+=1
            if shapeTransferFailed != 0 or attrTransferFailed != 0:
                if shapeTransferFailed != 0:
                    txt="Rendering attribute transfer failed for {} shape(s)".format(shapeTransferFailed)
                    self.log.printL("e", txt)
                if attrTransferFailed != 0:
                    txt="Rendering attribute transfer failed for {} attribute(s)".format(attrTransferFailed)
                    self.log.printL("w", txt)
            else:
                txt="Rendering attribute transfered properly {} on object(s)".format(len(self.targetList))
                self.log.printL("i", txt)
        else:
            self.log.printL("e", "Cannot transfer rendering attributes, target and source list mismatch")

        return dict(resultB=self.log.resultB, logL=self.log.logL)



    def disconnectAllShadEng(self, objectList = [], verbose = False):
        self.log.funcName ="'disconnectAllShadEng' "
        disconnectShapes = []
        shapeList = miscUtils.getShape(objectList, failIfNoShape = False)
        for eachShape in shapeList:
            shadEngList = mc.ls(mc.listHistory(eachShape,future = True),type="shadingEngine")
            for eachShadEng in shadEngList:
                attrList = mc.listConnections(eachShadEng,source = True,type='shape', connections =  True, plugs = True)
                if attrList:
                    i = -2
                    while i< len(attrList)-2:
                        i+=2
                        shapeAttr = attrList[i+1]
                        shadEngAttr = str(attrList[i])
                        if eachShape.split("|")[-1] in shapeAttr and eachShadEng+".dagSetMembers" in shadEngAttr:
                            #print "#### {:>7}: try to disconnect '{}'  from  '{}'".format("Info", shapeAttr,shadEngAttr) 
                            result = mc.disconnectAttr(shapeAttr, shadEngAttr)
                            if eachShape not in disconnectShapes:
                                disconnectShapes.append(eachShape)
                            if verbose == True: print result
                        if i>200: break
        txt="Shaders have been disconnected on {} object(s) ".format(len(disconnectShapes))
        self.log.printL("i", txt)
        return dict(resultB=self.log.resultB, logL=self.log.logL)



    def deleteUnusedShadingNodes(self):
        self.log.funcName ="'deleteUnusedShadingNodes' "

        ignoredShadEngL = [u'initialParticleSE', u'initialShadingGroup']
        ignoredNodeTypeL = [u'colorManagementGlobals', u'mesh', u'shape']

        ignoredNodeL = mc.ls("*",type= ignoredNodeTypeL)
        if not ignoredNodeL: ignoredNodeL=[]

        ignoredNodeL = ignoredShadEngL+ignoredNodeL
        for each in ignoredShadEngL:
            ignoredNodeL.extend(mc.hyperShade (listUpstreamNodes= each))
        #ignoredNodeL  = list(set(ignoredNodeL)|set(mc.ls("*",type= ignoredNodeTypeL)))#union

        allShadEngL = mc.ls("*",type="shadingEngine")
        if not allShadEngL: allShadEngL=[]
        allShadNodeL = list(allShadEngL)
        for each in allShadEngL:
            allShadNodeL.extend(mc.hyperShade (listUpstreamNodes= each))

        usedShadEnL = mc.listConnections(mc.ls("*",type="mesh"), destination = True, source = False, type = "shadingEngine")
        if not usedShadEnL: usedShadEnL=[]
        usedShadNodeL = list(usedShadEnL)
        for each in usedShadEnL:
            usedShadNodeL.extend(mc.hyperShade (listUpstreamNodes= each))

        unusedShadNodeL = mc.ls(list(set(allShadNodeL)-set(usedShadNodeL)-set(ignoredNodeL)))
        if unusedShadNodeL:
            mc.lockNode(unusedShadNodeL,lock=False)
            deletedNodeList = []
            undeletableNodeList = []

            for each in unusedShadNodeL:
                try:
                    mc.delete(each)
                    deletedNodeList.append(each)
                except:
                    undeletableNodeList.append(each)

            if deletedNodeList : 
                txt="{:>4} unused shading nodes deleted: {}".format(len(deletedNodeList), deletedNodeList)
                self.log.printL("i", txt)
            if undeletableNodeList: 
                txt="{:>4} unused shading nodes could not be deleted: {}".format(len(undeletableNodeList), undeletableNodeList)
                self.log.printL("i", txt)
        mc.refresh()
        return dict(resultB=self.log.resultB, logL=self.log.logL)




def softClean(struct2CleanList=["asset"], verbose = False, keepRenderLayers = True,GUI = True, nameSpaceToKeepL = []):
    """
    this script intend to remove from the scene every node that do not has a link with the selected structure.
    It also clean the empty namespaces
    """
    outSucceedB = True
    outLogL = []
    mc.refresh(suspend = True)
    undeletable = ['sideShape','frontShape','front','sideShape','side','perspShape','perspShape','persp','topShape','top','topShape','frontShape','characterPartition',
                'defaultObjectSet','initialShadingGroup','defaultLightSet','renderPartition','initialParticleSE','strokeGlobals','defaultRenderQuality','defaultRenderingList1',
                'defaultTextureList1','renderLayerManager','particleCloud1','hyperGraphInfo','shaderGlow1','hardwareRenderingGlobals','globalCacheControl','postProcessList1',
                'lambert1','defaultRenderGlobals','time1','dynController1','lightList1','hyperGraphLayout','defaultLightList1','defaultLayer','defaultHardwareRenderGlobals',
                'defaultShaderList1','ikSystem','sequenceManager1','defaultColorMgtGlobals','defaultViewColorManager','lightLinker1','layerManager','defaultResolution',
                'initialMaterialInfo','renderGlobalsList1','dof1','hardwareRenderGlobals','defaultRenderLayer','defaultRenderUtilityList1']

    doNotDelete = ["set_control","set_meshCache","set_subdiv_0", "set_subdiv_1","set_subdiv_2","set_subdiv_3","set_subdiv_4","set_subdiv_5","set_subdiv_6","set_subdiv_7","set_subdiv_8","set_subdiv_init","par_subdiv","defaultArnoldRenderOptions","defaultArnoldFilter","defaultArnoldDriver","defaultArnoldDisplayDriver"]
    doNotDelete =  mc.ls(doNotDelete)

    if keepRenderLayers == True:
        doNotDelete = doNotDelete + mc.ls(type='renderLayer')
    else:
        mc.editRenderLayerGlobals( currentRenderLayer='defaultRenderLayer' )    


    doNotDeleteObjL = []
    for each in nameSpaceToKeepL:
        doNotDeleteObjL.extend(mc.ls(each+":*"))




    intiSelection = mc.ls(selection = True)
    deletedNodes = 0



    #remove from any namespace all the nodes of my structre to clean
    mc.select(struct2CleanList, replace = True, ne = True)
    myAssetNodeList = mc.file(exportSelected = True, preview = True, preserveReferences=True, constructionHistory=True, channels=True, constraints= True, expressions=True, shader =True, force=True)
    myAssetNodeList = myAssetNodeList + doNotDelete

    # replace with the above code (too slow on large scene)
    #mc.container (name="asset1", includeNetwork = True, includeShaders=True, includeHierarchyBelow=True, includeTransform=True, preview=True, addNode= struct2CleanList, force= True)
    #myAssetNodeList = mc.ls(selection = True)+doNotDelete
    objRemFromNameSpaceI = 0
    for each in myAssetNodeList:
        if ":"in each:
            if "|grp_xgen|" in mc.ls(each, long=True)[0] or (mc.nodeType(each)=="shadingEngine" and mc.lockNode(each, q=True)[0]):
                continue # do not remove name space on xgen elements (and lockecd shading engines)
            else:
                mc.lockNode(each, lock=False)
                newEach= mc.rename(each,each.split(":")[-1],ignoreShape=True)
                objRemFromNameSpaceI += 1
                if verbose == True:
                    logMessage = u"#### {:>7}: 'softClean' Remove from any namespace:  '{}' --> '{}' ".format("Info",each,newEach)
                    print logMessage
                    outLogL.append(logMessage)

    if objRemFromNameSpaceI > 0:
        logMessage ="#### {:>7}: 'softClean' {} nodes has been removed from name spaces".format("Info",objRemFromNameSpaceI)
        if GUI == True : print logMessage
        outLogL.append(logMessage)


    #delete all nodes that do not belong to my structure
    mc.select(struct2CleanList, replace = True, ne = True)
    myAssetNodeList = mc.file(exportSelected = True, preview = True, preserveReferences=True, constructionHistory=True, channels=True, constraints= True, expressions=True, shader =True, force=True)
    myAssetNodeList = myAssetNodeList + doNotDelete

    # replace with the above code (too slow on large scene)
    #mc.container (name="asset1", includeNetwork = True, includeShaders=True, includeHierarchyBelow=True, includeTransform=True, preview=True, addNode= struct2CleanList, force= True)
    #myAssetNodeList = mc.ls(selection = True)+doNotDelete

    toDelete = list(set(mc.ls()) - set(myAssetNodeList)-set(mc.ls(lockedNodes = True))-set(mc.ls(referencedNodes = True))-set(mc.ls(type = "reference"))-set(doNotDeleteObjL)-set(undeletable))
    if toDelete:
        mc.delete(toDelete)
        deletedNodes = deletedNodes + len(toDelete)
        #mc.select(toDelete, replace = True, ne = True)


    ### delete all RN gost nodes
    refNodes = list(set(mc.ls(type = "reference")))
    for each in refNodes:
        try:
            mc.referenceQuery(each,filename=True)
        except:
            mc.lockNode(each,lock=False)
            mc.delete(each)
            deletedNodes += 1

    failedToDeleteNodeL = mc.ls(toDelete)
    deletedNodeL = list(set(toDelete) - set(failedToDeleteNodeL))
    

    logMessage ="#### {:>7}: 'softClean' has deleted {} nodes: {}".format("Info",len(deletedNodeL), deletedNodeL)
    if GUI == True : print logMessage
    outLogL.append(logMessage)

    if failedToDeleteNodeL:
        logMessage ="#### {:>7}: 'softClean' failed to delete {} nodes: {}".format("Info",len(failedToDeleteNodeL),failedToDeleteNodeL)
        if GUI == True : print logMessage
        outLogL.append(logMessage)

    #try to get back to the initial selection
    try:
        mc.select(intiSelection, replace = True, ne = True)
    except:
        mc.select(cl=True)


    ## remove all namespaces
    returnL = miscUtils.removeAllNamespace(emptyOnly=True)
    if returnL[1]:
        logMessage ="#### {:>7}: 'softClean' has deleted {} namespaces: {}".format("Info",len(returnL[1]),returnL[1])
        if GUI == True : print logMessage
        outLogL.append(logMessage)
    mc.refresh(suspend = False)
    return outSucceedB, outLogL



def importGrpLgt(lgtRig = "lgtRig_character", gui=True, hideLgt = False):

    log = miscUtils.LogBuilder(gui=gui, funcName ="importGrpLgt")

    if mc.ls("|asset"):        
        mainFilePath = mc.file(q=True, list = True)[0]
        mainFilePathElem = mainFilePath.split("/")
        assetName = mainFilePathElem[-2]
        assetType = mainFilePathElem[-3]
        assetFileType = mainFilePathElem[-1].split("-")[0].split("_")[-1]
        if  mainFilePathElem[-4] == "asset":
            lgtRigFilePath = miscUtils.normPath(miscUtils.pathJoin("$ZOMB_MISC_PATH","shading","lightRigs",lgtRig+".ma"))
            lgtRigFilePath_exp = miscUtils.normPath(os.path.expandvars(os.path.expandvars(lgtRigFilePath)))
        else:
            txt= "You are not working in an 'asset' structure directory"
            log.printL("e", txt, guiPopUp = True)
            raise ValueError(txt)
    else :
        log.printL("e", "No '|asset' could be found in this scene", guiPopUp = True)
        raise ValueError(txt)

    grpLgt =  mc.ls("grp_light*", l=True)
    mc.delete(grpLgt)

    log.printL("i", "Importing '{}'".format(lgtRigFilePath_exp))
    myImport = mc.file( lgtRigFilePath_exp, i= True, type= "mayaAscii", ignoreVersion=True, preserveReferences= True )
    mc.parent("grp_light","asset")


    lgtDefault =  mc.ls("lgt_default*", l=True, type = "light")
    if len(lgtDefault)!=1:
        txt= "'{}' 'lgt_default' light has been found".format( len(lgtDefault))
        log.printL("e", txt, guiPopUp = True)
        raise ValueError(txt)

    lgtDefault = lgtDefault[0]    

    shadingEngineList =  mc.ls("*",type = "shadingEngine")
    shadingEngine2LinkList = []
    for each in shadingEngineList:
        if each == "initialParticleSE" or each == "initialShadingGroup":
            continue
        elif not re.match('^sgr_[a-zA-Z0-9]{1,24}$', each):
                log.printL("w", "Skipping '{}' light linking, since it does not match naming convention 'sgr_materialName'".format(each))
                continue
        else:
            shadingEngine2LinkList.append(each)

    mc.lightlink( light=lgtDefault, object=shadingEngine2LinkList )
    log.printL("i", "'{}' light linked  to '{}' shaders".format(lgtDefault, len(shadingEngine2LinkList)))
    if hideLgt:
        mc.hide("|asset|grp_light")

    return dict(resultB=log.resultB, logL=log.logL)



def fixMaterialInfo (shadingEngineL = [], GUI = True):
    returnB = True
    logL = []
    fixedEhadingEngineL=[]


    if not shadingEngineL:
        shadingEngineL = mc.ls(type='shadingEngine')
        if "initialParticleSE" in shadingEngineL: shadingEngineL.remove("initialParticleSE")
        if "initialShadingGroup" in shadingEngineL: shadingEngineL.remove("initialShadingGroup")

    for each in shadingEngineL:
        if not mc.ls(mc.listConnections(each+".message",destination = True), type = "materialInfo"):
            matInfoNodeS = mc.shadingNode("materialInfo", asShader=True, name="sho_"+each.replace("sgr_","")+"_materialInfo")
            mc.connectAttr(each+".message",matInfoNodeS+".shadingGroup",force=True)
            if not mc.listConnections(matInfoNodeS+".texture[0]" , source = True):
                lambertS = mc.listConnections(each+".surfaceShader" , source = True)[-1]
                mc.connectAttr(lambertS+".message",matInfoNodeS+".texture[0]",force=True)
            fixedEhadingEngineL.append(each)

    logMessage ="#### {:>7}: 'fixMaterialInfo' regenerated materialInfo for {} SE nodes: {}".format("Info",len(fixedEhadingEngineL),fixedEhadingEngineL)
    if GUI == True: print logMessage
    logL.append(logMessage)


    return [returnB, logL]



def assetGrpClean( clean = True, GUI = True):
    returnB = True
    logL = []

    if not mc.ls("|asset"):
        logMessage = "#### {:>7}: 'assetGrpClean' No '|asset' found in this scene".format("Error")
        logL.append(logMessage)
        returnB = False
        if GUI == True : print logMessage
        return dict(returnB = returnB, logL = logL)
    else:
        mainFilePath = mc.file(q=True, list = True)[0]
        mainFilePathElem = mainFilePath.split("/")
        assetType = mainFilePathElem[-3]


    validDefaultGrpL = ["|asset|grp_geo", "|asset|grp_rig"]
    validSetGrpL = ["|asset|grp_geo", "|asset|grp_placeHolders", "|asset|grp_rig", "|asset|grp_particles","|asset|grp_xgen"]
    validChrGrpL = ["|asset|grp_geo", "|asset|grp_placeHolders", "|asset|grp_rig","|asset|grp_prx"]
    if assetType == "set":
        validGrpL = validSetGrpL
    elif assetType == "chr":
        validGrpL = validChrGrpL
    else:
        validGrpL = validDefaultGrpL


    assetRootL = mc.listRelatives ("|asset",ni=1,f=1,c=1)
    for each in assetRootL:
        if mc.nodeType(each) != 'transform' or "grp_" not in each.split("|")[-1]:
            logMessage = "#### {:>7}: 'assetGrpClean' {} is not a group named 'grp_*'".format( each)
            logL.append(logMessage)
            returnB = False
            if GUI == True : print logMessage
        else:
            if each not in validGrpL:
                if clean:
                    try:
                        logMessage = "#### {:>7}: 'assetGrpClean' deleting {} ".format("Info", each)
                        mc.delete(each)
                    except Exception,err:
                        returnB = False
                        logMessage = "#### {:>7}: 'assetGrpClean' could not delete {} --> '{}'".format( each, err)
                else:
                    logMessage = "#### {:>7}: 'assetGrpClean' to delete: {}".format("Info", each)

                logL.append(logMessage)
                if GUI == True : print logMessage

    if not logL:
        logMessage = "#### {:>7}: 'assetGrpClean' '|asset' group is clean, nothing done".format("Info")
        logL.append(logMessage)
        if GUI == True : print logMessage


    return dict(returnB=returnB, logL=logL)


def standInchecks():
    proxiL = mc.ls('prx_*', type='mesh')

    for eachProxy in proxiL:
        print "eachProxy: ", eachProxy
        mc.setAttr(eachProxy+".visibility" ,1)
        mc.setAttr(eachProxy+".aiSelfShadows" ,0)
        mc.setAttr(eachProxy+".aiVisibleInDiffuse" ,0)
        mc.setAttr(eachProxy+".aiVisibleInGlossy" ,0)
        mc.setAttr(eachProxy+".castsShadows" ,0)
        mc.setAttr(eachProxy+".receiveShadows" ,0)
        mc.setAttr(eachProxy+".motionBlur" ,0)
        mc.setAttr(eachProxy+".primaryVisibility" ,0)
        mc.setAttr(eachProxy+".visibleInReflections" ,0)
        mc.setAttr(eachProxy+".visibleInRefractions" ,0)



def setInstancerLod(inParent="", lod=2, gui=True):
    log = miscUtils.LogBuilder(gui=gui, funcName ="setInstancerLod")
    """
    lod = 0 : geometry
    lod = 1 : bounding boxes
    lod = 2 : bounding box
    """
    if lod == 0: 
        lodS = "geometry"
    elif lod == 1: 
        lodS = "bounding boxes"
    elif lod == 2: 
        lodS = "bounding box"
    else:
        log.printL("e", "'{}' is not valid for 'lod' input, pick a value between 0 and 2".format( lod))
        return

    if not inParent:
        instancerL = mc.ls( type='instancer', l =True)
    else:
        descendentL = mc.listRelatives(inParent, type='instancer',allDescendents= True, fullPath=True)
        parentRootL = mc.ls(inParent, type='instancer', l =True)
        if not descendentL: descendentL = []
        if not parentRootL: parentRootL = []
        instancerL = descendentL + parentRootL

    for each in instancerL:
        miscUtils.setAttrC(each+".levelOfDetail",lod)
    log.printL("i", "{} instancer(s) switched to {} lod: '{}'".format( len(instancerL), lodS,instancerL))
           
    return dict(resultB=log.resultB, logL=log.logL)



def assetObjectClean( inParent= "|asset|grp_geo", clean = True, GUI = True):
    log = miscUtils.LogBuilder(gui=GUI, funcName ="assetObjectClean")

    meshList, instanceList = miscUtils.getAllTransfomMeshes(inParent = inParent)
    existingGeoL = list(meshList)
    existingGeoL.extend(instanceList)
    auxObjectL=[]

    for each in existingGeoL:
        if re.match('^aux_[a-zA-Z0-9_]{1,24}$', each.split("|")[-1]):
            auxObjectL.append(each)
    if clean:
        mc.delete(auxObjectL)
        txt= "deleting {} 'aux_' objects: '{}'".format(len(auxObjectL),auxObjectL)
        log.printL("i", txt)
    else:
        txt= "{} 'aux_' objects found: '{}'".format(len(auxObjectL),auxObjectL)
        log.printL("i", txt)

    return dict(resultB=log.resultB, logL=log.logL)


def releaseDateCompare(assetType = "prp", myFilter = "", compareWith="workingfile"):
    assetDirS = os.environ["ZOMB_ASSET_PATH"]
    assetDirS = miscUtils.pathJoin(assetDirS,assetType)
    allAssetL = os.listdir(assetDirS)
    allAssetL.sort()

    animFileL=[]
    outDatedFileL = []

    print ""
    if not myFilter:
        print "listing file check for '{}' assets".format(assetType)
    elif compareWith=="workingfile":
        print "The following '{}' '{}' references files are not up to date, a newer working file has been published since the last release".format(myFilter,assetType)
    else:
        print "The following '{}' '{}' references files are not up to date compared to the other reference file".format(myFilter,assetType)

    # if assetType == "set":
    #     print "#### Warning: modeling, anim, and render working file are actualy the same file for 'sets': master"

    for each in allAssetL:
        if not ".prp" in each and each != "prp_devTest_default"and each != "Thumbs.db":
            refAnimFileS = each+"_animRef.mb"
            refAnimFilePathS = miscUtils.pathJoin(assetDirS,each,'ref',refAnimFileS)
            refRenderFileS = each+"_renderRef.mb"
            refRenderFilePathS = miscUtils.pathJoin(assetDirS,each,'ref',refRenderFileS)

            if assetType == "set":
                modelingFileS = each+"_master.ma"
                modelingFilePathS = miscUtils.pathJoin(assetDirS,each,modelingFileS)
                animFileS = each+"_master.ma"
                animFilePathS = miscUtils.pathJoin(assetDirS,each,animFileS)
                renderFileS = each+"_master.ma"
                renderFilePathS = miscUtils.pathJoin(assetDirS,each,renderFileS)
            else:
                modelingFileS = each+"_modeling.ma"
                modelingFilePathS = miscUtils.pathJoin(assetDirS,each,modelingFileS)
                animFileS = each+"_anim.ma"
                animFilePathS = miscUtils.pathJoin(assetDirS,each,animFileS)
                renderFileS = each+"_render.ma"
                renderFilePathS = miscUtils.pathJoin(assetDirS,each,renderFileS)
            
            dateAnimRefS =   "................"
            statDateAnimRef = 0
            if os.path.isfile(refAnimFilePathS):
                statInfo = os.stat(refAnimFilePathS)
                statSize = statInfo.st_size
                if statSize > 75000:
                    statDateAnimRef = statInfo.st_mtime
                    dateAnimRefS = datetime.fromtimestamp(int(statDateAnimRef)).strftime(u"%Y-%m-%d %H:%M")
                    
            dateRenderRefS = "................"
            statDateRenderRef = 0    
            if os.path.isfile(refRenderFilePathS):
                statInfo = os.stat(refRenderFilePathS)
                statSize = statInfo.st_size
                if statSize > 75000:
                    statDateRenderRef = statInfo.st_mtime
                    dateRenderRefS = datetime.fromtimestamp(int(statDateRenderRef)).strftime(u"%Y-%m-%d %H:%M")

            dateModelingS = "................"
            statDateModeling = 0
            if os.path.isfile(modelingFilePathS):
                statInfo = os.stat(modelingFilePathS)
                statSize = statInfo.st_size
                if statSize > 75000:
                    statDateModeling = statInfo.st_mtime
                    dateModelingS = datetime.fromtimestamp(int(statDateModeling)).strftime(u"%Y-%m-%d %H:%M")

            if assetType != "set":
                dateAnimS = "................"
                statDateAnim = 0
                if os.path.isfile(animFilePathS):
                    statInfo = os.stat(animFilePathS)
                    statSize = statInfo.st_size
                    if statSize > 75000:
                        statDateAnim = statInfo.st_mtime
                        dateAnimS = datetime.fromtimestamp(int(statDateAnim)).strftime(u"%Y-%m-%d %H:%M")
                        animFileL.append(each)

                dateRenderS = "................"
                statDateRender = 0
                if os.path.isfile(renderFilePathS):
                    statInfo = os.stat(renderFilePathS)
                    statSize = statInfo.st_size
                    if statSize > 75000:
                        statDateRender = statInfo.st_mtime
                        dateRenderS = datetime.fromtimestamp(int(statDateRender)).strftime(u"%Y-%m-%d %H:%M")               

            if compareWith=="workingfile":
                if assetType == "set":
                    if not myFilter:
                        print "{:^48} master: {}   animRef: {}    renderRef: {}".format(each, dateModelingS, dateAnimRefS, dateRenderRefS)
                    elif myFilter == "anim":
                        if statDateModeling > statDateAnimRef:
                            print "{:^48} master: {}    animRef: {}".format(each, dateModelingS, dateAnimRefS)
                            outDatedFileL.append(each)
                    elif myFilter == "render":
                        if statDateModeling > statDateRenderRef:
                            print "{:^48} master: {}    renderRef: {}".format(each, dateModelingS, dateRenderRefS)
                            outDatedFileL.append(each)
                else:
                    if not myFilter:
                        print "{:^48} modeling: {}    anim: {}    animRef: {}    render: {}    renderRef: {}".format(each, dateModelingS, dateAnimS, dateAnimRefS, dateRenderS, dateRenderRefS)
                    elif myFilter == "anim":
                        if statDateAnim > statDateAnimRef:
                            print "{:^48} anim: {}    animRef: {}".format(each, dateAnimS, dateAnimRefS)
                            outDatedFileL.append(each)
                    elif myFilter == "render":
                        if statDateRender > statDateRenderRef:
                            print "{:^48} render: {}    renderRef: {}".format(each, dateRenderS, dateRenderRefS)
                            outDatedFileL.append(each)
            else:
                if assetType == "set":
                    if not myFilter:
                        print "{:^48} master: {}   animRef: {}    renderRef: {}".format(each, dateModelingS, dateAnimRefS, dateRenderRefS)
                    elif myFilter == "anim":
                        if statDateRenderRef > statDateAnimRef:
                            print "{:^48} renderRef: {}    animRef: {}".format(each, dateModelingS, dateAnimRefS)
                            outDatedFileL.append(each)
                    elif myFilter == "render":
                        if statDateAnimRef > statDateRenderRef:
                            print "{:^48} animRef: {}    renderRef: {}".format(each, dateModelingS, dateRenderRefS)
                            outDatedFileL.append(each)
                else:
                    if not myFilter:
                        print "{:^48} modeling: {}    anim: {}    animRef: {}    render: {}    renderRef: {}".format(each, dateModelingS, dateAnimS, dateAnimRefS, dateRenderS, dateRenderRefS)
                    elif myFilter == "anim":
                        if statDateRenderRef > statDateAnimRef:
                            print "{:^48} renderRef: {}    animRef: {}".format(each, dateAnimS, dateAnimRefS)
                            outDatedFileL.append(each)
                    elif myFilter == "render":
                        if statDateAnimRef > statDateRenderRef:
                            print "{:^48} animRef: {}    renderRef: {}".format(each, dateRenderS, dateRenderRefS)
                            outDatedFileL.append(each)
    if outDatedFileL:
        print "#### {:>7}:  {} files are ,not up to date: {}".format("Info",len(outDatedFileL), outDatedFileL)







def rigSetRemove(gui = True, inRoot = "asset"):
    log = miscUtils.LogBuilder(gui=gui, funcName ="rigSetRemove")

    try:
        if mc.ls("asset|grp_rig", type = 'transform'):
            mc.delete("asset|grp_rig")
            log.printL("i", "rig removed")
        if mc.ls("set_meshCache", type = 'objectSet'):
            mc.delete("set_meshCache")
    except Exception,err:
        log.printL("e", err)


    resultD = miscUtils.getGroupList(gui = True, inRoot = "asset|grp_geo")
    groupL = resultD["groupL"]
    if groupL:
        mc.sets(groupL, name="set_meshCache")
        txt = "new 'set_meshCache' created, {} groups added : {}".format(len(groupL),groupL)
        log.printL("i", txt)
    else:
        log.printL("e", "Could not create 'set_meshCache', no group to add could be found")

    return dict(resultB=log.resultB, logL=log.logL)



def optimizeSetforAnim(gui = True, deteteXgen =True, deleteAnimSetContent = True):
    log = miscUtils.LogBuilder(gui=gui, funcName ="optimizeSetforAnim")

    try:
        if mc.ls("asset|grp_xgen", type = 'transform') and deteteXgen:
            mc.delete("asset|grp_xgen")
            log.printL("i", "grp_xgen removed")
        if mc.ls("set_delForAnim", type = 'objectSet') and deleteAnimSetContent:
            toDeleteL = mc.ls(mc.sets("set_delForAnim",q=1),l=1)
            mc.delete(toDeleteL)
            log.printL("i", "deteted {} object from 'set_delForAnim': {}".format(len(toDeleteL),toDeleteL))
        if mc.ls("set_delForAnim", type = 'objectSet'):
            mc.delete("set_delForAnim")
    except Exception,err:
        log.printL("e", err)


    return dict(resultB=log.resultB, logL=log.logL)





def animRefJson(gui = True, mode ="write", inputD = {} ,dryRun=True):
    log = miscUtils.LogBuilder(gui=gui, funcName ="animRefJson")

    scnInfos = infosFromScene()
    damAst = scnInfos.get("dam_entity")
    privScnFile = scnInfos["rc_entry"]

    sPublicFilePath = damAst.getPath("public", "animRef_json")
    sPrivFilePath = damAst.getPath("private", "animRef_json")

    if mode== "write" or mode== "add":
        if inputD:
            if mode== "write":
                animRefcontentD = inputD
            else:
                animRefcontentD = jsonRead(sPublicFilePath)
                animRefcontentD.update(inputD)

            if not os.path.isdir(os.path.dirname(sPrivFilePath)):
                os.makedirs(os.path.dirname(sPrivFilePath))
            jsonWrite(sPrivFilePath, animRefcontentD)

            # let's publish
            sComment = "from animRef v{}".format(privScnFile.versionFromName())
            pubFile = damAst.getRcFile("public", "animRef_json", weak=True)
            parentDir = pubFile.parentDir()
            parentDir.publishFile(sPrivFilePath, autoLock=True, autoUnlock=True, comment=sComment, dryRun=dryRun, saveChecksum=False)
            txt = "Published new animRef.json: {}".format(sPublicFilePath)
            log.printL("i", txt)
        else:
            txt = "nothing to write, inputD is empty : {}".format(inputD)
            log.printL("e", txt)
    elif mode == "read":
        animRefcontentD = jsonRead(sPublicFilePath)

    return dict(resultB=log.resultB, logL=log.logL, animRefcontentD = animRefcontentD)



def compareGrpStruct2animRef(gui = True):
    log = miscUtils.LogBuilder(gui=gui, funcName ="compareGrpStruct2animRef")

    animRefJsonResD = animRefJson(gui = gui, mode ="read")
    animRefGroupL = animRefJsonResD["animRefcontentD"]["groupL"]

    getGroupListResD = miscUtils.getGroupList(gui = gui, inRoot = "asset|grp_geo")
    currentFileGroupL = getGroupListResD["groupL"]

    missingGrpInAnimRefL = list(set(currentFileGroupL)-set(animRefGroupL))
    missingGrpInCurrentFileL = list(set(animRefGroupL)-set(currentFileGroupL))

    if not missingGrpInAnimRefL and not  missingGrpInCurrentFileL:
        log.printL("i", "group structure is conform to animRef")
    else:
        if missingGrpInAnimRefL :
            txt = "{} group(s) could not be found in the animRef file: '{}': ".format(len(missingGrpInAnimRefL), missingGrpInAnimRefL)
            log.printL("e", txt)
        if missingGrpInCurrentFileL :
            txt = "{} group(s) could not be found in the current file: '{}': ".format(len(missingGrpInCurrentFileL), missingGrpInCurrentFileL)
            log.printL("e", txt)

    return dict(resultB=log.resultB, logL=log.logL)
    


def UVSetCount(gui = True):
    log = miscUtils.LogBuilder(gui=gui, funcName ="UVSetCount")
    multiUVmapObjL=[]

    meshList, instanceList = miscUtils.getAllTransfomMeshes(inParent = "|asset|grp_geo")

    for each in meshList:
        uvMapList = mc.polyUVSet(each, query=True, allUVSets=True )
        if "uvSet_display" in uvMapList:
            uvMapList.remove("uvSet_display")
        if len(uvMapList)>1:
            multiUVmapObjL.append(each)

    if multiUVmapObjL :
        txt = "{} meshes has several uv maps, please clean: '{}': ".format(len(multiUVmapObjL), multiUVmapObjL)
        log.printL("e", txt)

    return dict(resultB=log.resultB, logL=log.logL)



def lookForBumpNodes(gui = True):
    log = miscUtils.LogBuilder(gui=gui, funcName ="lookForBumpNodes")

    bumpTypeL = ["aiBump3d","bump3d","bump2d","aiBump2d"]
    bumpNodeL = mc.ls(type=bumpTypeL)

    if bumpNodeL :
        txt = "{} bump nodes found in this scene, please replace with displacement nodes: '{}': ".format(len(bumpNodeL), bumpNodeL)
        log.printL("e", txt)
    else: 
        bumpNodeL = []
    return dict(resultB=log.resultB, logL=log.logL, bumpNodeL=bumpNodeL)



def dmnToon2aiSurface(gui = True):
    log = miscUtils.LogBuilder(gui=gui, funcName ="dmnToon2aiSurface")
    wrongShaderL =[]

    shadingEngineL = mc.ls(type="shadingEngine")
    if "initialParticleSE" in shadingEngineL: shadingEngineL.remove("initialParticleSE")
    if "initialShadingGroup" in shadingEngineL:shadingEngineL.remove("initialShadingGroup")
    for eachSE in shadingEngineL:
        aiInputNodeS = mc.listConnections (eachSE+".aiSurfaceShader", source=True, destination=False)
        aiInputNodeTypeS = mc.nodeType(aiInputNodeS)
        if aiInputNodeTypeS != "dmnToon":
            wrongShaderL.append(eachSE) 
    if wrongShaderL :
        txt = "{} shaders are not valid, please make sure a 'dmn_toon' is plug to the 'aiSurface' on the folloing shading engines: '{}': ".format(len(wrongShaderL), wrongShaderL)
        log.printL("e", txt)

    return dict(resultB=log.resultB, logL=log.logL, wrongShaderL=wrongShaderL)


def deleteUVs(meshL=[], doNotDeleteL=["map1","uvSet_display","uv_preview"], inParent = "asset|grp_geo", gui = True):
    #pour effacer tous les uvs
    log = miscUtils.LogBuilder(gui=gui, funcName ="deleteUVs")
    cleanedMeshL = []

    if not meshL and inParent:
        meshList, instanceList = miscUtils.getAllTransfomMeshes(inParent = inParent)
        meshL = list(meshList)
        meshL.extend(instanceList)

    txt = "About to clean UVS on: '{}': ".format(meshL)
    log.printL("i", txt)

    txt = "Following UVs will not be deleted: '{}': ".format(doNotDeleteL)
    log.printL("i", txt)


    for meshS in meshL:
        sUvSetList = mc.polyUVSet(meshS,q=1,auv=1)
        sDeletedUvList = []
        for each in reversed(sUvSetList):
            if each not in doNotDeleteL:
                mc.polyUVSet(meshS,d=1, uvSet=each)
                sDeletedUvList.append(each)
                if meshS not in cleanedMeshL:
                    cleanedMeshL.append(meshS)    
        
        for i in pm.getAttr(meshS+".uvSet", mi=True):
            if i >= len(mc.polyUVSet(meshS,q=1,auv=1)):
                mc.removeMultiInstance(meshS+".uvSet[{}]".format(i))
        if sDeletedUvList:
            txt = "{} Uvs deleted on {} : '{}': ".format(len(sDeletedUvList),meshS ,sDeletedUvList)
            log.printL("i", txt)

    txt = "{} meshes have been UV cleaned: '{}': ".format(len(cleanedMeshL), cleanedMeshL)
    log.printL("i", txt)

    return dict(resultB=log.resultB, logL=log.logL)