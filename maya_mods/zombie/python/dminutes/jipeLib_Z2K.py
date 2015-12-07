#!/usr/bin/python
# -*- coding: utf-8 -*-
################################################################
# Name    : Temp Zomby jipeLib
# Version : 001
# Description : all Z2K'scripts related functions
# Author : Jean-Philippe Descoins
# Date : 2015_09_10
# Comment : WIP
################################################################
#    ! Toute utilisation de ce se script sans autorisation     #
#                         est interdite !                      #
#    ! All use of this script without authorization is         #
#                           forbidden !                        #
#                                                              #
#                                                              #
#                 © Jean-Philippe Descoins                     #
################################################################
import os
import maya.cmds as cmds
from dminutes import assetconformation

# general function 

# ADD CHECK for DOUBLE NAMES



# Z2K base general functions -----------------
def getBaseModPath(*args, **kwargs):
    """Desription :recupere le path de base des modules
       Return : Path ending with "/"
       Dependencies : os - 
    """
    basePath = ""
    allModL = os.environ.get("MAYA_MODULE_PATH").split(";")
    for p in allModL:
        if "/z2k-pipeline-toolkit/maya_mods" in p:
            basePath = p + "/"
    return basePath


# ------------------------ OS/Z2K Functions ------------------------------------
def getAssetL (assetCat="chr",*args,**kwargs):
    """ Description: return the asset list filtered by category (chr/prp/set/env/c2d...)
        Return : [LIST]
        Dependencies : cmds - 
    """
    
    theDir = os.path.normpath( os.environ.get("ZOMB_ASSET_PATH")) + os.sep + assetCat
    print "theDir=", theDir
    if os.path.isdir(theDir):
        assetL = sorted(os.listdir(theDir) )
        if not len(assetL):
            assetL=["Empty Folder"]
        
    else:
        assetL=["Invalide folder"]

    return assetL

def getCatL (*args,**kwargs):
    """ Description: recupere la list des category d asset (chr-prp-set-c2d ...etc)
        Return : LIST
        Dependencies : os - 
    """
    
    theDir = os.environ.get("ZOMB_ASSET_PATH")
    print "theDir=", theDir
    if os.path.isdir(theDir):
        assetL = sorted(os.listdir(theDir) )
        if not len(assetL):
            assetL=["Empty Folder"]
        
    else:
        assetL=["Invalide folder"]

    return assetL

def getAssetTypeL (*args, **kwargs):
    """ Description: recupere la list des type d asset ("anim","previz","modeling","render","master"...etc)
        Return : LIST
        Dependencies : os - 
    """
    print "getAssetTypeL()"
    return ["anim","previz","modeling","render","master"]

def getShotName(*args, **kwargs):
    """ Description: renvoi le nom du shot
        Return : STRING
        Dependencies : cmds - 
    """
    
    print "getShotName()"
    # get shot name
    currentSceneP,currentScene = cmds.file(q=1,sceneName=True),cmds.file(q=1,sceneName=True,shortName=True)
    shotName = currentScene.rsplit("_",1)[0]
    print "shotName=", shotName
    if shotName[:2]+shotName[6:9] in ["sq_sh"]:
        return shotName
    else:
        return "BAD SCENE NAME"

def infosFromMayaScene(*args, **kwargs):
    """ Description: decompose les infos à partir de la scene courante: 
                scenePath-fileName-assetName-assetCat-assetType-version
        Return : dict
        Dependencies : cmds - getCatL - getAssetTypeL
    """
    print ("infosFromMayaScene()")
    testOk = True
    outD = {}
    scenePathTmp = cmds.file(q=1 , sceneName=True)
    print "scenePathTmp=", scenePathTmp
    if   "asset" in scenePathTmp :
        print "folder asset ok"
        categoryL = getCatL()
        assetTypeL= getAssetTypeL()
        print "categoryL=", categoryL
        print "assetTypeL=", assetTypeL
        #path and short name
        outD["scenePath"]= cmds.file(q=1,sceneName=True)
        outD["fileName"]= cmds.file(q=1,sceneName=True,shortName=True)
        outD["assetName"] = outD["fileName"].rsplit("_",1)[0]
        outD["assetCat"] = outD["fileName"].split("_",1)[0]
        outD["assetType"] = outD["fileName"].rsplit("_",1)[1].split("-",1)[0]
        outD["version"] = outD["fileName"].split("-",1)[1][:4]

        if outD["assetName"][:2]+outD["assetName"][6:9] in ["sq_sh"]:
            print "this is a shot", outD["assetName"]


        # verification
        
        # assetCat
        if not outD["assetCat"]  in categoryL :
            print "* bad assetCat -->",outD["assetCat"],"not in",categoryL
            testOk = False
        else:
            print "*","assetCat ok:".rjust(15),outD["assetCat"]
        
        # Version
        if not outD["version"][0]  in ["v"] and not len(outD["version"])in [4]:
            print "* bad version"
            testOk = False
        else:
            print "*","version ok:".rjust(15),outD["version"]

        # assetType
        if not outD["assetType"] in assetTypeL and not len(outD["version"])in [4]:
            print "* bad assetType"
            testOk = False
        else:
            print "*","assetType ok:".rjust(15),outD["assetType"]

        # assetName
        if not outD["assetName"].count("_") not in [3] :
            print "* bad assetName"
            testOk = False
        else:
            print "*","assetName ok:".rjust(15),outD["assetName"]
        

        # finally return the dico
        if testOk:
            return outD
        else:
            return False
    else:
        return False

