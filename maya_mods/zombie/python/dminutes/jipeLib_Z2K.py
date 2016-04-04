#!/usr/bin/python
# -*- coding: utf-8 -*-
################################################################
# Name    : Temp Zomby jipeLib
# Version : 001
# Description : all Z2K'scripts related functions
# Author : Jean-Philippe Descoins
# Date : 2015_09_10
# Comment : WIP# TO DO:
# - spped up the check structure
# - ADD CHECK for DOUBLE NAMES

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
import maya.mel as mel
import itertools
from dminutes import assetconformation
import tkRig as tk
reload (tk)

# TK wrap/TWEAK 

def tkMirror(*args, **kwargs):
    # special case of added controlers
    # upperBrowL = ['Left_Brow_upRidge_01_ctrl', 'Left_Brow_upRidge_02_ctrl', 'Left_Brow_upRidge_03_ctrl', 'Left_Brow_upRidge_04_ctrl', 
    #             'Right_Brow_upRidge_01_ctrl', 'Right_Brow_upRidge_02_ctrl', 'Right_Brow_upRidge_03_ctrl', 'Right_Brow_upRidge_04_ctrl'
    #             ]
    upperBrowD = {'Left_Brow_upRidge_01_ctrl':'Right_Brow_upRidge_01_ctrl',
                  'Left_Brow_upRidge_02_ctrl':'Right_Brow_upRidge_02_ctrl',
                  'Left_Brow_upRidge_03_ctrl':'Right_Brow_upRidge_03_ctrl',
                  'Left_Brow_upRidge_04_ctrl':'Right_Brow_upRidge_04_ctrl', 

                  'Right_Brow_upRidge_01_ctrl':'Left_Brow_upRidge_01_ctrl',
                  'Right_Brow_upRidge_02_ctrl':'Left_Brow_upRidge_02_ctrl',
                  'Right_Brow_upRidge_03_ctrl':'Left_Brow_upRidge_03_ctrl',
                  'Right_Brow_upRidge_04_ctrl':'Left_Brow_upRidge_04_ctrl',   
                
                }

    cursel= cmds.ls(sl=1)
    upperSymL = []
    tkendSel = []
    print "cursel=", cursel
    for i  in cursel:
        # print "    *",i.split(":",1)[-1]

        if  i.split(":",1)[-1] in upperBrowD.keys():
            upperSymL.append(i)
        else:
            tkendSel.append(i)

    # jp TK mirror wrap ----------------------------------------------------------
    print "upperSymL=", upperSymL
    print "tkendSel=", tkendSel
    if tkendSel:
        tk.mirrorPose(tkendSel)

    # jp upperSymLspecial mirror ------------------------------------------------
    # set the values
    attrTableD = {  "sx":1,
                    "sy":1,
                    "sz":1,
                    "rx":-1,
                    "ry":-1,
                    "rz":1,
                    "tx":1,
                    "ty":1,
                    "tz":-1,
       }

    oppositeValD={}
    for i in upperSymL:
        
        # get corresponding opposite side
        if ":" in i:
            curChr = i.split(":",1)[0] 
            key = i.split(":",1)[-1]
            oppositeSide =curChr+":"+ upperBrowD[key]
        else:
            curChr = i
            key = i
            oppositeSide = upperBrowD[i]

        print "*",i,"<>",oppositeSide

        
        # get the values
        oppositeValD[oppositeSide]={}
        print i,"<>", oppositeSide
        for attr,fact in attrTableD.iteritems():
            # print "  ",attr,fact
            curVal = cmds.getAttr(i+"."+attr)
            # print "    curval=", curVal
            oppositeValD[oppositeSide][attr]=fact*curVal


    # set attr
    for obj,attrD in oppositeValD.iteritems():
        print "->",obj
        for attr,val in attrD.iteritems():
            # print "   ",attr,val
            cmds.setAttr(obj+"."+attr,val)
        


# general function

def collectAttr(InObjList,mode = "all",*args,**kwargs):
        ''' Description : collect the attrib of the passed InObjList,
                          mode  = ["all"/"selection"]
                Return : list of the obj.attributs
                Dependencies : cmds -
        '''
        gChannelBoxName = mel.eval('$temp=$gChannelBoxName')
        outlist = []

        # ----- internal function -----
        def objLAttrLloop (objL,attrList,*args,**kwargs):
            # loop to append obj.attr to outputList excluding bad results.
            outlist = []
            if type(objL) is list:
                for obj in objL:
                    try:
                        if cmds.objExists(obj):
                            for attr in attrList:
                                outlist.append(obj + "." + attr)
                    except:
                        pass
            return outlist
        # -----------------------------------

        if len(InObjList) > 0:
            if mode in ["all"]:
                for obj in InObjList:
                    try:
                        attrList = cmds.listAttr(obj, k=True)
                        attrList.extend(cmds.listAttr(obj, cb=True))
                    except:
                        pass

                    for attr in attrList:
                        outlist.append(obj + "." + attr)
                    # print obj
            if mode in ["selection"]:
                mainObjL = cmds.channelBox(gChannelBoxName, q=True, mol=True,)
                shapeObjL = cmds.channelBox(gChannelBoxName, q=True, sol=True,)
                historyObjL = cmds.channelBox(gChannelBoxName, q=True, hol=True,)
                outputObjL = cmds.channelBox(gChannelBoxName, q=True, ool=True,)
                mainSelAttrL = cmds.channelBox(gChannelBoxName, q=True, sma=True,)
                shapeSelAttrL = cmds.channelBox(gChannelBoxName, q=True, ssa=True,)
                historySelAttrL = cmds.channelBox(gChannelBoxName, q=True, sha=True,)
                outputSelAttrL = cmds.channelBox(gChannelBoxName, q=True, soa=True,)

                # print mainObjL, shapeObjL, historyObjL, outputObjL
                # print mainSelAttrL, shapeSelAttrL, historySelAttrL, outputSelAttrL

                # append the output list with the selected attributs
                outlist = objLAttrLloop(mainObjL, mainSelAttrL)
                outlist.extend( objLAttrLloop(shapeObjL, shapeSelAttrL))
                outlist.extend( objLAttrLloop(historyObjL, historySelAttrL))
                outlist.extend( objLAttrLloop(outputObjL, outputSelAttrL))

        # print outlist
        return outlist

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
def getAssetL (assetCat="chr", *args, **kwargs):
    """ Description: return the asset list filtered by category (chr/prp/set/env/c2d...)
        Return : [LIST]
        Dependencies : cmds - 
    """

    theDir = os.path.normpath(os.environ.get("ZOMB_ASSET_PATH")) + os.sep + assetCat
    print "theDir=", theDir
    if os.path.isdir(theDir):
        assetL = sorted(os.listdir(theDir))
        if not len(assetL):
            assetL = ["Empty Folder"]

    else:
        assetL = ["Invalide folder"]

    return assetL

def getCatL (*args, **kwargs):
    """ Description: recupere la list des category d asset (chr-prp-set-c2d ...etc)
        Return : LIST
        Dependencies : os - 
    """

    theDir = os.environ.get("ZOMB_ASSET_PATH")
    print "theDir=", theDir
    if os.path.isdir(theDir):
        assetL = sorted(os.listdir(theDir))
        if not len(assetL):
            assetL = ["Empty Folder"]

    else:
        assetL = ["Invalide folder"]

    return assetL

def getAssetTypeL (*args, **kwargs):
    """ Description: recupere la list des type d asset ("anim","previz","modeling","render","master"...etc)
        Return : LIST
        Dependencies : os - 
    """
    print "getAssetTypeL()"
    return ["anim", "previz", "modeling", "render", "master"]

def getShotName(*args, **kwargs):
    """ Description: renvoi le nom du shot
        Return : STRING
        Dependencies : cmds - 
    """

    print "getShotName()"
    # get shot name
    currentSceneP = cmds.file(q=1, l=1)[0]
    currentScene = os.path.basename(currentSceneP)
    shotName = currentScene.rsplit("_", 1)[0]
    print "shotName=", shotName
    if shotName[:2] + shotName[6:9] in ["sq_sh"]:
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
    # scenePathTmp = cmds.file(q=1 , sceneName=True)
    scenePathTmp = cmds.file(q=1 , expandName=True)

    print "scenePathTmp=", scenePathTmp
    if   "asset" in scenePathTmp :
        print "folder asset ok"
        categoryL = getCatL()
        assetTypeL = getAssetTypeL()
        print "categoryL=", categoryL
        print "assetTypeL=", assetTypeL
        #path and short name
        outD["scenePath"] = cmds.file(q=1 , expandName=True)
        # outD["fileName"]= cmds.file(q=1,sceneName=True,shortName=True)
        outD["fileName"] = outD["scenePath"].rsplit("/", 1)[-1]

        outD["assetName"] = outD["fileName"].rsplit("_", 1)[0]
        outD["assetCat"] = outD["fileName"].split("_", 1)[0]
        outD["assetType"] = outD["fileName"].rsplit("_", 1)[1].split("-", 1)[0]
        outD["version"] = outD["fileName"].split("-", 1)[1][:4]

        if outD["assetName"][:2] + outD["assetName"][6:9] in ["sq_sh"]:
            print "this is a shot", outD["assetName"]


        # verification

        # assetCat
        if not outD["assetCat"]  in categoryL :
            print "* bad assetCat -->", outD["assetCat"], "not in", categoryL
            testOk = False
        else:
            print "*", "assetCat ok:".rjust(15), outD["assetCat"]

        # Version
        if not outD["version"][0]  in ["v"] and not len(outD["version"])in [4]:
            print "* bad version"
            testOk = False
        else:
            print "*", "version ok:".rjust(15), outD["version"]

        # assetType
        if not outD["assetType"] in assetTypeL and not len(outD["version"])in [4]:
            print "* bad assetType"
            testOk = False
        else:
            print "*", "assetType ok:".rjust(15), outD["assetType"]

        # assetName
        if not outD["assetName"].count("_") not in [3] :
            print "* bad assetName"
            testOk = False
        else:
            print "*", "assetName ok:".rjust(15), outD["assetName"]


        # finally return the dico
        if testOk:
            return outD
        else:
            return False
    else:
        return False

def createIncrementedFilePath(filePath="", vSep="_v", extSep=".ma", digits=3, *args, **kwargs):
    """ Description: return incremented File path starting with the last version present in the 
        folder of the given file.
        first split the extension of the file
        then search the version by le right side and split the first instance of it
        Work ideally with folder with the only correctly versionned files.
        Return : string of the versioned filePath
        Dependencies :  os
    """

    print "createVersionIncrementedPath(%s)" % filePath
    NotFoundBool = True
    filePath = os.path.normpath(filePath)

    # get last version in folder
    theDir, theFile = filePath.rsplit(os.sep, 1)[0], filePath.rsplit(os.sep, 1)[1].rsplit(extSep, 1)[0]
    fullDirContentL = [f.rsplit(extSep, 1)[0] for f in os.listdir(os.path.normpath(filePath).rsplit(os.sep, 1)[0]) if  extSep in f]
    print fullDirContentL
    # list all files with the same base name
    # ############################################################ checker si le repertoire est avec au moins 1 fichier
    ConcernedFileL = []
    if len(fullDirContentL) > 0:
        # get concernedFiles
        for f in fullDirContentL:
            print "\t", (theFile.rsplit(extSep, 1)[0]).rsplit(vSep, 1)[0].upper() , " / ", f.upper()

            if theFile.rsplit(vSep, 1)[0].upper() in [  f.rsplit(vSep, 1)[0].upper() ] and len(theFile) == len(f):
                ConcernedFileL.append(f)

        print "ConcernedFileL = %s" % (ConcernedFileL)

        if len(ConcernedFileL) > 0:
            NotFoundBool = False
            lastv = theDir + os.sep + sorted(ConcernedFileL, key=lambda member: member.lower())[-1]
            print "lastv = %s" % (lastv)
            outPath = lastv
        else :
            NotFoundBool = True

    # set the default Versionning
    if NotFoundBool in [True, 1]:
        outPath = theDir + os.sep + theFile


    # finally oparate the versionning
    bazPath, curVer = outPath.rsplit(vSep, 1)

    curVer = str(int(curVer) + 1).zfill(digits)
    filePath = bazPath + vSep + curVer + extSep
    print "\t filePath=", filePath


    print "\t return: %s" % filePath
    return filePath



# printer  -------------------------------------------------------
def printF(text="", st="main", toScrollF="", toFile="", inc=False, GUI=True,
    openMode="a+", versionning=True, *args, **kwargs):
    """ Description: printer avec mise en forme integrer et link vers file or maya layout
        Return : [BOOL,LIST,INTEGER,FLOAT,DICT,STRING]
        Dependencies : cmds - 
    """

    # print "printF()",GUI,toFile
    stringToPrint = ""

    text = str(object=text)
    if st in ["title", "t"]:
        stringToPrint += "\n" + text.center(40, "-") + "\n"
    if  st in ["main", "m"]:
        stringToPrint += "    " + text + "\n"
    if st in ["result", "r"]:
        stringToPrint += " -RESULT: " + text.upper() + "\n"

    if not toFile in [""] and not GUI:
        # print the string to a file
        with open(toFile, openMode) as f:
            f.write(stringToPrint)
            print stringToPrint

    else:
        # print to textLayout
        cmds.scrollField(toScrollF, e=1, insertText=stringToPrint, insertionPosition=0, font="plainLabelFont")
        print stringToPrint

# decorator generique ----------------------------
def waiter (func, *args, **kwargs):

    def deco(self, *args, **kwargs):
        result = True
        cmds.waitCursor(state=True)
        print "wait..."
        print"tarace"
        try:
            print func
            result = func(self, *args, **kwargs)
        except Exception, err:
            print "#ERROR in {0}(): {1}".format(func.__name__, err)
            print "     ->", Exception

            # cmds.waitCursor( state=False )

        cmds.waitCursor(state=False)
        print "...wait"
        if not result and self.GUI:
            print "try GUI ANYWAY "
            cmds.frameLayout(self.BDebugBoardF, e=1, cll=True, cl=0)

        return result
    return deco

# 3D maya functions ---------------------------
def getCstActiveWeightPlugs(theCst,*args, **kwargs):
    print "getCstActiveWeightPlugs()"
    activeTarget = []
    # get weight plugs 
    for i in cmds.listAttr( theCst+".target[:]",multi=1):
        if "targetParentMatrix" in i:
            if cmds.getAttr(theCst + "."+ i):
                # print "    theCst=",i,cmds.getAttr(theCst+"."+i)
                activeTarget.append(theCst+"."+i.split(".targetParentMatrix",1)[0]+".targetWeight" )
    # print "activeTarget=", activeTarget
    return activeTarget


def Ltest(objL, *args, **kwargs):
    # old way
    # if type(objL) is not list:
    #     objL = [objL]

    # new way
    if not isinstance(objL, list):
        objL = [objL]

    return objL

def GetSel(mode="normal", order="sl", *args):
    ''' Description : get selection List
                    mode : -"normal" = shortest name path
                           -"fullpath" = fullpath name
                    order : -"sl" = basical aleatoire order
                            -"os" = ordererd by selection time
        Return : [List] : selectionList
        Dependencies : cmds - 
    '''
    # recuperation de la selection
    # Use : None
    objlist = []
    if order in ["os"]:
        if mode in ["normal"]:
            objlist = cmds.ls(fl=True, os=True)
        if mode in ["fullpath"]:
            objlist = cmds.ls(fl=True, l=True, os=True)
        # print objlist
    if order in ["sl"]:
        if mode in ["normal"]:
            objlist = cmds.ls(fl=True, sl=True)
        if mode in ["fullpath"]:
            objlist = cmds.ls(fl=True, l=True, sl=True)
        # print objlist
    return objlist

def getChilds(cursel=[], mode="transform", *args):
    print "getChilds()"
    # mode = type filter shape/set/dagObjects
    listOut = []
    # renvoie la list correspondante aux enfants, si il n'y en a pas renvoie l'obj lui meme
    if type(cursel) is not list:
        cursel = [cursel]

    try:
        Childs = cmds.listRelatives(cursel, c=True, ni=True, type=mode)
        for i in Childs:
            if not cmds.getAttr(i + ".intermediateObject"):
                listOut.append(i)
    except:
        listOut = cursel
    return listOut

def addAttr(inObj="", theAttrName="", theValue=1,
    theAttrType="long", keyable=True, theMin=0, theMax=1, dv=1, *args, **kwargs):
    """ Description: add the specied attribut to the speciefied obj
        Return : True
        Dependencies : cmds - 
    """

    print "addAttr()"
    toReturnB = True
    if cmds.objExists(inObj):
        if not cmds.objExists(inObj + "." + theAttrName):
            cmds.addAttr(inObj, longName=theAttrName, attributeType=theAttrType, keyable=keyable, dv=1, min=theMin, max=theMax)
            cmds.setAttr(inObj + "." + theAttrName, theValue)
        else:
            print "    attrib allready exists"
    else:
        print "    Object doesn't exists"
    return toReturnB

def matchByXformMatrix(cursel=[], mode=0, *args, **kwargs):
    ''' Description : Match SRT in world cursel objects to the first one
                    mode : - 0/first = the first object is the reference
                           - 1/parallal = the first half is reference for the second half
        Return : Bool
        Dependencies : cmds - 
    '''
    print "matchByXformMatrix()"
    if mode in [0, "first"]:
        objMatched = cursel.pop(0)
        objMatchingL = cursel
        #print objMatched, "->", objMatchingL

        # get world position of the constraining object
        ObjectMatricDico = {}
        McoorOld = cmds.xform(objMatched, matrix=True, q=True, worldSpace=True)
        scaleOld = cmds.xform(objMatched, scale=True, q=True, relative=True)
        ObjectMatricDico[objMatched] = {"Mcoord": McoorOld, "scale":scaleOld}
        # print "Matrix gettet:",ObjectMatricDico

        for objMatching in objMatchingL:
            # set back world position of the constrained object
            for key, val in ObjectMatricDico[objMatched].iteritems() :
                if key in ["Mcoord"]:
                    cmds.xform(objMatching, m=val, worldSpace=True)
                    # print "Mcoord",val
                if key in ["scale"]:

                    cmds.xform(objMatching, scale=val, relative=True)
                    # print "scale",val
            # print "Matrix setted"
        return True

