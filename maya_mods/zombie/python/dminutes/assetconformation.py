import maya.cmds as mc
import re
import string



def checkMeshNamingConvention(printInfo = True):
    """
    check all the meshes naming convention, '(geo|aux)_name_complement##' where 'name' and 'complement##' are strings of 16 alphanumeric characters
    only meshes of the main name space are taken into account, referenced meshes are therefore ignored.
        - printInfo (boolean) : print the 'multipleMesh' list 
        - return (list) : wrongMeshNamingConvention, all the meshes with a bad naming convetion
    """
    wrongMeshNamingConvention = []
    allTransMesh =  mc.listRelatives (mc.ls("*:",type = "mesh"), parent = True, fullPath = True, type = "transform")
    
    for each in allTransMesh:
        eachShort = each.split("|")[-1]
        if not (re.match('^(geo|aux)_[a-zA-Z0-9]{1,16}$', eachShort) or re.match('^(geo|aux)_[a-zA-Z0-9]{1,16}_[a-zA-Z0-9]{1,16}$', eachShort)):
            wrongMeshNamingConvention.append(each)
    
    if printInfo == True:
        if wrongMeshNamingConvention:
            print "#### warning: 'checkMeshNamingConvention': the following MESH(ES) do not match the mesh naming convention '(geo|aux)_name_complement##' where name and complement## are strings of 16 alphanumeric characters"
            for each in wrongMeshNamingConvention:
                print "#### warning: 'checkMeshNamingConvention': "+each
        else:
            print "#### info: 'checkMeshNamingConvention': MESH naming convention is correct"                
            
    return wrongMeshNamingConvention
    
    


def checkGroupNamingConvention(printInfo = True):
    """
    prendre en compte les camera...
    """
    wrongGroupNamingConvention = []
    myList =  mc.listRelatives (mc.ls("*:",type = "transform",recursive = False), parent = True, fullPath = True, type = "transform")

    allGroup = []
    for each in myList:
        if each not in allGroup:
            allGroup.append(each)
    
    for each in allGroup:
        eachShort = each.split("|")[-1]
        if not (re.match('^grp_[a-zA-Z0-9]{1,16}$', eachShort) or re.match('^grp_[a-zA-Z0-9]{1,16}_[a-zA-Z0-9]{1,16}$', eachShort) or re.match('\|asset|\|shot', each)):
            wrongGroupNamingConvention.append(each)
    
    if printInfo == True:
        print ""
        if wrongGroupNamingConvention:
            print "#### warning: 'checkGroupNamingConvention': the following GROUP(S) do not match the mesh naming convention 'grp_name_complement##' where name and complement## are strings of 16 alphanumeric characters"
            for each in wrongGroupNamingConvention:
                print "#### warning: 'checkGroupNamingConvention': "+each
        else:
            print "#### info: 'checkGroupNamingConvention': GROUP naming convention is correct"                
            
    return wrongGroupNamingConvention   
    



def meshShapeNameConform(fixShapeName = False, myTransMesh = []):
    """
    This function, makes sure every mesh shape name is concistant with its transform name: "transformName+Shape"
    Only shapes of the main name space are taken into account, referenced shapes are therefore ignored
        - fixShapeName (boolean): fix invalid shapes names if True, only log info otherwise
        - return (list): the meshes list that still have an invalid shape name
    """
    if not myTransMesh:
        myTransMesh =  mc.listRelatives (mc.ls("*:", type = "mesh"), parent = True, fullPath = True, type = "transform")
        checkAllScene = True
    else:
        checkAllScene = False
    renamedNumber = 0
    shapesToFix = []
    for each in myTransMesh:  
        myShape = mc.listRelatives (each, children = True, fullPath = True, type = "shape")
        if len(myShape)!= 1:
            print "#### error:'meshShapeNameConform' no or multiple shapes found for :"+myMesh
            break
        myShape = myShape[0]
        myShapeCorrectName = each+"|"+each.split("|")[-1]+"Shape"
        if myShape != myShapeCorrectName and fixShapeName == True:
            print "#### info: 'meshShapeNameConform': rename '"+myShape.split("|")[-1]+"' --> as --> '"+myShapeCorrectName.split("|")[-1]+"'"
            mc.rename(myShape,each.split("|")[-1]+"Shape")
            renamedNumber = renamedNumber +1
        elif myShape != myShapeCorrectName and fixShapeName == False:
            print "#### warning: 'meshShapeNameConform': '"+each+"' has a wrong shape name: '"+myShape.split("|")[-1]+"' --> should be renamed as: --> '"+myShapeCorrectName.split("|")[-1]+"'"
            shapesToFix.append(each)
    if renamedNumber != 0:
        print "#### info: 'meshShapeNameConform': "+str(renamedNumber)+" shape(s) fixed"
        return None
    elif shapesToFix:
        print "#### info: 'meshShapeNameConform': "+str(len(shapesToFix))+" shape(s) to be fixed"
        return shapesToFix
    elif checkAllScene == True:
        print "#### info: 'meshShapeNameConform': all meshes shapes names are correct"
        return None
    else:
        return None

 