def createIncrementedFilePath( filePath="", vSep= "_v",extSep=".ma", digits=3, *args, **kwargs):
    """ Description: return incremented File path starting with the last version present in the 
        folder of the given file.
        first split the extension of the file
        then search the version by le right side and split the first instance of it
        Work ideally with folder with the only correctly versionned files.
        Return : string of the versioned filePath
        Dependencies :  os
    """
    
    print "createVersionIncrementedPath(%s)" %filePath
    NotFoundBool = True
    filePath = os.path.normpath(filePath)
    
    # get last version in folder
    theDir,theFile = filePath.rsplit(os.sep,1)[0],filePath.rsplit(os.sep,1)[1].rsplit(extSep,1)[0]
    fullDirContentL =[f.rsplit(extSep,1)[0] for f in os.listdir( os.path.normpath(filePath).rsplit(os.sep,1)[0] ) if  extSep in f]
    print fullDirContentL
    # list all files with the same base name
    # ############################################################ checker si le repertoire est avec au moins 1 fichier
    ConcernedFileL= []
    if len(fullDirContentL)>0:
        # get concernedFiles
        for f in fullDirContentL:
            print "\t",( theFile.rsplit(extSep,1)[0] ).rsplit(vSep,1)[0].upper() ," / ",  f.upper()

            if theFile.rsplit(vSep,1)[0].upper() in [  f.rsplit(vSep,1)[0].upper() ] and len(theFile) == len(f):
                ConcernedFileL.append(f)
            
        print "ConcernedFileL = %s" %( ConcernedFileL )
        
        if len(ConcernedFileL)>0:
            NotFoundBool = False
            lastv = theDir + os.sep + sorted(ConcernedFileL, key=lambda member: member.lower() )[-1]
            print "lastv = %s" %( lastv )
            outPath = lastv
        else :
            NotFoundBool = True

    # set the default Versionning
    if NotFoundBool in [True,1]:
        outPath =  theDir + os.sep + theFile


    # finally oparate the versionning
    bazPath,curVer =  outPath.rsplit(vSep, 1)

    curVer = str(int(curVer)+1).zfill(digits)
    filePath = bazPath + vSep + curVer + extSep
    print "\t filePath=",filePath


    print "\t return: %s" % filePath
    return filePath



# printer  -------------------------------------------------------
def printF( text="", st="main", toScrollF="", toFile = "", inc=False, GUI= True,
    openMode="a+",versionning=True, *args, **kwargs):
    """ Description: printer avec mise en forme integrer et link vers file or maya layout
        Return : [BOOL,LIST,INTEGER,FLOAT,DICT,STRING]
        Dependencies : cmds - 
    """

    # print "printF()",GUI,toFile
    stringToPrint=""

    text = str(object=text)
    if st in ["title","t"]:
        stringToPrint += "\n"+text.center(40, "-")+"\n"
    if  st in ["main","m"]:
        stringToPrint += "    "+text+"\n"
    if st in ["result","r"]:
        stringToPrint += " -RESULT: "+text.upper()+"\n"

    if not toFile in [""] and not GUI:
        # print the string to a file
        with open(toFile, openMode) as f:
            f.write( stringToPrint )
            print stringToPrint

    else:
        # print to textLayout
        cmds.scrollField(toScrollF, e=1,insertText=stringToPrint, insertionPosition=0, font = "plainLabelFont")
        print stringToPrint

# decorator generique ----------------------------
def waiter (func,*args, **kwargs):

    def deco(self,*args, **kwargs):
        result = True
        cmds.waitCursor( state=True )
        print "wait..."
        print"tarace"
        try:
            print func
            result = func(self,*args, **kwargs)
        except Exception,err:
            print "#ERROR in waiter():",err

            # cmds.waitCursor( state=False )
        
        cmds.waitCursor( state=False )
        print "...wait"
        if not result and self.GUI:
            print "try GUI ANYWAY MOTHER fOCKER!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            cmds.frameLayout(self.BDebugBoardF,e=1,cll=True,cl=0)

        return result
    return deco

# 3D maya functions ---------------------------
def Ltest(objL,*args,**kwargs):
    # old way
    # if type(objL) is not list:
    #     objL = [objL]

    # new way
    if not isinstance(objL,list):
        objL = [objL]

    return objL

def matchByXformMatrix(cursel=[], mode=0, *args, **kwargs):
    ''' Description : Match SRT in world cursel objects to the first one
                    mode : - 0/first = the first object is the reference
                           - 1/parallal = the first half is reference for the second half
        Return : Bool
        Dependencies : cmds - 
    ''' 
    print "matchByXformMatrix()"
    if mode in [0,"first"]:
        objMatched = cursel.pop(0)
        objMatchingL = cursel
        #print objMatched, "->", objMatchingL

        # get world position of the constraining object 
        ObjectMatricDico = {}
        McoorOld = cmds.xform(objMatched, matrix=True, q=True, worldSpace=True)
        scaleOld = cmds.xform(objMatched, scale=True,q=True, relative=True)
        ObjectMatricDico[objMatched] = {"Mcoord": McoorOld,"scale":scaleOld}
        # print "Matrix gettet:",ObjectMatricDico

        for objMatching in objMatchingL:
            # set back world position of the constrained object 
            for key,val in ObjectMatricDico[objMatched].iteritems() :
                if key in ["Mcoord"]:
                    cmds.xform(objMatching, m=val, worldSpace=True)
                    # print "Mcoord",val
                if key in ["scale"]:

                    cmds.xform(objMatching, scale=val, relative=True)
                    # print "scale",val
            # print "Matrix setted"
        return True