def jlistSets(*args, **kwargs):
        """
        description : wrapper of cmds.listSets() that return empty list []
                     if None originaly returned. Avoid treatment problems.
        """
        toReturnL = cmds.listSets(*args, **kwargs)
        if not toReturnL:
            toReturnL = []

        return toReturnL

def OverideColor(theColor, mode="normal", TheSel=None, *args):
    ''' Description : Override the color of the selected obj
            Return : theColor
            Dependencies : cmds - GetSel()
    '''
    # Override la color de la shape de l'obj selected
    if mode in ["normal"]:
        EnableSwith = True
    if mode in ["default"]:
        EnableSwith = False
    if TheSel not in [None]:
        cursel = list(TheSel)
    else :
        cursel = GetSel()
    for obj in cursel:
        if cmds.objExists(obj):
            shapeNodes = cmds.listRelatives(obj, shapes=True, path=True)
            print " shapeNodes = ", shapeNodes
            if type(shapeNodes) is not list:
                shapeNodes = [shapeNodes]
                print shapeNodes


            for shape in shapeNodes:
                try:
                    print " shape = ", shape
                    if shape in [ None, "None" ]:
                        shape = obj
                    cmds.setAttr("%s.overrideEnabled" % (shape), EnableSwith)
                    cmds.setAttr("%s.overrideColor" % (shape), theColor)
                except Exception, err:
                    print "erreur :", Exception, err
        else:
            print "  object doesn't exist:", obj
    # print "theColor = ",theColor
    return theColor

def getColor(objL=None, *args, **kwargs):
    theColor = 0
    theColorL = []
    cursel = Ltest(objL)
    if not len(cursel) :
        cursel = GetSel()
    print "cursel=", cursel
    for obj in cursel:
        shapeNodes = cmds.listRelatives(obj, shapes=True, path=True)
        print " shapeNodes = ", shapeNodes
        if type(shapeNodes) is not list:
            shapeNodes = [shapeNodes]
            print shapeNodes


        for shape in shapeNodes:
            try:
                print " shape = ", shape
                if shape in [ None, "None" ]:
                    shape = obj
                theColor = cmds.getAttr("%s.overrideColor" % (shape))
            except Exception, err:
                print "erreur :", Exception, err
                theColor = None
        theColorL.append(theColor)
    print "theColor = ", theColor
    return theColorL


def setFilterTest(setName="", includedSetL=["objectSet", "textureBakeSet", "vertexBakeSet", "character"],
        excludedSetL=["shadingEngine", "displayLayer", "ilrBakeLayer"],
        bookmarksSets=False, defaultSets=False, lockedSets=False,
        *args, **kwargs):
        """ Description: Permet de recuperer les set Object visible dans l'outliner, avec la possibilité de changer les filtres
            Return : BOOL
            Dependencies : cmds - 
        """
        # print "setFilterTest()"
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

        # accepted sets # Rendering - dispLayers - LayerTurttle
        if (not nodeType in  includedSetL) or (nodeType in excludedSetL) :
            return False

        # # Rendering - dispLayers - LayerTurttle
        # if nodeType in excludedSetL:
        #     return False

        # bookmarks
        if not bookmarksSets :
            if cmds.getAttr(setName + "." + "annotation") in ["bookmarkAnimCurves"]:
                return False

        # maya default sets
        if not defaultSets:
            if setName in cmds.ls(defaultNodes=True) :
                return False

        # locked sets
        if not lockedSets:
            if setName in cmds.ls(lockedNodes=True) :
                return False

        # others filtered by attribs
        excludeAttrL = ["verticesOnlySet", "edgesOnlySet", "facetsOnlySet", "editPointsOnlySet", "renderableOnlySet"]
        for attr in excludeAttrL:
            if cmds.getAttr (setName + "." + attr) :
                return False

        # finally return True if nothing of all the rest
        return True

def getOutlinerSets(*args, **kwargs):
    """ Description: return the outliner visible filtered objects sets 
        Return : [LIST]
        Dependencies : cmds -  setFilterTest()
    """

    outL = (set(cmds.ls(type="objectSet")) - set(jlistSets(type=1)) - set(jlistSets(type=2)) - set(cmds.ls(defaultNodes=1)) - set(cmds.ls(lockedNodes=True)) - set(cmds.ls(undeletable=1)))
    #return [setName for setName in cmds.ls(sets=True) if setFilterTest(setName=setName)]
    return outL

def getSetContent (inSetL=[], *args, **kwargs):
        """
        description : return the objL in a setlist
        Return : [list]
        """
        outL = []
        objL = []
        for i in inSetL:
            if cmds.objExists(i):
                objL = cmds.listConnections(i + "." + "dagSetMembers", source=1,d=0)
                if objL:
                    outL.extend(objL)
        return outL

def getSel(*args, **kwargs):
        objL = cmds.ls(os=True, fl=True, l=True,)
        return objL

def getPointsOnCurve(listcurves):
    ''' Description : get the controls points on the curves of listcurves[]
            Return : list of the points
            Dependencies : cmds -
    '''
    if type(listcurves) is not list:
        listcurves = [listcurves]

    PointsOnCurves = []

    try :
        listcurves = cmds.listRelatives(listcurves, shapes=True, fullPath=True)
    except:
        pass
    for curve in listcurves:

        curvespoints = cmds.getAttr(curve + ".cv[*]")
        for i in range(len(curvespoints)):
            # print i
            # print curvespoints[i]
            PointsOnCurves.append(curve + ".cv[" + str(i) + "]")
    print "getPointsOnCurve() outlist : \n", PointsOnCurves
    return PointsOnCurves

def getGeoInHierarchy(cursel=[], theType="mesh", *args, **kwargs):
    listOut = []
    cursel = Ltest(cursel)
    if not len(cursel) > 0 :
        cursel = cmds.ls(os=True, flatten=True, allPaths=True)
    # select mesh in hierarchy
    cursel = cmds.listRelatives(cursel, allDescendents=True, path=True)
    listOut = [a for a in cursel if cmds.listRelatives(a, c=1, type=theType, path=True)]

    return listOut

def delete_displayLayer(FilterL=["defaultLayer"], *args, **kwargs):
    print "delete_displayLayer()"

    displ = cmds.ls(type="displayLayer", long=True)
    for lay in displ:
        if lay not in FilterL:
            cmds.delete(lay)

def createDisplayLayer (n="default_Name", inObjL=[], displayType=0, hideOnPlayback=0, enableOverride=True, *args, **kwargs):
    print "createDisplayLayer(%s,%s,%s)" % (n, displayType, hideOnPlayback)

    # create layer if doesn't exist
    if not cmds.objExists(n):
        cmds.createDisplayLayer(name=n, number=1, empty=True, nr=True)

    # set the layer state
    cmds.setAttr(n + ".displayType", displayType)
    cmds.setAttr(n + ".hideOnPlayback", hideOnPlayback)
    cmds.setAttr(n + ".enabled", enableOverride)

    # add obj list to the layer
    cmds.editDisplayLayerMembers(n, inObjL, nr=True)


def NodeTypeScanner(execptionTL=[], exceptDerived=True, specificTL=[], specificDerived=True,
    mayaDefaultObjL=["characterPartition", "defaultLightList1", "dynController1", "globalCacheControl",
    "hardwareRenderGlobals", "hardwareRenderingGlobals", "defaultHardwareRenderGlobals", "hyperGraphInfo",
    "hyperGraphLayout", "ikSystem", "characterPartition", "char_aurelienPolo_wip_18_sceneConfigurationScriptNode",
    "char_aurelienPolo_wip_18_uiConfigurationScriptNode", "sequenceManager1", "strokeGlobals", "time1", "defaultViewColorManager",
    "defaultColorMgtGlobals", "defaultObjectSet", "defaultTextureList1", "lightList1", "defaultObjectSet",
    "sceneConfigurationScriptNode", "uiConfigurationScriptNode",
    "persp", "top", "front", "side", "left", "back", "bottom", "defaultCreaseDataSet", "defaultLayer"
    ], *args, **kwargs):
    """ Description: Return Node list base on specific type /excepted type filtered
                    If nothing it give evrething in scene
                    basic type herited coulb be "dagNode" / "transform" /
        Return : LIST
        Dependencies : cmds - 
    """

    theTypeL = []
    allTypeL = cmds.ls(nodeTypes=1)
    toReturnL = []
    toLoopL = []
    # specificTypeList
    if not len(specificTL) > 0:

        theTypeL = allTypeL
    else:
        theTypeL = [cmds.nodeType(x, derived=specificDerived, isTypeName=True) for x in specificTL]
    print "specificTL=", specificTL
    print "theTypeL=", theTypeL

    # exclude exceptionType List
    if len(execptionTL) > 0:
        derivedTypeTmpL = [ cmds.nodeType(x, derived=exceptDerived, isTypeName=True) for x in execptionTL]
        execptionTL_derived = list(itertools.chain.from_iterable(derivedTypeTmpL))
        toLoopL = list(set(theTypeL) - set(execptionTL_derived) - set(execptionTL))
        print "execptionTL=", execptionTL
        print "execptionTL_derived=", execptionTL_derived
        print "toLoopL=", toLoopL
    else:
        toLoopL = theTypeL

    for typ in sorted(toLoopL):
        # print "****",typ
        toReturnL.extend([x for x in cmds.ls(type=typ) if  x not in mayaDefaultObjL ])



    # assure que les objects sont une seul fois dans la list
    toReturnL = list(set(toReturnL))
    return toReturnL


def UnusedNodeAnalyse(execptionTL=['containerBase', 'entity'], specificTL=[] , mode="delete", verbose=True, exculdeNameFilterL=["Arnold"], *args, **kwargs):
    """ Description: Test if nodes have connections based on type and excluded_type in all the scene and either delete/select/print it.
                    mode = "check" /"delete" / "select" / "print"
        Return : [BOOL,Dict]
        Dependencies : cmds - NodeTypeScanner() - isConnected()
    """
    print "UnusedNodeAnalyse()"
    toReturnB = True
    nodeL = NodeTypeScanner(execptionTL=execptionTL, specificTL=specificTL)
    print "*nodeL=", len(nodeL)

    #filter exculededNames
    for excluN in exculdeNameFilterL:
        for i in nodeL:
            if excluN in i:
                nodeL.remove(i)

    unconectedCL = []
    # loop
    for node in nodeL:
        if not isConnected(node=node, exceptionL=["nodeGraphEditorInfo", "defaultRenderUtilityList"])[0]:
            # print "-","toDELETe:",node
            unconectedCL.append(node)

    print "unconectedCL=", len(unconectedCL)

    # finally
    errorL = []
    deletedL = []
    debugD = {}

    if len(unconectedCL):
        for node in unconectedCL:
            # print "////",node
            try:
                if not cmds.lockNode(node, q=1)[0]:
                    print "try deleting", node, cmds.lockNode(node, q=1)[0]
                    if mode in ["delete"]:
                        cmds.delete (node)
                    deletedL.append(node)
            except Exception, err:
                errorL.append(node)
                print "ERROR on {0} : {1}".format(node, err)
    if len(errorL) > 0:
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
    print "unconectedCL=", len(unconectedCL)


    return [toReturnB, debugD]



# Z2k func

def z2k_selAll_asset_Ctr(*args, **kwargs):
    print "z2k_selAll_asset_Ctr()"
    # select all controler of selected asset
    toSel = None
    cursel = cmds.ls(sl=1)
    if len(cursel):
        if ":" in cursel[0]:
            toSel = cursel[0].split(":")[0] + ":set_control"
        else:
            toSel = "set_control"
        cmds.select(toSel)
    return toSel


##### SPINE TWEAK #####
def spineTweak():
    '''
    Tweak toonKit spine
    :return:
    '''

    # Get ikSpline curve
    curv = 'Spine_IK_Init_Crv'

    # Get and stock cv's positions
    cvPosList = list()
    for i in range(0,5):
        cvName = curv + '.cv[%s]'%i
        pos = cmds.xform(cvName, q=True, a=True, translation=True)
        cvPosList.append(pos)

    # Detache skin on curve
    cmds.skinCluster( 'Spine_IK_Init_CrvShape', unbind=True, e=True)

    # Reapply stocked positions
    for i in range(0,5):
        cvName = curv + '.cv[%s]'%i
        pos = cmds.xform(cvName, translation=cvPosList[i])

    # List driver joints
    drivJointList = ['Spine_IK_Start_Ctrl_Def', 'Spine_IK_FK1_Ctrl_Def', 'Spine_IK_FK2_Ctrl_Def', 'Spine_IK_FK3_Ctrl_Def','Spine_IK_End_Ctrl_Def']

    # Select curve and bones
    drivJointList.append(curv)
    cmds.select(drivJointList)

    # Bind skin to curve
    skinCl = cmds.skinCluster(toSelectedBones=True, normalizeWeights=2, skinMethod=0)[0]

    # Set skin weights
    for i in range(0,5):
        cvName = curv + '.cv[%s]'%i
        cmds.select(cvName)

        if i == 0:
            cmds.skinPercent(skinCl, transformValue=[('Spine_IK_Start_Ctrl_Def', 1)], normalize=True)

        elif i == 1:
            cmds.skinPercent(skinCl, transformValue=[('Spine_IK_Start_Ctrl_Def', 1)], normalize=True)

        elif i == 2:
            cmds.skinPercent(skinCl, transformValue=[('Spine_IK_FK1_Ctrl_Def', 1)], normalize=True)

        elif i == 3:
            cmds.skinPercent(skinCl, transformValue=[('Spine_IK_FK2_Ctrl_Def', 1)], normalize=True)

        elif i == 4:
            cmds.skinPercent(skinCl, transformValue=[('Spine_IK_FK3_Ctrl_Def', 1)], normalize=True)

#--------------------- CHECK FUNCTION ------------------------------
def checkBaseStructure(*args, **kwargs):
        """
        Descrition: Check if th Basic hierachy is ok
        Return: [result,debugDict]
        Dependencies: cmds - getOutlinerSets()
        """
        print "checkBaseStructure()"
        tab = "    "
        debugL = []
        debugDetL = []

        debugD = {}
        toReturnB = True

        # check if asset gp and set here

        baseExcludeL = ["persp", "top", "front", "side", "left", "back", "bottom", "defaultCreaseDataSet", "defaultLayer"]
        baseObjL = ["asset", ]
        baseSetL = ["set_meshCache", "set_control", ]
        additionnalSetL = ["set_subdiv_0", "set_subdiv_1", "set_subdiv_2", "set_subdiv_3", "set_subdiv_init"]
        if "baseLayerL" in kwargs.keys():
            baseLayerL = kwargs["baseLayerL"]
        else:
            baseLayerL = ["control", "geometry"]
        extraLayerL = ["instance"]

        if "baseCTRL" in kwargs.keys():
            baseCTRL = kwargs["baseCTRL"]
        else:
            baseCTRL = ["BigDaddy", "BigDaddy_NeutralPose", "Global_SRT", "Local_SRT", "Global_SRT_NeutralPose", "Local_SRT_NeutralPose"]


        AllBaseObj = baseLayerL + baseObjL + baseSetL
        print tab + "AllBaseObj=", AllBaseObj
        topObjL = list(set(cmds.ls(assemblies=True,)) - set(baseExcludeL))
        topSetL = getOutlinerSets()
        layerL = list(set(cmds.ls(type="displayLayer",)) - set(baseExcludeL))

        # ---------- prints --------------
        print tab + "topObjL:", len(topObjL)
        for i in topObjL:
            print tab + "    -", i
        print tab + "topSetL:", len(topSetL)
        for i in topSetL:
            print tab + "    -", i
        print tab + "layerL:", len(layerL)
        for i in layerL:
            print tab + "    -", i

        # ---------------------------------
        # topObjL test
        debugD["topObjL"] = {}
        if not sorted(baseObjL) == sorted(topObjL):
            debugD["topObjL"]["result"] = "PAS CONFORME"
            debugD["topObjL"]["Found"] = topObjL
            toReturnB = False
        else:
            debugD["topObjL"]["result"] = "OK"

        # topSetL test
        debugD["topSetL"] = {}
        debugD["topSetL"]["Found"] = ""
        debugD["topSetL"]["result"] = []
        for i in topSetL:

            if not i in baseSetL and not i in additionnalSetL:
        # if not sorted(baseSetL) == sorted(topSetL):
                debugD["topSetL"]["result"].append(False)
                debugD["topSetL"]["Found"] += " -" + i
                toReturnB = False
            else:
                debugD["topSetL"]["result"].append(True)
        # if 1 flase dans tout les test alors pas bon
        if False in debugD["topSetL"]["result"]:
            debugD["topSetL"]["result"] = "PAS CONFORME"
        else:
            debugD["topSetL"]["result"] = "OK"


       # Layers test
        debugD["layerL"] = {}
        if sorted(baseLayerL) != sorted(layerL) and sorted(baseLayerL + extraLayerL) != sorted(layerL):
            debugD["layerL"]["result"] = "PAS CONFORME"
            debugD["layerL"]["Found"] = layerL
            toReturnB = False
        else:
            debugD["layerL"]["result"] = "OK"


        # baseCTRL test
        debugD["baseCTRL"] = {}
        test = "OK"
        notFoundL = []
        for i in baseCTRL:
            if not cmds.objExists(i):
                toReturnB = False
                test = "PAS CONFORME"
                notFoundL.append(i)

        debugD["baseCTRL"]["result"] = test
        debugD["baseCTRL"]["NOT_Found"] = notFoundL

        print "toReturnB=", toReturnB
        return toReturnB, debugD

