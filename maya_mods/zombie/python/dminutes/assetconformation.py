import maya.cmds as mc

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


def setSubdiv(preview = 0, arnold = 1):
    """
    this function will apply the subdivision to the geometries depending the subdivion set they belong to
    preview (int): 0 desactivate the subdivision, 1 apply the subdivision value (according to the subgivision set), other values leave the subdiv setting unchanged
    arnold (int): 0 desactivate the subdivision, 1 apply the subdivision value (according to the subgivision set), other values leave the subdiv setting unchanged
    """
    print ""
    print "#### info: exectute 'setSubdiv("+str(preview)+","+str(arnold)+")'"
    if preview == 0:
        print "#### info: preview = off  |",
    elif preview == 1:
        print "#### info: preview = on  |",
    else : 
        print "#### info: preview = untouched",
    if arnold == 0:
        print " arnold = off"
    elif arnold == 1:
        print " arnold = on"
    else : 
        print " arnold = untouched"


    subdivSets = mc.ls("set_subdiv_*", type = "objectSet")
    if not subdivSets:
        print "#### error: no subdivision set could be found (set_subdiv_*). Please create them first"
        return

    for eachSetSubdiv in subdivSets:
        geoInSet = mc.sets(eachSetSubdiv, query = True)
        if geoInSet == None: geoInSet = []
        
        if eachSetSubdiv != "set_subdiv_init" and geoInSet:
            subdivLevel =  int(eachSetSubdiv.split("set_subdiv_")[1])
            previewSubdivLevel = subdivLevel    
            if  0 <= subdivLevel <=9 :
                if previewSubdivLevel > 3: 
                    previewSubdivLevel = 3
                print "#### info: scaning 'set_subdiv_"+str(subdivLevel)+"'"
                for eachGeo in geoInSet:
                    eachGeoShape =  mc.listRelatives(eachGeo, noIntermediate=True, shapes=True, path=True)[0]
                    print "    "+eachGeoShape
                    if preview == 0 or preview == 1:
                        mc.setAttr(eachGeoShape+".displaySmoothMesh",2)
                        mc.setAttr(eachGeoShape+".useSmoothPreviewForRender",0)
                        mc.setAttr(eachGeoShape+".renderSmoothLevel",0)
                        mc.setAttr(eachGeoShape+".smoothLevel",subdivLevel*preview)
                    if arnold == 0 or arnold == 1:
                        if not mc.attributeQuery ("aiSubdivType", node = eachGeoShape , exists = True):
                            print "#### error: "+eachGeoShape+".aiSubdivType attribute coud not be found, please check if Arnold is properly installed on your computer"
                        else:
                            if arnold == 0:
                                subdivType = 0
                            else:
                                subdivType = 1
                            mc.setAttr(eachGeoShape+".aiSubdivType",subdivType)
                            mc.setAttr(eachGeoShape+".aiSubdivIterations",subdivLevel*arnold)

    if "set_subdiv_init" in subdivSets and mc.sets("set_subdiv_init", query = True) != None:
        print "#### warning: a geo object is still in the 'set_subdiv_init', please asssign it to a 'set_subdiv*'"