def jlistSets( *args,**kwargs):
        """
        description : wrapper of cmds.listSets() that return empty list []
                     if None originaly returned. Avoid treatment problems.
        """
        toReturnL = cmds.listSets(*args,**kwargs)
        if not toReturnL:
            toReturnL=[]

        return toReturnL

def setFilterTest(setName="",includedSetL=["objectSet","textureBakeSet","vertexBakeSet","character"],
        excludedSetL=["shadingEngine","displayLayer","ilrBakeLayer"],
        bookmarksSets = False, defaultSets=False,lockedSets=False,
        *args, **kwargs):
        """ Description: Permet de recuperer les set Object visible dans l'outliner, avec la possibilité de changer les filtres
            Return : BOOL
            Dependencies : cmds - 
        """
        # #plugin object sets
        # try:
        #     apiNodeType = cmds.nodeType(setName, api=True)
        # except RuntimeError:
        #     return False
        # if apiNodeType == "kPluginObjectSet":
        #     return True

        # get setType
        try:
            nodeType = cmds.nodeType(setName)
        except RuntimeError:
            return False
            
        # accepted sets
        if not nodeType in  includedSetL:
            return False

        # Rendering - dispLayers - LayerTurttle
        if nodeType in excludedSetL:
            return False

        # bookmarks
        if not bookmarksSets:
            if cmds.getAttr(setName+"."+ "annotation") in ["bookmarkAnimCurves"]:
                return False

        # maya default sets
        if not defaultSets:
            if setName in cmds.ls(defaultNodes=True):
                return False
        
        # locked sets
        if not lockedSets:
            if setName in cmds.ls(lockedNodes=True):
                return False

        # others filtered by attribs
        excludeAttrL = ["verticesOnlySet", "edgesOnlySet", "facetsOnlySet", "editPointsOnlySet", "renderableOnlySet"]
        for attr in excludeAttrL:
            if cmds.getAttr (setName+"."+attr) :
                return False

        # finally return True if nothing of all the rest
        return True

def getOutlinerSets(*args, **kwargs):
        """ Description: return the outliner visible filtered objects sets 
            Return : [LIST]
            Dependencies : cmds -  setFilterTest()
        """
        
        return [setName for setName in cmds.ls(sets=True) if setFilterTest(setName=setName)]

def getSetContent ( inSetL=[],*args,**kwargs):
        """
        description : return the objL in a setlist
        Return : [list]
        """
        outL = []
        objL = []
        for i in inSetL:
            if cmds.objExists(i):
                objL= cmds.listConnections(i+"."+"dagSetMembers",source=1)
                if objL:
                    outL.extend(objL)
        return outL

def getSel(*args, **kwargs):
        objL = cmds.ls( os=True, fl=True, l=True, )
        return objL

def getGeoInHierarchy(cursel=[],theType="mesh",*args,**kwargs):
    listOut = []
    cursel = Ltest(cursel)
    if not len(cursel)>0 : 
        cursel= cmds.ls(os=True, flatten=True,allPaths=True)
    # select mesh in hierarchy
    cursel = cmds.listRelatives(cursel,allDescendents=True, path=True)
    listOut = [a for a in cursel if cmds.listRelatives(a,c=1,type=theType, path=True)]
    
    return listOut

def delete_displayLayer( FilterL=["defaultLayer"], *args, **kwargs):
    print "delete_displayLayer()"

    displ = cmds.ls(type="displayLayer", long=True)
    for lay in displ:
        if lay not in FilterL:
            cmds.delete(lay)

def createDisplayLayer ( n="default_Name", inObjL=[], displayType=0, hideOnPlayback=0,enableOverride=True, *args, **kwargs):
    print "createDisplayLayer(%s,%s,%s)" % (n,displayType,hideOnPlayback)

    # create layer if doesn't exist
    if not cmds.objExists(n):
        cmds.createDisplayLayer(name=n, number=1,empty=True,nr=True)

    # set the layer state
    cmds.setAttr(n + ".displayType", displayType)
    cmds.setAttr(n + ".hideOnPlayback",hideOnPlayback)
    cmds.setAttr(n + ".enabled",enableOverride)

    # add obj list to the layer
    cmds.editDisplayLayerMembers(n, inObjL,nr=True)


def NodeTypeScanner( execptionTL = [], exceptDerived= True, specificTL=[], specificDerived=False,
    mayaDefaultObjL=["characterPartition","defaultLightList1","dynController1","globalCacheControl",
    "hardwareRenderGlobals","hardwareRenderingGlobals","defaultHardwareRenderGlobals","hyperGraphInfo",
    "hyperGraphLayout","ikSystem","characterPartition","char_aurelienPolo_wip_18_sceneConfigurationScriptNode",
    "char_aurelienPolo_wip_18_uiConfigurationScriptNode","sequenceManager1","strokeGlobals","time1","defaultViewColorManager",
    "defaultColorMgtGlobals","defaultObjectSet","defaultTextureList1","lightList1","defaultObjectSet",
    "sceneConfigurationScriptNode","uiConfigurationScriptNode"],
    *args, **kwargs):
    """ Description: Return Node list base on specific type /excepted type filtered
                    If nothing it give evrething in scene
                    basic type herited coulb be "dagNode" / "transform" /
        Return : LIST
        Dependencies : cmds - 
    """

    theTypeL =[]
    allTypeL = cmds.ls(nodeTypes=1)
    toReturnL = []
    if not len(specificTL) >0:
            theTypeL = allTypeL
    else:
        theTypeL = specificTL

    for typ in theTypeL:
        # print "****",typ
        if len(theTypeL)>0:
            filtered = [x for x in cmds.ls(type=typ) if  x not in mayaDefaultObjL ]
            if len(filtered)>0:
                for obj in filtered:
                    if not obj in mayaDefaultObjL:
                        testB = False
                        if len(execptionTL)>0:
                            for ex in execptionTL:
                                if  cmds.nodeType(obj) in  cmds.nodeType(ex, derived=exceptDerived, isTypeName=True,):
                                    # print "#######",cmds.nodeType(obj), "is bad"
                                    testB = True
                                    break
                            if not testB:
                                toReturnL.append(obj)
                                    
                        else:
                            toReturnL.append(obj)

    return toReturnL

