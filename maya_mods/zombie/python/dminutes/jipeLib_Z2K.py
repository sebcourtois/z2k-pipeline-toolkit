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



def matchByXformMatrix(cursel=[], mode=0, *args, **kwargs):
    ''' Description : Match SRT in world cursel objects to the first one
                    mode : - 0/first = the first object is the reference
                           - 1/parallal = the first half is reference for the second half
        Return : Bool
        Dependencies : cmds - 
    ''' 
    print "matchByXformMatrix()"
    if mode in [0,"first "]:
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







#♠--------------------- Wip enlever tout les self ------------------------------
def jlistSets(self, *args,**kwargs):
        """
        description : wrapper of cmds.listSets() that return empty list []
                     if None originaly returned. Avoid treatment problems.
        """
        toReturnL = cmds.listSets(*args,**kwargs)
        if not toReturnL:
            toReturnL=[]

        return toReturnL


def setFilterTest(self,setName="",includedSetL=["objectSet","textureBakeSet","vertexBakeSet","character"],
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


def getOutlinerSets(self,*args, **kwargs):
        """ Description: return the outliner visible filtered objects sets 
            Return : [LIST]
            Dependencies : cmds -  setFilterTest()
        """
        
        return [setName for setName in cmds.ls(sets=True) if self.setFilterTest(setName=setName)]


def getSetContent (self, inSetL=[],*args,**kwargs):
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



def getSel(self,*args, **kwargs):
        objL = cmds.ls( os=True, fl=True, l=True, )
        return objL



def isKeyed (self, inObj, *args, **kwargs):
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



def isConnected (self, node="", exceptionL=["nodeGraphEditorInfo","defaultRenderUtilityList","objectSet"], *args, **kwargs):
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

def isSkinned(self, inObjL=[], verbose=False, printOut = False,*args,**kwargs):
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
            self.printF("isSkinned()", st="t")
            self.printF(toReturnB, st="r")
            self.printF("skinned_object = {0} / {1}".format(len(outSkinClusterL),len(inObjL) ) )
            for i in debugL:
                self.printF("    No skin on: {0}".format(i) )
            # --------------------------


        return [toReturnB,outSkinClusterL]


def NodeTypeScanner(self,execptionTL = [], exceptDerived= True, specificTL=[], specificDerived=False,
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



