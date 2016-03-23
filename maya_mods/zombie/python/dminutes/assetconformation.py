import maya.cmds as mc
import pymel.core as pm
import re
import string
import os

from pytd.util.logutils import logMsg


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
    



def createSubdivSets(GUI = True):
    """
    This function creates a "set_subdiv_init" that gather all the "geo_*" objects found in the scene.
    and bunch of empty sets named "set_subdiv_X" (where X is a digit) are also created.
    All theses sets are liked to a partition named 'par_subdiv'. this prevent a "geo_*" objects to exists in 2 different "set_subdiv_*" sets.
    the user must afterward move the all the "geo_*" objects from the "set_subdiv_init" set to the "set_subdiv_X" depending the level of subdivision that is requiered.
    then, the setSubdiv() procedure must be executed to apply the subdivision to the objects through the shapes attributes  
    """
    returnB = True
    logL = []

    subdivSets = mc.ls("set_subdiv_*", type = "objectSet")
    subdivPartitions = mc.ls("par_*", type = "partition")
    existingGeo = mc.ls("geo_*", type = "transform")
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

    geoInSet = mc.sets(subdivSets, query = True)
    if geoInSet == None: geoInSet = []

    addedGeoToInitSet = []
    for eachGeo in existingGeo:
        if eachGeo not in geoInSet:
            mc.sets(eachGeo, forceElement="set_subdiv_init")
            addedGeoToInitSet.append(eachGeo)

    if addedGeoToInitSet:
        logMessage = "#### {:>7}: 'createSubdivSets' {} geo added to 'set_subdiv_init': {}".format("Info",len(addedGeoToInitSet),addedGeoToInitSet)
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
        logL.append(logMessage)
        returnB = False
    processedTransL =[]
    skippedTransL =[]
    for eachSetSubdiv in subdivSets:
        geoInSet = mc.ls(mc.sets(eachSetSubdiv, query = True),l=True)
        if not geoInSet: geoInSet = []       
        if eachSetSubdiv != "set_subdiv_init" and geoInSet:
            subdivLevel =  int(eachSetSubdiv.split("set_subdiv_")[1])
            previewSubdivLevel = subdivLevel    
            if  0 <= subdivLevel <=9 :
                for eachGeo in geoInSet:
                    if mc.nodeType(eachGeo)!="mesh":
                        eachGeoShape =  mc.listRelatives(eachGeo, noIntermediate=True, shapes=True, path=True)[0]
                    eachGeoParentL = mc.listRelatives(eachGeoShape, allParents = True, fullPath = True)
                    if not set(eachGeoParentL) & set(processedTransL):
                        mc.setAttr(eachGeoShape+".displaySmoothMesh",0)
                        mc.setAttr(eachGeoShape+".useSmoothPreviewForRender",0)
                        mc.setAttr(eachGeoShape+".renderSmoothLevel",0)
                        mc.setAttr(eachGeoShape+".useGlobalSmoothDrawType",1)
                        if not mc.getAttr(eachGeoShape+".smoothLevel", lock = True):
                            if previewSubdivLevel == 0:
                                mc.setAttr(eachGeoShape+".smoothLevel", 0)
                            if previewSubdivLevel == 1:
                                mc.connectAttr("|asset|grp_geo.smoothLevel1", eachGeoShape+".smoothLevel", f=True)
                            if previewSubdivLevel > 1:
                                mc.connectAttr("|asset|grp_geo.smoothLevel2", eachGeoShape+".smoothLevel",f=True)
                        if not mc.attributeQuery ("aiSubdivType", node = eachGeoShape , exists = True):
                            logMessage = "#### {:>7}: 'setSubdiv' {}.aiSubdivType attribute coud not be found, please check if Arnold is properly installed on your computer".format(eachGeoShape)
                            if GUI == True: raise ValueError(logMessage)
                            logL.append(logMessage)
                            returnB = False
                        else:
                            mc.setAttr(eachGeoShape+".aiSubdivType",1)
                            mc.setAttr(eachGeoShape+".aiSubdivIterations",subdivLevel)
                        processedTransL.append(eachGeo)
                    else:
                        skippedTransL.append(eachGeo)
          
    mc.setAttr("|asset|grp_geo.smoothLevel1", 1)
    mc.setAttr("|asset|grp_geo.smoothLevel2", 2)
    
    if processedTransL and not skippedTransL:
        logMessage = "#### {:>7}: 'setSubdiv' {} meshes processed".format("Info", len(processedTransL))
        if GUI == True: print logMessage
        logL.append(logMessage)
    if processedTransL and skippedTransL:
        logMessage = "#### {:>7}: 'setSubdiv' {} meshes processed and {} instances skipped ".format("Info", len(processedTransL), len(skippedTransL))
        if GUI == True: print logMessage
        logL.append(logMessage)

    if "set_subdiv_init" in subdivSets and mc.sets("set_subdiv_init", query = True) != None:
        logMessage = "#### {:>7}: 'setSubdiv' A geo object is still in the 'set_subdiv_init', please asssign it to a 'set_subdiv*'".format("Error")
        if GUI == True: mc.confirmDialog( title='Error:', message=logMessage, button=['Ok'], defaultButton='Ok' )
        logL.append(logMessage)
        returnB = False

    return dict(returnB=returnB, logL=logL)