# wip to make faster
def UnusedNodeAnalyse( execptionTL = [], specificTL= [], mode = "delete",verbose=True, *args, **kwargs):
    """ Description: Test if nodes have connections based on type and excluded_type in all the scene and either delete/select/print it.
                    mode = "check" /"delete" / "select" / "print"
        Return : [BOOL,Dict]
        Dependencies : cmds - NodeTypeScanner() - isConnected()
    """
    
    toReturnB = True
    nodeL = NodeTypeScanner(execptionTL=execptionTL, specificTL=specificTL)
    print "*nodeL=", len(nodeL)
    unconectedCL =[]
    # loop
    for node in nodeL:
        if not isConnected(node=node)[0]:
            # print "-","toDELETe:",node
            unconectedCL.append(node)

    print "unconectedCL=", len(unconectedCL)
    
    # finally 
    errorL = []
    deletedL =[]
    debugD = {}

    if len(unconectedCL):
        for node in unconectedCL:
            print "////",node
            try:
                if not cmds.lockNode(node, q=1)[0]:
                    print "try deleting",node,cmds.lockNode(node,q=1)[0]
                    if mode in ["delete"]:
                        cmds.delete (node)
                    deletedL.append(node)
            except Exception,err:
                errorL.append(node)
                print "ERROR on {0} : {1}".format(node,err)
    if len(errorL)>0:
        toReturnB = False
    
    debugD["errorL"] = errorL
    debugD["deletedL"] = deletedL

    if mode in ["select"]:
        cmds.select (unconectedCL) 

    elif mode in ["print"]:
        for node in unconectedCL:
            print node
    elif mode in ["check"]:
        if len(deletedL):
            toReturnB = False
    print "tatata",len(unconectedCL)
    

    return [toReturnB,debugD]





#--------------------- CHECK FUNCTION ------------------------------
def checkBaseStructure(*args,**kwargs):
        """
        Descrition: Check if th Basic hierachy is ok
        Return: [result,debugDict]
        Dependencies: cmds - getOutlinerSets()
        """
        print "checkBaseStructure()"
        tab= "    "
        debugL = []
        debugDetL = []

        debugD = {}
        toReturnB = True

        # check if asset gp and set here

        baseExcludeL = ["persp","top","top1","front","front1","side","side1","left","left1","back","back1","bottom1","bottom","defaultCreaseDataSet","defaultLayer"]
        baseObjL = ["asset",]
        baseSetL = ["set_meshCache","set_control",]
        additionnalSetL = ["set_subdiv_0", "set_subdiv_1", "set_subdiv_2", "set_subdiv_3", "set_subdiv_init"]
        baseLayerL = ["control","geometry"]
        baseCTRL = ["BigDaddy","BigDaddy_NeutralPose","Global_SRT","Local_SRT","Global_SRT_NeutralPose","Local_SRT_NeutralPose"]
        AllBaseObj = baseLayerL + baseObjL + baseSetL
        print tab+"AllBaseObj=", AllBaseObj
        topObjL = list(set(cmds.ls(assemblies=True,) ) - set(baseExcludeL) )
        topSetL = getOutlinerSets()
        layerL = list(set(cmds.ls(type="displayLayer",)) - set(baseExcludeL) )

        # ---------- prints --------------
        print tab+ "topObjL:",len(topObjL)
        for i in topObjL:
            print tab+ "    -",i
        print tab+ "topSetL:",len(topSetL)
        for i in topSetL:
            print tab+ "    -",i
        print tab+ "layerL:",len(layerL)
        for i in layerL:
            print tab+ "    -",i

        # ---------------------------------
        # topObjL test
        debugD["topObjL"] = {}    
        if not sorted(baseObjL) == sorted(topObjL):
            debugD["topObjL"]["result"] = "PAS CONFORME"
            debugD["topObjL"]["Found"] = topObjL
            toReturnB= False
        else:
            debugD["topObjL"]["result"] = "OK"

        # topSetL test
        debugD["topSetL"] = {}
        debugD["topSetL"]["Found"] = ""
        debugD["topSetL"]["result"] = []
        for i in topSetL:

            if not i in baseSetL and not i in additionnalSetL:
        # if not sorted(baseSetL) == sorted(topSetL):
                debugD["topSetL"]["result"].append( False )
                debugD["topSetL"]["Found"] += " -" + i
                toReturnB= False
            else:
                debugD["topSetL"]["result"].append( True )
        # if 1 flase dans tout les test alors pas bon
        if False in debugD["topSetL"]["result"]:
            debugD["topSetL"]["result"] = "PAS CONFORME"
        else:
            debugD["topSetL"]["result"] = "OK"


       # Layers test
        debugD["layerL"] = {}
        if not sorted(baseLayerL) == sorted(layerL):
            debugD["layerL"]["result"] = "PAS CONFORME"
            debugD["layerL"]["Found"] = layerL
            toReturnB= False
        else:
            debugD["layerL"]["result"] = "OK"


        # baseCTRL test
        debugD["baseCTRL"] = {}
        test= "OK"
        notFoundL=[]
        for i in baseCTRL:
            if not cmds.objExists(i):
                toReturnB= False
                test= "PAS CONFORME"
                notFoundL.append(i)

        debugD["baseCTRL"]["result"] = test
        debugD["baseCTRL"]["NOT_Found"] = notFoundL

        print "toReturnB=", toReturnB
        return toReturnB,debugD