def checkAssetStructure(assetgpN="asset", expectedL=["grp_rig", "grp_geo"],
        additionalL=["grp_placeHolders"],extraL=["grp_light"], *args, **kwargs):
        """ Description: check inside the asset_gp
            Return : [result,debugDict]
            Dependencies : cmds - 
        """
        print "checkAssetStructure()"
        extendedL = expectedL[:]
        # switch expeted list depending on the name of the scene
        sceneName = os.path.basename(cmds.file(q=1, l=1)[0])
        if sceneName[:3] in ["set",]:
            print "it's a set"
            extendedL.extend(additionalL)
        if "render" in sceneName.split("_")[3]:
            print "it's a render asset"
            extendedL.extend(additionalL)
        toReturnB = False
        debugD = {}
        tab = "    "
        expect_str = " - ".join(extendedL)
        if cmds.objExists(assetgpN):
            childL = cmds.listRelatives(assetgpN, c=True)
            print tab, expect_str, childL
            debugD[expect_str] = {}
            print "*expectedL:", sorted(expectedL)
            print "*childL   :", sorted(childL)
            print "*extendedL:", sorted(extendedL)
            if ( sorted(expectedL) == sorted(childL) ) or ( sorted(extendedL) == sorted(childL)) or ( sorted(expectedL+extraL) == sorted(childL))  :
                toReturnB = True
                debugD[ expect_str ]["result"] = "OK"
                print tab, toReturnB
            else:
                toReturnB = False
                debugD[expect_str]["result"] = "PAS CONFORME"
                debugD[expect_str]["Found"] = childL
                print tab, toReturnB




        return toReturnB, debugD

def Apply_Delete_setSubdiv (applySetSub=True, toDelete=["set_subdiv_0", "set_subdiv_1", "set_subdiv_2", "set_subdiv_3", "set_subdiv_init"], *args, **kwargs):
    """ Description: apply setSubdiv() if present and delete it
        Return : [BOOL,LIST,INTEGER,FLOAT,DICT,STRING]
        Dependencies : cmds - assetconformation.setSubdiv()
    """
    print "Apply_Delete_setSubdiv()"

    toReturnB = True
    setSub = False
    if applySetSub:
        try:
            assetconformation.setSubdiv(GUI = False)
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

    return [toReturnB, setSub, deletedL]

def checkSRT (inObjL=[], *args, **kwargs):
    # print "checkSRT()"
    tab = "    "
    toReturnB = True
    debugD = {}
    tmpDict = {}

    attribD = {"translateX":0.0, "translateY":0.0, "translateZ":0.0,
                  "rotateX":0.0, "rotateY":0.0, "rotateZ":0.0,
                  "scaleX":1.0, "scaleY":1.0, "scaleZ":1.0,
                }

    for obj in inObjL:
        badassResult = False
        errAttrL = []
        for i, j in attribD.iteritems():
            if not round(cmds.getAttr(obj + "." + i), 3) == round(j, 3):
                # print tab + obj
                # print tab+"    err:",i, round(cmds.getAttr(obj+"."+i),3), "<>",j
                toReturnB = False
                badassResult = True
                errAttrL.append(i)

        if badassResult:
            debugD[obj] = errAttrL


    # print tab,"DONE", toReturnB,debugD

    # print "toReturnB=",toReturnB
    return [toReturnB, debugD]

def isSet_meshCache_OK (theSet="set_meshCache", theType="prop", *args, **kwargs):
        """ Description: check si le contenue du setMeshCache est conforme au type donné
                theType : "set" or "something else / si c'est un "set" il cherche des group
                            only, sinon le reste du tps des mesh only
            Return : BOOL
            Dependencies : cmds - getSetContent
        """
        toReturn = True
        debug = ""
        print "theType=", theType
        setContentL = getSetContent(inSetL=[theSet])
        print "setContentL=", setContentL
        if setContentL:
            if theType not in ["setPreviz", "set"]:
                # cas general on veut seulement des mesh dans le set
                for i in setContentL:
                    sL = cmds.listRelatives(i, s=1, ni=1)
                    if  sL:
                        if not cmds.objectType(i) in ["transform"] and not len(sL) > 0 :
                            toReturn = False
                            debug = "certain object ne sont pas des MESH"
                    else:
                        toReturn = False
                        debug = "certain object ne sont pas des MESH"

            else:
                print "set"
                # is a set donc on doit avoir seulement des group pour le moement
                for i in setContentL:
                    sL = cmds.listRelatives(i, s=1, ni=1)
                    # print "sL=", sL,cmds.objectType(i)
                    if  sL or not cmds.objectType(i) in ["transform"] :
                        toReturn = False
                        debug = "certain object ne sont pas des Groups"

        else:
            toReturn = False
            debug = "le set est vide"


        return [toReturn, debug]

def isKeyed (inObj, *args, **kwargs):
        """ Description: Check if the given object'keyable attrib are effictively keyed
            Return : [BOOL,DebugList]
            Dependencies : cmds - isConnected() -
        """

        toReturnB = False
        debugD = {}
        if len(inObj) > 0:
            if cmds.objExists(inObj):
                conL = cmds.listConnections(inObj)
                # print "conL=", conL
                if conL:
                    if len(conL) > 0 :
                        # print"lengthed"
                        attrL = cmds.listAttr(inObj, k=True)
                        if attrL:
                            if len(attrL) > 0:
                                for attr in attrL:
                                    attrN = inObj + "." + attr
                                    if cmds.connectionInfo(attrN, isDestination=True):
                                        conL = cmds.listConnections(attrN, s=True, d=0,t="animCurve")
                                        # print "conL=", conL
                                        debugD[attrN] = conL
                                        toReturnB = True


        return [toReturnB, debugD]

def isConnected (node="", exceptionL=["nodeGraphEditorInfo", "defaultRenderUtilityList", "objectSet"], *args, **kwargs):
        toReturnB = True
        conL = []

        # print "///",node
        if cmds.listConnections(node):
            for i in cmds.listConnections(node):
                # print "    " +node + " <-> "+ i
                if not i in [node]:
                    if cmds.objectType(i) not in exceptionL:
                        conL.append(i)

            if len (conL) == 0:
                toReturnB = False
        else:
            toReturnB = False

        return [toReturnB, conL]

def isSkinned(inObjL=[], verbose=False, printOut=False, *args, **kwargs):
        ''' Description : Get the list of the SlinClusters of the selected mesh
                Return : [resultBool,outSkinClusterL,noSkinL]
                Dependencies : cmds - 
        '''
        toReturnB = False
        outSkinClusterL = []
        outSkinnedObj = []
        tab = "    "
        if len(inObjL):
            for obj in inObjL:
                # print "  obj =", obj
                skinClusterList = []
                history = cmds.listHistory(obj, il=2)
                # print "    history = ", history
                if history not in [None, "None"]:
                    for node in history:
                        # print "   node=",node
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

        print tab, "SkinCluster/obj = {0} / {1}".format(len(outSkinClusterL), len(inObjL))


        return [toReturnB, outSkinClusterL, noSkinL]

def isHiddenObjInSet(theSet="set_meshCache", *args, **kwargs):
    """ Description: Check s'il y a des obj hidden dans le set
        Return : [BOOL,LIST,INTEGER,FLOAT,DICT,STRING]
        Dependencies : cmds - 
    """
    print "isHiddenObjInSet()"
    toReturnB = True
    debugL = []
    vL = []
    setContentL = getSetContent(inSetL=[theSet])
    for i in setContentL:
        v = cmds.getAttr(i + "." + "v")
        if not v:
            debugL.append(i)
            vL.append(v)
    if len(debugL):
        toReturnB = False

    return toReturnB, debugL

# ------------------------ cleaning Function -----------------
# object cleaning
def resetSRT(inObjL=[], *args, **kwargs):
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
            except Exception, err:
                toReturnB = False
                debugL.append(err)


    debugD["errors"] = debugL
    debugD["resetedL"] = resetedL


    # print tab,"DONE",toReturnB
    return [toReturnB, debugD]

def resetCTR(inObjL=[], userDefined=True, SRT=True, *args, **kwargs):
    """ Description: remet les valeur SRT a (1,1,1) (0,0,0) (0,0,0) et user defined attr to default
        Return : [toReturnB,debugD]
        Dependencies : cmds - checkSRT()
    """
    print "resetCTR()"

    tab = "    "
    cursel = inObjL
    debugD = {}
    debugL = []
    resetedL = []
    toReturnB = True

    for i in cursel:
        # print i
        if SRT:
            # if  not checkSRT([i])[0]:
            # print "    reseting",i
            try:
                cmds.xform(i, ro=(0, 0, 0), t=(0, 0, 0), s=(1, 1, 1))
                resetedL.append(i)
            except Exception, err:
                toReturnB = False
                debugL.append(err)
        if userDefined:
            udAttrL = cmds.listAttr(i, ud=1, k=1)
            if udAttrL:
                for attr in udAttrL:
                    try:
                        dv = cmds.addAttr(i + "." + attr, q=True, defaultValue=True)
                        if not dv in [None] and cmds.getAttr(i + "." + attr, settable=1):
                            cmds.setAttr(i + "." + attr, dv)
                        else:
                            # cmds.setAttr(i+"."+attr,0)
                            print "No default value"
                    except Exception, err:
                        toReturnB = False
                        debugL.append(err)


    debugD["errors"] = debugL
    debugD["resetedL"] = resetedL


    # print tab,"DONE",toReturnB
    return [toReturnB, debugD]


def checkKeys(inObjL=[], *args, **kwargs):
    """ Description: check if there is some keys on keyables of inObjL
        Return : [BOOL,LIST,INTEGER,FLOAT,DICT,STRING]
        Dependencies : cmds - isKeyed()
    """
    toReturnB = True
    debugD = {}
    for obj in inObjL:
        test, debugL = isKeyed(inObj=obj)
        # print "    *",test,debugL
        if test:
            toReturnB = False
            debugD[obj] = debugL

    # print "##",debugD
    return [toReturnB, debugD]

def cleanKeys(inObjL=[], *args, **kwargs):
    """ Description: delete all animation on inObj
        Return : [toReturnB,cleanedL,debugD]
        Dependencies : cmds - checkKeys()
    """
    print "cleanKeys()"
    toReturnB = True
    debugD = []
    cleanedL = []
    print "inObjL=", inObjL
    oktest, debugD = checkKeys(inObjL=inObjL,)
    print "cleanKeys(2)"
    if not oktest:
        for obj, j in debugD.iteritems():
            for toDeleteL in j.values():
                try:
                    cmds.delete(toDeleteL)
                    cleanedL.append(toDeleteL)
                except Exception, err:
                    toReturnB = False
                    debugD[obj] = err
                    print "ERROR:", obj, err

    return [toReturnB, cleanedL, debugD]

def cleanUnusedInfluence(inObjL="", *args, **kwargs):
    """ Description: Delete unused influance on given inObjL . Return Flase if some obj doesn't have a skinClust
        Return : [BOOL, totalSkinClusterL, deletedDict{skinCluster:DeletedInfluenceL}]
        Dependencies : cmds - isSkinned() - 
    """
    print "cleanUnusedInfluance()"

    # to convert to real python code with cmds.skinCluster(theSkincluster, removeUnusedInfluence=True)
    tab = "    "
    toReturnB = True
    deletedDict = {}
    outCount = 0
    totalSkinClusterL = []
    if len(inObjL) > 0:
        for obj in inObjL:
            skinned, skinClusterL, noSkinL = isSkinned(inObjL=[obj])
            totalSkinClusterL.extend(skinClusterL)
            # print tab,obj,skinned,skinClusterL,noSkinL
            if skinned in [True, 1]:
                for skinCluster in (skinClusterL):
                    # print tab,skinCluster

                    # get def list all and the unsused w
                    defL = cmds.skinCluster(skinCluster, q=1, inf=True)
                    wDefL = cmds.skinCluster(skinCluster, q=1, wi=True)
                    toDeleteL = list(set(defL) - set(wDefL))
                    # print tab,"toDeleteL=", toDeleteL

                    # turn of the skinNode for faster exec
                    baseSkinNState = cmds.getAttr (skinCluster + ".nodeState")
                    cmds.setAttr (skinCluster + ".nodeState", 1)

                    # removing loop
                    if len(toDeleteL) > 0:
                        for i in toDeleteL:
                            # print tab,"**",skinCluster,i
                            try:
                                u = cmds.skinCluster(skinCluster, e=True, ri=i,)
                            except Exception, err:
                                print err
                                toReturnB = False

                        outCount += 1
                        deletedDict[skinCluster] = toDeleteL
                        # print outCount,len(deletedDict)
                    # turn on skinNode
                    cmds.setAttr (skinCluster + ".nodeState", 0)


    return [toReturnB, totalSkinClusterL, deletedDict]

def setSmoothness(inObjL=[], mode=0, *args, **kwargs):
    print "setSmoothness()"
    tab = "    "
    toReturnB = True
    debugD = {}
    # handle the display of mesh in viewport
    if type(inObjL) is not list:
        inObjL = list(inObjL)
    for obj in inObjL:
        # print tab,obj
        try :
            shapeL = cmds.listRelatives(obj, s=1, ni=1, f=1)
            if shapeL:
                for shape in shapeL:
                    print "    ", shape
                    # connect the attr if not connected
                    if not cmds.connectionInfo(shape + "." + "smoothLevel", isDestination=True):
                        cmds.displaySmoothness(obj, polygonObject=mode)
        except Exception, err:
            toReturnB = False
            debugD[obj] = err

    print tab, "DONE", toReturnB, debugD



    return [toReturnB, debugD]

def disableShapeOverrides(inObjL=[], *args, **kwargs):
    # desactivate Overide des geometry contenu dans le set "set_meshCache"
    print "disableShapeOverrides()"
    tab = "   "
    toReturnB = True
    debugD = {}
    attrL = ["overrideEnabled", "overrideDisplayType"]
    for obj in inObjL:
        for attr in attrL:
            try:
                cmds.setAttr (cmds.listRelatives(obj, c=True, ni=True, type="shape", fullPath=True)[0] + "." + attr, 0)
            except Exception, err:
                toReturnB = False
                debugD[obj] = attr
                # print Exception,err
    print tab, "DONE", toReturnB



    return [toReturnB, debugD]




def connectVisibility(connectOnShape=True, force=True, driverObj="Global_SRT", driverAttr="showMesh", *args, **kwargs):
    """ Description: cree et connect un attrib "showMesh" au visibility des shape du "set_meshCache"
        Return : True
        Dependencies : cmds - addAttr() - getSetContent() - getChilds()
    """
    print "connectVisibility()"
    toReturnB = True
    debug = ""
    try :
        # driverObj= "Global_SRT"
        # driverAttr= "showMesh"
        addAttr(inObj=driverObj, theAttrName=driverAttr, dv=1,)
        cmds.setAttr(driverObj + "." + driverAttr, 1)
        targetObjL = getSetContent(inSetL=["set_meshCache"])

        finalTargetObjL = []
        if len(targetObjL):
            for obj in targetObjL:

                # get shpae obj
                if connectOnShape:
                    finalTargetObjL = getChilds(cursel=[obj], mode="shape",)
                    print "finalTargetObjL=", finalTargetObjL
                else:
                    finalTargetObjL = targetObjL
                # finally connect
                for target in finalTargetObjL:
                    if not cmds.connectionInfo(target + "." + "visibility", isDestination=True):
                        cmds.connectAttr(driverObj + "." + driverAttr, target + "." + "visibility", f=force)
                    else:
                        print "Attribute allready Connected"
    except Exception, err:
        toReturnB = False
        print obj, Exception, err
        debug = err

    return toReturnB, debug

# scene cleaning
def cleanMentalRayNodes (toDeleteL=['mentalrayGlobals', 'mentalrayItemsList', 'miDefaultFramebuffer', 'miDefaultOptions',
    'Draft', 'DraftMotionBlur', 'DraftRapidMotion', 'Preview', 'PreviewCaustics', 'PreviewFinalGather', 'PreviewGlobalIllum',
    'PreviewImrRayTracyOff', 'PreviewImrRayTracyOn', 'PreviewMotionblur', 'PreviewRapidMotion', 'Production', 'ProductionFineTrace',
    'ProductionMotionblur', 'ProductionRapidFur', 'ProductionRapidHair', 'ProductionRapidMotion',
    ],
    *args, **kwargs):
    """ Description: Delete all mentalrayNodes in toDeleteL
        Return : [toReturnB,toDeleteL,deletedL,failL]
        Dependencies : cmds - 
    """

    print "cleanMentalRayNodes()"
    tab = "    "
    toReturnB = True
    deletedL = []
    failL = []
    print tab, "toDeleteL=", toDeleteL

    for i in toDeleteL:
        if cmds.objExists(i):
            try:
                cmds.lockNode(i, lock=False)
                cmds.delete(i)
                deletedL.append(i)
            except:
                toReturnB = False
                failL.append(i)


    return [toReturnB, toDeleteL, deletedL, failL]

