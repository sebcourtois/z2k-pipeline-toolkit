import maya.cmds as mc
import pymel.core as pm
import re
import string
import miscUtils
import os

from pytd.util.logutils import logMsg


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
    



def createSubdivSets():
    """
    This function creates a "set_subdiv_init" that gather all the "geo_*" objects found in the scene.
    and bunch of empty sets named "set_subdiv_X" (where X is a digit) are also created.
    All theses sets are liked to a partition named 'par_subdiv'. this prevent a "geo_*" objects to exists in 2 different "set_subdiv_*" sets.
    the user must afterward move the all the "geo_*" objects from the "set_subdiv_init" set to the "set_subdiv_X" depending the level of subdivision that is requiered.
    then, the setSubdiv() procedure must be executed to apply the subdivision to the objects through the shapes attributes  
    """
    print ""
    print "#### info: exectute 'createSubdivsets()'"
    subdivSets = mc.ls("set_subdiv_*", type = "objectSet")
    subdivPartitions = mc.ls("par_*", type = "partition")
    existingGeo = mc.ls("geo_*", type = "transform")
    subdivSetsInitList = ["set_subdiv_init","set_subdiv_0","set_subdiv_1","set_subdiv_2","set_subdiv_3"]
    if not existingGeo:
        print "#### error: no 'geo_*' object could be foud in the scene"
        return


    if "par_subdiv" not in subdivPartitions:
        mc.partition( name="par_subdiv")

    for eachSet in subdivSetsInitList:
        if eachSet not in subdivSets:
            print "#### info: creates: "+eachSet
            mc.sets(name=eachSet, empty=True)
            mc.partition( eachSet, add="par_subdiv")

    geoInSet = mc.sets(subdivSets, query = True)
    if geoInSet == None: geoInSet = []

    for eachGeo in existingGeo:
        if eachGeo not in geoInSet:
            mc.sets(eachGeo, forceElement="set_subdiv_init")
            print "#### info: add geo to 'set_subdiv_init': "+eachGeo

     
def setSubdiv():
    """
    creates 'smoothLevel1' and 'smoothLevel2' extra attributes on the 'grp_geo' 
    and connect them to the smoothLevel (preview subdiv level) of the geo shapes
    """
    if not mc.ls("|asset|grp_geo", l = True):
        msg = "#### error 'setSubdiv': no '|asset|grp_geo' found"
        raise ValueError(msg)

    
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
        msg = "#### error 'setSubdiv' : no subdivision set could be found (set_subdiv_*). Please create them first"
        raise ValueError(msg)

    for eachSetSubdiv in subdivSets:
        geoInSet = mc.sets(eachSetSubdiv, query = True)
        if geoInSet == None: geoInSet = []
        
        if eachSetSubdiv != "set_subdiv_init" and geoInSet:
            subdivLevel =  int(eachSetSubdiv.split("set_subdiv_")[1])
            previewSubdivLevel = subdivLevel    
            if  0 <= subdivLevel <=9 :
                print "#### info: scaning 'set_subdiv_"+str(subdivLevel)+"'"
                for eachGeo in geoInSet:
                    eachGeoShape =  mc.listRelatives(eachGeo, noIntermediate=True, shapes=True, path=True)[0]
                    print "    "+eachGeoShape
                    mc.setAttr(eachGeoShape+".displaySmoothMesh",2)
                    mc.setAttr(eachGeoShape+".useSmoothPreviewForRender",0)
                    mc.setAttr(eachGeoShape+".renderSmoothLevel",0)
                    if previewSubdivLevel == 1:
                        mc.connectAttr("|asset|grp_geo.smoothLevel1", eachGeoShape+".smoothLevel", f=True)
                    if previewSubdivLevel > 1:
                        mc.connectAttr("|asset|grp_geo.smoothLevel2", eachGeoShape+".smoothLevel",f=True)
                    if not mc.attributeQuery ("aiSubdivType", node = eachGeoShape , exists = True):
                        print "#### error: "+eachGeoShape+".aiSubdivType attribute coud not be found, please check if Arnold is properly installed on your computer"
                    else:
                        mc.setAttr(eachGeoShape+".aiSubdivType",1)
                        mc.setAttr(eachGeoShape+".aiSubdivIterations",subdivLevel)

    if "set_subdiv_init" in subdivSets and mc.sets("set_subdiv_init", query = True) != None:
        print "#### warning: a geo object is still in the 'set_subdiv_init', please asssign it to a 'set_subdiv*'"

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