def checkAssetStructure(assetgpN="asset", expectedL=["grp_rig","grp_geo"],
        additionalL=["grp_placeHolders"],*args,**kwargs):
        """ Description: check inside the asset_gp
            Return : [result,debugDict]
            Dependencies : cmds - 
        """
        print "checkAssetStructure()",
        extendedL = expectedL[:]
        # switch expeted list depending on the name of the scene
        sceneName = cmds.file(q=1,sceneName=True, shortName=True)
        if sceneName[:3] in ["set"]:
            print "it's a set"
            extendedL.extend(additionalL)
        toReturnB = False
        debugD = {}
        tab="    "
        expect_str = " - ".join(extendedL)
        if cmds.objExists(assetgpN):
            childL = cmds.listRelatives(assetgpN,  c=True)
            print tab,expect_str, childL
            debugD[expect_str] = {}
            print "*",sorted(expectedL) 
            print "*",sorted(childL)
            print "*",sorted(extendedL) 
            if (sorted(expectedL) == sorted(childL) ) or ( sorted(extendedL) == sorted(childL) ) :
                toReturnB = True
                debugD[ expect_str ]["result"] = "OK"
                print tab, toReturnB
            else:
                toReturnB = False
                debugD[expect_str]["result"] = "PAS CONFORME"
                debugD[expect_str]["Found"] = childL
                print tab, toReturnB

        
        

        return toReturnB,debugD

def Apply_Delete_setSubdiv (applySetSub=True, toDelete=["set_subdiv_0", "set_subdiv_1", "set_subdiv_2", "set_subdiv_3", "set_subdiv_init"],*args, **kwargs):
    """ Description: apply setSubdiv() if present and delete it
        Return : [BOOL,LIST,INTEGER,FLOAT,DICT,STRING]
        Dependencies : cmds - assetconformation.setSubdiv()
    """
    print "Apply_Delete_setSubdiv()"
    
    toReturnB = True
    setSub = False
    if applySetSub:
        try:
            assetconformation.setSubdiv()
            setSub = True
        except:
            print "    No setSubDiv to Apply in the scene"

    deletedL = []
    for i in toDelete:
        try:
            cmds.delete(i)
            deletedL.append(i)
        except:
            pass

    return [toReturnB,setSub,deletedL]

def checkSRT (inObjL=[], *args,**kwargs):
    # print "checkSRT()"
    tab= "    "
    toReturnB = True
    debugD = {}
    tmpDict ={}

    attribD =   {"translateX":0.0, "translateY":0.0, "translateZ":0.0,
                  "rotateX":0.0, "rotateY":0.0, "rotateZ":0.0,
                  "scaleX":1.0, "scaleY":1.0, "scaleZ":1.0,
                }

    for obj in inObjL:
        badassResult = False
        errAttrL= []
        for i,j in attribD.iteritems():
            if not round(cmds.getAttr(obj+"."+i),3) == round(j,3):
                # print tab + obj
                # print tab+"    err:",i, round(cmds.getAttr(obj+"."+i),3), "<>",j
                toReturnB = False
                badassResult = True
                errAttrL.append(i)
                
        if badassResult:
            debugD[obj]= errAttrL


    # print tab,"DONE", toReturnB,debugD

    # print "toReturnB=",toReturnB
    return [toReturnB,debugD]

def isSet_meshCache_OK (theSet="set_meshCache",theType="prop",*args, **kwargs):
        """ Description: check si le contenue du setMeshCache est conforme au type donné
                theType : "set" or "something else / si c'est un "set" il cherche des group
                            only, sinon le reste du tps des mesh only
            Return : BOOL
            Dependencies : cmds - getSetContent
        """
        toReturn =True
        debug =""
        print "theType=", theType
        setContentL = getSetContent(inSetL=[theSet])
        print "setContentL=", setContentL
        if setContentL:
            if theType not in ["setPreviz"]:
                # cas general on veut seulement des mesh dans le set
                for i in setContentL:
                    sL= cmds.listRelatives(i,s=1,ni=1)
                    if  sL:
                        if not cmds.objectType(i) in ["transform"] and not len(sL)>0 :
                            toReturn= False
                            debug ="certain object ne sont pas des MESH"
                    else:
                        toReturn= False
                        debug ="certain object ne sont pas des MESH"

            else:
                print "set"
                # is a set donc on doit avoir seulement des group pour le moement
                for i in setContentL:
                    sL= cmds.listRelatives(i,s=1,ni=1)
                    # print "sL=", sL,cmds.objectType(i)
                    if  sL or not cmds.objectType(i) in ["transform"] :
                        toReturn =False
                        debug ="certain object ne sont pas des Groups"

        else:
            toReturn= False
            debug ="le set est vide"


        return [toReturn,debug]