def cleanTurtleNodes (toDeleteL=["TurtleDefaultBakeLayer"], check=False, *args, **kwargs):
    """ Description: Delete all turtle in toDeleteL
        Return : [toReturnB,toDeleteL,deletedL,failL]
        Dependencies : cmds - 
    """

    print "cleanMentalRayNodes()"
    tab = "    "
    toReturnB = True
    deletedL = []
    failL = []
    print tab, "toDeleteL=", toDeleteL

    for i in toDeleteL:
        if cmds.objExists(i):
            try:
                cmds.lockNode(i, lock=False)
                if not check:
                    cmds.delete(i)
                deletedL.append(i)
            except:
                toReturnB = False
                failL.append(i)


    return [toReturnB, toDeleteL, deletedL, failL]


def cleanRefNodes(toDeleteL=["UNKNOWN_REF_NODE", "SHAREDREFERENCENODE", "REFERENCE"], testMode=False, *args, **kwargs):
        print "cleanRefNodes()"
        tab = "    "
        toReturnB = False
        objtoDeleteL = []
        deletedL = []
        print tab, "toDeleteL=", toDeleteL
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
                        print tab, "DELETED:", ref
                        deletedL.append(curToDelType)
                    except Exception, e:
                            print tab, "%s" % e

        if len(objtoDeleteL) == len(deletedL):
            toReturnB = True
        else:
            toReturnB = False

        return [toReturnB, objtoDeleteL, deletedL]


def check_NS (NS_exclusion=[], *args, **kwargs):
    toReturnB = True
    # "UI","shared" NS are used by maya itself
    NS_exclusionBL = ["UI", "shared"]
    badNSL = []
    nsL = cmds.namespaceInfo(listOnlyNamespaces=True)
    NS_exclusionBL.extend(NS_exclusion)
    if len(nsL):
        for i in nsL:
            if i not in NS_exclusionBL:
                toReturnB = False
                badNSL.append(i)
    return [toReturnB, badNSL]

def remove_All_NS (NSexclusionL=[""], limit=100, *args, **kwargs):
        """ Description: Delete all NameSpace appart the ones in the NSexclusionL
            Return : nothing
            Dependencies : cmds - 
        """
        tab = "    "
        print "remove_All_NS()"
        toReturnB = True
        # "UI","shared" NS are used by maya itself
        NS_exclusionBL = ["UI", "shared"]
        NS_exclusionBL.extend(NSexclusionL)
        # set the current nameSpace to the root nameSpace
        cmds.namespace(setNamespace=":")
        # get NS list
        nsL = cmds.namespaceInfo(listOnlyNamespaces=True)# list content of a namespace


        for loop in range(len(nsL) + 2):
            nsL = cmds.namespaceInfo(listOnlyNamespaces=True)
            for ns in nsL:
                if ns not in NS_exclusionBL:
                    print tab + "ns:", ns
                    cmds.namespace(removeNamespace=ns, mergeNamespaceWithRoot=True)

        # recursive
        count = 0
        nsLFin = cmds.namespaceInfo(listOnlyNamespaces=True)
        while len(nsLFin) > 2:
            remove_All_NS(NSexclusionL=NSexclusionL)
            count += 1
            if count > limit:
                break

        return [toReturnB]


# WIIIIP APPEND THE SPECIAL CASE OF SET AND DO NOTHING in the check script
def cleanDisplayLayerWithSet (tableD={"set_meshCache":["geometry", 2, 0], "set_control":["control", 0, 0] }, preDelAll=True, *arg, **kwargs):
    """ Description: Clean the display Layers by rebuilding it with the content of the corresponding sets 
                        setL <-> layerL
        Return : [BOOL,LIST,INTEGER,FLOAT,DICT,STRING]
        Dependencies : cmds - createDisplayLayer() - delete_displayLayer()
    """

    tab = "    "
    toReturnB = True
    debugL = []

    # pre deleting all layers if rebuild is possible
    if preDelAll:
        oktest = True
        for theSet, paramL in tableD.iteritems():
            if not cmds.objExists(theSet):
                oktest = False
        if oktest:
            delete_displayLayer()

    # rebuild with given sets
    for theSet, paramL in tableD.iteritems():
        if cmds.objExists(theSet):
            inObjL = cmds.listConnections(theSet + ".dagSetMembers", source=1, d=0)
            if inObjL:
                createDisplayLayer (n=paramL[0], inObjL=inObjL, displayType=paramL[1], hideOnPlayback=paramL[2])
                debugL.append(theSet + " :DONE")
            else:
                toReturnB = False
                debugL.append(theSet + " :EMPTY")
        else:
            toReturnB = False
            debugL.append(theSet + " :DOESN'T EXISTS")

    return [toReturnB, debugL]


def cleanUnusedConstraint(*args, **kwargs):
    """ Description: Delete All Un-connected Constraint
        Return : BOOL,debugD
        Dependencies : cmds - UnusedNodeAnalyse()
    """
    print "cleanUnusedConstraint()"

    toReturnB, debugD = UnusedNodeAnalyse(execptionTL=[], specificTL=["constraint", ], mode="delete")
    # print "**debugD=", debugD
    return [toReturnB, debugD]

def cleanUnUsedAnimCurves(*args, **kwargs):
    """ Description: Delete All Un-connected Anim_Curves
        Return : BOOL,debugD
        Dependencies : cmds - UnusedNodeAnalyse()
    """
    print "cleanUnUsedAnimCurves()"

    toReturnB, debugD = UnusedNodeAnalyse(execptionTL=[], specificTL=["animCurve"], mode="delete")

    return [toReturnB, debugD]

def CleanDisconnectedNodes(*args, **kwargs):
    """ Description: Delete All Un-connected non dag Nodes
        Return : BOOL,debugD
        Dependencies : cmds - UnusedNodeAnalyse()
    """
    print "CleanDisconnectedNodes()"

    toReturnB, debugD = UnusedNodeAnalyse(execptionTL=['containerBase', 'entity', "dagNode", "defaultRenderUtilityList", "partition", "constraint", "animCurve", ], specificTL=[], mode="delete")

    return [toReturnB, debugD]



def deleteActiveBlendShape_grp(*args, **kwargs):
    print "deleteActiveBlendShape_grp()"
    # old not in use
    toReturnB = False
    try:
        cmds.delete("grp_activeBS")
        toReturnB = True
    except Exception, err:
       print err

    gp = "imported_gp"
    gpb = "BS_ACTIVES_grp"
    if cmds.objExists(gp) == True and cmds.objExists(gpb) == True:
        if cmds.listRelatives(gp, c=1, type="transform")[0] in [gpb]:
            print"a"
            try:
                cmds.delete(gp)
            except Exception, err:
                print err
    return True

def get_BS_TargetObjD(BS_Node="", *args, **kwargs):
    # construction correspondance dictionnary {ObjName:corresponding BS index}

    connectedL = cmds.listConnections(BS_Node, d=1,s=0, t="mesh", skipConversionNodes=1, p=1)
    # print connectedL
    outDict = {}
    if connectedL:
        for i in connectedL:
            if "worldMesh" in i:
                conL = cmds.listConnections(i,d=0, s=1, p=1)
                for j in conL:
                    if BS_Node in j:
                        index = j.split("inputTargetGroup[", 1)[-1].split("]", 1)[0]
                        tObj = cmds.listRelatives(i.split(".", 1)[0], p=1)[0]
                        outDict[str(index)] = tObj
    return outDict



def getTypeInHierarchy(cursel=[], theType="mesh", *args, **kwargs):
    listOut = []
    cursel = Ltest(cursel)
    if not len(cursel) > 0 :
        cursel = cmds.ls(os=True, flatten=True, allPaths=True)
    # select mesh in hierarchy
    if theType in ["mesh"]:
        cursel = cmds.listRelatives(cursel, allDescendents=True, path=True)
        listOut = [a for a in cursel if cmds.listRelatives(a, c=1, type=theType, path=True)]
    else:
        listOut = cmds.listRelatives(cursel, allDescendents=True, path=True, type=theType,)


    return listOut


def chr_delete_BS_active_group (*args, **kwargs):
    # delete le group " BS_ACTIVES_grp"
    debugL = []
    for i in ["BS_ACTIVES_grp","imported_gp"]:
        try:
            cmds.delete (i)

        except Exception, err:
            print err
            debugL.append("    -nothing to delete")
    return True, debugL
#---------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------
# apply special settings CHR / fixe TK rigs
#---------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------


def chr_fixTKFacialRig_EyeBrow_Middle (*args, **kwargs):
    """ Description: Fix le rig facial en ajoutant un blend param sur le ctr "EyeBrow_Middle"
                    Adouci son comportement de following des eyeBrows
        Return : [BOOL,DebugList]
        Dependencies : cmds - 
    """
    print "fixTKFacialRig_EyeBrow_Middle()"
    objA = "Head_FK"
    objB = "TK_EyeBrow_switcher_Child"
    theCTR = "EyeBrow_Middle"
    attrN = "Attenuation"
    attMaxV = 100
    attrMinV = 0
    attrDefaultV = 1.5
    attrType = "double"
    cstAttrTarget = ""
    canDo = True
    toReturnB = True # finally the result is allways True
    debugL = []
    # constraining
    for obj in [objA, objB, theCTR]:
        if not cmds.objExists(obj):
            canDo = False

    if canDo:
        try:
            # apply constraint
            theCst = cmds.parentConstraint(objA, objB, mo=True, w=1)[0]
            print "theCst=", theCst

            #get the connection port
            cstAttrL = cmds.listAttr(theCst, ud=1)
            print cstAttrL
            for i in cstAttrL:
                if objA in i:
                    print i
                    cstAttrTarget = i

            # addThe Attr
            cmds.addAttr(theCTR, longName=attrN, attributeType=attrType, min=attrMinV, dv=attrDefaultV, max=attMaxV,
                                                    keyable=True,)

            # connect the Attr
            cmds.connectAttr(theCTR + "." + attrN, theCst + "." + cstAttrTarget, f=1)

            # result handling
            toReturnB = True
        except:
            info = "FixRig Allready Applyed"
            print "info=", info
            debugL.append(info)
    else:
        info = "the needed objects are not present in the scene"
        print "info=", info
        debugL.append(info)

    return toReturnB, debugL

def chr_UnlockForgottenSRT():
    """ Description: Unlock the forgotten srt lock on ToonKit rig, only if all Objects of the list exists in the scene and some lock also!
        Return : [BOOL,LIST]
        Dependencies : cmds - 
    """

    faceL = ['Right_LowerEye_2_Ctrl', 'Noze_Main_Ctrl', 'Right_LowerEye_0_Ctrl', 'Left_LowerEye_1_Ctrl', 'Left_EyeBrow_in_1', 'Right_Eye', 'Left_nostril', 
    'Right_Eyelid_In', 'Left_Brow_ridge_out', 'Left_EyeBrow_out', 'Right_EyeBrow_out_1', 'Left_EyeBrow_Global', 'Left_LowerEye_0_Ctrl', 
    'Left_Brow_ridge_out_1', 'Right_UpperEye_1_Ctrl', 'Right_LowerEye_1_Ctrl', 'Left_UpperEye_2_Ctrl', 'Left_LowerLid_Main_Ctrl', 'Left_Eye', 
    'Left_Cheek', 'Left_EyeBrow_in', 'Left_CheekBone', 'EyeBrow_Middle', 'Right_nostril', 'Right_Brow_ridge_out_1', 'Left_EyeBrow_out_1', 
    'Left_Brow_ridge_in', 'Right_LowerEye_3_Ctrl', 'Right_UpperEye_0_Ctrl', 'Right_EyeBrow_Global', 'Right_EyeBrow_out', 'Left_LowerEye_3_Ctrl', 
    'Right_Brow_ridge_in', 'Right_CheekBone', 'Right_Cheek', 'Left_UpperEye_1_Ctrl', 'Right_Brow_ridge_in_1', 'Right_Ear_Bone_Ctrl', 
    'Right_UpperEye_3_Ctrl', 'Left_Eyelid_Out', 'Right_EyeBrow_in', 'Left_UpperLid_Main_Ctrl', 'Left_UpperEye_0_Ctrl', 'Left_LowerEye_2_Ctrl', 
    'Right_EyeBrow_in_1', 'Left_Eye_Bulge', 'Left_Eyelid_In', 'Right_Brow_ridge_out', 'Right_UpperLid_Main_Ctrl', 'Left_UpperEye_3_Ctrl', 
    'Left_Brow_ridge_in_1', 'Left_Ear_Bone_Ctrl', 'Right_Eyelid_Out', 'Right_LowerLid_Main_Ctrl', 'Right_UpperEye_2_Ctrl', 'Right_Base_Depressor1', 
    'Right_Bottom_Teeth', 'Right_UpperLip_1_Ctrl', 'Left_Tongue_2', 'Left_Tongue_3', 'Left_Tongue_1', 'Right_LowerLip_1_Ctrl', 'Top_Teeth', 'Tongue_1', 
    'Tongue_0', 'Tongue_3', 'Tongue_2', 'Base_UpperLip_Main_Ctrl', 'LowerLip_Center', 'Right_Base_Depressor', 'Right_LowerLip_2_Ctrl', 'Left_Base_Levator1', 
    'Left_Base_Depressor', 'Jaw_Bone_Ctrl', 'Left_UpperLip_2_Ctrl', 'Right_Base_Levator1', 'Right_Base_Levator', 'Right_UpperLip_2_Ctrl', 'Top_Teeth_Global', 
    'Base_Depressor', 'Left_Base_Depressor1', 'Left_Base_Levator', 'Left_Bottom_Teeth', 'Left_Top_Teeth', 'Right_Tongue_2', 'Right_Tongue_3', 'Bottom_Teeth', 
    'Right_Tongue_1', 'Left_LowerLip_1_Ctrl', 'Right_Top_Teeth', 'Bottom_Teeth_Global', 'UpperLip_Center', 'Left_UpperLip_1_Ctrl', 'Left_LowerLip_2_Ctrl', 
    'chin']
    bodyFunkyL = ['Left_Leg_Extra_0', 'Left_Leg_Extra_1', 'Left_Leg_Extra_2', 'Left_Leg_Extra_3', 'Left_Leg_Extra_4', 'Left_Leg_Extra_5', 'Left_Leg_Extra_6', 
    'Spine_IK_Extra_6_Ctrl', 'Spine_IK_Extra_5_Ctrl', 'Spine_IK_Extra_4_Ctrl', 'Spine_IK_Extra_3_Ctrl', 'Spine_IK_Extra_2_Ctrl', 'Left_Arm_Extra_0', 
    'Left_Arm_Extra_1', 'Left_Arm_Extra_2', 'Left_Arm_Extra_3', 'Left_Arm_Extra_4', 'Left_Arm_Extra_5', 'Left_Arm_Extra_6', 'Right_Arm_Extra_0', 
    'Right_Arm_Extra_1', 'Right_Arm_Extra_2', 'Right_Arm_Extra_3', 'Right_Arm_Extra_4', 'Right_Arm_Extra_5', 'Right_Arm_Extra_6', 'Right_Leg_Extra_0', 
    'Right_Leg_Extra_1', 'Right_Leg_Extra_2', 'Right_Leg_Extra_3', 'Right_Leg_Extra_4', 'Right_Leg_Extra_5', 'Right_Leg_Extra_6', 'Spine_IK_Extra_1_Ctrl']
    toLockL = ["Head_FK"]
    scLockL = faceL + bodyFunkyL
    canDo = True
    updatedL = []
    attrL = ["sx", "sy", "sz"]
    for obj in scLockL:
        if not cmds.objExists(obj):
            canDo = False
            print "BOOOM"
    if canDo:
        print "scene valid for scalingFreeman()"

        for i in sorted(scLockL):
            for attr in attrL:
                lockState = cmds.getAttr(i + "." + attr, l=1)
                if lockState:
                    print i.ljust(40), attr, lockState
                    cmds.setAttr(i + "." + attr, l=0, k=1)
                    updatedL.append(i + "." + attr)

    # add some locks finally
    for obj in toLockL:
        if cmds.objExists(obj):
            for attr in attrL:
                cmds.setAttr(obj + "." + attr, l=1, k=0)
    print "total updated=", len(updatedL)

    return True, updatedL

def set_grp_geo_SmoothLevel(*args, **kwargs):
    """ Description: Set les attr de smoothness des anim_REF à leur valeurs smother pour pouvoir utiliser les raccouci clavier
                     de smooth display
        Return : [BOOL]
        Dependencies : cmds - 
    """
    debugL = []
    canDo = True
    for i in ["grp_geo.smoothLevel1", "grp_geo.smoothLevel2"]:
        if not cmds.objExists(i):
            canDo = False
    if canDo:
        try:
            cmds.setAttr ("grp_geo.smoothLevel1", 1)
            cmds.setAttr ("grp_geo.smoothLevel2", 2)
            cmds.displaySmoothness("set_meshCache", polygonObject=0)
        except:
            pass
    return [True, debugL]

def chr_clean_set_control_bad_members(*args, **kwargs):
    print "chr_clean_set_control_bad_members()"
    canDo = True
    debugL= []
    toRemL = ['Left_FOOT_IK_2_Ref_Bone_Ctrl', 'Left_FOOT_IK_2_Ref_EffScl', 'Right_FOOT_IK_2_Ref_Bone_Ctrl',  'Right_FOOT_IK_2_Ref_EffScl']
    for i in toRemL:
        if not cmds.objExists(i):
            canDo = False
    if canDo:
        for i in toRemL:
            try:
                if cmds.sets(i,im="set_control"):
                    cmds.sets(i, rm="set_control")
                    debugL.append(i)
            except Exception,err:
                print "   ",err
    return [True,debugL]

