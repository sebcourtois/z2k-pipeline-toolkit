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
import maya.cmds as cmds

# printF is in each script

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



#♠--------------------- CHECK FUNCTION ------------------------------
def NodeTypeScanner(execptionTL = [], exceptDerived= True, specificTL=[], specificDerived=False,
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


def isKeyed ( inObj, *args, **kwargs):
        """ Description: Check if the given object'keyable attrib are effictively keyed
            Return : [BOOL,DebugList]
            Dependencies : cmds - isConnected() -
        """

        toReturnB = False
        debugD ={}
        if cmds.objExists(inObj):
            if cmds.listConnections(inObj):
                AttrL = cmds.listAttr(inObj,k=True)
                if len(AttrL)>0:
                    for attr in AttrL:
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

def isSkinned( inObjL=[], verbose=False, printOut = False,*args,**kwargs):
        ''' Description : Get the list of the SlinClusters of the selected mesh
                Return : List of skinClusters
                Dependencies : cmds - 
        '''                 
        toReturnB = False
        outSkinClusterL=[]
        outSkinnedObj = []
        tab = "    "
        if len(inObjL):
            for obj in inObjL:
                print "    obj =", obj
                skinClusterList = []
                history = cmds.listHistory(obj, il=2)
                print "    history = ", history
                if history not in [None,"None"]:
                    for node in history:
                        if cmds.nodeType(node) == "skinCluster":
                            skinClusterList.append(node)
                            outSkinClusterL.append(node)
                            outSkinnedObj.append(obj)
                else :
                    print "#Error# getSkinCluster(): No History stack"
                    toReturnB = False

                if len(skinClusterList) < 1:
                    shapes = cmds.listRelatives(obj, s=True)
                    for shape in shapes:
                        history = cmds.listHistory(shape)
                        for node in history:
                            if cmds.nodeType(node) == "skinCluster":
                                skinClusterList.append(node)
                                outSkinClusterL.append(node)
                
        

        debugL = list(set(inObjL) - set(outSkinnedObj))
        if len(outSkinClusterL) >= len(inObjL):
            toReturnB = True

        print tab,"Total obj = {0} / {1}".format(len(outSkinClusterL),len(inObjL) )

        if verbose :
            # prints -------------------
            printF("isSkinned()", st="t")
            printF(toReturnB, st="r")
            printF("skinned_object = {0} / {1}".format(len(outSkinClusterL),len(inObjL) ) )
            for i in debugL:
                printF("    No skin on: {0}".format(i) )
            # --------------------------


        return [toReturnB,outSkinClusterL]

def checkSRT ( inObjL=[], verbose=False,*args,**kwargs):
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

        if verbose:
            # prints -------------------
            printF("checkSRT()", st="t")
            printF(toReturnB, st="r")
            printF ( " not zero total: {0}/{1}".format( len(debugD.keys()),len(inObjL), ) )
            for i,j in debugD.iteritems():

                printF ( "    - {0} : {1}".format( i.ljust(15), " ".join(j) ) )
            # --------------------------


        # print "toReturnB=",toReturnB
        return [toReturnB,debugD]



def checkKeys(inObjL=[],verbose=False, *args, **kwargs):

        toReturnB = True
        debugD = {}
        for obj in inObjL:
            # print "obj=", obj
            test,debugL = isKeyed(inObj=obj)
            # print "    *",test,debugL
            if test:
                toReturnB = False
                debugD[obj] = debugL
                # print "    debugD=", debugL
        # prints -------------------
        if verbose:
            printF("checkKeys()", st="t")
            printF(toReturnB, st="r")
            printF ( " error on: {0}/{1}".format( len(debugD.keys()),len(inObjL), ) )
            for i,j in debugD.iteritems():
                printF ( "     - {0}: {1}".format( i.ljust(15),j.keys() ) )
        # --------------------------
        # print "##",debugD
        return [toReturnB,debugD]


























# ------------------------ cleaning Function -----------------

def resetSRT( inObjL=[], *args,**kwargs):
        # remet les valeur SRT a (1,1,1) (0,0,0) (0,0,0)
        print "resetSRT()"
        tab = "    "
        cursel = inObjL
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

        # print tab,"DONE",toReturnB

        # prints -------------------
        printF("resetSRT()", st="t")
        printF(toReturnB, st="r")
        printF ( " Reseted : {0}/{1}".format( len(resetedL),len(inObjL), ) )
        printF ( " error on: {0}/{1}".format( len(debugL),len(inObjL), ) )
        for j in debugL:
            printF ( "     on : {0}".format( j.ljust(15) ) )
       

        # --------------------------

        return [toReturnB,debugL]


def cleanKeys( inObjL=[],verbose=True, *args, **kwargs):
        print "cleanKeys()"
        toReturnB = True
        debugD = []
        cleanedL = []
        print "inObjL=", inObjL
        oktest, debugD = checkKeys(inObjL=inObjL, verbose=False)
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
                        print "AHAHAH",obj,err

         # prints -------------------
        if verbose:
            printF("cleanKeys()", st="t")
            printF(toReturnB, st="r")
            printF ( " Cleaned : {0}/{1}".format( len(cleanedL),len(inObjL), ) )
            printF ( " error on: {0}/{1}".format( len(debugD.keys()),len(inObjL), ) )
            for i,j in debugD.iteritems():
                printF ( "     - {0}: {1}".format( i.ljust(15),j.values() ) )
        # --------------------------

        return [toReturnB,debugD]



def cleanUnusedInfluence( inObjL="",*args,**kwargs):
        """ Description: Delete unused influance on given inObjL . Return Flase if some obj doesn't have a skinClust
            Return : [BOOL,deletedDict{skinCluster:DeletedInfluenceL}]
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
                isSkinned,skinClusterL = isSkinned(inObjL=[obj])
                totalSkinClusterL.extend(skinClusterL)
                print tab,obj,isSkinned,skinClusterL
                if isSkinned in [True,1]:
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
                        if len(toDeleteL)>1:
                            for i in toDeleteL:
                                print tab,"**",skinCluster,i
                                try:
                                    u=cmds.skinCluster(skinCluster,e=True,  ri=i, )
                                except Exception,err:
                                    print err
                                    toReturnB=False
                            
                            outCount +=1
                            deletedDict[skinCluster]= toDeleteL
                        # turn on skinNode    
                        cmds.setAttr (skinCluster+".nodeState", 0)
                


        # prints -------------------
        printF("cleanUnusedInfluance()", st="t")
        printF(toReturnB, st="r")
        printF ( "total cleaned skinCluster: {0}/{1}".format(outCount, len(totalSkinClusterL) ) )
        for i,j in deletedDict.iteritems():
            printF ( "influance Deleted on {0}: {1}".format( i.ljust(15),j ) )
        # --------------------------


        return [toReturnB,deletedDict]




def cleanUnusedNode( execptionTL = [], specificTL= [], mode = "delete",verbose=True, *args, **kwargs):
        """ Description: Test if nodes have connections based on type and excluded_type in all the scene and either delete/select/print it.
                        mode = "delete" / "select" / "print"
            Return : [BOOL,Dict]
            Dependencies : cmds - NodeTypeScanner()
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
        if mode in ["delete"]:
            if len(unconectedCL):
                for node in unconectedCL:
                    try:
                        if not cmds.lockNode(node, q=1)[0]:
                            print "try deleting",node,cmds.lockNode(node,q=1)[0]
                            cmds.delete (node)
                            deletedL.append(node)
                    except Exception,err:
                        errorL.append(node)
                        # print "ERROR on {0} : {1}".format(node,err)
            if len(errorL)>0:
                toReturnB = False
                debugD["Errored"] = errorL

        if mode in ["select"]:
            cmds.select (unconectedCL) 

        if mode in ["print"]:
            pass


        # prints -------------------
        if verbose:
            printF(toReturnB, st="r")
            printF("errorL:")
            for i in errorL:
                printF("    -{0} error".format(i))
            printF("total errored = {0}".format(len(errorL)))
            
            printF("deleteL:")
            for i in deletedL:
                printF("    -{0} deleted".format(i))
            printF("total deleted = {0}".format(len(deletedL)))
        # --------------------------


        return [toReturnB,debugD]



# wip to make faster
def CleanDisconnectedNodes(*args, **kwargs):
        """ Description: Delete All Un-connected non dag Nodes
            Return : BOOL,debugD
            Dependencies : cmds - cleanUnusedNode()
        """
        printF( "CleanDisconnectedNodes()", st="t")
        toReturnB,debugD = cleanUnusedNode(execptionTL = ["dagNode"], specificTL=[], mode="delete")

        return [toReturnB,debugD]


def cleanUnUsedAnimCurves( mode = "delete", *args, **kwargs):
        """ Description: Delete All Un-connected Anim_Curves
            Return : BOOL,debugD
            Dependencies : cmds - cleanUnusedNode()
        """
        printF( "cleanUnUsedAnimCurves()", st="t")
        toReturnB,debugD = cleanUnusedNode(execptionTL = [], specificTL=["animCurve"], mode="delete")

        return toReturnB,debugD


def cleanUnusedConstraint(mode = "delete",*args, **kwargs):
        """ Description: Delete All Un-connected Constraint
            Return : BOOL,debugD
            Dependencies : cmds - cleanUnusedNode()
        """
        print "cleanUnusedConstraint()"
        printF( "cleanUnusedConstraint()", st="t")
        toReturnB,debugD = cleanUnusedNode(execptionTL = [], specificTL=["constraint",], mode="delete")

        return [toReturnB,debugD]

def cleanUnUsedAnimCurves( mode = "delete", *args, **kwargs):
        """ Description: Delete All Un-connected Anim_Curves
            Return : BOOL,debugD
            Dependencies : cmds - cleanUnusedNode()
        """
        printF( "cleanUnUsedAnimCurves()", st="t")
        toReturnB,debugD = cleanUnusedNode(execptionTL = [], specificTL=["animCurve"], mode="delete")

        return toReturnB,debugD





















 # decorators ---------------------------
def Z2KprintDeco(func, *args, **kwargs):
        def deco(*args, **kwargs):
            # print u"Exécution de la fonction '%s'." % func.__name__
            func( toScrollF=BDebugBoard, toFile = DebugPrintFile, *args, **kwargs)
        return deco

def waiter (func,*args, **kwargs):
        def deco(*args, **kwargs):
            result = True
            cmds.waitCursor( state=True )
            print "wait..."
            try:
                print func
                result = func(*args, **kwargs)
            except Exception,err:
                print "#ERROR JP:",err
                # cmds.waitCursor( state=False )
            cmds.waitCursor( state=False )
            print "...wait"
            if not result and GUI:
                print "try GUI ANYWAY MOTHER fOCKER!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
                cmds.frameLayout(BDebugBoardF,e=1,cll=True,cl=0)

            return result
        return deco













# ------------ printer -----------------
@Z2KprintDeco
def printF(  text="", st="main", toScrollF="", toFile = "", GUI = False,
        openMode="a+", *args, **kwargs):
        # print "printF()",GUI,toFile
        stringToPrint=""
 
        text = str(object=text)
        if st in ["title","t"]:
            stringToPrint += "\n"+text.center(40, "-")+"\n"
        if  st in ["main","m"]:
            stringToPrint += "    "+text+"\n"
        if st in ["result","r"]:
            stringToPrint += " -RESULT: "+text.upper()+"\n"

        if not toFile in [""] :
            # print the string to a file
            with open(toFile, openMode) as f:
                f.write( stringToPrint )
                print stringToPrint

        if not GUI :
            # print to textLayout
            cmds.scrollField(toScrollF, e=1,insertText=stringToPrint, insertionPosition=0, font = "plainLabelFont")
            print stringToPrint