def isKeyed ( inObj, *args, **kwargs):
        """ Description: Check if the given object'keyable attrib are effictively keyed
            Return : [BOOL,DebugList]
            Dependencies : cmds - isConnected() -
        """

        toReturnB = False
        debugD ={}
        if len(inObj) >0:
            if cmds.objExists(inObj):
                conL = cmds.listConnections(inObj)
                # print "conL=", conL
                if conL:
                    if len(conL)>0 :
                        # print"lengthed"
                        attrL = cmds.listAttr(inObj,k=True)
                        if attrL:
                            if len(attrL)>0:
                                for attr in attrL:
                                    attrN = inObj + "."+ attr
                                    if cmds.connectionInfo(attrN,isDestination=True):
                                        conL = cmds.listConnections(attrN,s=True,t="animCurve")
                                        # print "conL=", conL
                                        debugD[attrN] = conL
                                        toReturnB =True


        return [toReturnB,debugD]

def isConnected ( node="", exceptionL=["nodeGraphEditorInfo","defaultRenderUtilityList","objectSet"], *args, **kwargs):
        toReturnB=True
        conL = []
        
        # print "///",node
        if cmds.listConnections(node):
            for i in cmds.listConnections(node):
                # print "    " +node + " <-> "+ i
                if not i in [node]:
                    if cmds.objectType(i) not in exceptionL:
                        conL.append(i)

            if len (conL) == 0:
                toReturnB= False
        else:
            toReturnB= False

        return [toReturnB,conL]

def isSkinned(inObjL=[], verbose=False, printOut = False,*args,**kwargs):
        ''' Description : Get the list of the SlinClusters of the selected mesh
                Return : [resultBool,outSkinClusterL,noSkinL]
                Dependencies : cmds - 
        '''                 
        toReturnB = False
        outSkinClusterL=[]
        outSkinnedObj = []
        tab = "    "
        if len(inObjL):
            for obj in inObjL:
                print "  obj =", obj
                skinClusterList = []
                history = cmds.listHistory(obj, il=2)
                # print "    history = ", history
                if history not in [None,"None"]:
                    for node in history:
                        print "   node=",node
                        if cmds.nodeType(node) == "skinCluster":
                            skinClusterList.append(node)
                            outSkinClusterL.append(node)
                            outSkinnedObj.append(obj)
                else :
                    print "#Error# getSkinCluster(): No skin, No History stack"
                    toReturnB = False

                if len(skinClusterList) < 1:
                    shapes = cmds.listRelatives(obj, s=True)
                    for shape in shapes:
                        history = cmds.listHistory(shape)
                        for node in history:
                            if cmds.nodeType(node) == "skinCluster":
                                skinClusterList.append(node)
                                outSkinClusterL.append(node)
                
        

        noSkinL = list(set(inObjL) - set(outSkinnedObj))
        print "outSkinnedObj=", outSkinnedObj
        print "noSkinL=", noSkinL
        if len(outSkinClusterL) >= len(inObjL):
            toReturnB = True

        print tab,"SkinCluster/obj = {0} / {1}".format(len(outSkinClusterL),len(inObjL) )


        return [toReturnB,outSkinClusterL,noSkinL]



# ------------------------ cleaning Function -----------------
# object cleaning
def resetSRT( inObjL=[], *args,**kwargs):
    """ Description: remet les valeur SRT a (1,1,1) (0,0,0) (0,0,0)
        Return : [toReturnB,debugD]
        Dependencies : cmds - checkSRT()
    """
    print "resetSRT()"

    tab = "    "
    cursel = inObjL
    debugD = {}
    debugL = []
    resetedL = []
    toReturnB = True
    
    for i in cursel:
        
        if  not checkSRT([i])[0]:
            # print "    reseting",i
            try:
                cmds.xform(i, ro=(0, 0, 0), t=(0, 0, 0), s=(1, 1, 1))
                resetedL.append(i)
            except Exception,err:
                toReturnB=False
                debugL.append(err)


    debugD["errors"] = debugL
    debugD["resetedL"]= resetedL


    # print tab,"DONE",toReturnB
    return [toReturnB,debugD]

def checkKeys(inObjL=[],*args, **kwargs):
    """ Description: check if there is some keys on keyables of inObjL
        Return : [BOOL,LIST,INTEGER,FLOAT,DICT,STRING]
        Dependencies : cmds - isKeyed()
    """
    toReturnB = True
    debugD = {}
    for obj in inObjL:
        test,debugL = isKeyed(inObj=obj)
        # print "    *",test,debugL
        if test:
            toReturnB = False
            debugD[obj] = debugL
    
    # print "##",debugD
    return [toReturnB,debugD]

def cleanKeys( inObjL=[], *args, **kwargs):
    """ Description: delete all animation on inObj
        Return : [toReturnB,cleanedL,debugD]
        Dependencies : cmds - checkKeys()
    """
    print "cleanKeys()"
    toReturnB = True
    debugD = []
    cleanedL = []
    print "inObjL=", inObjL
    oktest, debugD = checkKeys(inObjL=inObjL, )
    print "cleanKeys(2)"
    if not oktest:
        for obj,j in debugD.iteritems():
            for toDeleteL in j.values():
                try:
                    cmds.delete(toDeleteL)
                    cleanedL.append(toDeleteL)
                except Exception,err:
                    toReturnB = False
                    debugD[obj] = err
                    print "ERROR:",obj,err

    return [toReturnB,cleanedL,debugD]