def chr_rename_Teeth_BS_attribs(*args, **kwargs):
    # reset all attr of selected controls
    print "chr_rename_Teeth_BS_attribs()"
    debugL = []
    toRenameUpL = ["Top_Teeth_Global.upperteeth_gum", "Top_Teeth_Global.upperteeth_high", "Top_Teeth_Global.upperteeth_round", "Top_Teeth_Global.uppertteeth_assymetry", "Top_Teeth_Global.upperteeth_squeez"]
    toRenameDnL = ["Bottom_Teeth_Global.lowerteeth_gum", "Bottom_Teeth_Global.lowerteeth_high", "Bottom_Teeth_Global.lowerteeth_round", "Bottom_Teeth_Global.lowerteeth_assymetry", "Bottom_Teeth_Global.lowerteeth_squeez", ]
    allRL = toRenameUpL + toRenameDnL
    print allRL
    canDo = True
    for i in allRL:
        if not cmds.objExists(i):
            canDo = False
    if canDo:
        # reorder attr a l arrache qui foiraient de TK
        if cmds.objExists("Bottom_Teeth_Global.lowerteeth_assymetry"):
            cmds.deleteAttr("Bottom_Teeth_Global.lowerteeth_assymetry")
            cmds.undo()

        for j in allRL:
            if  cmds.objExists(j):
                print "renaming", j
                newName = j.replace("uppertteeth", "upperteeth").replace("lowertteeth","lowerteeth").replace("lower", "").replace("upper", "")
                print j,"->", newName
                cmds.renameAttr(j , newName.rsplit(".")[-1])
                debugL.append("{0} has been renamed".format(j))

    return True, debugL

def chr_rename_Teeth_BS_attribs_Vampires(*args, **kwargs):
    # reset all attr of selected controls
    print "chr_rename_Teeth_BS_attribs_Vampires()"
    debugL = []
    toRenameUpL = [
                'Top_Teeth_Global.upperteeth_canines',
                'Top_Teeth_Global.upperteeth_gencivedown',
                'Top_Teeth_Global.upperteeth_gum',# doesn't exists in lower part
                'Top_Teeth_Global.upperteeth_high',
                'Top_Teeth_Global.upperteeth_pointues_100',
                'Top_Teeth_Global.upperteeth_pointues_50',
                'Top_Teeth_Global.upperteeth_pointues_75',
                'Top_Teeth_Global.upperteeth_pointues_avant',
                'Top_Teeth_Global.upperteeth_round',
                'Top_Teeth_Global.upperteeth_squeez',
                ]
    toRenameDnL = [
                'Bottom_Teeth_Global.lowerteeth_basique',
                'Bottom_Teeth_Global.lowerteeth_canines',
                'Bottom_Teeth_Global.lowerteeth_genciveUp',
                'Bottom_Teeth_Global.lowerteeth_pointu_100',
                'Bottom_Teeth_Global.lowerteeth_pointu_50',
                'Bottom_Teeth_Global.lowerteeth_pointu_75',
                'Bottom_Teeth_Global.lowerteeth_pointues_avant',
                'Bottom_Teeth_Global.lowertteeth_high',
                'Bottom_Teeth_Global.lowertteeth_round',
                'Bottom_Teeth_Global.lowertteeth_squeez',
                ]
    allRL = toRenameUpL + toRenameDnL
    # allRL= ["Bottom_Teeth_Global.lowerteeth_canines"]
    print allRL
    canDo = True
    for i in allRL:
        if not cmds.objExists(i):
            canDo = False
    print "canDo=", canDo
    if canDo:
        # reorder attr a l arrache qui foiraient de TK
        # if cmds.objExists("Bottom_Teeth_Global.lowerteeth_assymetry"):
        #     cmds.deleteAttr("Bottom_Teeth_Global.lowerteeth_assymetry")
        #     cmds.undo()

        for j in allRL:
            if  cmds.objExists(j):
                print "renaming", j
                newName = j.replace("uppertteeth", "upperteeth").replace("lowertteeth","lowerteeth").replace("lower", "").replace("upper", "")
                print j,"->", newName
                newName= newName.replace("teeth_gencivedown","teeth_gum_Up_Dn").replace("teeth_genciveUp","teeth_gum_Up_Dn")
                cmds.renameAttr(j , newName.rsplit(".")[-1])
                debugL.append("{0} has been renamed".format(j))

    return True, debugL

def chr_TongueFix(*args, **kwargs):
    print "chr_TongueFix()"
    # WIP
    # fix le rig de la langue en supprimant toute les contraintes et en refaisant la hierarchy avec des parentages + add bridge
    # et refait la contrainte pour lier au reste proprement, afin d'enlever les problemes de scale.
    debugL = []
    bridgeName = "Tongue_Bridge"
    canDo = True
    ctrL = ['Tongue_0', 'Tongue_1', 'Tongue_2', 'Right_Tongue_3', 'Tongue_3']
    for i in ctrL:
        if not cmds.objExists(i):
            canDo = False
    if canDo:
        if not cmds.objExists(bridgeName):
            allCstL = getTypeInHierarchy(cursel=["TK_Tongue_System"], theType="constraint")
            print len(allCstL), allCstL

            # delete cst
            for cst in allCstL:
                print "cst=", cst

                if not "Tongue_0_Root" in cst:
                    if cmds.objExists(cst):


                        if "_prCns" in cst:
                            # get cst conn
                            theParent = cmds.listConnections(cst + '.target[0].targetParentMatrix', d=False, s=True)[0]
                            theChild = cmds.listConnections(cst + '.constraintTranslate.constraintTranslateX', d=True, s=False)[0]
                            print theChild, "c->p", theParent

                            # re parent has it has to be
                            cmds.parent (theChild, theParent)
            # delete cst
            for i in allCstL:
                cmds.delete(i)


            # create bridge group parent it in the hierarchy and cst
            print "BRIDGING:"
            bridgeGp = cmds.group(name=bridgeName, world=1, em=1)
            cmds.parent (bridgeGp, "TK_Tongue_System")
            # matchByXformMatrix(cursel=["Jaw_Bone_Ctrl",bridgeGp], mode=0)
            cmds.parentConstraint("Jaw_Bone_Ctrl", bridgeGp, mo=0)
            cmds.scaleConstraint("Jaw_Bone_Ctrl", bridgeGp,)
            cmds.parent ("TK_Tongue_0_Root", bridgeGp)


            debugL.append("Rig_replaced, all cst deleted")
        else:
            debugL.append("Nothing Done")

    return True, debugL

def chr_CstScaleandOptimFix(bridgeName="Dn_Teeth_Bridge", RootPrefixeToCut="TK_", rootL=[], *args, **kwargs):
    print "chr_CstScaleandOptimFix()"
    """ Description: fix le rig des Teeth up down, nozex3,earsx2,chin, et assimilé en supprimant toute les contraintes et en refaisant la hierarchy avec des parentages + add bridge
                      et refait la contrainte pour lier au reste proprement, afin d'enlever les problemes de scale.
    
        Return : [BOOL,LIST]
        Dependencies : cmds - getTypeInHierarchy()
    """
    print "chr_CstScaleandOptimFix()"

    canDo = True

    debugL = [bridgeName.split("_Bridge", 1)[0] + ":"]
    for k in rootL:
        if not cmds.objExists(k):
            canDo = False


    if canDo:

        theRootCstParent = ""

        if not cmds.objExists(bridgeName):
            theRootFilter = rootL[0].replace(RootPrefixeToCut, "")
            allCstL = getTypeInHierarchy(cursel=rootL, theType="constraint")
            print len(allCstL), allCstL

            # delete cst
            for cst in allCstL:
                print "cst=", cst

                print "    ", theRootFilter
                if cmds.objectType(cst) in ["parentConstraint"]:
                # if "_prCns" in cst:
                    if cmds.objExists(cst):
                        if not theRootFilter in cst:
                            # get cst conn
                            theParent = cmds.listConnections(cst + '.target[0].targetParentMatrix', d=False, s=True)[0]
                            theChild = cmds.listConnections(cst + '.constraintTranslate.constraintTranslateX', d=True, s=False)[0]
                            print "*", theChild, "c->p", theParent

                            # re parent has it has to be
                            cmds.parent (theChild, theParent)
                        else:
                            theRootCstParent = cmds.listConnections(cst + '.target[0].targetParentMatrix', d=False, s=True)[0]


            # delete cst
            print "Deleting CST"
            for i in allCstL:
                cmds.delete(i)


            # create bridge group parent it in the hierarchy and cst
            print "Bridging"
            bridgeGp = cmds.group(name=bridgeName, world=1, em=1)
            cmds.parent (bridgeGp, cmds.listRelatives(rootL[0], p=1)[0])
            # matchByXformMatrix(cursel=["Jaw_Bone_Ctrl",bridgeGp], mode =0)
            cmds.parentConstraint(theRootCstParent, bridgeGp, mo=0)
            cmds.scaleConstraint(theRootCstParent, bridgeGp,)
            cmds.parent (rootL[0], bridgeGp)


            debugL.append("    -Rig_replaced, all cst deleted")
        else:
            debugL.append("    -Nothing Done")
    else:
        debugL.append ("    -Nothing Done, the scene doesn't match")


    return True , debugL

def chr_TeethFix(*args, **kwargs):
    """ Description: Fix le rig des dents
        Return : [BOOL,LIST]
        Dependencies : cmds - chr_CstScaleandOptimFix()
    """
    print "chr_TeethFix()"

    result = ""
    resultL = []
    debugL = []
    result, debugL = chr_CstScaleandOptimFix(bridgeName="Dn_Teeth_Bridge", RootPrefixeToCut="TK_",
                rootL=["TK_Bottom_Teeth_Global_Root",
                "TK_Left_Bottom_Teeth_Root",
                "TK_Right_Bottom_Teeth_Root",
                "TK_Bottom_Teeth_Root"],)


    result2, debugL2 = chr_CstScaleandOptimFix(bridgeName="Up_Teeth_Bridge", RootPrefixeToCut="TK_",
            rootL=["TK_Top_Teeth_Global_Root",
            "TK_Left_Top_Teeth_Root",
            "TK_Right_Top_Teeth_Root",
            "TK_Top_Teeth_Root"])

    resultL = [result, result2]
    debugL += debugL2
    return resultL, debugL

def chr_chinEarsFix(*args, **kwargs):
    """ Description: Fix le rig des ears et du chin
        Return : [BOOL,LIST]
        Dependencies : cmds - chr_CstScaleandOptimFix()
    """
    print "chr_chinEarsFix()"
    result = ""
    resultL = []
    debugL = []
    result, debugL = chr_CstScaleandOptimFix(bridgeName="chin_Bridge", RootPrefixeToCut="TK_",
            rootL=["TK_chin_Root", ])

    result2, debugL2 = chr_CstScaleandOptimFix(bridgeName="ear_R_Bridge", RootPrefixeToCut="TK_",
                rootL=["TK_Right_Ear_Root", ])

    result3, debugL3 = chr_CstScaleandOptimFix(bridgeName="ear_L_Bridge", RootPrefixeToCut="TK_",
                rootL=["TK_Left_Ear_Root", ])

    resultL = [result, result2, result3]
    print "resultL", resultL
    debugL += debugL2 + debugL3
    return resultL, debugL

def chr_changeCtrDisplays(*args, **kwargs):
    """ Description: Change les colors des ctrs, et re-ajuste le display de certain ctrs
        Return : [BOOL,LIST]
        Dependencies : cmds - 
    """
    print "chr_changeCtrDisplays()"
    debugL = []

    canDo = True
    greenC = 23
    greenL = ['Right_UpperEye_3_Ctrl', 'Right_UpperEye_2_Ctrl', 'Right_UpperEye_1_Ctrl', 'Right_UpperEye_0_Ctrl',
                'Right_LowerEye_2_Ctrl', 'Right_LowerEye_3_Ctrl', 'Right_LowerEye_0_Ctrl', 'Right_LowerEye_1_Ctrl',
                'Left_UpperEye_0_Ctrl', 'Left_UpperEye_2_Ctrl', 'Left_UpperEye_1_Ctrl', 'Left_UpperEye_3_Ctrl',
                'Left_LowerEye_2_Ctrl', 'Left_LowerEye_1_Ctrl', 'Left_LowerEye_3_Ctrl', 'Left_LowerEye_0_Ctrl',
                'Right_Levator_2_Ctrl', 'Left_Levator_2_Ctrl', 'Right_LowerLip_Inter', 'Right_UpperLip_Inter',
                'Left_UpperLip_Inter', 'Left_LowerLip_Inter',
                'Left_Eye_Bulge', 'Right_Eye_Bulge', 'Right_nostril', 'Left_nostril',
                'Fly_Main_Ctrl',
                ]+['Right_Base_Depressor1', 'Right_Base_Depressor', 'Base_Depressor', 'Left_Base_Depressor', 
                'Left_Base_Depressor1', 'Left_Base_Levator1', 'Left_Base_Levator', 'Base_UpperLip_Main_Ctrl', 
                'Right_Base_Levator', 'Right_Base_Levator1',
                ]


    brownLightC = 25
    brownLightL = ['Spine_IK_Extra_6_Ctrl', 'Spine_IK_Extra_5_Ctrl', 'Spine_IK_Extra_4_Ctrl', 'Spine_IK_Extra_3_Ctrl',
                'Spine_IK_Extra_2_Ctrl', 'Spine_IK_Extra_1_Ctrl', 'Left_Leg_Extra_0', 'Right_Arm_Extra_0', 'Right_Arm_Extra_1',
                'Right_Arm_Extra_2', 'Right_Arm_Extra_3', 'Right_Arm_Extra_4', 'Right_Arm_Extra_5', 'Right_Arm_Extra_6',
                'Right_Leg_Extra_0', 'Left_Arm_Extra_0', 'Left_Arm_Extra_1', 'Left_Arm_Extra_2', 'Left_Arm_Extra_3',
                'Left_Arm_Extra_4', 'Left_Arm_Extra_5', 'Left_Arm_Extra_6', 'Left_Leg_Extra_1', 'Left_Leg_Extra_2',
                'Left_Leg_Extra_3', 'Left_Leg_Extra_4', 'Left_Leg_Extra_5', 'Left_Leg_Extra_6', 'Right_Leg_Extra_1',
                'Right_Leg_Extra_2', 'Right_Leg_Extra_3', 'Right_Leg_Extra_4', 'Right_Leg_Extra_5', 'Right_Leg_Extra_6',
                'NECK_Deformers_ExtraCtrl_7', 'NECK_Deformers_ExtraCtrl_3', 'NECK_Deformers_ExtraCtrl_5',
                'NECK_Deformers_ExtraCtrl_1', 'Spine_IK_Extra_7_Ctrl']
    redDarkC = 4
    redDarkL = ['Head_Bulge_Start_Ctrl', 'Head_Bulge_End_Handle_Ctrl', 'Head_Bulge_End_Ctrl', "BigDaddy",
                ]+['Right_LowerLip_1_Ctrl', 'Right_LowerLip_2_Ctrl', 'Right_UpperLip_2_Ctrl', 'Right_UpperLip_1_Ctrl',
                 'Left_UpperLip_1_Ctrl', 'Left_UpperLip_2_Ctrl', 'Left_LowerLip_2_Ctrl', 'Left_LowerLip_1_Ctrl',
                 ]


    redClearC = 13
    redClearL = ["Global_SRT", ]


    yellowC = 17
    yellowL = []

    blackC = 1
    blackL = ['Right_Riso_0_Ctrl', 'Right_Zygo_0_Ctrl', 'Right_Levator1_1_Ctrl', 'Right_Levator_1_Ctrl', 'Left_Levator_1_Ctrl', 
            'Left_Levator1_1_Ctrl', 'Left_Zygo_0_Ctrl', 'Left_Riso_0_Ctrl',
            ]+['Left_Depressor_Handle_1_Control', 'Left_Depressor1_Handle_1_Control', 'Right_Depressor_Handle_1_Control', 'Right_Riso_1_Ctrl', 
            'Right_Zygo_1_Ctrl', 'Right_Levator_0_Ctrl', 'Right_Depressor1_Handle_1_Control', 'Right_Levator1_0_Ctrl', 'Left_Riso_1_Ctrl', 
            'Left_Zygo_1_Ctrl', 'Left_Levator1_0_Ctrl', 'Left_Levator_0_Ctrl']


    #allready done test
    if getColor(objL="Fly_Main_Ctrl")[0] in [greenC] and getColor(objL="BigDaddy")[0] in [redDarkC]:
        canDo = False
        print "Tweak Allready done"
        debugL.append("Tweak Allready done")

    # for k in greenL+brownLightL+redDarkL:
    #     if not cmds.objExists(k):
    #         canDo = False


    if canDo:
        # to green
        OverideColor(greenC, mode="normal", TheSel=greenL,)
        # to brownLight
        OverideColor(brownLightC, mode="normal", TheSel=brownLightL,)
        # redDark
        OverideColor(redDarkC, mode="normal", TheSel=redDarkL,)
        # redClear
        OverideColor(redClearC, mode="normal", TheSel=redClearL,)
        # yellow
        # OverideColor(yellowC, mode="normal",TheSel = yellowL, )
        debugL.append("-Base Colors changed")

        # black
        OverideColor(blackC, mode="normal", TheSel=blackL)

        # special offset du display du fly -----------------------------------------------
        print "fly display"
        zooB = True
        target = "Fly_Main_Ctrl"
        refL = ['Global_SRT', 'LowerBody']
        for i in refL + [target]:
            if not  cmds.objExists(i):
                zooB = False
        if zooB:
            pointL = getPointsOnCurve(target)
            bbox = cmds.exactWorldBoundingBox(refL)
            factor = 2.5
            cmds.move(0, 0, -(bbox[3] - bbox[0]) / factor , pointL, r=1, os=1, wd=1,)
            debugL.append("-fly display changed")


        # change foots display --------------------------------------------------------------
        print "foots display"
        zooB = True
        footL = ['Right_Leg_IK', 'Left_Leg_IK']
        for k in footL:
            if not cmds.objExists(k):
                zooB = False
        if zooB:
            for j in footL:
                pointL = getPointsOnCurve(j)
                bbox = cmds.exactWorldBoundingBox(pointL)
                pivT = cmds.xform(j, t=1, q=1, ws=1, worldSpaceDistance=1)
                cmds.scale(1.1, 0.1, 1.1, pointL, p=(pivT[0], 0, pivT[2],))
            debugL.append("-foots display changed")


        # move vis_Holder --------------------------------------------------------------
        print "vis_Holder display"
        zooB = True
        visH = ["VisHolder_Main_Ctrl"]
        refL = ['Local_SRT', 'VisHolder_Main_Ctrl']
        for k in refL + visH :
            if not cmds.objExists(k):
                zooB = False
        if zooB:
            factor = 3.5
            pointL = getPointsOnCurve(visH)
            bbox = cmds.exactWorldBoundingBox(refL)
            cmds.move((bbox[3] - bbox[0]) / factor , 1, 0, pointL, r=1, os=1, wd=1,)
            debugL.append("-vis_Holder display changed")


    return True, debugL

