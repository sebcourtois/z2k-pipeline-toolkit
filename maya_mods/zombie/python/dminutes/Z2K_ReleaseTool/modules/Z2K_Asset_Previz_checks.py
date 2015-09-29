#!/usr/bin/python
# -*- coding: utf-8 -*-
########################################################
# Name    : Z2K_Asset_Previz_checks
# Version : v008
# Description : Create previz maya file in .mb with some cleaning one the leadAsset
# Comment : BASE SCRIPT OUT OF Z2K in v002
# Author : Jean-Philippe Descoins
# Date : 2015-26-08
# Comment : wip
#
# TO DO:
#       - separate interface from base class
#       - add BigDaddy check
#       x MentalRayCleanNodes (['mentalrayGlobals','mentalrayItemsList','miDefaultFramebuffer','miDefaultOptions'])
#       x check geometry all to zero
#       x BUG check colorLum
#       - check geometry modeling history
#       - Ckeck les path de texture, tout doit être ecris avec la variable d environement non resolved
#       WIP Clean ref Nodes + exception arnold etc
#       ? Check UV smoothing/display paremeters
#       ? delete mentalRayNode
#       x check BaseStructure
#       x check group geo check for attrib of smooth: connect grp_geo smooth lvl2 to set_meshCache obj if pas existant
#       x check Under_AssetStructure
#       x Clean NameSpace
#       x Delete unused Nodes 
#       x isSkinned
#       x cleanUnusedInfluence
#       x disableShapeOverrides
#       x Clean display Layers
#       x check keyed CTR
#       x Check controls SRT 
#       x Reset controls SRT
#       x Reduce smooth display
#       x delete unUsed animCurves
#       x delete unsusedConstraints
#       x Check if there is some keys on controlers and geometries
#       x show bool result
########################################################




import os,sys
import maya.cmds as cmds
import maya.mel as mel
from functools import partial
import inspect