def cleanUnusedInfluence(inObjL="",*args,**kwargs):
    """ Description: Delete unused influance on given inObjL . Return Flase if some obj doesn't have a skinClust
        Return : [BOOL, totalSkinClusterL, deletedDict{skinCluster:DeletedInfluenceL}]
        Dependencies : cmds - isSkinned() - 
    """
    print "cleanUnusedInfluance()"

    # to convert to real python code with cmds.skinCluster(theSkincluster, removeUnusedInfluence=True)
    tab = "    "
    toReturnB=True
    deletedDict = {}
    outCount = 0
    totalSkinClusterL= []
    if len(inObjL)>0:
        for obj in inObjL:
            skinned,skinClusterL,noSkinL = isSkinned(inObjL=[obj])
            totalSkinClusterL.extend(skinClusterL)
            # print tab,obj,skinned,skinClusterL,noSkinL
            if skinned in [True,1]:
                for skinCluster in (skinClusterL):
                    print tab,skinCluster

                    # get def list all and the unsused w
                    defL = cmds.skinCluster(skinCluster,q=1,  inf=True)
                    wDefL = cmds.skinCluster(skinCluster,q=1,  wi=True)
                    toDeleteL = list(set(defL)-set(wDefL))
                    print tab,"toDeleteL=", toDeleteL

                    # turn of the skinNode for faster exec
                    baseSkinNState = cmds.getAttr (skinCluster +".nodeState")
                    cmds.setAttr (skinCluster+".nodeState", 1)

                    # removing loop
                    if len(toDeleteL)>0:
                        for i in toDeleteL:
                            print tab,"**",skinCluster,i
                            try:
                                u=cmds.skinCluster(skinCluster,e=True,  ri=i, )
                            except Exception,err:
                                print err
                                toReturnB=False
                        
                        outCount +=1
                        deletedDict[skinCluster]= toDeleteL
                        print outCount,len(deletedDict)
                    # turn on skinNode    
                    cmds.setAttr (skinCluster+".nodeState", 0)


    return [toReturnB,totalSkinClusterL,deletedDict]

def setSmoothness(inObjL=[], mode=0, *args,**kwargs):
    print "setSmoothness()"
    tab="    "
    toReturnB = True
    debugD = {}
    # handle the display of mesh in viewport
    if type(inObjL) is not list:
        inObjL = list(inObjL)
    for obj in inObjL:
        # print tab,obj
        try :
            shapeL=cmds.listRelatives(obj,s=1,ni=1)
            if shapeL:
                for shape in shapeL:
                    print "    ",shape
                    # connect the attr if not connected
                    if not cmds.connectionInfo(shape + "."+"smoothLevel",isDestination=True):
                        cmds.displaySmoothness( obj, polygonObject=mode )
        except Exception,err:
            toReturnB = False
            debugD[obj]= err

    print tab,"DONE",toReturnB, debugD   

    

    return [toReturnB,debugD]

def disableShapeOverrides(inObjL=[],*args, **kwargs):
    # desactivate Overide des geometry contenu dans le set "set_meshCache"
    print "disableShapeOverrides()"
    tab = "   "
    toReturnB = True
    debugD= {}
    attrL = ["overrideEnabled","overrideDisplayType"]
    for obj in inObjL:
        for attr in attrL:
            try:
                cmds.setAttr (cmds.listRelatives(obj, c=True, ni=True, type="shape", fullPath=True)[0]+"."+ attr,0)
            except Exception,err:
                toReturnB = False
                debugD[obj]= attr

    print tab,"DONE",toReturnB

    

    return [toReturnB,debugD]



# scene cleaning
def cleanMentalRayNodes ( toDeleteL=['mentalrayGlobals','mentalrayItemsList','miDefaultFramebuffer','miDefaultOptions',
    'Draft','DraftMotionBlur','DraftRapidMotion','Preview','PreviewCaustics','PreviewFinalGather','PreviewGlobalIllum',
    'PreviewImrRayTracyOff','PreviewImrRayTracyOn','PreviewMotionblur','PreviewRapidMotion','Production','ProductionFineTrace',
    'ProductionMotionblur','ProductionRapidFur','ProductionRapidHair','ProductionRapidMotion',
    ],
    *args, **kwargs):
    """ Description: Delete all mentalrayNodes in toDeleteL
        Return : [toReturnB,toDeleteL,deletedL,failL]
        Dependencies : cmds - 
    """
    
    print "cleanMentalRayNodes()"
    tab = "    "
    toReturnB = True
    deletedL=[]
    failL=[]
    print tab,"toDeleteL=", toDeleteL

    for i in toDeleteL:
        if cmds.objExists(i):
            try:
                cmds.lockNode(i, lock=False)
                cmds.delete(i)
                deletedL.append(i)
            except:
                toReturnB=False
                failL.append(i)


    return [toReturnB,toDeleteL,deletedL,failL]

def cleanTurtleNodes ( toDeleteL=["TurtleDefaultBakeLayer"], check=False, *args, **kwargs):
    """ Description: Delete all turtle in toDeleteL
        Return : [toReturnB,toDeleteL,deletedL,failL]
        Dependencies : cmds - 
    """
    
    print "cleanMentalRayNodes()"
    tab = "    "
    toReturnB = True
    deletedL=[]
    failL=[]
    print tab,"toDeleteL=", toDeleteL

    for i in toDeleteL:
        if cmds.objExists(i):
            try:
                cmds.lockNode(i, lock=False)
                if not check:
                    cmds.delete(i)
                deletedL.append(i)
            except:
                toReturnB=False
                failL.append(i)


    return [toReturnB,toDeleteL,deletedL,failL]