def chr_neckBulge_Factor_to_zero(*args, **kwargs):
    """ Description: met le neck bulge factor à 0
        Return : BOOL
        Dependencies : cmds - 
    """
    print "chr_neckBulge_Factor_to_zero()"

    if cmds.objExists("Head_ParamHolder_Main_Ctrl.Neck_Bulge_Factor"):
        cmds.setAttr("Head_ParamHolder_Main_Ctrl.Neck_Bulge_Factor", 0)
    return True

def chr_BS_teeth_Noze_Fix(*args, **kwargs):
    print "chr_BS_teeth_Noze_Fix()"
    # fix the teeth squeeze BS and add the noze pinch bs to the characters


    # get asset BS path (have to contain all teeth and additif BS shapes)

    # get asset bsd file

    # check correspondance


    # import BS  in the scene

    # apply .bsd file

    # delete importe objects


def armTwistFix (*args, **kwargs):
    print "armTwistFix()"

    # Left_Rounding_Deformer_End_Crv_upV_pathCns_Mult1 #tweak rotation


def chr_improve_Knuckles(*args, **kwargs):
    """ Description: Add factoring and connexion on the basic Knuckles rig splited in flexion/extension and rotation_factor
                     Add knuckle_scale attributes on the corresponding phalanx controlers
                     All Rigging Tweaking attribut are accessible on the knuckes deformers directly:
                     - Flexion/extension translateX and Y
                     - rotation factoring 
        Return : 
        Dependencies : cmds - 
    """

    print "chr_improve_Knuckles()"

    canDo = True
    defL = ['Left_Index_meta_offset_jnt', 'Left_Middle_meta_offset_jnt', 'Left_Ring_meta_offset_jnt',
            'Left_Pinky_meta_offset_jnt',
            'Right_Index_meta_offset_jnt', 'Right_Middle_meta_offset_jnt', 'Right_Ring_meta_offset_jnt',
             'Right_Pinky_meta_offset_jnt',
            ]

    thePlugA = "tx"
    thePlugB = "ty"

    # default values
    rotation_factor = 0.5
    Ty_flexion_factor = -0.5
    Tx_flexion_factor = 0.3
    Ty_extension_factor = -0.3
    Tx_extension_factor = 0.5

    for i in defL :
        if not cmds.objExists(i):
            canDo = False

    if canDo:
        for j in defL:
            #-------------------- translate tree ----------------------------------------------------------

            # create multiply node
            multiply_T_N = cmds.createNode("multiplyDivide", name=j + "Multiply_T_facto")

            # create condition
            ConditionYN = cmds.createNode("condition", name=j + "condition_T_flex_ext")
             # cond node greter or  equal
            cmds.setAttr(ConditionYN + ".operation", 3)
            cmds.setAttr(ConditionYN + ".secondTerm", 0)
            cmds.setAttr(ConditionYN + ".colorIfTrueR", Tx_flexion_factor) # TX Flex
            cmds.setAttr(ConditionYN + ".colorIfTrueG", Ty_flexion_factor)
            # cmds.setAttr(ConditionYN + ".colorIfTrueB", 0)
            cmds.setAttr(ConditionYN + ".colorIfFalseR", Tx_extension_factor)# TX ext
            cmds.setAttr(ConditionYN + ".colorIfFalseG", Ty_flexion_factor)
            # cmds.setAttr(ConditionYN + ".colorIfFalseB", 0)

            # get connection on ty
            ty_inCon = cmds.listConnections(j + "." + thePlugA, s=1, d=0, p=1)[0]
            print "ty_inCon=", ty_inCon
             # get connection on tx
            tx_inCon = ty_inCon

            # connect ty to multi
            cmds.connectAttr(ty_inCon, ConditionYN + ".firstTerm", f=True)
            # cmds.connectAttr(ty_inCon, ConditionYN + ".colorIfTrueR", f=True)
            # cmds.connectAttr(ty_inCon, ConditionYN + ".colorIfTrueG", f=True)
            # cmds.connectAttr(ty_inCon, ConditionYN + ".colorIfFalseR", f=True)
            # cmds.connectAttr(ty_inCon, ConditionYN + ".colorIfFalseG", f=True)

            # connect ty to cond
            cmds.connectAttr(ConditionYN + ".outColor", multiply_T_N + ".input2", f=True)

            # connect ty to multi
            cmds.connectAttr(tx_inCon , multiply_T_N + ".input1X", f=True)
            cmds.connectAttr(tx_inCon , multiply_T_N + ".input1Y", f=True)

            # connect multi to the plugs
            cmds.connectAttr(multiply_T_N + ".outputX", j + "." + thePlugA, f=True)
            cmds.connectAttr(multiply_T_N + ".outputY", j + "." + thePlugB, f=True)

            # set values
            # cmds.setAttr(multiply_T_N+"."+ "input2X",multPlugAT)
            # cmds.setAttr(multiply_T_N+"."+ "input2Y",multPlugBT)

            #-------------------- rotate tree ----------------------------------------------------------
             # get controling attrib
            controlingCTR_Attr = cmds.listConnections(ty_inCon.split(".", 1)[0], s=1, d=0, scn=1,)[0]
            print "controlingCTR_Attr=", controlingCTR_Attr

            # create Multiply_R_factor node
            multiply_R_N = cmds.createNode("multiplyDivide", name=j + "Multiply_R_facto")#  multidoublelinear

            # connect
            cmds.connectAttr(controlingCTR_Attr + ".rotate", multiply_R_N + ".input1", f=True)
            cmds.connectAttr(multiply_R_N + ".output", j + ".rotate", f=True)

            # set rotation factor values
            cmds.setAttr(multiply_R_N + "." + "input2X", rotation_factor)
            cmds.setAttr(multiply_R_N + "." + "input2Y", rotation_factor)
            cmds.setAttr(multiply_R_N + "." + "input2Z", rotation_factor)

            # add attr to each
            cmds.addAttr(j, longName="Ty_flexion_factor", attributeType="float", keyable=True, min=-10, max=10, dv=Ty_flexion_factor)
            cmds.addAttr(j, longName="Tx_flexion_factor", attributeType="float", keyable=True, min=-10, max=10, dv=Tx_flexion_factor)
            cmds.addAttr(j, longName="Ty_extension_factor", attributeType="float", keyable=True, min=-10, max=10, dv=Ty_extension_factor)
            cmds.addAttr(j, longName="Tx_extension_factor", attributeType="float", keyable=True, min=-10, max=10, dv=Tx_extension_factor)
            cmds.addAttr(j, longName="rotation_factor", attributeType="float", keyable=True, min=-10, max=10, dv=rotation_factor)

            # connect attr to factor nodes
            cmds.connectAttr(j + ".Tx_flexion_factor", ConditionYN + ".colorIfTrueR", f=True)
            cmds.connectAttr(j + ".Ty_flexion_factor", ConditionYN + ".colorIfTrueG", f=True)
            cmds.connectAttr(j + ".Tx_extension_factor", ConditionYN + ".colorIfFalseR", f=True)
            cmds.connectAttr(j + ".Ty_extension_factor", ConditionYN + ".colorIfFalseG", f=True)
            cmds.connectAttr(j + ".rotation_factor", multiply_R_N + ".input2X", f=True)
            cmds.connectAttr(j + ".rotation_factor", multiply_R_N + ".input2Y", f=True)
            cmds.connectAttr(j + ".rotation_factor", multiply_R_N + ".input2Z", f=True)


            #-------------------- scale tree ----------------------------------------------------------
            # connect the deformer scale to the first phalanx controler
            cmds.addAttr(controlingCTR_Attr.split(".", 1)[0], longName="Knuckle_scale_X", attributeType="float", keyable=True, min=-5, max=5, dv=1)
            cmds.addAttr(controlingCTR_Attr.split(".", 1)[0], longName="Knuckle_scale_Y", attributeType="float", keyable=True, min=-5, max=5, dv=1)
            cmds.addAttr(controlingCTR_Attr.split(".", 1)[0], longName="Knuckle_scale_Z", attributeType="float", keyable=True, min=-5, max=5, dv=1)

            cmds.connectAttr(controlingCTR_Attr + ".Knuckle_scale_X", j + ".scaleX", f=True)
            cmds.connectAttr(controlingCTR_Attr + ".Knuckle_scale_Y", j + ".scaleY", f=True)
            cmds.connectAttr(controlingCTR_Attr + ".Knuckle_scale_Z", j + ".scaleZ", f=True)

            # add one desactivation attrib

            # return all created nodes



def chr_fixeLatticeParams(bulge_factor=1.25, *args, **kwargs):
    """ Description:  -Fix les valeur de lattice "local influance" causant des deformation disgracieuse
                      -Set l'attribut Head_bulge à une valeur par default de 1.25
        Return : [True,List]
        Dependencies : cmds - 
    """
    # WIP
    print "chr_fixeLatticeParams()"
    debugL = []
    ffdL = ['Right_eyeFace_ffd', 'Left_eyeFace_ffd', 'geo_head_ffd', 'ffd_geo_Right_Eye', 'ffd_geo_Left_Eye','ffd_Head_Bulge']
    locInfluance = 8
    canDo = True
    # set local influance
    for k in ffdL[-3:]:
        if not cmds.objExists(k):
            canDo = False
            debugL.append("Nothing done")
    if canDo:
        for i in ffdL:
            if cmds.objExists(i):
                cmds.setAttr(i+ ".localInfluenceS", locInfluance)
                cmds.setAttr(i+ ".localInfluenceT", locInfluance)
                cmds.setAttr(i+ ".localInfluenceU", locInfluance)
                cmds.setAttr(i+ ".localInfluenceU", locInfluance)
                cmds.setAttr(i+ ".outsideFalloffDist", 0.001)

                debugL.append("-" + i+ ": Fixed")
        
        # set lattice to "inside mode"
        for j in ffdL[:2]:
            if cmds.objExists(j):
                cmds.setAttr(j+ ".outsideLattice", 0)

    # set bugle_factor
    theAttr = "Head_Bulge_End_Ctrl.Head_Bulge_Bulge_Factor"
    if cmds.objExists (theAttr):
        cmds.setAttr(theAttr,bulge_factor)
    
    return True,debugL

def chr_setVis_Params(*args, **kwargs):
    """ Description: Set les parametre par default des attribut du vis holder pour l'animation
        Return : [True]
        Dependencies : cmds - 
    """
    print "chr_setVis_Params()"
    
    obj= "VisHolder_Main_Ctrl"
    if cmds.objExists(obj):
        try:
            cmds.setAttr(obj + ".Big_daddy_visibility", 0)
            cmds.setAttr(obj + ".Global", 1)
            cmds.setAttr(obj + ".Controls", 1)

            
            cmds.setAttr(obj + ".RigStuff", 0)
            cmds.setAttr(obj + ".Deformers", 0)
            cmds.setAttr(obj + ".SmoothLevel", 0)

            cmds.setAttr(obj + ".Geometry", 1)
            cmds.setAttr(obj + ".Controls_0", 1)
            cmds.setAttr(obj + ".Controls_1", 0)
            cmds.setAttr(obj + ".Controls_2", 0)
            cmds.setAttr(obj + ".Controls_3", 0)

            cmds.setAttr(obj + ".Head_Res", 0)
            cmds.setAttr(obj + ".Body_res", 1)
        except Exception,err:
            print err
    return [True]

def chr_hideCurveAiAttr(*args, **kwargs):
    print "chr_hideCurveAiAttr()"
    """ Description: Rend les attributs arnauld non keyable et non visible sur toutes les shapes des obj du set_control (help for anim and keys)
        Return : [True,doneList]
        Dependencies : cmds - 

    """
    doneL = []
    attrToHideL= ["aiRenderCurve","aiCurveWidth","aiSampleRate","aiCurveShaderR","aiCurveShaderG","aiCurveShaderB"]
    cursel = cmds.sets("set_control",q=1)
    for i in cursel:
        for attr in attrToHideL:
            if cmds.objExists(i+"."+attr):
                cmds.setAttr(i+"."+attr,k=0,)
                doneL.append(i+"."+attr)

    return [True, doneL]

def chr_replace_chr_vis_Exp_System(*args, **kwargs):
    print "chr_replace_chr_vis_Exp_System()"
    """ Description: Remplace le system original de toonkit comportant environ 320 expression par des nodes multiplyLinear
                     Renvoie toujours True et le nombre d'expression deleted/replaced
        Return : [BOOL,int]
        Dependencies : cmds -        
    """
    inObj = "VisHolder_Main_Ctrl"
    mainVisAttr= "Controls"
    lvl0 = "Controls_0"
    activeLvl = lvl0

    # activate all to not loose conection info
    # vars
    inObj = "VisHolder_Main_Ctrl"
    mainVisAttr= "Controls"
    lvl0 = "Controls_0"
    lvl1 = "Controls_1"
    lvl2 = "Controls_2"
    lvl3 = "Controls_3"
    
    # get multiply node to connect to
    multiply_Vis = ""
   
    # show all controlers levels
    try:
        cmds.setAttr(inObj+"."+mainVisAttr,1)
        cmds.setAttr(inObj+"."+lvl0,1)
        cmds.setAttr(inObj+"."+lvl0,1)
        cmds.setAttr(inObj+"."+lvl1,1)
        cmds.setAttr(inObj+"."+lvl2,1)
        cmds.setAttr(inObj+"."+lvl3,1)
    except:
        pass


    # get expression connected to vis
    replacedExpL = []
    spkipedObjL = []
    Attr = "overrideVisibility"
    cursel = cmds.sets("set_control",q=1)
    # print cursel
    for i in cursel:
        # print "*",i
        shapeL = [i + "|"+ x for x in cmds.listRelatives(i,c=1,s=1,f=0) ]
        for j in shapeL:
            if cmds.objExists( j+"."+Attr ):
                # print j,Attr
                exp= cmds.listConnections( j+"."+Attr, s=1, d=0, scn=1,)
                if exp:
                    exp = exp[0]
                    # print "exp=", exp
                    inExpConL = []
                    inputL = cmds.listAttr(exp+".input[*]")
                    for i in inputL:
                        inExpConL.append(cmds.listConnections(exp+"."+i,s=1,d=0)[0])
                        # print "    <->",inExpConL
                    # print "inExpConL=", inExpConL
                    compensed= list(set(inExpConL) )
                    if compensed == ["VisHolder_Main_Ctrl"]:
                        # print "YEAHHHHHHH"
                        if cmds.objectType(exp) in ["expression"]:
                            # print "   ",exp
                            currentStr = cmds.expression(exp,string=1,q=1 )
                            # print "    ->",currentStr
                            activeLvl = currentStr.rsplit("{0}.Controls * {0}.".format(inObj),1)[-1]
                            

                            if not "." in activeLvl:
                                # replace the expression by node multiply 
                                # create Multiply_R_factor node
                                multiply_Vis = cmds.createNode("multDoubleLinear", name=j + "Ctr_Shape_Switch_Vis#")

                                # connect
                                
                                cmds.connectAttr(inObj + "." + mainVisAttr, multiply_Vis + "." + "input1",f=1)
                                cmds.connectAttr(inObj + "." + activeLvl  , multiply_Vis + "." + "input2",f=1)

                                cmds.connectAttr(multiply_Vis+"."+ "output", j + "." + "visibility",f=1)


                                # delete old expression
                                
                                cmds.delete(exp)
                                replacedExpL.append(exp)

                            else:
                                # print "     @activeLvl:",activeLvl
                                spkipedObjL.append(j)

                        else:
                            spkipedObjL.append(j)

                else:
                    spkipedObjL.append(j)

            else:
                spkipedObjL.append(j)

    # adding additive rigs here
    upperBrowBreakL  = ['Right_Brow_upRidge_03_ctrl', 'Right_Brow_upRidge_01_ctrl', 'Right_Brow_upRidge_04_ctrl', 'Right_Brow_upRidge_02_ctrl', 
                          'Left_Brow_upRidge_03_ctrl', 'Left_Brow_upRidge_04_ctrl', 'Left_Brow_upRidge_01_ctrl', 'Left_Brow_upRidge_02_ctrl']

    upperBrowsAdditveL = ["Left_Brow_upRidge_grp", "Right_Brow_upRidge_grp"]
    canDo = True
    for i in upperBrowsAdditveL:
        if not cmds.objExists(i):
            canDo=False
    if canDo:
        print "* upperBrow disconnection:"
        for i in upperBrowBreakL:
            shapeL = [i + "|"+ x for x in cmds.listRelatives(i,c=1,s=1,f=0) ]
            for j in shapeL:
                conL = cmds.listConnections(j+".v",s=1,d=0,p=1)
                if conL:
                    print "isCon",conL

                    cmds.disconnectAttr( conL[0], j + ".visibility")
                    if cmds.objectType(conL[0]) in ["multDoubleLinear"] :
                        print "deleting inCon"
                        cmds.delete(conL[0].split(".")[0])

        print "* upperBrowsAdditveL connexion:"
        for j in upperBrowsAdditveL:
            # shapeL = [i + "|"+ x for x in cmds.listRelatives(i,c=1,s=1,f=0) ]
            # for j in shapeL:
                if cmds.objExists( j+"."+Attr ):
                    # create multi node
                    multiply_Vis = cmds.createNode("multDoubleLinear", name= j + "Ctr_Shape_Switch_Vis#")
                    # connect
                    cmds.connectAttr(inObj + "." + mainVisAttr, multiply_Vis + "." + "input1",f=1)
                    cmds.connectAttr(inObj + "." + lvl2  , multiply_Vis + "." + "input2",f=1)
                    cmds.connectAttr(multiply_Vis+"."+ "output", j + "." + "visibility",f=1)
                    print "  multiply_Vis=", multiply_Vis
                    print "  mainVisAttr=", mainVisAttr
                    print "  activeLvl=", activeLvl


    print len(replacedExpL)
    return [True,len(replacedExpL)]