def getMeshesWithSameName(printInfo = True):
    """
    list all the meshes that share the same short name,
    only meshes of the main name space are taken into account, referenced meshes are therefore ignored.
        - printInfo (boolean) : print the 'multipleMesh' list 
        - return (list) : multipleMesh
    """
    allTransMesh =  mc.listRelatives (mc.ls("*:", type = "mesh"), parent = True, fullPath = True, type = "transform")
    multipleMesh = []
    for eachTrasnMesh in allTransMesh:
        shortName = eachTrasnMesh.split("|")[-1]
        if str(allTransMesh).count(shortName+"'") > 1:
            multipleMesh.append(eachTrasnMesh)
    if multipleMesh:
        if printInfo is True:
            print "#### warning: 'getMeshesWithSameName': somes meshes have the same short name: "
            for each in multipleMesh:
                    print "#### warning: 'getMeshesWithSameName': "+each
        return multipleMesh
    else:
        if printInfo is True:
            print "#### info: 'getMeshesWithSameName': no multiple short names in the scene"
        return None     


def renameMeshAsUnique(myMesh):
    """
    Makes the given mesh name unique by adding a digit and/or incrementing it till the short name is unique in the scene. 
    Only meshes of the main name space are taken into account, referenced meshes are therefore ignored.
    myMesh  (string) : the long name of a mesh (a transform parent of a mesh shape) that has to be renamed to have a unique short name in the scene

    """
    allTransMesh =  mc.listRelatives (mc.ls("*:", type = "mesh"), parent = True, fullPath = True, type = "transform")
    shortName = myMesh.split("|")[-1]
    digit = re.findall('([0-9]+$)', myMesh)
    if digit:
        digit = digit[0]
        newShortName = string.rstrip(shortName,digit)
        newDigit = string.zfill(str(int(digit)+1), len(digit))
        i = 1
        while str(allTransMesh).count(newShortName+newDigit) > 0:
            newDigit = string.zfill(str(int(digit)+i), len(digit))
            i = i+1
        mc.rename(myMesh,newShortName+newDigit)
        print "#### info: 'renameMeshAsUnique' rename "+myMesh+"  -->  "+string.rstrip(myMesh,digit)+newDigit
        meshShapeNameConform(fixShapeName = True, myTransMesh = [string.rstrip(myMesh,digit)+newDigit])
        
    else:
        digit = "1"
        i = 1
        while str(allTransMesh).count(shortName+digit) > 0:
            digit = str(int(digit)+1)
            i = i+1
        myMeshNew = mc.rename(myMesh,shortName+digit)
        print "#### info: 'renameMeshAsUnique' rename "+myMesh+"  -->  "+myMesh+digit
        meshShapeNameConform(fixShapeName = True, myTransMesh = [string.rstrip(myMesh,digit)+newDigit])

                        
def makeAllMeshesUnique():
    """
    makes all the meshes short names unique by adding a digit and/or incrementing it till the short name is unique in the scene
    then makes sure the shapes names are corrects
    """           
    multipleMesh = getMeshesWithSameName(False)
    if multipleMesh :
        while multipleMesh:
            renameMeshAsUnique(multipleMesh[0])
            multipleMesh = getMeshesWithSameName(False)
    else:
        print "#### info: 'makeAllMeshesUnique' no multiple mesh found, all meshes have unique short name "
        

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
    subdivSets = mc.ls("set_*", type = "objectSet")
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
            mc.sets(eachGeo, add="set_subdiv_init")
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