def cleanRefNodes(toDeleteL = ["UNKNOWN_REF_NODE","SHAREDREFERENCENODE","REFERENCE"],testMode=False,*args,**kwargs):
        print "cleanRefNodes()"
        tab = "    "
        toReturnB = False
        objtoDeleteL=[]
        deletedL=[]
        print tab,"toDeleteL=", toDeleteL
         # clean UNKNOWN REF NODES =======================
        for ref in cmds.ls(type='reference'):
            for curToDelType in toDeleteL:
                
                if curToDelType.upper() in cmds.objectType(ref).upper():
                    print tab, '* %s' % ref
                    objtoDeleteL.append(ref)
                    try:
                        cmds.lockNode(ref, lock=False)
                        if not testMode:
                            cmds.delete(ref)
                        print tab,"DELETED:", ref
                        deletedL.append(curToDelType)
                    except Exception, e:
                            print tab,"%s"% e

        if len(objtoDeleteL) == len(deletedL):
            toReturnB = True
        else:
            toReturnB = False

        return [toReturnB,objtoDeleteL,deletedL]


def check_NS (NS_exclusion=[],*args, **kwargs):
    toReturnB= True
    # "UI","shared" NS are used by maya itself
    NS_exclusionBL=["UI","shared"]
    badNSL =[]
    nsL = cmds.namespaceInfo(listOnlyNamespaces=True)
    NS_exclusionBL.extend(NS_exclusion)
    if len(nsL):
        for i in nsL:
            if i not in NS_exclusionBL:
                toReturnB = False
                badNSL.append(i)
    return [toReturnB,badNSL]

def remove_All_NS ( NSexclusionL = [""], limit = 100, *args,**kwargs):
        """ Description: Delete all NameSpace appart the ones in the NSexclusionL
            Return : nothing
            Dependencies : cmds - 
        """
        tab= "    "
        print "remove_All_NS()"
        toReturnB = True
        # "UI","shared" NS are used by maya itself
        NS_exclusionBL=["UI","shared"]
        NS_exclusionBL.extend(NSexclusionL)
        # set the current nameSpace to the root nameSpace
        cmds.namespace(setNamespace = ":")
        # get NS list
        nsL = cmds.namespaceInfo(listOnlyNamespaces=True)# list content of a namespace  
        

        for loop in range(len(nsL)+2):
            nsL = cmds.namespaceInfo(listOnlyNamespaces=True)
            for ns in nsL:
                if ns not in NS_exclusionBL:
                    print tab+"ns:",ns
                    cmds.namespace( removeNamespace =ns, mergeNamespaceWithRoot=True)

        # recursive
        count = 0
        nsLFin = cmds.namespaceInfo(listOnlyNamespaces=True)
        while len(nsLFin)>2:
            remove_All_NS(NSexclusionL = NSexclusionL)
            count += 1
            if count > limit:
                break

        return [toReturnB]


# WIIIIP APPEND THE SPECIAL CASE OF SET AND DO NOTHING in the check script
def cleanDisplayLayerWithSet (tableD={"set_meshCache":["geometry",2,0],"set_control":["control",0,0] }, preDelAll=True, *arg, **kwargs):
    """ Description: Clean the display Layers by rebuilding it with the content of the corresponding sets 
                        setL <-> layerL
        Return : [BOOL,LIST,INTEGER,FLOAT,DICT,STRING]
        Dependencies : cmds - createDisplayLayer() - delete_displayLayer()
    """
    
    tab = "    "
    toReturnB= True
    debugL = []

    # pre deleting all layers if rebuild is possible
    if preDelAll:
        oktest= True
        for theSet,paramL in tableD.iteritems():
            if not cmds.objExists(theSet):
                oktest=False
        if oktest:
            delete_displayLayer()

    # rebuild with given sets
    for theSet,paramL in tableD.iteritems():
        if cmds.objExists(theSet):
            inObjL = cmds.listConnections( theSet+".dagSetMembers",source=1)
            if inObjL:
                createDisplayLayer ( n=paramL[0], inObjL=inObjL, displayType=paramL[1], hideOnPlayback=paramL[2])
                debugL.append(theSet + " :DONE")
            else:
                toReturnB= False
                debugL.append(theSet + " :EMPTY")
        else:
            toReturnB= False
            debugL.append(theSet + " :DOESN'T EXISTS")
    
    return [toReturnB,debugL]


def cleanUnusedConstraint(*args, **kwargs):
    """ Description: Delete All Un-connected Constraint
        Return : BOOL,debugD
        Dependencies : cmds - UnusedNodeAnalyse()
    """
    print "cleanUnusedConstraint()"
    
    toReturnB,debugD = UnusedNodeAnalyse(execptionTL = [], specificTL=["constraint",], mode="delete")
    # print "**debugD=", debugD
    return [toReturnB,debugD]

def cleanUnUsedAnimCurves( *args, **kwargs):
    """ Description: Delete All Un-connected Anim_Curves
        Return : BOOL,debugD
        Dependencies : cmds - UnusedNodeAnalyse()
    """
    print "cleanUnUsedAnimCurves()"

    toReturnB,debugD = UnusedNodeAnalyse(execptionTL = [], specificTL=["animCurve"], mode="delete")

    return [toReturnB,debugD]

def CleanDisconnectedNodes(*args, **kwargs):
    """ Description: Delete All Un-connected non dag Nodes
        Return : BOOL,debugD
        Dependencies : cmds - UnusedNodeAnalyse()
    """
    print "CleanDisconnectedNodes()"
    
    toReturnB,debugD = UnusedNodeAnalyse(execptionTL = ["dagNode","defaultRenderUtilityList"], specificTL=[], mode="delete")

    return [toReturnB,debugD]