def chr_reArrangeCtr_displayLevel(*args, **kwargs):
    """ Description: Re order the controlers in the right display level, and optimise speed by replacing expressions by nodes.
        Return : [BOOL,Int(number of replaced expressions)]
        Dependencies : cmds - 
    """
    print "chr_reArrangeCtr_displayLevel()"

    #body
    toLvl0L=['Head_Bulge_End_Ctrl', 'Head_Bulge_End_Handle_Ctrl',]
    
    # facial 01
    toLvl1L=['Right_UpperLip_1_Ctrl', 'Left_Tongue_2', 'Left_Tongue_3', 'Left_Tongue_1', 'Right_LowerLip_1_Ctrl', 'Top_Teeth', 'Tongue_1', 'Tongue_0', 
    'Tongue_3', 'Tongue_2', 'Left_MouthCorner', 'LowerLip_Center', 'Right_LowerLip_2_Ctrl', 'Left_UpperLip_2_Ctrl', 'Right_MouthCorner', 
    'Right_UpperLip_2_Ctrl', 'Bottom_Teeth_Global', 'Top_Teeth_Global', 'Left_Bottom_Teeth', 'Left_Top_Teeth', 'Right_Tongue_2', 'Right_Tongue_3', 
    'Bottom_Teeth', 'Right_Tongue_1', 'Left_LowerLip_1_Ctrl', 'Right_Top_Teeth', 'Right_Bottom_Teeth', 'UpperLip_Center', 'Left_UpperLip_1_Ctrl', 
    'Left_LowerLip_2_Ctrl', 'Left_nostril', 'Right_nostril', 'Noze_Main_Ctrl', 'Left_CheekBone', 'Right_CheekBone', 'Left_Cheek', 'Right_Cheek', 
    'Right_LowerEye_2_Ctrl', 'Right_UpperEye_1_Ctrl', 'Right_UpperEye_3_Ctrl', 'Right_UpperEye_0_Ctrl', 'Right_LowerEye_3_Ctrl', 'Right_LowerEye_0_Ctrl', 
    'Right_LowerEye_1_Ctrl', 'Right_UpperLid_Main_Ctrl', 'Right_Eyelid_In', 'Right_Eyelid_Out', 'Right_LowerLid_Main_Ctrl', 'Right_UpperEye_2_Ctrl', 
    'Left_Eyelid_Out', 'Left_UpperLid_Main_Ctrl', 'Left_LowerLid_Main_Ctrl', 'Left_LowerEye_2_Ctrl', 'Left_LowerEye_0_Ctrl', 'Left_LowerEye_1_Ctrl', 
    'Left_UpperEye_0_Ctrl', 'Left_LowerEye_3_Ctrl', 'Left_Eyelid_In', 'Left_UpperEye_2_Ctrl', 'Left_UpperEye_1_Ctrl', 'Left_UpperEye_3_Ctrl', 
    'Right_EyeBrow_out_1', 'Right_EyeBrow_in_1', 'Right_EyeBrow_in', 'Right_EyeBrow_out', 'Right_EyeBrow_Global', 'Left_EyeBrow_in', 'Left_EyeBrow_out_1', 
    'Left_EyeBrow_out', 'Left_EyeBrow_in_1', 'Left_EyeBrow_Global', 'EyeBrow_Middle', 'Right_Eye_Pupille_Main_Ctrl', 'Left_Eye_Pupille_Main_Ctrl', 
    'Right_Eye_Bulge', 'Left_Eye_Bulge', 'Head_Bulge_Start_Ctrl']


    # facial 02
    toLvl2L=['Right_Base_Levator1', 'Right_Base_Levator', 'Base_UpperLip_Main_Ctrl', 'Left_Base_Levator', 'Left_Base_Levator1', 'Left_Base_Depressor1', 
    'Left_Base_Depressor', 'Base_Depressor', 'Right_Base_Depressor', 'Right_Base_Depressor1', 'Right_Brow_ridge_in', 'Right_Brow_ridge_out_1', 
    'Right_Brow_ridge_out', 'Right_Brow_ridge_in_1', 'Right_Brow_upRidge_03_ctrl', 'Right_Brow_upRidge_01_ctrl', 'Right_Brow_upRidge_04_ctrl', 
    'Right_Brow_upRidge_02_ctrl', 'Left_Brow_ridge_out_1', 'Left_Brow_ridge_in_1', 'Left_Brow_ridge_in', 'Left_Brow_ridge_out', 'Left_Brow_upRidge_03_ctrl', 
    'Left_Brow_upRidge_04_ctrl', 'Left_Brow_upRidge_01_ctrl', 'Left_Brow_upRidge_02_ctrl',
    ]+['Left_Eye', 'Right_Eye',
    ]+['Right_Riso_0_Ctrl', 'Right_Zygo_0_Ctrl', 'Right_Levator1_1_Ctrl', 'Right_Levator_1_Ctrl', 'Left_Levator_1_Ctrl', 
        'Left_Levator1_1_Ctrl', 'Left_Zygo_0_Ctrl', 'Left_Riso_0_Ctrl']

    # to not touch
    toLvl3L= ['Left_Arm_Root', 'Right_Arm_Root',"Aim",
            ]+['Left_Depressor1_Handle_1_Control', 'Left_Depressor_Handle_1_Control', 'Right_Depressor_Handle_1_Control', 
            'Right_Depressor1_Handle_1_Control', 'Right_Zygo_1_Ctrl', 'Left_Zygo_1_Ctrl',
            ]+  ['Right_Riso_1_Ctrl', 'Right_Levator_0_Ctrl', 'Right_Levator1_0_Ctrl', 'Left_Riso_1_Ctrl', 'Left_Levator1_0_Ctrl', 'Left_Levator_0_Ctrl']


    # vars
    inObj = "VisHolder_Main_Ctrl"
    mainVisAttr= "Controls"
    lvl0 = "Controls_0"
    lvl1 = "Controls_1"
    lvl2 = "Controls_2"
    lvl3 = "Controls_3"
    

    # start settings loop
    allL = toLvl0L+toLvl1L+toLvl2L+toLvl3L
    if len(allL):
        for i in allL :
            curLvl = lvl0

            if i in toLvl1L:
                curLvl = lvl1
            elif i in toLvl2L:
                curLvl = lvl2
            elif i in toLvl3L:
                # handle le cas ou il n y a pas d attribut "controls_3" dans le rig
                if not cmds.objExists(inObj+"."+lvl3):
                    # print "ADD ATTR"
                    cmds.addAttr( inObj, longName=lvl3, attributeType="enum",enumName="False:True", keyable=True,  dv=0)
                    cmds.setAttr(inObj + "."+lvl3,channelBox=1)
                    movAttrL=  ["Head","Head_Res","Body_res","Deformers","SmoothLevel","Geometry","RigStuff"]
                    movAttrL.reverse()
                    for mattr in [lvl3]+movAttrL:
                        # print "*****",mattr
                        lock = cmds.getAttr(inObj+"."+mattr,l=1)
                        cmds.setAttr(inObj+"."+mattr,l=0)
                        cmds.deleteAttr(inObj,at=mattr)
                        cmds.undo()
                        cmds.setAttr(inObj+"."+mattr,l=lock)
                    
                curLvl = lvl3

            if cmds.objExists(i):
                # print "****",i
                if cmds.listRelatives(i,c=1,s=1,):
                    shapeL = [i+"|"+ x for x in cmds.listRelatives(i,c=1,s=1,)]
                    if shapeL:
                        for j in shapeL:
                            if "IK" in j:
                                print "**************************************",j
                            if cmds.connectionInfo( j + "."+ "visibility",isDestination=True):
                                multiply_Vis = cmds.listConnections( j + "."+ "visibility",s=1,d=0, scn=1,)[0]
                                # print "multiply_Vis=", multiply_Vis
                                # print curLvl, cmds.listConnections(multiply_Vis + "." + "input2",p=1)[0]
                                if not curLvl  in cmds.listConnections(multiply_Vis + "." + "input2",p=1)[0] :
                                    # print "connect"
                                    # cmds.disconnectAttr(inObj + "." + curLvl, multiply_Vis + "." + "input2" )
                                    cmds.connectAttr(inObj + "." + curLvl, multiply_Vis + "." + "input2", f=1)

                else:
                    print "NO SHAPE FOUND ON {0}".format(i)

    return [True,""]


def improveArcades(*args, **kwargs):
    """ Description: replace automove behavior by independant link to each individual brow ctr and Add a blend attribut to control it.
        Return : [True,debugL]
        Dependencies : cmds -  getCstActiveWeightPlugs()
    """
    print "improveArcades()"
    # WIP NOT IN SERVICE
    follow_dv = 0.5
    follow_attrN = "follow"
    headCtr = "Head_FK"
    browLL = ['Left_EyeBrow_in', 'Left_EyeBrow_in_1', 'Left_EyeBrow_out_1', 'Left_EyeBrow_out']
    arcadeLL = ['Left_Brow_ridge_in', 'Left_Brow_ridge_in_1', 'Left_Brow_ridge_out_1', 'Left_Brow_ridge_out']
    browRL = ['Right_EyeBrow_in', 'Right_EyeBrow_in_1', 'Right_EyeBrow_out_1', 'Right_EyeBrow_out']
    arcadeRL= ['Right_Brow_ridge_in', 'Right_Brow_ridge_in_1', 'Right_Brow_ridge_out_1', 'Right_Brow_ridge_out',]

    oSwitchGpL = "TK_Right_Brow_ridge_switcher_Root_RigParameters"
    oSwitchGpR = "TK_Left_Brow_ridge_switcher_Root_RigParameters"

    oToDeleteLL = ["TK_Right_Brow_ridge_switcher_Parent_0","TK_Right_Brow_ridge_switcher_Parent_1","TK_Right_Brow_ridge_switcher_Root_RigParameters"]
                
    oToDeleteLR = ["TK_Left_Brow_ridge_switcher_Parent_0","TK_Left_Brow_ridge_switcher_Parent_1","TK_Left_Brow_ridge_switcher_Root_RigParameters"]

    oToDeleteL = oToDeleteLL+ oToDeleteLR
    browL = browLL + browRL
    ctrL = arcadeLL + arcadeRL 
    canDo = True
       
    for i in ctrL + oToDeleteL + browL:
        if not cmds.objExists(i):
            canDo = False
    if canDo:

        # deleting base obj -------------------------------------------------------------------------------------------------
        for i in oToDeleteL:
            cmds.delete(i)

        for i in ctrL:
            print "*",i
            ctrRoot = cmds.listRelatives(cmds.listRelatives(i,p=1)[0],p=1)[0]
            allCstL = [x for x in cmds.listHistory(ctrRoot, levels=1,) if "Constraint" in   cmds.objectType(x)]
            print ctrRoot
            print "    ",len(allCstL), allCstL

            # deleting connected ---------------------------------------------------------------------------------------------
            for cst in allCstL:
                try:
                    print "        ", cmds.objectType(cst)
                    theParent = cmds.listConnections(cst + '.target[0].targetParentMatrix', d=False, s=True)[0]
                    print "    DELETING->",theParent
                    cmds.delete(theParent)
                    pass
                except:
                    pass

        

        # constraining each little ctrl arcade<- brow
        for daddy, ctr in zip(browL,ctrL):
            
            # get ctrRoot
            oCtrRoot = cmds.listRelatives(ctr,p=1)[0]
            
            # unlock srt de ctrRoot
            for attr in ["sx", "sy", "sz","rx","ry","rz", "tx","ty","tz"]:
                cmds.setAttr(ctrRoot+"."+attr,l=0,k=1)
            
            # create a matched child group for the constraint rig to avoid the 180 and scale -1 probleme
            ctrRoot = cmds.group(name= ctr + "_followRig_grp",em=1,p=oCtrRoot)
            cmds.xform(ctrRoot,t=(0,0,0),ro=(0,0,0),s=(1,1,1))

            # parent ctr to it
            cmds.parent(ctr,ctrRoot)
            cmds.xform(ctr,t=(0,0,0),ro=(0,0,0),s=(1,1,1))

            # constraining ctrl head
            cmds.parentConstraint(headCtr,ctrRoot, mo=1)
            # cmds.scaleConstraint(headCtr,ctrRoot, mo=1)

            # ----------------------------------------------------------------------------------- parent cst tree
            # get all the plugs on the cst
            pCst = cmds.parentConstraint(daddy,ctrRoot, mo=1)[0]
            activeTargetL = getCstActiveWeightPlugs(pCst)
            
            # creating reverse node and add attr to ctr
            reverse_N = cmds.createNode("reverse", name=ctrRoot + "reverse_Cst")
            if not cmds.objExists(ctr+ "."+ follow_attrN):
                cmds.addAttr(ctr, longName=follow_attrN, attributeType="float", keyable=True, min=0, max=1, dv=follow_dv)
            
            # connect
            cmds.connectAttr(ctr + "."+ follow_attrN, activeTargetL[1], f=True)
            cmds.connectAttr(ctr + "."+ follow_attrN, reverse_N + ".inputX", f=True)
            cmds.connectAttr(reverse_N + ".outputX", activeTargetL[0], f=True)
              
            # ----------------------------------------------------------------------------------- scale cst tree
            sCst = cmds.scaleConstraint(daddy,ctrRoot, mo=1)[0]
            activeTargetL = getCstActiveWeightPlugs(sCst)
            
            # connect
            cmds.connectAttr(ctr + "."+ follow_attrN, activeTargetL[1], f=True)
            cmds.connectAttr(ctr + "."+ follow_attrN, reverse_N + ".inputY", f=True)
            cmds.connectAttr(reverse_N + ".outputY", activeTargetL[0], f=True)



def chr_Fix_LookAt(*args, **kwargs):
    """ Description: Fix des bug potientiel sur le rig du lookAt. Lorsque que la contrainte n'est pas
                     faite sur le bon objet du rig.
        Return : [True,LIST]
        Dependencies : cmds - 
    """
    print "chr_Fix_LookAt()"
            
    # var
    toReturnB = True
    debugL = []
    LsideD = {"TargetGP" : "TK_Left_Eye_Root",
    "badSourceGP" : "TK_Left_Eye_Direction_Root",
    "goodSourceGP" : "TK_Left_Eye_Direction_Output",
    "currentSourceGP" :"",
    "fixBool" : False,
    }
    RsideD = {"TargetGP" : "TK_Right_Eye_Root",
    "badSourceGP" : "TK_Right_Eye_Direction_Root",
    "goodSourceGP" : "TK_Right_Eye_Direction_Output",
    "currentSourceGP" :"",
    "fixBool" : False,
    }
    AllDictL = [LsideD,RsideD]
    # TargetGP = "TK_Left_Eye_Root"
    # badSourceGP = "TK_Left_Eye_Direction_Root"
    # goodSourceGP = "TK_Left_Eye_Direction_Output"
    # currentSourceGP =""
    # fixBool = False
    
    for curD in AllDictL:
        TargetGP = curD["TargetGP"]
        badSourceGP = curD["badSourceGP"]
        goodSourceGP = curD["goodSourceGP"]
        currentSourceGP =curD["currentSourceGP"]
        fixBool = curD["fixBool"]

        # start each
        allCstL = [x for x in cmds.listHistory(TargetGP, levels=1,) if "Constraint" in   cmds.objectType(x)]
        print "allCstL=", allCstL

        # get current source
        if len(allCstL):
            for cst in allCstL:
                if cmds.objectType(cst) in ["parentConstraint"]:
                    currentSourceGP =cmds.listConnections(cst + '.target[0].targetParentMatrix', d=False, s=True)[0]    
                    
        else:
            currentSourceGP = ""

        print "currentSourceGP=", currentSourceGP

        # checks
        print currentSourceGP,"<>",goodSourceGP
        if not currentSourceGP in [goodSourceGP]:
            print "  bad Source"
            fixBool = True
        else:
            print "  good Source"
            debugL.append(TargetGP+": Allready OK")
        # Fix 
        if fixBool:
            # delete constraint
            if len(allCstL):
                cmds.delete(allCstL)

            # create new constraint
            pcst= cmds.parentConstraint(goodSourceGP,TargetGP,mo=True)
            scst= cmds.scaleConstraint(goodSourceGP,TargetGP,mo=True)

            debugL.append(TargetGP+": Fixed")
    
    return [True,debugL]