def setShadingMask(selectFailingNodes = False, verbose = True, gui = True):
    if verbose == True: print ""
    if verbose == True: print "#### {:>7}: running setShadingMask(selectFailingNodes = {}, verbose = {} )".format("info",selectFailingNodes, verbose)

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

    dmnMask05_R = []# visages, decor custom
    dmnMask05_G = []# yeux, decor custom
    dmnMask05_B = []# bouches, decor custom

    dmnMask06_R = []# shading custom
    dmnMask06_G = []# shading custom
    dmnMask06_B = []# shading custom

    dmnMask00 = [0,0,0]
    dmnMask01 = [0,0,0]
    dmnMask02 = [0,0,0]
    dmnMask03 = [0,0,0]
    dmnMask04 = [0,0,0]

    failingNodes = []
    succedingNodes = []

    if mc.ls("|asset"):        
        mainFilePath = mc.file(q=True, list = True)[0]
        mainFilePathElem = mainFilePath.split("/")
        if  mainFilePathElem[-4] != "asset":
            if gui:
                raise ValueError("#### Error: you are not working in an 'asset' structure directory")
            else:
                tx= "#### Error: you are not working in an 'asset' structure directory"
                jpZ.printF( text=tx, st="main",  toFile = "", GUI= 0)
    else :
        if gui:
            raise ValueError("#### Error: no '|asset' could be found in this scene")

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
    if verbose == True: 
        print "#### {:>7}: {} dmnToon nodes to process ".format("Info",len(dmnToonList))
        print "#### {:>7}: 'dmnMask00' set to -->  {} ".format("Info", dmnMask00)
        print "#### {:>7}: 'dmnMask01' set to -->  {} ".format("Info", dmnMask01)
        print "#### {:>7}: 'dmnMask02' set to -->  {} ".format("Info", dmnMask02)
        print "#### {:>7}: 'dmnMask03' set to -->  {} ".format("Info", dmnMask03)
        print "#### {:>7}: 'dmnMask04' set to -->  {} ".format("Info", dmnMask04)

    for each in dmnToonList:
        maskNumber = 5

        if not mc.listConnections(each+".dmnMask00",connections = True):
            if mc.getAttr(each+".dmnMask00", lock = True): 
                mc.setAttr(each+".dmnMask00", lock = False)
                print "#### {:>7}: '{}.dmnMask00' has been unlocked".format("Warning", each)
            mc.setAttr (each+".dmnMask00", dmnMask00[0], dmnMask00[1], dmnMask00[2], type="double3")
            maskNumber = maskNumber - 1
        else:
            print "#### {:>7}: '{}.dmnMask00' is already connected, can't change value".format("Error", each)

        if not mc.listConnections(each+".dmnMask01",connections = True):
            if mc.getAttr(each+".dmnMask01", lock = True): 
                mc.setAttr(each+".dmnMask01", lock = False)
                print "#### {:>7}: '{}.dmnMask01' has been unlocked".format("Warning", each)
            mc.setAttr (each+".dmnMask01", dmnMask01[0], dmnMask01[1], dmnMask01[2], type="double3")
            maskNumber = maskNumber - 1
        else:
            print "#### {:>7}: '{}.dmnMask01' is already connected, can't change value".format("Error", each)

        if not mc.listConnections(each+".dmnMask02",connections = True):
            if mc.getAttr(each+".dmnMask02", lock = True): 
                mc.setAttr(each+".dmnMask02", lock = False)
                print "#### {:>7}: '{}.dmnMask02' has been unlocked".format("Warning", each)
            mc.setAttr (each+".dmnMask02", dmnMask02[0], dmnMask02[1], dmnMask02[2], type="double3")
            maskNumber = maskNumber - 1
        else:
            print "#### {:>7}: '{}.dmnMask02' is already connected, can't change value".format("Error", each)

        if not mc.listConnections(each+".dmnMask03",connections = True):
            if mc.getAttr(each+".dmnMask03", lock = True): 
                mc.setAttr(each+".dmnMask03", lock = False)
                print "#### {:>7}: '{}.dmnMask03' has been unlocked".format("Warning", each)
            mc.setAttr (each+".dmnMask03", dmnMask03[0], dmnMask03[1], dmnMask03[2], type="double3")
            maskNumber = maskNumber - 1
        else:
            print "#### {:>7}: '{}.dmnMask03' is already connected, can't change value".format("Error", each)

        if not mc.listConnections(each+".dmnMask04",connections = True):
            if mc.getAttr(each+".dmnMask04", lock = True): 
                mc.setAttr(each+".dmnMask04", lock = False)
                print "#### {:>7}: '{}.dmnMask04' has been unlocked".format("Warning", each)
            mc.setAttr (each+".dmnMask04", dmnMask04[0], dmnMask04[1], dmnMask04[2], type="double3")
            maskNumber = maskNumber - 1
        else:
            print "#### {:>7}: '{}.dmnMask04' is already connected, can't change value".format("Error", each)

        if maskNumber == 0:
            succedingNodes.append(each)
        else:
            failingNodes.append(each)

    if len(succedingNodes) > 0 :
        print "#### {:>7}: {} dmnToon nodes masks have been set succesfully ".format("Info",len(succedingNodes))
    else:
        succedingNodes = None

    if len(failingNodes) > 0 :
        if SelectFailingNodes == True: 
            mc.select(failingNodes)
        if gui:
            raise ValueError("#### {:>7}: {} dmnToon nodes masks cannot be set: {}".format("Error",len(failingNodes), failingNodes))
    else:
        failingNodes = None

    return failingNodes