class checkModule(object):
    name = "AssetPreviz_Module"
    cf = name

    basePath =  os.environ.get("MAYA_MODULE_PATH").split(";")[0]
    upImg= basePath +"/zombie/python/dminutes/Z2K_ReleaseTool/icons/Z2K_ReleaseTool/Z2K_PREVIZ_LOGO_A3.bmp"


    def __init__(self,*args, **kwargs):
        print "init"
        self.ebg = True
        self.DebugPrintFile =""
        self.trueColor = self.colorLum( [0,0.75,0],-0.2 )
        self.falseColor =  self.colorLum(  [0.75,0,0] , -0.2)


    


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

    def isSkinned(self, inObjL=[], verbose=False, *args, **kwargs):
        """ Description: test if a skincluster is attached to the obj in inObjL
            Return : BOOL
            Dependencies : cmds - 
        """
        print "isSkinned()"
        toReturnB = False
        tab = "    "
        outSkinClusterL = []
        outSkinnedObj = []
        debugL = []
        if len(inObjL)>0:
            for obj in inObjL:
                print "   ",obj
                if cmds.objExists(obj):
                    # get underShapeL
                    underShapeL = cmds.listRelatives(obj, c=True, ni=True, shapes=True)
                    print "  underShapeL: len=", len(underShapeL),underShapeL
                    for shape in underShapeL:
                        # print "shape=", shape
                        # getting source objL
                        attrib = shape +'.inMesh'
                        if cmds.objExists(attrib):
                            if cmds.connectionInfo(attrib, isDestination=True):
                                sourceL = cmds.listConnections( attrib, d=False, s=True,p=False,shapes=True )
                                if type(sourceL) is not list:
                                    sourceL = [sourceL]
                                
                                # sourceL loop
                                for source in sourceL:
                                    if cmds.objectType(source) in ["skinCluster"]:
                                        print tab,"OK :", source
                                        outSkinClusterL.append(source)
                                        outSkinnedObj.append(obj)
                                    else:
                                        pass
                                        # print tab,"BAD : connectedTo  :", source
                            else:
                                pass
                                # print tab,"BAD : noConnection :", shape
                                
                        else:
                            pass
                            # print tab,"BAD : noAttrib_inMesh :", shape
                            
                

        debugL = list(set(inObjL) - set(outSkinnedObj))
        if len(outSkinClusterL) > 0 :
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

    # decorators ---------------------------
    def Z2KprintDeco(func, *args, **kwargs):
        def deco(self,*args, **kwargs):
            # print u"Exécution de la fonction '%s'." % func.__name__
            func(self, toScrollF=self.BDebugBoard, toFile = self.DebugPrintFile,*args, **kwargs)
        return deco

    def waiter (func,*args, **kwargs):
        def deco(self,*args, **kwargs):
            result = True
            cmds.waitCursor( state=True )
            print "wait..."
            try:
                print func
                result = func(self,*args, **kwargs)
            except Exception,err:
                print "#ERROR JP:",err
                # cmds.waitCursor( state=False )
            cmds.waitCursor( state=False )
            print "...wait"
            if not result:
                cmds.frameLayout(self.BDebugBoardF,e=1,cll=True,cl=0)

            return result
        return deco

    # ------------ printer -----------------
    # @Z2KprintDeco
    def printF(self, text="",st="main",toScrollF="", toFile = "C:/jipe_Local/00_JIPE_SCRIPT/PythonTree/RIG_WORKGROUP/tools/batchator_Z2K/Release_debug.txt",
        openMode="a+", *args, **kwargs):
        stringToPrint=""
 
        text = str(object=text)
        if st in ["title","t"]:
            stringToPrint += "\n"+text.center(40, "-")+"\n"
        if  st in ["main","m"]:
            stringToPrint += "    "+text+"\n"
        if st in ["result","r"]:
            stringToPrint += " -RESULT: "+text.upper()+"\n"

        if not toFile in [""]:
            # print the string to a file
            with open(toFile, openMode) as f:
                f.write( stringToPrint )

        else:
            # print to textLayout
            cmds.scrollField(toScrollF, e=1,insertText=stringToPrint, insertionPosition=0, font = "plainLabelFont")
            

    


    # cleaning/checking functions --------------------------------------------
  
    def checkBaseStructure(self,*args,**kwargs):
        """
        Descrition: Check if th Basic hierachy is ok
        Return: [Bool,detail]
        """
        print "checkBaseStructure()"
        tab= "    "
        debugL = []
        debugDetL = []

        debugD = {}
        toReturnB = True

        # check if asset gp and set here

        baseExcludeL = ["persp","top","front","side","defaultCreaseDataSet","defaultLayer"]
        baseObjL = ["asset",]
        baseSetL = ["set_meshCache","set_control"]
        baseLayerL = ["control","geometry"]
        AllBaseObj = baseLayerL + baseObjL + baseSetL
        print tab+"AllBaseObj=", AllBaseObj
        topObjL = list(set(cmds.ls(assemblies=True,) ) - set(baseExcludeL) )
        topSetL = self.getOutlinerSets()
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
        if not sorted(baseSetL) == sorted(topSetL):
            debugD["topSetL"]["result"] = "PAS CONFORME"
            debugD["topSetL"]["Found"] = topSetL
            toReturnB= False
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

        # prints -------------------
        self.printF("checkBaseStructure()", st="t")
        self.printF(toReturnB, st="r")
        for i,dico in debugD.iteritems():
            toPrint=""
            if not dico["result"] in ["OK"]:
                toPrint = str(i).ljust(15)+": "+ str( dico["result"]+"    Found="+ str(dico.get("Found","")))
            else:
                toPrint = i.ljust(15)+": "+ str( dico["result"] )
            self.printF( toPrint )
        # -------------------

        print "toReturnB=", toReturnB
        return toReturnB,debugD

    def checkAssetStructure(self, assetgpN="asset", expectedL=["grp_rig","grp_geo"],*args,**kwargs):
        print "checkAssetStructure()"
        toReturnB = False
        debugD = {}
        tab="    "
        expect_str = " - ".join(expectedL)
        if cmds.objExists(assetgpN):
            childL = cmds.listRelatives(assetgpN,  c=True)
            print tab,expect_str, childL
            debugD[expect_str] = {}
            if sorted(expectedL) == sorted(childL):
                toReturnB = True
                debugD[ expect_str ]["result"] = "OK"
                print tab, toReturnB
            else:
                toReturnB = False
                debugD[expect_str]["result"] = "PAS CONFORME"
                debugD[expect_str]["Found"] = childL
                print tab, toReturnB

        # prints -------------------
        self.printF("checkAssetStructure()", st="t")
        self.printF(toReturnB, st="r")
        for i,dico in debugD.iteritems():
            self.printF( i.ljust(10)+" : "+ str( dico["result"] ) )
            if len(dico.get("Found",""))>0:
                self.printF("     -Found= " + str( dico.get("Found","")   ) )
        # --------------------------
        

        return toReturnB,debugD

    def checkGrp_geo(self,theGroup="asset|grp_geo",theAttrL= ["smoothLevel1","smoothLevel2"] ,*args, **kwargs):
        """ check if the attrib of smooth are present
        """
        print("checkGrp_geo()")
        toCreateL = []
        toReturnB = True
        if cmds.objExists(theGroup):
            print "{0}: ok".format(theGroup)
            for theAttr in theAttrL:
                if not cmds.objExists(theGroup+"."+ theAttr):
                    toReturnB = False
                    toCreateL.append(theGroup+"."+ theAttr)
                else:
                    toReturnB = True
        else:
            toReturnB = False
            toCreateL =  theAttrL     


        # prints -------------------
        self.printF("checkGrp_geo()", st="t")
        self.printF(toReturnB, st="r")
        if len(toCreateL):
            self.printF("Missing AttribL={0}".format(toCreateL))
        # --------------------------

        return [toReturnB,toCreateL]

    def cleanGrp_geo (self, theGroup="asset|grp_geo",theAttrL= ["smoothLevel1","smoothLevel2"] ,assetType="previz", *args, **kwargs):
        print "cleanGrp_geo()"
        
        erroredL = []
        createdL= []
        toReturnB = True
        if cmds.objExists(theGroup):
            print "  theGroup=", theGroup
            for theAttr in theAttrL:
                print "    theAttr=", theAttr
                if not cmds.objExists(theGroup+"."+ theAttr):
                    print "     creating attr"

                    try:
                        print "creating attrib:",theAttr
                        cmds.addAttr(theGroup, longName=theAttr, attributeType = "long", keyable=True, min = 0, max=2) 
                        
                        toReturnB = True
                        createdL.append(theGroup+"."+theAttr)



                    except Exception,err:
                        print "bug"
                        print "    ##",err,Exception
                        toReturnB = False
                        erroredL.append(theAttr)

                else:
                    print "      -Allready exists"
                    toReturnB = True

                # set smooth attr to 0
                cmds.setAttr(theGroup+"."+theAttr,0)
            
            # connecting attrib
            if assetType in ["previz"]:
                for i in self.getSetContent(inSetL=["set_meshCache"]):
                    print "*",i
                    shapeL=cmds.listRelatives(i,s=1,ni=1)
                    if shapeL:
                        for shape in shapeL:
                            print "    ",shape
                            # connect the attr if not connected
                            if not cmds.connectionInfo(shape + "."+"smoothLevel",isDestination=True):
                                cmds.connectAttr(theGroup+"."+theAttrL[1], shape + "."+"smoothLevel", f=True)
                            
                            # set the display mesh preview option
                            cmds.setAttr(shape+"."+"displaySmoothMesh",2)

        else:
            toReturnB = False
        

        # prints -------------------
        self.printF("cleanGrp_geo()", st="t")
        self.printF(toReturnB, st="r")
        if len(createdL):

            self.printF("created Attrib: {0}/{1}".format(len(createdL),len(theAttrL)) )
        # --------------------------
        return [toReturnB,createdL]

    def cleanMentalRayNodes (self, toDeleteL=['mentalrayGlobals','mentalrayItemsList','miDefaultFramebuffer','miDefaultOptions'],*args, **kwargs):
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


        # prints -------------------
        self.printF("cleanMentalRayNodes()", st="t")
        self.printF(toReturnB, st="r")
        if len(failL):
            self.printF( "failL= {0}".format( failL  ) )
        # --------


        return [toReturnB,failL]

    def cleanRefNodes(self, toDeleteL = ["UNKNOWN_REF_NODE","SHAREDREFERENCENODE","REFERENCE"],*args,**kwargs):
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
                        cmds.delete(ref)
                        print tab,"DELETED:", ref
                        deletedL.append(curToDelType)
                    except Exception, e:
                            print tab,"%s"% e

        if len(objtoDeleteL) == len(deletedL):
            toReturnB = True
        else:
            toReturnB = False


        # prints -------------------
        self.printF("cleanRefNodes()", st="t")
        self.printF(toReturnB, st="r")
        self.printF( "objectDeleted={0}/{1}".format( len(objtoDeleteL),len(deletedL)  ) )
        # --------

        return [toReturnB]

    def remove_All_NS (self, NSexclusionL = [""],limit = 100,*args,**kwargs):
        """ Description: Delete all NameSpace appart the ones in the NSexclusionL
            Return : nothing
            Dependencies : cmds - 
        """
        tab= "    "
        print "remove_All_NS()"
        toReturnB = True

        # "UI","shared" NS are used by maya itself
        NS_exclusion=["UI","shared"]
        NS_exclusion.extend(NSexclusionL)
        # set the current nameSpace to the root nameSpace
        cmds.namespace(setNamespace = ":")
        # get NS list
        nsL = cmds.namespaceInfo(listOnlyNamespaces=True)# list content of a namespace  
        

        for loop in range(len(nsL)+2):
            nsL = cmds.namespaceInfo(listOnlyNamespaces=True)
            for ns in nsL:
                if ns not in NS_exclusion:
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

        # prints -------------------
        self.printF("remove_All_NS()", st="t")
        self.printF(toReturnB, st="r")
        # --------------------------

        return [toReturnB]

    def delete_displayLayer(self, FilterL=["defaultLayer"], *args, **kwargs):
        print "delete_displayLayer()"

        displ = cmds.ls(type="displayLayer", long=True)
        for lay in displ:
            if lay not in FilterL:
                cmds.delete(lay)

    def createDiplayLayer (self,  n="default_Name", inObjL=[], displayType=0, hideOnPlayback=0,enableOverride=True, *args, **kwargs):
        # createDiplayLayer( state = {0:Normal state, 1:Templated, 2:Reference}
        print "createDiplayLayer(%s,%s,%s)" % (n,displayType,hideOnPlayback)

        # create layer if doesn't exist
        if not cmds.objExists(n):
            cmds.createDisplayLayer(name=n, number=1,empty=True,nr=True)

        # set the layer state
        cmds.setAttr(n + ".displayType", displayType)
        cmds.setAttr(n + ".hideOnPlayback",hideOnPlayback)
        cmds.setAttr(n + ".enabled",enableOverride)

        # add obj list to the layer
        cmds.editDisplayLayerMembers(n, inObjL,nr=True)

    def cleanDisplayLayerWithSet (self, tableD={"set_meshCache":["geometry",2,0],"set_control":["control",0,0] }, preDelAll=True, *arg, **kwargs):
        """ Description: Clean the display Layers by rebuilding it with the content of the corresponding sets 
                            setL <-> layerL
            Return : [BOOL,LIST,INTEGER,FLOAT,DICT,STRING]
            Dependencies : cmds - createDiplayLayer() - delete_displayLayer()
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
                self.delete_displayLayer()

        # rebuild with given sets
        for theSet,paramL in tableD.iteritems():
            if cmds.objExists(theSet):
                inObjL = cmds.listConnections( theSet+".dagSetMembers",source=1)
                if inObjL:
                    self.createDiplayLayer ( n=paramL[0], inObjL=inObjL, displayType=paramL[1], hideOnPlayback=paramL[2])
                    debugL.append(theSet + " :DONE")
                else:
                    toReturnB= False
                    debugL.append(theSet + " :EMPTY")
            else:
                toReturnB= False
                debugL.append(theSet + " :DOESN'T EXISTS")
        

        # prints -------------------
        self.printF("cleanDisplayLayerWithSet()", st="t")
        self.printF(toReturnB, st="r")
        for i in debugL:
            self.printF(i)
        # --------------------------
        return [toReturnB]


    def cleanUnusedNode(self, execptionTL = [], specificTL= [], mode = "delete",verbose=True, *args, **kwargs):
        """ Description: Test if nodes have connections based on type and excluded_type in all the scene and either delete/select/print it.
                        mode = "delete" / "select" / "print"
            Return : [BOOL,Dict]
            Dependencies : cmds - NodeTypeScanner()
        """
        
        toReturnB = True
        nodeL = self.NodeTypeScanner(execptionTL=execptionTL, specificTL=specificTL)
        print "*nodeL=", len(nodeL)
        unconectedCL =[]
        # loop
        for node in nodeL:
            if not self.isConnected(node=node)[0]:
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
            self.printF(toReturnB, st="r")
            self.printF("errorL:")
            for i in errorL:
                self.printF("    -{0} error".format(i))
            self.printF("total errored = {0}".format(len(errorL)))
            
            self.printF("deleteL:")
            for i in deletedL:
                self.printF("    -{0} deleted".format(i))
            self.printF("total deleted = {0}".format(len(deletedL)))
        # --------------------------


        return [toReturnB,debugD]
    

    def cleanUnusedConstraint(self,mode = "delete",*args, **kwargs):
        """ Description: Delete All Un-connected Constraint
            Return : BOOL,debugD
            Dependencies : cmds - cleanUnusedNode()
        """
        print "cleanUnusedConstraint()"
        self.printF( "cleanUnusedConstraint()", st="t")
        toReturnB,debugD = self.cleanUnusedNode(execptionTL = [], specificTL=["constraint",], mode="delete")

        return [toReturnB,debugD]

    def cleanUnUsedAnimCurves(self, mode = "delete", *args, **kwargs):
        """ Description: Delete All Un-connected Anim_Curves
            Return : BOOL,debugD
            Dependencies : cmds - cleanUnusedNode()
        """
        self.printF( "cleanUnUsedAnimCurves()", st="t")
        toReturnB,debugD = self.cleanUnusedNode(execptionTL = [], specificTL=["animCurve"], mode="delete")

        return toReturnB,debugD

    # wip to make faster
    def CleanDisconnectedNodes(self,*args, **kwargs):
        """ Description: Delete All Un-connected non dag Nodes
            Return : BOOL,debugD
            Dependencies : cmds - cleanUnusedNode()
        """
        self.printF( "CleanDisconnectedNodes()", st="t")
        toReturnB,debugD = self.cleanUnusedNode(execptionTL = ["dagNode"], specificTL=[], mode="delete")

        return [toReturnB,debugD]

    def setSmoothness(self, inObjL=[], mode=0, *args,**kwargs):
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

        # prints -------------------
        self.printF("setSmoothness()", st="t")
        self.printF(toReturnB, st="r")
        self.printF ( " error on: {0}/{1}".format( len(debugD.keys()),len(inObjL), ) )
        for i,j in debugD.iteritems():
            self.printF ( "     - {0}: {1}".format( i.ljust(15),j ) )
        # --------------------------

        return [toReturnB,debugD]

    def disableShapeOverrides(self,inObjL=[],*args, **kwargs):
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

         # prints -------------------
        self.printF("disableShapeOverrides()", st="t")
        self.printF(toReturnB, st="r")
        self.printF ( " error on: {0}/{1}".format( len(debugD.keys()),len(inObjL), ) )
        for i,j in debugD.iteritems():
            self.printF ( "     - {0}: {1}".format( i.ljust(15),j ) )
        # --------------------------

        return [toReturnB,debugD]



    def cleanUnusedInfluence(self, inObjL="",*args,**kwargs):
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
                isSkinned,skinClusterL = self.isSkinned(inObjL=[obj])
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
        self.printF("cleanUnusedInfluance()", st="t")
        self.printF(toReturnB, st="r")
        self.printF ( "total cleaned skinCluster: {0}/{1}".format(outCount, len(totalSkinClusterL) ) )
        for i,j in deletedDict.iteritems():
            self.printF ( "influance Deleted on {0}: {1}".format( i.ljust(15),j ) )
        # --------------------------


        return [toReturnB,deletedDict]
    
    def checkSRT (self, inObjL=[], verbose=False,*args,**kwargs):
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
            self.printF("checkSRT()", st="t")
            self.printF(toReturnB, st="r")
            self.printF ( " not zero total: {0}/{1}".format( len(debugD.keys()),len(inObjL), ) )
            for i,j in debugD.iteritems():

                self.printF ( "    - {0} : {1}".format( i.ljust(15), " ".join(j) ) )
            # --------------------------


        # print "toReturnB=",toReturnB
        return [toReturnB,debugD]

    def resetSRT(self, inObjL=[], *args,**kwargs):
        # remet les valeur SRT a (1,1,1) (0,0,0) (0,0,0)
        print "resetSRT()"
        tab = "    "
        cursel = inObjL
        debugL = []
        resetedL = []
        toReturnB = True
        
        for i in cursel:
            
            if  not self.checkSRT([i])[0]:
                # print "    reseting",i
                try:
                    cmds.xform(i, ro=(0, 0, 0), t=(0, 0, 0), s=(1, 1, 1))
                    resetedL.append(i)
                except Exception,err:
                    toReturnB=False
                    debugL.append(err)

        # print tab,"DONE",toReturnB

        # prints -------------------
        self.printF("resetSRT()", st="t")
        self.printF(toReturnB, st="r")
        self.printF ( " Reseted : {0}/{1}".format( len(resetedL),len(inObjL), ) )
        self.printF ( " error on: {0}/{1}".format( len(debugL),len(inObjL), ) )
        for j in debugL:
            self.printF ( "     on : {0}".format( j.ljust(15) ) )
       

        # --------------------------

        return [toReturnB,debugL]

   
    def checkKeys(self,inObjL=[],verbose=False, *args, **kwargs):

        toReturnB = True
        debugD = {}
        for obj in inObjL:
            # print "obj=", obj
            test,debugL = self.isKeyed(inObj=obj)
            # print "    *",test,debugL
            if test:
                toReturnB = False
                debugD[obj] = debugL
                # print "    debugD=", debugL
        # prints -------------------
        if verbose:
            self.printF("checkKeys()", st="t")
            self.printF(toReturnB, st="r")
            self.printF ( " error on: {0}/{1}".format( len(debugD.keys()),len(inObjL), ) )
            for i,j in debugD.iteritems():
                self.printF ( "     - {0}: {1}".format( i.ljust(15),j.keys() ) )
        # --------------------------
        # print "##",debugD
        return [toReturnB,debugD]

    def cleanKeys(self, inObjL=[],verbose=True, *args, **kwargs):
        print "cleanKeys()"
        toReturnB = True
        debugD = []
        cleanedL = []
        print "inObjL=", inObjL
        oktest, debugD = self.checkKeys(inObjL=inObjL, verbose=False)
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
            self.printF("cleanKeys()", st="t")
            self.printF(toReturnB, st="r")
            self.printF ( " Cleaned : {0}/{1}".format( len(cleanedL),len(inObjL), ) )
            self.printF ( " error on: {0}/{1}".format( len(debugD.keys()),len(inObjL), ) )
            for i,j in debugD.iteritems():
                self.printF ( "     - {0}: {1}".format( i.ljust(15),j.values() ) )
        # --------------------------

        return [toReturnB,debugD]
    

    # ---------------------------------------------------------------------------------------------------------
    #--------------------- Buttons functions ----------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------------------
    @waiter
    def btn_checkStructure(self, controlN="", GUI=False,*args, **kwargs):
        boolResult=True

        # set progress bar
        self.pBar_upd(step=1, maxValue=4, e=True)

        # steps
        if not self.checkBaseStructure()[0]:
            boolResult = False
        self.pBar_upd(step= 1,)
        if not self.checkAssetStructure( assetgpN="asset", expectedL=["grp_rig","grp_geo"])[0]:
            boolResult = False
        self.pBar_upd(step= 1,)

        if not self.cleanGrp_geo(theGroup="asset|grp_geo", theAttrL=["smoothLevel1","smoothLevel2"])[0]:
            boolResult = False
        self.pBar_upd(step= 1,)
        if not self.checkGrp_geo( )[0]:
            boolResult = False
        self.pBar_upd(step= 1,)

        # colors
        print "*btn_checkStructure:",boolResult
        self.colorBoolControl(controlL=[controlN], boolL=[boolResult], labelL=[""], GUI=GUI)
        
        return boolResult

    @waiter
    def btn_CleanScene(self, controlN="", GUI=False,*args, **kwargs):
        boolResult=True

        # set progress bar
        self.pBar_upd(step=1, maxValue=8, e=True)

        # steps
        if not self.cleanRefNodes()[0]:
            boolResult = False
        self.pBar_upd(step= 1,)
        if not self.cleanMentalRayNodes()[0]:
            boolResult = False
        self.pBar_upd(step= 1,)
        if not self.remove_All_NS(NSexclusionL=[""], limit=100)[0]:
            boolResult = False
        self.pBar_upd(step= 1,)
        if not self.cleanDisplayLayerWithSet(setL=["set_meshCache","set_control"],layerL=["geometry","control"])[0]:
            boolResult = False
        self.pBar_upd(step= 1,)
        if not self.cleanUnUsedAnimCurves( mode="delete")[0]:
            boolResult = False
        self.pBar_upd(step= 1,)
        if not self.cleanUnusedConstraint( mode="delete")[0]:
            boolResult = False 
        self.pBar_upd(step= 1,)
        if not self.CleanDisconnectedNodes( mode="delete")[0]:
            boolResult = False 
        self.pBar_upd(step= 1,)
               
        # colors
        print "*btn_CleanScene:",boolResult
        self.colorBoolControl(controlL=[controlN], boolL=[boolResult], labelL=[""], GUI=GUI)
        
        return boolResult
        
    @waiter
    def btn_CleanObjects(self, controlN="", GUI=False,*args, **kwargs):
        boolResult=True

        # set progress bar
        self.pBar_upd(step=1, maxValue=10, e=True)

        meshCacheObjL = self.getSetContent(inSetL=["set_meshCache"] )
        controlObjL = self.getSetContent(inSetL=["set_control"] )

        # steps
        # if not self.isSkinned(inObjL= meshCacheObjL,verbose=True)[0] :
        #     boolResult = False
        self.pBar_upd(step= 1,)
        if not self.cleanUnusedInfluence(inObjL=meshCacheObjL)[0] :
            boolResult = False
        self.pBar_upd(step= 1,)
        if not self.setSmoothness(inObjL=meshCacheObjL,mode=0)[0] :
            boolResult = False
        self.pBar_upd(step= 1,)
        if not self.disableShapeOverrides(inObjL=meshCacheObjL)[0] :
            boolResult = False
        self.pBar_upd(step= 1,)
        if not self.checkSRT(inObjL =meshCacheObjL, verbose=True)[0] :
            boolResult = False
        self.pBar_upd(step= 1,)
        if not self.cleanKeys(inObjL=controlObjL,verbose=True)[0] :
            boolResult = False
        self.pBar_upd(step= 1,)
        if not self.checkKeys(inObjL=controlObjL,verbose=True)[0] :
            boolResult = False
        self.pBar_upd(step= 1,)


        if not self.resetSRT(inObjL=controlObjL)[0] :
            boolResult = False
        self.pBar_upd(step= 1,)
        if not self.checkSRT(inObjL =controlObjL, verbose=True)[0] :
            boolResult = False
        self.pBar_upd(step= 1,)

        # colors
        print "*btn_CleanObjects:",boolResult
        self.colorBoolControl(controlL=[controlN], boolL=[boolResult], labelL=[""], GUI=GUI)

        return boolResult


    def btn_clearAll(self, *args, **kwargs):
        print "btn_clearAll()"

        cmds.scrollField(self.BDebugBoard, e=1, clear=True)
        cmds.progressBar(self.BValidationPBar,e=1,progress=0)

        defCol = [0.40,0.40,0.40]
        cmds.button(self.BcheckStructure, e=1, bgc= defCol)
        cmds.button(self.BCleanScene, e=1, bgc= defCol)
        cmds.button(self.BCleanObjects, e=1, bgc= defCol)
        cmds.button(self.BCleanAll, e=1, bgc= defCol)


    def btn_cleanAll(self, GUI=False, *args, **kwargs):
        print "btn_cleanAll()"
        boolResult = True
        if not self.btn_checkStructure(controlN=self.BcheckStructure, GUI=GUI):
            boolResult = False
        print "*1",boolResult
        if not self.btn_CleanScene(controlN=self.BCleanScene, GUI=GUI):
            boolResult = False
        print "*2",boolResult
        if not self.btn_CleanObjects(controlN=self.BCleanObjects, GUI=GUI):
            boolResult = False
        
        # colors
        print "*3",boolResult
        self.colorBoolControl(controlL=[self.BCleanAll], boolL=[boolResult], labelL=[""],GUI=GUI)
        return boolResult


   

    # ----------------------------------jipe general functions -------------------------------
    def colorLighten(self, thecolor=[0,0,0], factor= 0.5, *args, **kwargs):
        outColor = [ (1- x) * factor + x for x in thecolor ]
        return outColor

    def colorDarken(self, thecolor=[0,0,0], factor= 0.5, *args, **kwargs):
        outColor = [ x * factor for x in thecolor ]
        return outColor

    def colorLum (self, thecolor=[0,0,0], factor= 0.5,  *args, **kwargs):
        outColor = thecolor
        if factor > 0 :
            outColor = [ (1- x) * factor + x for x in thecolor ]

        elif factor < 0 :
            outColor = [ x * abs(1 + factor) for x in thecolor ]

        return outColor

    # -------------------------- interface function --------------------------------
    def colorBoolControl(self, controlL=[], boolL=[],labelL=[""], GUI=False, *args, **kwargs):
        # color the controlL depending on the given Bool
        if GUI:
            for i,j,label in zip(controlL,boolL,labelL):
                    if j in [True,1]:
                        cmds.button(i, e=1, backgroundColor=self.trueColor, ebg=self.ebg)
                    else:
                        cmds.button(i, e=1, backgroundColor=self.falseColor, ebg=self.ebg)


    def pBar_upd (self, step=0,maxValue=10,e=False,GUI=False, *args, **kwargs):
        # print "pBar_upd()",step
        if GUI:
            if e:
                cmds.progressBar(self.BValidationPBar,e=1,maxValue=maxValue,progress=step)
            else:
                if step:
                    cmds.progressBar(self.BValidationPBar,e=1,step=step,)



    # ------------- Layout -------------------------------------------------------
    def createWin(self, *args,**kwargs):
        # test si la windows exist / permet d'avoir plusieurs windows grace a var "cf" de la class
        if cmds.window(self.cf, q=True, exists=True):
            cmds.deleteUI(self.cf, window=True)
        #create la window et rename apres
        self.cf = cmds.window(self.cf ,rtf=True, tlb=False, t=(self.cf + " : " + str(self.cf)))
        outputW = cmds.window(self.cf, e=True, sizeable=True, t=(self.cf + " : " + str(self.cf)))
        
        # show window
        cmds.showWindow(self.cf)
        return outputW


    def insertLayout(self, parent="",*args, **kwargs):

        if parent in [""]:
            parent = self.createWin()

        cmds.setParent(parent)
        self.bigDadL = cmds.frameLayout(label=self.name.center(50), fn="boldLabelFont", lv=0)
        self.layoutImportModule = cmds.columnLayout("layoutImportModule",adj=True)
        cmds.tabLayout(tabsVisible=0,borderStyle="full")
        cmds.columnLayout("layoutModule",columnOffset= ["both",0],adj=True,)

        cmds.image(image=self.upImg)
        cmds.columnLayout("layoutImportModule",columnOffset= ["both",0],adj=True,)
        self.BCleanAll = cmds.button("CLEAN-CHECK ALL",c= partial(self.btn_cleanAll,True),en=1)

        self.BcheckStructure = cmds.button("checkStructure", )
        cmds.button(self.BcheckStructure,e=1,c= partial( self.btn_checkStructure,self.BcheckStructure,True) )

        self.BCleanScene = cmds.button("CleanScene",)
        cmds.button(self.BCleanScene,e=1,c= partial( self.btn_CleanScene,self.BCleanScene,True))

        self.BCleanObjects = cmds.button("CleanObjects",)
        cmds.button(self.BCleanObjects,e=1,c= partial( self.btn_CleanObjects,self.BCleanObjects,True) )
        
        self.BValidationPBar = cmds.progressBar(maxValue=3,s=1 )

        self.BDebugBoardF= cmds.frameLayout("DebugBoard",cll=True,cl=True)
        self.BDebugBoard = cmds.scrollField(w=250,h=300,)
        
        cmds.setParent("..")
        self.BClearAll = cmds.button("clear",c= self.btn_clearAll,)
  
        

#----------------------------------------------------------------------------------------------------------
#--------------------- EXEC -------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------

    