def chr_fix_mirror_parameters(*args, **kwargs):
    """ Description: Fix les problems d' attribut de mirror sur les controlers des rig delivered. Les valeur sont souvent mauvaise.
                     Ce fix recopy les parametre de aurelien_polo sur l asset en cours.
        Return : [BOOL,LIST,INTEGER,FLOAT,DICT,STRING]
        Dependencies : cmds - 
    """
    
    print "chr_fix_mirror_parametersAA()"
    debugL = []
    outTrueL =['Left_Bottom_Teeth', 'Right_Bottom_Teeth', 'Left_Top_Teeth', 'Right_Top_Teeth', 'Right_Shoulder', 'Left_Shoulder', 'Left_Hand_0', 'Left_Thumb_0', 'Left_Thumb_1', 'Left_Thumb_2', 'Left_Meta_Index', 'Left_Index_0', 'Left_Index_1', 'Left_Index_2', 'Left_Pinky_Meta_Bone_Ctrl', 'Right_Middle_1', 'Right_Middle_2', 'Right_Ring_Meta_Bone_Ctrl', 'Right_Ring_0_Bone_Ctrl', 'Right_Ring_1_Bone_Ctrl', 'Right_Ring_2_Bone_Ctrl', 'Right_Foot_FK_0', 'Right_Foot_FK_1', 'Left_Arm_FK_1', 'Left_Arm_FK_0', 'Left_Pinky_0_Bone_Ctrl', 'Left_Pinky_1_Bone_Ctrl', 'Left_Pinky_2_Bone_Ctrl', 'Left_Meta_Middle', 'Left_Middle_0', 'Left_Middle_1', 'Left_Middle_2', 'Left_Ring_Meta_Bone_Ctrl', 'Left_Ring_0_Bone_Ctrl', 'Left_Ring_1_Bone_Ctrl', 'Left_Ring_2_Bone_Ctrl', 'Right_Leg_FK_0', 'Right_Foot_Heel', 'Right_Foot_Reverse_0', 'Right_Foot_Reverse_1', 'Right_Foot_Reverse_2', 'Left_EyeBrow_out_1', 'Left_EyeBrow_in', 'Left_EyeBrow_out', 'Right_Arm_FK_1', 'Right_Arm_FK_0', 'Right_Hand_0', 'Right_Thumb_0', 'Left_nostril', 'Right_nostril', 'Right_Ear_Bone_Ctrl', 'Right_Thumb_1', 'Right_Thumb_2', 'Right_Meta_Index', 'Right_Index_0', 'Right_Index_1', 'Right_Index_2', 'Right_Pinky_Meta_Bone_Ctrl', 'Right_Pinky_0_Bone_Ctrl', 'Right_Pinky_1_Bone_Ctrl', 'Right_Pinky_2_Bone_Ctrl', 'Right_Meta_Middle', 'Right_Middle_0', 'Left_UpperEye_0_Ctrl', 'Right_UpperEye_0_Ctrl', 'Right_UpperEye_1_Ctrl', 'Right_UpperEye_2_Ctrl', 'Right_UpperEye_3_Ctrl', 'Right_LowerEye_0_Ctrl', 'Right_LowerEye_1_Ctrl', 'Right_LowerEye_2_Ctrl', 'Right_LowerEye_3_Ctrl', 'Right_Leg_FK_1', 'Right_Levator1_0_Ctrl', 'Right_Levator1_1_Ctrl', 'Right_Levator_0_Ctrl', 'Right_Levator_1_Ctrl', 'Right_Cheek', 'Right_Zygo_0_Ctrl', 'Right_Zygo_1_Ctrl', 'Left_Foot_FK_0', 'Right_Riso_0_Ctrl', 'Right_Riso_1_Ctrl', 'Left_Zygo_0_Ctrl', 'Left_Zygo_1_Ctrl', 'Left_Levator1_0_Ctrl', 'Left_Levator1_1_Ctrl', 'Left_Levator_0_Ctrl', 'Left_Levator_1_Ctrl', 'Left_Riso_0_Ctrl', 'Left_Riso_1_Ctrl', 'Left_CheekBone', 'Right_CheekBone', 'Right_Tongue_2', 'Right_Tongue_3', 'Right_Tongue_1', 'Left_Foot_FK_1', 'Left_Foot_Heel', 'Left_Foot_Reverse_0', 'Left_Foot_Reverse_1', 'Left_Foot_Reverse_2', 'Left_Leg_FK_1', 'Left_Leg_FK_0', 'Left_UpperEye_1_Ctrl', 'Left_UpperEye_2_Ctrl', 'Left_UpperEye_3_Ctrl', 'Left_LowerEye_0_Ctrl', 'Left_LowerEye_1_Ctrl', 'Left_LowerEye_2_Ctrl', 'Left_LowerEye_3_Ctrl', 'Right_EyeBrow_Global', 'Right_EyeBrow_in_1', 'Right_Brow_ridge_in', 'Right_Brow_ridge_out_1', 'Right_EyeBrow_out_1', 'Right_EyeBrow_in', 'Right_Brow_ridge_in_1', 'Right_EyeBrow_out', 'Right_Brow_ridge_out', 'Left_EyeBrow_Global', 'Left_EyeBrow_in_1']
    outFalseL = ['Bottom_Teeth_Global', 'Bottom_Teeth', 'Top_Teeth_Global', 'Top_Teeth', 'Right_Hand_ParamHolder_Main_Ctrl', 'Left_Foot_ParamHolder_Main_Ctrl', 'Right_Foot_ParamHolder_Main_Ctrl', 'Left_Hand_ParamHolder_Main_Ctrl', 'Left_Arm_Root', 'Right_Leg_Extra_0', 'Right_Arm_Extra_6', 'Right_Arm_Round_Root', 'Right_Arm_Root_Tangent', 'Right_Arm_End', 'Right_Arm_End_Tangent', 'Right_Arm_Elbow', 'Right_Arm_Round_0', 'Right_Arm_Round_1', 'Right_Arm_Extra_0', 'Right_Arm_Extra_1', 'Right_Arm_Extra_2', 'Right_Arm_Extra_3', 'Right_Arm_Extra_4', 'Right_Arm_Extra_5', 'Right_Leg_upV', 'Left_Arm_Extra_0', 'Left_Arm_Extra_1', 'Left_Arm_Extra_2', 'Left_Arm_Extra_3', 'Left_Arm_Extra_4', 'Left_Arm_Extra_5', 'Left_Arm_Extra_6', 'Left_Arm_Round_Root', 'Left_Arm_Round_Root_Tangent', 'Left_Arm_Round_Eff', 'Left_Arm_Round_Eff_Tangent', 'Left_Arm_Elbow', 'Left_Arm_Round_0', 'Left_Arm_Round_1', 'Left_Arm_IK', 'Left_Arm_upV', 'Left_Cheek', 'Left_Depressor_Handle_1_Control', 'Left_Depressor1_Handle_1_Control', 'Left_MouthCorner', 'Left_LowerLip_1_Ctrl', 'Left_LowerLip_2_Ctrl', 'Left_LowerLip_Inter', 'Left_UpperLip_1_Ctrl', 'Left_UpperLip_2_Ctrl', 'Left_UpperLip_Inter', 'Left_Leg_Extra_5', 'Left_Leg_Extra_6', 'Left_Leg_Round_Root', 'Left_Leg_Round_Root_Tangent', 'Left_Leg_Round_Eff', 'Left_Leg_Round_Eff_Tangent', 'Left_Leg_Knee', 'Left_Leg_Round_0', 'Left_Leg_Round_1', 'Left_Pant_Bottom_Global_Main_Ctrl', 'Left_Pant_Ext_Main_Ctrl', 'Left_Pant_Int_Main_Ctrl', 'Left_Pant_Front_Main_Ctrl', 'Left_Pant_Back_Main_Ctrl', 'Right_Leg_IK', 'Left_Brow_ridge_in', 'Left_Brow_ridge_out_1', 'Left_Brow_ridge_in_1', 'Left_Brow_ridge_out', 'Right_Collar_0_1_Bone_Ctrl', 'Right_Collar_0_2_Bone_Ctrl', 'Right_Arm_upV', 'Right_Arm_Root', 'Right_Arm_IK', 'Left_Collar_2_2_Bone_Ctrl', 'Left_Collar_1_0_Bone_Ctrl', 'Left_Collar_1_2_Bone_Ctrl', 'Back_Collar_1_Bone_Ctrl', 'Back_Collar_2_Bone_Ctrl', 'Left_UpperLid_Main_Ctrl', 'Left_Eyelid_Out', 'Left_Eyelid_In', 'Left_Eye_Target_Main_Ctrl', 'Left_Eye', 'Left_Eye_Pupille_Main_Ctrl', 'Right_Eye_Target_Main_Ctrl', 'Right_Eye', 'Right_Eye_Pupille_Main_Ctrl', 'Right_Leg_Root', 'Right_Base_Depressor', 'Right_Base_Levator1', 'Right_Base_Depressor1', 'Right_Base_Levator', 'Right_Depressor1_Handle_1_Control', 'Right_UpperLip_1_Ctrl', 'Right_UpperLip_2_Ctrl', 'Right_UpperLip_Inter', 'Right_MouthCorner', 'Right_LowerLip_1_Ctrl', 'Right_LowerLip_2_Ctrl', 'Right_LowerLip_Inter', 'Right_Depressor_Handle_1_Control', 'Left_Base_Levator', 'Left_Base_Depressor', 'Left_Base_Depressor1', 'Left_Base_Levator1', 'Left_Tongue_2', 'Left_Tongue_3', 'Left_Tongue_1', 'Left_Leg_Extra_0', 'Left_Leg_Extra_1', 'Left_Leg_Extra_2', 'Left_Leg_Extra_3', 'Left_Leg_Extra_4', 'Left_Leg_IK', 'Left_Leg_upV', 'Left_Leg_Root', 'Right_Leg_Extra_1', 'Right_Leg_Extra_2', 'Right_Leg_Extra_3', 'Right_Leg_Extra_4', 'Right_Leg_Extra_5', 'Right_Leg_Extra_6', 'Right_Leg_Round_Root', 'Right_Leg_Round_Root_Tangent', 'Right_Leg_Round_End', 'Right_Leg_Round_End_Tangent', 'Right_Leg_Knee', 'Right_Leg_Round_0', 'Right_Leg_Round_1', 'Right_Pant_Bottom_Global_Main_Ctrl', 'Right_Pant_Ext_Main_Ctrl', 'Right_Pant_Int_Main_Ctrl', 'Right_Pant_Front_Main_Ctrl', 'Right_Pant_Back_Main_Ctrl', 'Left_LowerLid_Main_Ctrl', 'Right_LowerLid_Main_Ctrl', 'Right_UpperLid_Main_Ctrl', 'Right_Eyelid_Out', 'Right_Eyelid_In', 'Right_Collar_1_0_Bone_Ctrl', 'Right_Collar_1_2_Bone_Ctrl', 'Right_Collar_2_1_Bone_Ctrl', 'Right_Collar_2_2_Bone_Ctrl', 'Left_Collar_0_1_Bone_Ctrl', 'Left_Collar_0_2_Bone_Ctrl', 'Left_Collar_2_1_Bone_Ctrl', 'Right_Eye_Bulge', 'Left_Ear_Bone_Ctrl', 'Left_Eye_Bulge']

    theAttr = "_OSCAR_Attributes.Mirror"
    for i in outTrueL:
        # print  i + theAttr
        if cmds.objExists( i + theAttr):
            print i,"set to TRUE"
            cmds.setAttr( i + theAttr,True)

    for i in outFalseL:
        if cmds.objExists( i + theAttr):
            cmds.setAttr( i + theAttr,False)
            print i,"set to FALSE"

    return [True,debugL]


def chr_fix_MouthCornerNeutralsRotation(*args,**kwargs):
    """ Description: Remet à zero la rotation des Mouth corners_neutral pose qui decale la symetrie de la bouche.
                     La rotation n'influant aucun autres objet du rig.
        Return : [True,LIST]
        Dependencies : cmds - 
    """
    print "chr_fixCornerNeutralsRotation()"

    debugL = []
    leftSide = 'TK_Left_MouthCorner_Locals_Root|TK_Left_MouthCorner_Locals_Main_Ctrl_NeutralPose'
    rightSide = 'TK_Right_MouthCorner_Locals_Root|TK_Right_MouthCorner_Locals_Main_Ctrl_NeutralPose'
    toFixL =  [leftSide, rightSide]
               
    attrL = ["rx","ry","rz"]
    for i in toFixL:
        print "  ",i
        for attr in attrL:
            if cmds.objExists(i):
                oldVal = cmds.getAttr(i + "." + attr)
                print "    ",attr, "=",oldVal
                if cmds.getAttr(i + "." + attr) not in [0]:
                    cmds.setAttr(i + "." + attr,0)
                    debugL.append(i+": Fixed")
                else:
                    debugL.append(i+": AllReady OK")
            else:
                print i,"doesn't exist!"
                debugL.append(i+": Doesn't exist")
    return [True,debugL] 


def chr_fix_EybrowUpper_ExtCorner_cst(*args, **kwargs):
    print "chr_fix_EybrowUpper_ExtCorner()"
    ctrAL =  ['Right_Brow_upRidge_04_offset_grp', 'Left_Brow_upRidge_04_offset_grp']
    ctrBL =  ['Left_Brow_upRidge_04_drive_grp','Right_Brow_upRidge_04_drive_grp',"Left_Brow_upRidge_04_drive_customAxis_grp"]
    ctrL=ctrAL + ctrBL

    canDo = True
    notFoundL = []
    fixedL=[]
    for i in ctrL:
        if not cmds.objExists(i):
            notFoundL.append(i)
    # if canDo:
    for i in ctrL:
        
        if cmds.objExists(i):
            print "-"*20,"* fixing",i
            # get cst
            allCstL = getTypeInHierarchy(cursel=i, theType="constraint")
            if allCstL:
                print "@",i,">>>>>ALL CST List=",allCstL
                for cst in allCstL:
                    for target in cmds.listAttr(cst + '.target[*]'):
                        if ".targetParentMatrix" in target:
                            # theParent = cmds.listConnections(cst + "."+target, d=False, s=True)[0]
                            # print "  *GOODparent=",theParent
                            plugL = getCstActiveWeightPlugs(cst) 
                            print "++ plugL=",len(plugL)

                                
                            for thePlug in plugL:   
                                print " thePlug=",thePlug,cmds.getAttr(thePlug)
                                theSource = cmds.listConnections(thePlug,s=1,d=0,p=1)[0]
                                if "Head_FK" in theSource:
                                        cmds.setAttr(theSource,1)
                                        print "    theSource=",theSource,cmds.getAttr(theSource)
                                    
                                else:


                                    
                                    cmds.setAttr(theSource,0)
                                    print "    theSource=",theSource,cmds.getAttr(theSource)
                                    fixedL.append(i+"."+theSource)
    
    print "notFoundL=", notFoundL
    print "fixedL=", fixedL



def chr_fix_cheeks_cst(*args, **kwargs):
    """ Description: Ajout un parent "fk_head" à la contrainte des cheeks_controls 
                     Ils deviennent contraint a 50% sur les corners mouth
        Return : [True,LIST]
        Dependencies : cmds - getTypeInHierarchy
    """
    
    print "chr_fix_EybrowUpper_ExtCorner()"
    ctrAL =  ['TK_Left_CheekCtrl_Root', 'TK_Right_CheekCtrl_Root']
    ctrBL =  []
    ctrL=ctrAL + ctrBL

    canDo = True
    notFoundL = []
    fixedL=[]
    for i in ctrL:
        if not cmds.objExists(i):
            notFoundL.append(i)
    if canDo:
        for i in ctrL:
            
            if cmds.objExists(i):
                print "-"*20,"* fixing",i
                # get cst
                allCstL = getTypeInHierarchy(cursel=i, theType="constraint")
                print ">>>>>",allCstL
                for cst in allCstL:
                    for target in cmds.listAttr(cst + '.target[*]'):
                        if ".targetParentMatrix" in target:
                            theParent = cmds.listConnections(cst + "."+target, d=False, s=True)[0]
                            #print "parent=",theParent
                            if not theParent in ["Head_FK","Head_FK_grp_offset_Pivot"]:
                                # add a new constraint
                                print "  ->add constraint"
                                cmds.parentConstraint("Head_FK",i,mo=1)
                                cmds.scaleConstraint("Head_FK",i,)


                                # connecting
                                # # create multiply node
                                # multiply_T_N = cmds.createNode("multiplyDivide", name=j + "Multiply_T_facto")
                                # # connect ty to multi
                                # cmds.connectAttr(tx_inCon , multiply_T_N + ".input1X", f=True)
                                # cmds.connectAttr(tx_inCon , multiply_T_N + ".input1Y", f=True)

                                # # connect multi to the plugs
                                # cmds.connectAttr(multiply_T_N + ".outputX", j + "." + thePlugA, f=True)
                                # cmds.connectAttr(multiply_T_N + ".outputY", j + "." + thePlugB, f=True)

                                # print "  *GOODparent=",theParent
                                # plugL = getCstActiveWeightPlugs(cst) 
                                # for thePlug in plugL:   
                                #     print " thePlug=",thePlug,cmds.getAttr(thePlug)
                                #     theSource = cmds.listConnections(thePlug,s=1,d=0,p=1)[0]
                                #     cmds.setAttr(theSource,1)
                                #     print "    theSource=",theSource,cmds.getAttr(theSource)
                                    
                            else:
                                print "  ->already ok"
                                # print "*BADparent=",theParent
                                # theSource = cmds.listConnections(thePlug,s=1,d=0,p=1)[0]
                                # cmds.setAttr(theSource,0)
                                # print "    theSource=",theSource,cmds.getAttr(theSource)
                                # fixedL.append(i+"."+theSource)
    
    print "notFoundL=", notFoundL
    print "fixedL=", fixedL


#to do: fixe scaling on the hands