class Asset_File_Conformer:
    def __init__(self):
        if mc.ls("|asset"):        
            self.mainFilePath = mc.file(q=True, list = True)[0]
            self.mainFilePathElem = self.mainFilePath.split("/")
            self.assetName = self.mainFilePathElem[-2]
            self.assetType = self.mainFilePathElem[-3]
            self.sourceList =[]
            self.targetList =[]
            self.sourceTargetListMatch = False
            self.sourceTargetTopoMatch = False
            self.sourceFile = ""
        else :
            raise ValueError("#### Error: no '|asset' could be found in this scene")


    def loadFile(self,sourceFile = "render", reference = True):

        if sourceFile in ["render","anim","modeling","previz"]:
            self.sourceFile = sourceFile
        else:
                raise ValueError("#### Error: the choosen sourceFile '"+sourceFile+"'' is not correct")


        if  self.mainFilePathElem[-4] == "asset":
            self.renderFilePath = miscUtils.normPath(miscUtils.pathJoin("$ZOMB_TEXTURE_PATH",self.assetType,self.assetName,self.assetName+"_"+self.sourceFile+".ma"))
            self.renderFilePath_exp = miscUtils.normPath(os.path.expandvars(os.path.expandvars(self.renderFilePath)))
        else:
            raise ValueError("#### Error: you are not working in an 'asset' structure directory")


        if reference:
            print "#### {:>7}: reference '{}'".format("Info",self.renderFilePath_exp)
            mc.file( self.renderFilePath_exp, type= "mayaAscii", ignoreVersion=True, namespace=self.sourceFile, preserveReferences= True, reference = True )
        else:
            print "#### {:>7}: importing '{}'".format("Info",self.renderFilePath_exp)
            mc.file( self.renderFilePath_exp, i= True, type= "mayaAscii", ignoreVersion=True, namespace=self.sourceFile, preserveReferences= True )


    def cleanFile(self):
        refNodeList = mc.ls(type = "reference")
        for each in refNodeList:
            print each
            if re.match('^render[0-9]{0,3}[:]{0,1}[a-zA-Z0-9_]{0,128}RN$', each) or re.match('^anim[0-9]{0,3}[:]{0,1}[a-zA-Z0-9_]{0,128}RN$', each) or re.match('^modeling[0-9]{0,3}[:]{0,1}[a-zA-Z0-9_]{0,128}RN$', each) or re.match('^previz[0-9]{0,3}[:]{0,1}[a-zA-Z0-9_]{0,128}RN$', each):
                fileRef= pm.FileReference(each)
                #fileRef = mc.referenceQuery(each,filename=True)# other way to do it
                try:
                    print "#### {:>7}:removing reference '{}'".format("Info",fileRef.path)
                    fileRef.remove()
                except :
                    pass

        nameSpaceList = mc.namespaceInfo(listOnlyNamespaces=True,r=True)
        for each in nameSpaceList:
            if re.match('^render[0-9]{0,3}', each) or re.match('^anim[0-9]{0,3}', each) or re.match('^modeling[0-9]{0,3}', each) or re.match('^previz[0-9]{0,3}', each):
                node2deleteList = mc.ls(each+":*")
                for node2delete in node2deleteList:
                    mc.lockNode(node2delete,lock = False)

        nameSpaceList = mc.namespaceInfo(listOnlyNamespaces=True)
        for each in nameSpaceList:
            if re.match('^render[0-9]{0,3}', each) or re.match('^anim[0-9]{0,3}', each) or re.match('^modeling[0-9]{0,3}', each) or re.match('^previz[0-9]{0,3}', each):
                print "#### {:>7}:removing namespace and its content: '{:<10}' ".format("Info",each)
                mc.namespace(removeNamespace=each, deleteNamespaceContent=True)


    

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
            souceFile = self.sourceFile

        if targetObjects == "set_meshCache" or isinstance(targetObjects, (list,tuple,set)):
            if targetObjects == "set_meshCache":
                if mc.ls("set_meshCache"):
                    targetObjects = mc.sets('set_meshCache',q=True)
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
                eachSource = sourceFile+":"+("|"+sourceFile+":").join(eachTarget.split("|"))

                if mc.ls(eachSource):
                    if mc.nodeType (eachSource)!= "transform":
                        print ("#### {:>7}: no '{}' source object has not the right type, only 'transform' nodes accepted".format("Error", eachSource))
                        errorOnSource = errorOnSource + 1
                    else:
                        self.sourceList.append(eachSource)
                else:
                    errorOnSource = errorOnSource + 1
                    print ("#### {:>7}: target --> '{:<30}'  has no correspondig source --> '{}'".format("Error",eachTarget, eachSource))

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
                print ("#### {:>7}: selection {}".format("Error",mySelection))
    

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
            print "#### {:>7}: source {}".format("Error", self.sourceList)
            print "#### {:>7}: target {}".format("Error", self.targetList)



    def checkSourceTargetTopoMatch(self):
        if self.sourceTargetListMatch == True:
            i = 0
            topoMismatch = 0
            while i < len(self.targetList):

                sourceVrtxCnt = len(mc.getAttr(self.sourceList[i]+".vrts[:]"))
                targetVrtxCnt = len(mc.getAttr(self.targetList[i]+".vrts[:]"))
                if sourceVrtxCnt != targetVrtxCnt:
                    topoMismatch = topoMismatch + 1
                    print ("#### {:>7}: Vertex number mismatch: '{}' vertex nb = {} -- '{}' vertex nb = {}".format("Error",self.sourceList[i],sourceVrtxCnt, self.targetList[i],targetVrtxCnt))

                sourceBBox =  mc.exactWorldBoundingBox(self.sourceList[i])
                targetBBox =  mc.exactWorldBoundingBox(self.targetList[i])
                if sourceVrtxCnt != targetVrtxCnt:
                    print ("#### {:>7}: Bounding box  mismatch: '{}' -- '{}'".format("Warning",self.sourceList[i], self.targetList[i]))

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
                sourceShapeList = mc.ls(mc.listRelatives(self.sourceList[i], allDescendents = True, fullPath = True, type = "mesh"), noIntermediate = True, l=False)
                if len(sourceShapeList)==0:
                    print ("#### {:>7}: source, no shape coud be found under transform : '{}'".format("Error",self.sourceList[i]))
                    uvTransferFailed +=1
                    continue
                elif len(sourceShapeList)==1:
                    sourceShape = sourceShapeList[0]
                else:
                    print ("#### {:>7}: several 'shapes' were found under: '{}' transform".format("Error",self.sourceList[i]))
                    uvTransferFailed +=1
                    continue

                targetShapeList = mc.ls(mc.listRelatives(self.targetList[i], allDescendents = True, fullPath = True, type = "mesh"), noIntermediate = False, l=False)
                if len(targetShapeList)==0:
                    print ("#### {:>7}: target, no shape coud be found under transform: '{}'".format("Error",self.sourceList[i]))
                    uvTransferFailed +=1
                    continue
                elif len(targetShapeList)==1:
                    targetShape = targetShapeList[0]
                else:
                    shapeOrigList =[]
                    for each in targetShapeList:
                        if mc.getAttr(each+".intermediateObject") == 1 and len(mc.listHistory(each+".inMesh"))==1 and "ShapeOrig" in each:
                            shapeOrigList.append(each)
                    if len(shapeOrigList) == 1:
                        targetShape = shapeOrigList[0]
                        shapeOrig = True
                    else:
                        print ("#### {:>7}: several 'ShapeOrig' were found under: '{}' transform".format("Error",self.sourceList[i]))
                        uvTransferFailed +=1
                        continue

                #print sourceShape+" --> "+targetShape
                if shapeOrig == True: mc.setAttr(targetShape+".intermediateObject", 0)
                mc.transferAttributes( sourceShape, targetShape, sampleSpace=1, transferUVs=2 ) #sampleSpace=1, means performed in model space
                mc.delete(targetShape, constructionHistory = True)
                if shapeOrig == True: mc.setAttr(targetShape+".intermediateObject", 1)

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
                    print ("#### {:>7}: source, no shape coud be found under transform : '{}'".format("Error",self.sourceList[i]))
                    sgTransferFailed +=1
                    continue
                elif len(sourceShapeList)==1:
                    sourceShape = sourceShapeList[0]
                else:
                    print ("#### {:>7}: several 'shapes' were found under: '{}' transform".format("Error",self.sourceList[i]))
                    sgTransferFailed +=1
                    continue

                targetShapeList = mc.ls(mc.listRelatives(self.targetList[i], allDescendents = True, fullPath = True, type = "mesh"), noIntermediate = True, l=False)
                if len(targetShapeList)==0:
                    print ("#### {:>7}: target, no shape coud be found under transform: '{}'".format("Error",self.sourceList[i]))
                    sgTransferFailed +=1
                    continue
                elif len(targetShapeList)==1:
                    targetShape = targetShapeList[0]
                else:
                    print ("#### {:>7}: several 'shapes' were found under: '{}' transform".format("Error",self.sourceList[i]))
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
                nodeList = mc.ls(mc.listHistory(mc.listConnections(shadEng+'.surfaceShader',connections = False)[0]),l=True) + mc.ls(mc.listHistory(mc.listConnections(shadEng+'.aiSurfaceShader',connections = False)[0]),l=True) + [shadEng]
                for each in nodeList:
                    if ":"in each:
                        mc.lockNode(each, lock=False)
                        newEach= mc.rename(each,each.split(":")[-1],ignoreShape=True)
                        renamedShadNodeNb += 1
                        if verbose: print "#### {:>7}: Remove from any namespace:  '{}' --> '{}' ".format("Info",each,newEach)
        print ("#### {:>7}: name space removed from {} shading nodes(s)".format("Info",renamedShadNodeNb))



    def disconnectAiMaterials(self):
        """
        not finished yet
        """
        shadEngineList = mc.ls("*",type = "shadingEngine")
        shadEngineList.remove("initialParticleSE")
        shadEngineList.remove("initialShadingGroup")
        if not shadEngineList :
            print "#### {:>7}: no shading engine".format("Error")
            return
        for each in shadEngineList:
            matShadNode =  mc.listConnections(each+'.aiSurfaceShader',connections = True, plugs=True)
            mc.disconnectAttr(matShadNode[1],matShadNode[0])


    def smoothPolyDisplay(self, inMeshList = [], verbose = False):
        intSel = mc.ls(selection=True)
        for each in inMeshList:
                mc.polySoftEdge (each, angle=180, constructionHistory=True)
                mc.bakePartialHistory( each, prePostDeformers=True)
                if verbose == True: print "#### {:>7}: polySoftEdge -> '{:^30}'".format("Info",each)
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
                        print ("#### {:>7}: {} shape(s) found under transform: '{}'".format("Error",len(sourceShapeLn), self.sourceList[i]))
                    if len(targetShapeLn) != 1:
                        print ("#### {:>7}: {} shape(s) found under transform: '{}'".format("Error",len(targetShapeLn), self.targetList[i]))
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
                    print ("#### {:>7}: Rendering attribute transfer failed for {} shape(s)".format("Error",shapeTransferFailed))
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


    def shadingGroupsForObject(self, oObj, warn=True):
        oShdGrpList = []
        oShape = None
        if isinstance(oObj, pm.general.MeshFace):
            indiceList = oObj.indices()
            for oShdEng in oObj.listHistory(type="shadingEngine"):
                if set(indiceList).intersection(set(oShdEng.members()[0].indices())):
                    oShdGrpList.append(oShdEng)

        elif isinstance(oObj, pm.general.NurbsSurfaceFace):
            oShape = oObj.node()

        elif isinstance(oObj, pm.nt.Transform):
            oShape = oObj.getShape()

        elif isinstance(oObj, (pm.nt.Mesh, pm.nt.NurbsSurface)):
            oShape = oObj

        elif warn:
            logMsg("Can't get shading groups from {}".format(repr(oObj)) , warning=True)

        if not oShdGrpList:
            if oShape:
                oShdGrpList = oShape.shadingGroups()
                if not oShdGrpList:
                    oShdGrpList = oShape.connections(type="shadingEngine")
        return oShdGrpList


    def conformShadingNetworkToNamespace(self, oMeshList, sNamespaceToMatch , **kwargs):
        bForce = kwargs.get("force", False)
        oShadingGroupMembersDct = {}
        oMatNotConformList = []

        for oShape in oMeshList:
            print "\nfor shape: ", oShape
            oMatSGList = self.shadingGroupsForObject(oShape)
            for oMatSG in oMatSGList:
                print "for shadingGroup: ", oMatSG

                oMatList = pm.ls(oMatSG.inputs(), type=mc.listNodeTypes('shader', ex="texture"))
                oMat = oMatList[0]

                ##ignore shadingGroups where materials are defaultNode
                if oMat.isDefaultNode():
                    continue

                ##ignore shadingGroups where materials are already in namespace to match
                sMatNamespace = oMat.namespace()
                print "sMatNamespace", sMatNamespace
                print "sNamespaceToMatch", sNamespaceToMatch
                if sMatNamespace == sNamespaceToMatch:
                    continue
                else:
                    oMatNotConformList.append(oMat)

                oMembers = oMatSG.members()
                for oMember in oMembers:
                    print "member :", oMember

                    if oMember.node() == oShape:
                        oShadingGroupMembersDct.setdefault(oMatSG, []).append(oMember)

        for k, v in oShadingGroupMembersDct.iteritems():
            print "for shadingGroup: ", k, ", specific members are: ", v

        if oMatNotConformList:
            if bForce:
                pass
            else:
                result = pm.confirmDialog(title='Materials not conform to Namespace...'
                                        , message="Found materials not conform to Namespace,\nCopy Shading Network, Conform to Namespace & Assign ?"
                                        , button=["OK", 'Cancel']
                                        , defaultButton='Cancel'
                                        , cancelButton='Cancel'
                                        , dismissString='Cancel')

                if result == "Cancel":
                    pm.warning("Materials Namespace conformation cancelled.")
                    return bForce
                else:
                    bForce = True

        else:
            if sNamespaceToMatch:
                logMsg('Materials already conformed to Namespace: "{0}"'.format(sNamespaceToMatch) , warning=True)
            return bForce


        ##Force current namespace to the one to match to duplicate in this namespace
        mc.namespace(set=":")
        mc.namespace(set=sNamespaceToMatch if sNamespaceToMatch else ":")

        oMatNotConformList = []

        oShapeAssignedList = []
        for oMatSG, oMembers in oShadingGroupMembersDct.iteritems():

            oNewMatSGs = pm.duplicate(oMatSG, rr=True, un=True)
            oNewMatSG = oNewMatSGs[0]
            print "old shadingGroup: ", oMatSG
            print "new shadingGroup: ", oNewMatSGs[0]
            print "oMembers", oMembers
            print oMembers[0]
            for oMember in oMembers:
                oShape = oMember.node()
                if oShape not in oShapeAssignedList:
                    oShapeAssignedList.append(oShape)
                    try:
                        pm.sets(oNewMatSG, e=True, forceElement=oShape)
                        logMsg('Material "{0}" assigned first to: "{1}"'.format(oNewMatSG, oShape) , warning=True)
                    except:
                        logMsg('Could not assign material "{0}" first to: "{1}"'.format(oNewMatSG, oShape) , warning=True)

            try:
                pm.sets(oNewMatSG, e=True, forceElement=oMembers)
                logMsg('Material "{0}" assigned to: "{1}"'.format(oNewMatSG, oMembers) , warning=True)
            except:
                logMsg('Could not assign material "{0}" to: "{1}"'.format(oNewMatSG, oMembers) , warning=True)

        mc.namespace(set=":")

        return bForce



    def disconnectAllShadEng(self, objectList = [], verbose = False):
        disconnectShapes = []
        shapeList = miscUtils.getShape(objectList, failIfNoShape = False)
        for eachShape in shapeList:
            shadEngList = mc.ls(mc.listHistory(eachShape,future = True),type="shadingEngine")
            for eachShadEng in shadEngList:
                attrList = mc.listConnections(eachShadEng,source = True,type='shape', connections =  True, plugs = True)
                i = -2
                while i< len(attrList)-2:
                    i+=2
                    shapeAttr = attrList[i+1]
                    shadEngAttr = str(attrList[i])
                    if eachShape in shapeAttr and eachShadEng+".dagSetMembers" in shadEngAttr:
                        #print "#### {:>7}: try to disconnect '{}'  from  '{}'".format("Info", shapeAttr,shadEngAttr) 
                        result = mc.disconnectAttr(shapeAttr, shadEngAttr)
                        if eachShape not in disconnectShapes:
                            disconnectShapes.append(eachShape)
                        if verbose == True: print result
                    if i>200: break
        print "#### {:>7}: shader have been disconnected on {} object(s) ".format("Info", len(disconnectShapes)) 





