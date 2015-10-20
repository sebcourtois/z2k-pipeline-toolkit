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

# Z2K base general functions -----------------
def getBasePath(*args, **kwargs):
    """
    recupere le path de base des modules
    """
    basePath = ""
    allModL = os.environ.get("MAYA_MODULE_PATH").split(";")
    for p in allModL:
        if "/z2k-pipeline-toolkit/maya_mods" in p:
            basePath = p + "/"
    return basePath

# printer 
def printF( text="", st="main", toScrollF="", toFile = "", GUI= True,
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

        if not toFile in [""] and not GUI:
            # print the string to a file
            with open(toFile, openMode) as f:
                f.write( stringToPrint )
                print stringToPrint

        else:
            # print to textLayout
            cmds.scrollField(toScrollF, e=1,insertText=stringToPrint, insertionPosition=0, font = "plainLabelFont")
            print stringToPrint

# 3D maya functions ---------------------------
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






























