import maya.cmds as mc
import re
import string


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
    
    allTransform = mc.ls(inParent,exactType = "transform", long = True)
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