def softClean(struct2CleanList=["asset"]):
    """
    this script intend to remove from the scene every node that do not has a link with the selected structure.
    It also clean the empty namespaces
    """
    undeletable = ['sideShape','frontShape','front','sideShape','side','perspShape','perspShape','persp','topShape','top','topShape','frontShape','characterPartition',
                'defaultObjectSet','initialShadingGroup','defaultLightSet','renderPartition','initialParticleSE','strokeGlobals','defaultRenderQuality','defaultRenderingList1',
                'defaultTextureList1','renderLayerManager','particleCloud1','hyperGraphInfo','shaderGlow1','hardwareRenderingGlobals','globalCacheControl','postProcessList1',
                'lambert1','defaultRenderGlobals','time1','dynController1','lightList1','hyperGraphLayout','defaultLightList1','defaultLayer','defaultHardwareRenderGlobals',
                'defaultShaderList1','ikSystem','sequenceManager1','defaultColorMgtGlobals','defaultViewColorManager','lightLinker1','layerManager','defaultResolution',
                'initialMaterialInfo','renderGlobalsList1','dof1','hardwareRenderGlobals','defaultRenderLayer','defaultRenderUtilityList1']

    doNotDelete = ["set_control","set_meshCache","set_subdiv_0", "set_subdiv_1","set_subdiv_2","set_subdiv_3","set_subdiv_init","par_subdiv","defaultArnoldRenderOptions","defaultArnoldFilter","defaultArnoldDriver","defaultArnoldDisplayDriver"]
    intiSelection = mc.ls(selection = True)
    deletedNodes = 0

    #remove from any namespace all the nodes of my structre to clean
    mc.container (name="asset1", includeNetwork = True, includeShaders=True, includeHierarchyBelow=True, includeTransform=True, preview=True, addNode= struct2CleanList, force= True)
    myAssetNodeList = mc.ls(selection = True)+doNotDelete
    for each in myAssetNodeList:
        if ":"in each:
            mc.lockNode(each, lock=False)
            newEach= mc.rename(each,each.split(":")[-1],ignoreShape=True)
            print "#### {:>7}: Remove from any namespace:  '{}' --> '{}' ".format("Info",each,newEach)


    #delete all nodes that do not belong to my structure
    mc.container (name="asset1", includeNetwork = True, includeShaders=True, includeHierarchyBelow=True, includeTransform=True, preview=True, addNode= struct2CleanList, force= True)
    myAssetNodeList = mc.ls(selection = True)+doNotDelete
    toDelete = list(set(mc.ls()) - set(myAssetNodeList)-set(mc.ls(lockedNodes = True))-set(mc.ls(referencedNodes = True))-set(mc.ls(type = "reference"))-set(undeletable))
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

    print "#### {:>7}: 'softClean' has deleted {} nodes".format("Info",deletedNodes)

    #try to get back to the initial selection
    try:
        mc.select(intiSelection, replace = True, ne = True)
    except:
        mc.select(cl=True)


    ## remove all namespaces
    miscUtils.removeAllNamespace(emptyOnly=True)









   