def createSetMeshCache(inParent= "|asset|grp_geo", GUI = True):
    returnB = True
    logL = []

    meshList, instanceList = miscUtils.getAllTransfomMeshes(inParent = inParent)
    existingGeoL = list(meshList)
    existingGeoL.extend(instanceList)

    if not existingGeoL:
        logMessage = "#### {:>7}: 'createSetMeshCache' geometries could be foud under '{}'".format( inParent)
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

    log = miscUtils.LogBuilder(gui=gui, funcName ="setShadingMask")

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

    dmnMask05_R = []# visages, custom
    dmnMask05_G = []# yeux, custom
    dmnMask05_B = []# bouches, custom

    dmnMask06_R = []# shading decor custom, gradient sourcil sur aurelien et francis, ombre orbites sirus
    dmnMask06_G = []# shading decor custom
    dmnMask06_B = []# shading decor custom

    dmnMask07_R = []# lighting custom
    dmnMask07_G = []# lighting custom
    dmnMask07_B = []# lighting custom

    dmnMask08_R = []# lighting custom
    dmnMask08_G = []# lighting custom
    dmnMask08_B = []# lighting custom

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
        if  mainFilePathElem[-4] != "asset":
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
    def __init__(self):
        if mc.ls("|asset"):        
            self.mainFilePath = mc.file(q=True, list = True)[0]
            self.mainFilePathElem = self.mainFilePath.split("/")
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

        mc.refresh()

        if  not (self.mainFilePathElem[-4] == "asset" or self.mainFilePathElem[-5] == "asset"):
            raise ValueError("#### Error: you are not working in an 'asset' structure directory")

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
            print self.renderFilePath_exp
            if not os.path.isfile(self.renderFilePath_exp):
                print "#### {:>7}: could not find: '{}', shading has not been done yet, let's try using '{}'".format("Error",self.sourceFile, self.sourceFile.replace("Ref","") )
                self.renderFilePath = miscUtils.normPath(miscUtils.pathJoin("$ZOMB_TEXTURE_PATH",self.assetType,self.assetName,self.assetName+"_"+self.sourceFile+".ma"))
                self.renderFilePath_exp = miscUtils.normPath(os.path.expandvars(os.path.expandvars(self.renderFilePath)))

        else:
            raise ValueError("#### Error: the choosen sourceFile '"+sourceFile+"'' is not correct")


        if reference:
            print "#### {:>7}: reference '{}'".format("Info",self.renderFilePath_exp)
            mc.file( self.renderFilePath_exp, type= fileType, ignoreVersion=True, namespace=self.sourceFile, preserveReferences= True, reference = True )
        else:
            print "#### {:>7}: importing '{}'".format("Info",self.renderFilePath_exp)
            mc.file( self.renderFilePath_exp, i= True, type= fileType, ignoreVersion=True, namespace=self.sourceFile, preserveReferences= False )
        mc.refresh()


    def cleanFile(self, verbose = False):
        toReturnB = True
        outLogL = []
        # mc.select("persp")
        # mc.select(clear=True)
        mc.refresh()

        refNodeList = mc.ls(type = "reference")
        for each in refNodeList:
            if re.match('^render[0-9]{0,3}[:]{0,1}[a-zA-Z0-9_]{0,128}RN$', each) or re.match('^anim[0-9]{0,3}[:]{0,1}[a-zA-Z0-9_]{0,128}RN$', each) or re.match('^renderRef[0-9]{0,3}[:]{0,1}[a-zA-Z0-9_]{0,128}RN$', each) or re.match('^animRef[0-9]{0,3}[:]{0,1}[a-zA-Z0-9_]{0,128}RN$', each) or re.match('^modeling[0-9]{0,3}[:]{0,1}[a-zA-Z0-9_]{0,128}RN$', each) or re.match('^previz[0-9]{0,3}[:]{0,1}[a-zA-Z0-9_]{0,128}RN$', each):
                fileRef= pm.FileReference(each)
                #fileRef = mc.referenceQuery(each,filename=True)# other way to do it
                try:
                    logMessage ="#### {:>7}: 'cleanFile' removing reference '{}'".format("Info",fileRef.path)
                    if verbose == True : print logMessage
                    outLogL.append(logMessage)
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

                logMessage ="#### {:>7}: 'cleanFile' removing namespace and its content: '{:<10}' ".format("Info",each)
                if verbose == True : print logMessage
                outLogL.append(logMessage)

        if not outLogL:
            logMessage ="#### {:>7}: 'cleanFile' nothing to clean, no '_render', '_renderRef','_anim','_animRef', '_previz' or '_modeling' reference found".format("Info",each)
            if verbose == True : print logMessage
            outLogL.append(logMessage)
        mc.refresh()

        return toReturnB, outLogL


    

    def initSourceTargetList(self, sourceFile = "", targetObjects = "set_meshCache"):
        """
        targetObjects = "set_meshCache" "selection" or a given list
            - set_meshCache, or given list :  the method initiate the sourceList (prefixing targets obj with the name space) and targetList automaticaly
            - selection, (2 transforms expected) fisrt object selected is the source, the second is the target

        """
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
                    print ("#### {:>7}: no 'set_meshCache' could be found".format("Error"))
                    errorOnTarget = errorOnTarget + 1
                    targetObjects= []                   

            for eachTarget in targetObjects:
                if mc.ls(eachTarget):
                    if mc.nodeType (eachTarget)!= "transform":
                        print ("#### {:>7}: no '{}' target object has not the right type, only 'transform' nodes accepted".format("Error", eachTarget))
                        errorOnTarget = errorOnTarget + 1
                    else:
                        self.targetList.append(eachTarget)
                else:
                    print ("#### {:>7}: no '{}' target object could be found".format("Error", eachTarget))
                    errorOnTarget = errorOnTarget + 1

            for eachTarget in self.targetList:
                #eachSource = sourceFile+":"+("|"+sourceFile+":").join(eachTarget.split("|"))
                eachSource = ("|"+sourceFile+":").join(eachTarget.split("|"))

                if mc.ls(eachSource):
                    if mc.nodeType (eachSource)!= "transform":
                        print ("#### {:>7}: no '{}' source object has not the right type, only 'transform' nodes accepted".format("Error", eachSource))
                        errorOnSource = errorOnSource + 1
                    else:
                        self.sourceList.append(eachSource)
                else:
                    errorOnSource = errorOnSource + 1
                    print ("#### {:>7}: target --> '{:<30}'  has no correspondig source --> '{}'".format("Error", eachTarget, eachSource))

            if errorOnTarget != 0: self.targetList =[]
            if errorOnSource != 0: self.sourceList =[]


        elif targetObjects == "selection":
            mySelection = mc.ls(selection=True)
            if len(mySelection)== 2:
                if mc.nodeType(mySelection[0]) == "transform":
                    self.sourceList = [mySelection[0]]
                else:
                    print ("#### {:>7}: selected source is not a 'transform' node".format("Error"))
                    errorOnSource = errorOnSource + 1

                if mc.nodeType(mySelection[1]) == "transform":
                    self.targetList = [mySelection[1]]
                else:
                    print ("#### {:>7}: selected target is not a 'transform' node".format("Error"))
                    errorOnTarget = errorOnTarget + 1
            else:
                print ("#### {:>7}: 2 objects must be selected, source first then target".format("Error"))
                print ("#### {:>7}: selection {}".format("Error", mySelection))
    

        else:
            raise ValueError("#### Error: can't recognize targetObjects: '"+targetObjects+"'' value, should be 'set_meshCache' or a list")

        if self.targetList and errorOnTarget == 0 and errorOnSource == 0:
            self.sourceTargetListMatch = True
            print "#### {:>7}: target and source list are conform".format("Info")
        else:
            self.sourceTargetListMatch = False
            print "#### {:>7}: target list and source list not conform".format("Error")




    def printSourceTarget(self):
        if self.targetList and len(self.sourceList) == len(self.targetList):
            targetNb = len (self.targetList)
            i = 0
            while i<targetNb:
                print self.sourceList[i]+" --> "+self.targetList[i]
                i+=1
        else:
            print "#### {:>7}: target list and source list not conform".format("Error")
            print "#### {:>7}: source {}".format( self.sourceList)
            print "#### {:>7}: target {}".format( self.targetList)



    def checkSourceTargetTopoMatch(self):
        if self.sourceTargetListMatch == True:
            i = 0
            topoMismatch = 0
            while  i < len(self.targetList):

                sourceVrtxCnt = len(mc.getAttr(self.sourceList[i]+".vrts[:]"))
                targetVrtxCnt = len(mc.getAttr(self.targetList[i]+".vrts[:]"))
                if sourceVrtxCnt != targetVrtxCnt:
                    topoMismatch = topoMismatch + 1
                    print ("#### {:>7}: Vertex number mismatch: '{}' vertex nb = {} -- '{}' vertex nb = {}".format(self.sourceList[i],sourceVrtxCnt, self.targetList[i],targetVrtxCnt))

                # sourceBBox =  mc.exactWorldBoundingBox(self.sourceList[i])
                # targetBBox =  mc.exactWorldBoundingBox(self.targetList[i])
                # if masterBBox != targetBBox:
                #     print ("#### {:>7}: Bounding box  mismatch: '{}' -- '{}'".format("Warning",self.sourceList[i], self.targetList[i]))

                areaTolF = 0.01 #percentage world area tolerance
                sourceWorldArea =  mc.polyEvaluate(self.sourceList[i], worldArea= True)
                targetWorldArea =  mc.polyEvaluate(self.targetList[i], worldArea= True)
                areaDifF = abs(float(sourceWorldArea - targetWorldArea)/sourceWorldArea *100)
                if areaDifF > areaTolF:
                    print "#### {:>7}: World area is {:.3f} percent different: '{}' -- '{}'".format("Warning",areaDifF, self.sourceList[i], self.targetList[i])

                i+=1

            if topoMismatch == 0:
                self.sourceTargetTopoMatch = True
            else:
                self.sourceTargetTopoMatch = False
        else:
            print "#### {:>7}: cannot check topoligie, target and source list mismatch".format("Error")



    def transferUV(self):

        if self.sourceTargetListMatch == True:
            i = -1
            uvTransferFailed = 0
            while i < len(self.targetList)-1:
                i+=1
                shapeOrig = False
                sourceShapeList = mc.ls(mc.listRelatives(self.sourceList[i], allDescendents = True, fullPath = True, type = "mesh"), noIntermediate = True, l=True)
                if len(sourceShapeList)==0:
                    print ("#### {:>7}: source, no shape coud be found under transform : '{}'".format(self.sourceList[i]))
                    uvTransferFailed +=1
                    continue
                elif len(sourceShapeList)==1:
                    sourceShape = sourceShapeList[0]
                else:
                    print ("#### {:>7}: several 'shapes' were found under: '{}' transform".format(self.sourceList[i]))
                    uvTransferFailed +=1
                    continue

                targetShapeList = mc.ls(mc.listRelatives(self.targetList[i], allDescendents = True, fullPath = True, type = "mesh"), noIntermediate = False, l=True)
                if len(targetShapeList)==0:
                    print ("#### {:>7}: target, no shape coud be found under transform: '{}'".format(self.targetList[i]))
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
                        print ("#### {:>7}: several 'ShapeOrig' were found under: '{}' transform".format("Error",self.targetList[i]))
                        uvTransferFailed +=1
                        continue

                # sampleSpace: Selects which space the attribute transfer is performed in. 
                # 0 is world space, (default)
                # 1 is model space, 
                # 4 is component-based, 
                # 5 is topology-based

                #print ("#### {:>7}: 'transferUV' from '{}' --> {}".format("Drebug",sourceShape,targetShape))
                sampleSpace = 4
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
                print "#### {:>7}: UVs has been transfered properly for all the {} object(s)".format("Info",len(self.targetList))
            else:
                print ("#### {:>7}: UVs transfer failed for {} object(s)".format("Error",uvTransferFailed))

        else:
            print "#### {:>7}: cannot transfer uvs, target and source list mismatch".format("Error")
            return False



        if uvTransferFailed == 0:
            return True
        else:
            return False



    def transferSG(self):
        if self.sourceTargetListMatch == True:
            i = -1
            sgTransferFailed = 0
            while i < len(self.targetList)-1:
                i+=1
                sourceShapeList = mc.ls(mc.listRelatives(self.sourceList[i], allDescendents = True, fullPath = True, type = "mesh"), noIntermediate = True, l=False)
                if len(sourceShapeList)==0:
                    print ("#### {:>7}: source, no shape coud be found under transform : '{}'".format(self.sourceList[i]))
                    sgTransferFailed +=1
                    continue
                elif len(sourceShapeList)==1:
                    sourceShape = sourceShapeList[0]
                else:
                    print ("#### {:>7}: several 'shapes' were found under: '{}' transform".format(self.sourceList[i]))
                    sgTransferFailed +=1
                    continue

                targetShapeList = mc.ls(mc.listRelatives(self.targetList[i], allDescendents = True, fullPath = True, type = "mesh"), noIntermediate = True, l=False)
                if len(targetShapeList)==0:
                    print ("#### {:>7}: target, no shape coud be found under transform: '{}'".format(self.sourceList[i]))
                    sgTransferFailed +=1
                    continue
                elif len(targetShapeList)==1:
                    targetShape = targetShapeList[0]
                else:
                    print ("#### {:>7}: several 'shapes' were found under: '{}' transform".format(self.sourceList[i]))
                    sgTransferFailed +=1
                    continue

                sourceShadEngList = mc.ls(mc.listHistory(sourceShape,future = True),type="shadingEngine")
                #print sourceShape+" --> "+targetShape
                if len(sourceShadEngList) == 1:
                    mc.sets(targetShape,e=True, forceElement=sourceShadEngList[0])
                elif len(sourceShadEngList) > 0:
                    mc.transferShadingSets(sourceShape,targetShape, sampleSpace=0, searchMethod=3)
                else:
                    print ("#### {:>7}: no 'shader' found on source object: '{}' transform".format("Error",sourceShape))
                    sgTransferFailed +=1


            if sgTransferFailed ==0:
                print "#### {:>7}: materials has been transfered properly for all the {} object(s)".format("Info",len(self.targetList))
            else:
                print ("#### {:>7}: materials transfer failed for {} object(s)".format("Error",sgTransferFailed))

        else:
            print "#### {:>7}: cannot transfer materials, target and source list mismatch".format("Error")
            return False
        if sgTransferFailed == 0:
            return True
        else:
            return False


    def removeNameSpaceFromShadNodes(self, objectList = [], verbose = False):
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
                        if verbose: print "#### {:>7}: Remove from any namespace:  '{}' --> '{}' ".format("Info",each,newEach)
        print ("#### {:>7}: name space removed from {} shading nodes(s)".format("Info",renamedShadNodeNb))
        mc.refresh()


    def disconnectAiMaterials(self):
        """
        not finished yet
        """
        mc.refresh()
        shadEngineList = mc.ls("*",type = "shadingEngine")
        shadEngineList.remove("initialParticleSE")
        shadEngineList.remove("initialShadingGroup")
        if not shadEngineList :
            print "#### {:>7}: no shading engine".format("Error")
            return
        for each in shadEngineList:
            matShadNode =  mc.listConnections(each+'.aiSurfaceShader',connections = True, plugs=True)
            mc.disconnectAttr(matShadNode[1],matShadNode[0])


    def smoothPolyDisplay(self, inMeshList = [], verbose = False, shapeOrigOnly = True):
        intSel = mc.ls(selection=True)
        for each in inMeshList:
                shapeOrigL = miscUtils.getShapeOrig(TransformS = each)
                if len(shapeOrigL)==0:
                    if shapeOrigOnly:
                        print "#### {:>7}: 'smoothPolyDisplay' no shapeOrig found under '{}' skipping operation on this mesh ".format("Warning",len(shapeOrigL),each, shapeOrigL)
                        continue
                    else:
                        print "#### {:>7}: 'smoothPolyDisplay' no shapeOrig found under '{}', proceeding with the shape".format("Warning",len(shapeOrigL),each, shapeOrigL)
                        target = each
                elif len(shapeOrigL)==1:
                    target = shapeOrigL[0]
                elif len(shapeOrigL)>1: 
                    target = shapeOrigL[0]
                    print "#### {:>7}: 'smoothPolyDisplay' {} shapeOrig found under '{}', proceeding with the first one: '{}'".format("Warning",len(shapeOrigL),each, target)

                mc.polySoftEdge (target, angle=180, constructionHistory=True)
                mc.bakePartialHistory(target, prePostDeformers=True)
                if verbose == True: print "#### {:>7}: smoothPolyDisplay -> '{:^30}'".format("Info",each)
        print ("#### {:>7}: smoothPolyDisplay done on {} object(s)".format("Info",len(inMeshList)))
        mc.select(intSel, replace=True)



    def transferRenderAttr(self, transferArnoldAttr =  True):
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
                        print ("#### {:>7}: {} shape(s) found under transform: '{}'".format(len(sourceShapeLn), self.sourceList[i]))
                    if len(targetShapeLn) != 1:
                        print ("#### {:>7}: {} shape(s) found under transform: '{}'".format(len(targetShapeLn), self.targetList[i]))
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
                    print ("#### {:>7}: Rendering attribute transfer failed for {} shape(s)".format(shapeTransferFailed))
                if attrTransferFailed != 0:
                    print ("#### {:>7}: Rendering attribute transfer failed for {} attribute(s)".format("Warning",attrTransferFailed))
            else:
                print ("#### {:>7}: Rendering attribute transfered properly {} on object(s)".format("Info",len(self.targetList)))
        else:
            print "#### {:>7}: cannot transfer rendering attributes, target and source list mismatch".format("Error")

        if shapeTransferFailed == 0:
            return True
        else:
            return False



    def disconnectAllShadEng(self, objectList = [], verbose = False):
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
        print "#### {:>7}: shader have been disconnected on {} object(s) ".format("Info", len(disconnectShapes))



    def deleteUnusedShadingNodes(self):
        # mc.select("persp")
        # mc.select(clear=True)

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

            if deletedNodeList : print "#### {:>7}: {:>4} unused shading nodes deleted: {}".format("Info",  len(deletedNodeList), deletedNodeList)
            if undeletableNodeList: print "#### {:>7}: {:>4} unused shading nodes could not be deleted: {}".format("Info",  len(undeletableNodeList), undeletableNodeList)
        mc.refresh()





