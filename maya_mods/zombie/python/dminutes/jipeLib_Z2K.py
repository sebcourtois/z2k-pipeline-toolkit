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


# general function 
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




# Z2K base general functions -----------------


def getBaseModPath(*args, **kwargs):
    """
    recupere le path de base des modules
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
    theDir = os.environ.get("ZOMB_ASSET_PATH")
    print "theDir=", theDir
    if os.path.isdir(theDir):
        assetL = sorted(os.listdir(theDir) )
        if not len(assetL):
            assetL=["Empty Folder"]
        
    else:
        assetL=["Invalide folder"]

    return assetL

# printer  -------------------------------------------------------
def printF( text="", st="main", toScrollF="", toFile = "", inc=False, GUI= True,
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
































