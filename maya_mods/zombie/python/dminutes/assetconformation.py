import maya.cmds as mc
import re
import string
import dminutes.jipeLib_Z2K as jpZ
reload (jpZ)


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