def softClean(struct2CleanList=["asset"], verbose = False, keepRenderLayers = True,GUI = True, nameSpaceToKeepL = []):
    """
    this script intend to remove from the scene every node that do not has a link with the selected structure.
    It also clean the empty namespaces
    """
    outSucceedB = True
    outLogL = []
    mc.refresh()
    undeletable = ['sideShape','frontShape','front','sideShape','side','perspShape','perspShape','persp','topShape','top','topShape','frontShape','characterPartition',
                'defaultObjectSet','initialShadingGroup','defaultLightSet','renderPartition','initialParticleSE','strokeGlobals','defaultRenderQuality','defaultRenderingList1',
                'defaultTextureList1','renderLayerManager','particleCloud1','hyperGraphInfo','shaderGlow1','hardwareRenderingGlobals','globalCacheControl','postProcessList1',
                'lambert1','defaultRenderGlobals','time1','dynController1','lightList1','hyperGraphLayout','defaultLightList1','defaultLayer','defaultHardwareRenderGlobals',
                'defaultShaderList1','ikSystem','sequenceManager1','defaultColorMgtGlobals','defaultViewColorManager','lightLinker1','layerManager','defaultResolution',
                'initialMaterialInfo','renderGlobalsList1','dof1','hardwareRenderGlobals','defaultRenderLayer','defaultRenderUtilityList1']

    doNotDelete = ["set_control","set_meshCache","set_subdiv_0", "set_subdiv_1","set_subdiv_2","set_subdiv_3","set_subdiv_init","par_subdiv","defaultArnoldRenderOptions","defaultArnoldFilter","defaultArnoldDriver","defaultArnoldDisplayDriver"]
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
    validSetGrpL = ["|asset|grp_geo", "|asset|grp_placeHolders", "|asset|grp_rig"]
    validChrGrpL = ["|asset|grp_geo", "|asset|grp_placeHolders", "|asset|grp_rig"]
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