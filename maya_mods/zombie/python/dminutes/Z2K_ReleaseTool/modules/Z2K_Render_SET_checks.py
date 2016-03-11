#!/usr/bin/python
# -*- coding: utf-8 -*-
########################################################
# Name    : Z2K_Chr_Previz_checks
# Version : v010
# Description : Create previz maya file in .mb with some cleaning one the leadAsset
# Comment : BASE SCRIPT OUT OF Z2K in v002
# Author : Jean-Philippe Descoins
# Date : 2015-26-08
# Comment : 
# TO DO:
#       - Add debug file in input of th e class ; a reporter sur les check des autres
#       x add turttle check
#       x Handle versioning problems if edti it's incremented/ if readonly it's not (if edit and if not publish add please publish edited)
#       WIP mettage en lIB et nouveau path and names
#       - clean obj button have to be grayed if checkStructure not done (setSmoothness need good structure)
#       - add auto remove camera if is camera du pipe
#       - separate interface from base class
#       - Ckeck les path de texture, tout doit être ecris avec la variable d environement non resolved
#       - check geometry modeling history
#       WIP Clean ref Nodes + exception arnold etc
#       ? Check UV smoothing/display paremeters
#       x if set_subdiv_* exists - apply setSubdiv else delete setSubdiv() 
#                   from dminutes import assetconformation
#                   reload(assetconformation)
#                   assetconformation.setSubdiv()
#       x add isSetMeshCacheOK()
#       x add delete_setSubdiv()
#       x add check for BigDaddy et BigDaddy_NeutralPose and base CTR
#       x add BigDaddy check
#       x MentalRayCleanNodes (['mentalrayGlobals','mentalrayItemsList','miDefaultFramebuffer','miDefaultOptions'])
#       x check geometry all to zero
#       x BUG check colorLum
#       x delete mentalRayNode
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

# THIS CHECKER IS THE MOST UP TO DATE, USE IT tO IMPLEMENTS CHARS AND SETS CHECK AND FUTUR ANIM


import os,sys
import maya.cmds as cmds
import maya.mel as mel
from functools import partial
import inspect

import dminutes.jipeLib_Z2K as jpZ
reload(jpZ)
# import   constant
import dminutes.Z2K_ReleaseTool.modules as ini
reload(ini)
from dminutes.Z2K_ReleaseTool.modules import *


from dminutes import shading
reload(shading)

from dminutes import rendering
reload (rendering)

from dminutes import miscUtils
reload (miscUtils)

from dminutes import assetconformation
reload(assetconformation)


from dminutes import modeling
reload(modeling)



class checkModule(object):
    name = "AssetPreviz_Module"
    cf = name

    basePath = jpZ.getBaseModPath()
    ICONPATH = Z2K_ICONPATH + "Z2K_SET_LOGO_A1.bmp"
    upImg= basePath + ICONPATH


    def __init__(self, GUI=True, parent="", debugFile ="", *args, **kwargs):
        print "init"
        self.GUI=GUI
        self.parent = parent
        self.ebg = True
        self.DebugPrintFile = debugFile
        self.trueColor = self.colorLum( [0,0.75,0],-0.2 )
        self.falseColor =  self.colorLum(  [0.75,0,0] , -0.2)

        # trickage pour le batch mode goret
        print "GUI=",self.GUI
        if self.GUI in [False,0]:
            self.BpreClean=""
            self.BcheckStructure=""
            self.BCleanScene=""
            self.BCleanObjects=""
            self.BDebugBoardF=""
            self.BDebugBoard = ""
            self.BCleanAll=""
            self.BClearAll=""

        else:
            self.insertLayout(parent=self.parent)

        # decorating functions
        self.printF= self.Z2KprintDeco(jpZ.printF)
        
        # print scene NAME
        infoDict = jpZ.infosFromMayaScene()
        self.printF("ASSET_NAME: {0}  -Version: {1}    - Categorie: {2}".format( infoDict["assetName"],infoDict["version"], infoDict["assetCat"] ) , st="t")
        self.printF("running Z2K_render_SET_check", st="t")


    # decorators ---------------------------
    def Z2KprintDeco(self, func, *args, **kwargs):
        print "func=", func.__name__
        def deco(*args, **kwargs):
            # print u"Exécution de la fonction '%s'." % func.__name__
            func(toScrollF=self.BDebugBoard, toFile = self.DebugPrintFile, GUI=self.GUI, *args, **kwargs)
        return deco



    # ---------------------------------------------------------------------------------------------------------
    #--------------------- Buttons functions ----------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------------------
    @jpZ.waiter
    def btn_preClean(self, controlN="", *args, **kwargs):
        boolResult=True

        # set progress bar
        self.pBar_upd(step=1, maxValue=14, e=True)

        # steps

        # 1   remove Camera
        self.printF("shading:   remove Shading Camera", st="t")
        result,debugS = shading.referenceShadingCamera( remove=True, GUI = False)
        # prints -------------------
        self.printF(result, st="r")
        self.printF( debugS )
        # -------------------
        if not result:
            boolResult = False
        self.pBar_upd(step= 1,)



        # 2   remove light rigs
        self.printF("shading:   clean lgtRig", st="t")
        result, errorL, infoL = shading.cleanlgtRig(verbose = False)
        # prints -------------------

        self.printF(result, st="r")
        if infoL: 
            for each in infoL:
                self.printF( each )
        if errorL:
            for each in errorL:
                self.printF( each )
        # -------------------
        if not result:
            boolResult = False
        self.pBar_upd(step= 1,)


        # 3   clean file (remove file comparator refs (previz, anim, render....))
        self.printF("asset conformation: clean files ", st="t")
        r2a = assetconformation.Asset_File_Conformer()
        result,details = r2a.cleanFile()
        # prints -------------------
        self.printF(result, st="r")
        for each in details:
            self.printF( each )
        # --------------------------
        if not result:
            boolResult = False
        self.pBar_upd(step= 1,)


        # 4   delete aovs
        self.printF("rendering:   delete AOVs", st="t")
        result,details = rendering.deleteAovs()
        # prints -------------------
        self.printF(result, st="r")
        self.printF(details)
        # --------------------------
        if not result:
            boolResult = False
        self.pBar_upd(step= 1,)


        # 5   soft clean
        self.printF("asset conformation:   soft clean", st="t")
        result, logL = assetconformation.softClean(keepRenderLayers = False, struct2CleanList=["asset"])
        # prints -------------------
        self.printF(result, st="r")
        for each in logL:
            self.printF( each )
        # --------------------------
        if not result:
            boolResult = False
        self.pBar_upd(step= 1,)


        # 6   delete unused nodes
        self.printF("miscUtils: delete unknown nodes ", st="t")
        result,details = miscUtils.deleteUnknownNodes(GUI= False)
        # prints -------------------
        self.printF(result, st="r")
        for each in details:
            self.printF( each )
        # --------------------------
        if not result:
            boolResult = False
        self.pBar_upd(step= 1,)
        

        # 7   delete color sets
        self.printF("miscUtils: delete all color set ", st="t")
        result,details = miscUtils.deleteAllColorSet(GUI= False)
        # prints -------------------
        self.printF(result, st="r")
        for each in details:
            self.printF( each )
        # --------------------------
        if not result:
            boolResult = False
        self.pBar_upd(step= 1,)

        
        # 8   delete history
        self.printF("modeling: delete all geo history ", st="t")
        result,details = modeling.geoGroupDeleteHistory(GUI = False)
        # prints -------------------
        self.printF(result, st="r")
        for each in details:
            self.printF( each )
        # --------------------------
        if not result:
            boolResult = False
        self.pBar_upd(step= 1,)


        # 9   create subdiv sets
        self.printF("assetconformation: create subdiv sets ", st="t")
        resultD = assetconformation.createSubdivSets(GUI = False)
        # prints -------------------
        self.printF(resultD["returnB"], st="r")
        for each in resultD["logL"]:
            self.printF( each )
        # --------------------------
        if not resultD["returnB"]:
            boolResult = False
        self.pBar_upd(step= 1,)


        # 10   apply setSubdiv
        self.printF("assetconformation: apply setSubdiv ", st="t")
        resultD = assetconformation.setSubdiv(GUI = False)
        # prints -------------------
        self.printF(resultD["returnB"], st="r")
        for each in resultD["logL"]:
            self.printF( each )
        # --------------------------
        if not resultD["returnB"]:
            boolResult = False
        self.pBar_upd(step= 1,)


        # 11   assetGrpClean
        self.printF("assetconformation: clean asset group ", st="t")
        resultD = assetconformation.assetGrpClean( clean = True, GUI = False)
        # prints -------------------
        self.printF(resultD["returnB"], st="r")
        for each in resultD["logL"]:
            self.printF( each )
        # --------------------------
        if not resultD["returnB"]:
            boolResult = False
        self.pBar_upd(step= 1,)


        # 12   display layer update
        self.printF("modeling: display layer update", st="t")
        resultD = modeling.layerUpdate(inParent="asset|grp_geo", GUI = False, displayMode = 2)
        # prints -------------------
        self.printF(resultD["resultB"], st="r")
        for each in resultD["logL"]:
            self.printF( each )
        # --------------------------
        if not resultD["resultB"]:
            boolResult = False
        self.pBar_upd(step= 1,)   



        # 13   checks shaders naming convention
        self.printF("shading: checks shaders naming convention", st="t")
        resultD = shading.checkShaderName(shadEngineList = [],  GUI = False, checkOnly = True )
        # prints -------------------
        self.printF(resultD["resultB"], st="r")
        for each in resultD["logL"]:
            self.printF( each )
        # --------------------------
        if not resultD["resultB"]:
            boolResult = False
        self.pBar_upd(step= 1,)


        # 14   set shading masks"
        self.printF("assetconformation: set shading masks", st="t")
        resultD = assetconformation.setShadingMask(selectFailingNodes = False, gui = False)
        # prints -------------------
        self.printF(resultD["resultB"], st="r")
        for each in resultD["logL"]:
            self.printF( each )
        # --------------------------
        if not resultD["resultB"]:
            boolResult = False
        self.pBar_upd(step= 1,)     



        # colors
        print "*btn_preClean:",boolResult
        self.colorBoolControl(controlL=[controlN], boolL=[boolResult], labelL=[""], )
        
        return boolResult

    @jpZ.waiter
    def btn_checkStructure(self, controlN="", *args, **kwargs):
        boolResult=True

        # set progress bar
        self.pBar_upd(step=1, maxValue=3, e=True)

        # steps

        # 1   checkBaseStructure()
        result,debugD = jpZ.checkBaseStructure()
        # prints -------------------
        self.printF("checkBaseStructure()", st="t")
        self.printF(result, st="r")
        for i,dico in debugD.iteritems():
            toPrint=""
            if not dico["result"] in ["OK"]:
                toPrintA = "BAD"
                if len(dico.get("Found",""))>0:
                    toPrintA = "     -Found= " + str( dico.get("Found","")   )
                if len(dico.get("NOT_Found",""))>0:
                    toPrintA = "     -NOT_Found= " + str( dico.get("NOT_Found","")   )

                toPrint = i.ljust(15)+": "+ str( dico["result"]+toPrintA)
            else:
                toPrint = i.ljust(15)+": "+ str( dico["result"] )
            self.printF( toPrint )
        # -------------------
        if not result:
            boolResult = False
        self.pBar_upd(step= 1,)


        # 2   checkAssetStructure()
        result,debugD = jpZ.checkAssetStructure(assetgpN="asset", expectedL=["grp_rig","grp_geo"],
        additionalL=["grp_placeHolders"])
        # prints -------------------
        self.printF("checkAssetStructure()", st="t")
        self.printF(result, st="r")
        for i,dico in debugD.iteritems():
            self.printF( i.ljust(10)+" : "+ str( dico["result"] ) )
            if len(dico.get("Found",""))>0:
                self.printF("     -Found= " + str( dico.get("Found","")   ) )
        # --------------------------
        if not result:
            boolResult = False
        self.pBar_upd(step= 1,)



        # 3   isSet_meshCache_OK()
        result,details = jpZ.isSet_meshCache_OK (theType="setPreviz")
        # prints -------------------
        self.printF("isSetMeshCacheOK()", st="t")
        self.printF(result, st="r")
        self.printF(details)
        # --------------------------
        if not result:
            boolResult = False
        self.pBar_upd(step= 1,)



        # colors
        print "*btn_checkStructure:",boolResult
        self.colorBoolControl(controlL=[controlN], boolL=[boolResult], labelL=[""], )
        
        return boolResult

    @jpZ.waiter
    def btn_CleanScene(self, controlN="", *args, **kwargs):
        boolResult=True

        # set progress bar
        self.pBar_upd(step=1, maxValue=9, e=True)

        # steps



        # 1 Apply_Delete_setSubdiv()
        result,setSub,deletedL = jpZ.Apply_Delete_setSubdiv()
        # prints -------------------
        self.printF("Apply_Delete_setSubdiv()", st="t")
        self.printF(result, st="r")
        self.printF("Set Subdiv applyed: {0}".format(setSub) )
        if len(deletedL):
            self.printF("deleted: {0} - {1}".format(len(deletedL),deletedL ) )
        # --------------------------
        if not result:
            boolResult = False
        self.pBar_upd(step= 1,)



        # 2 cleanRefNodes()
        result,objtoDeleteL,deletedL = jpZ.cleanRefNodes()
        # prints -------------------
        self.printF("cleanRefNodes()", st="t")
        self.printF(result, st="r")
        self.printF( "objectDeleted={0}/{1}".format( len(objtoDeleteL),len(deletedL)  ) )
        # --------
        if not result:
            boolResult = False
        self.pBar_upd(step= 1,)


 
        # 3 cleanMentalRayNodes()
        result,toDeleteL,deletedL,failL = jpZ.cleanMentalRayNodes()
        # prints -------------------
        self.printF("cleanMentalRayNodes()", st="t")
        self.printF(result, st="r")
        self.printF( "objectDeleted={0}/{1}".format( len(deletedL),len(toDeleteL)  ) )
        for i in deletedL:
            self.printF("- deleted: {0}".format(i))

        if len(failL):
            self.printF( "failL= {0}".format( failL  ) )
        # --------------------------
        if not result:
            boolResult = False
        self.pBar_upd(step= 1,)


        # 4 remove_All_NS()
        result= jpZ.remove_All_NS(NSexclusionL=[""], limit=100)[0]
        # prints -------------------
        self.printF("remove_All_NS()", st="t")
        self.printF(result, st="r")
        # --------------------------
        if not result:
            boolResult = False
        self.pBar_upd(step= 1,)



        # # 5 cleanDisplayLayerWithSet()
        # result,debugL = jpZ.cleanDisplayLayerWithSet(setL=["set_meshCache","set_control"],layerL=["geometry","control"])
        # # prints -------------------
        # self.printF("cleanDisplayLayerWithSet()", st="t")
        # self.printF(result, st="r")
        # for i in debugL:
        #     self.printF(i)
        # # --------------------------
        # if not result :
        #     boolResult = False
        # self.pBar_upd(step= 1,)



        # 6 cleanUnUsedAnimCurves()
        result,debugD = jpZ.cleanUnUsedAnimCurves( )
        # prints -------------------
        self.printF( "cleanUnUsedAnimCurves()", st="t")
        # prints inside-------------------
        self.printF(result, st="r")
        if len(debugD["errorL"]):
            self.printF("erroredL:")
            for i in debugD["errorL"] :
                self.printF("    -{0} error".format(i))
        self.printF("total errored = {0}".format( len(debugD["errorL"] ) ) )
        
        if len(debugD["deletedL"]):
            self.printF("deletedL:")
            for i in debugD["deletedL"]:
                self.printF("    -{0} deleted".format(i))
        self.printF("total deleted = {0}".format(len(debugD["deletedL"]) ) )
        # --------------------------
        # --------------------------
        if not result:
            boolResult = False
        self.pBar_upd(step= 1,)



        # 7 cleanUnusedConstraint()
        result,debugD = jpZ.cleanUnusedConstraint()
        # prints -------------------
        self.printF( "cleanUnusedConstraint()", st="t")
       # prints inside-------------------
        self.printF(result, st="r")
        if len(debugD["errorL"]):
            self.printF("erroredL:")
            for i in debugD["errorL"] :
                self.printF("    -{0} error".format(i))
        self.printF("total errored = {0}".format( len(debugD["errorL"] ) ) )
        
        if len(debugD["deletedL"]):
            self.printF("deletedL:")
            for i in debugD["deletedL"]:
                self.printF("    -{0} deleted".format(i))
        self.printF("total deleted = {0}".format(len(debugD["deletedL"]) ) )
        # --------------------------
        # --------------------------
        if not result:
            boolResult = False 
        self.pBar_upd(step= 1,)



        # 8 CleanDisconnectedNodes()
        result,debugD = jpZ.CleanDisconnectedNodes()
        # prints -------------------
        self.printF( "CleanDisconnectedNodes()", st="t")
        # prints inside-------------------
        self.printF(result, st="r")
        if len(debugD["errorL"]):
            self.printF("erroredL:")
            for i in debugD["errorL"] :
                self.printF("    -{0} error".format(i))
        self.printF("total errored = {0}".format( len(debugD["errorL"] ) ) )
        
        if len(debugD["deletedL"]):
            self.printF("deletedL:")
            for i in debugD["deletedL"]:
                self.printF("    -{0} deleted".format(i))
        self.printF("total deleted = {0}".format(len(debugD["deletedL"]) ) )
        # --------------------------
        # --------------------------
        if not result:
            boolResult = False 
        self.pBar_upd(step= 1,)
              


        # 9 cleanTurtleNodes
        result,toDeleteL,deletedL,failL = jpZ.cleanTurtleNodes()
        # prints -------------------
        self.printF("cleanTurtleNodes()", st="t")
        self.printF(result, st="r")
        self.printF( "objectDeleted={0}/{1}".format( len(deletedL),len(toDeleteL)  ) )
        for i in deletedL:
            self.printF("- deleted: {0}".format(i))

        if len(failL):
            self.printF( "failL= {0}".format( failL  ) )
        # --------------------------
        if not result:
            boolResult = False
        self.pBar_upd(step= 1,)



        # colors
        print "*btn_CleanScene:",boolResult
        self.colorBoolControl(controlL=[controlN], boolL=[boolResult], labelL=[""], )
        
        return boolResult
        
    @jpZ.waiter
    def btn_CleanObjects(self, controlN="", *args, **kwargs):
        boolResult=True

        # set progress bar
        self.pBar_upd(step=1, maxValue=6, e=True)

        meshCacheObjL = jpZ.getSetContent(inSetL=["set_meshCache"] ) 
        geoTransformList,instanceTransformL = miscUtils.getAllTransfomMeshes("asset|grp_geo")
        allTransL = geoTransformList+instanceTransformL
        controlObjL = jpZ.getSetContent(inSetL=["set_control"] )

        # steps


        # # 1 isSkinned (meshCacheObjL)
        # result,outSkinClusterL,noSkinL = jpZ.isSkinned(inObjL= meshCacheObjL,)
        # # prints -------------------
        # self.printF("isSkinned()", st="t")
        # self.printF(not result, st="r")
        # self.printF("skinned_object = {0} / {1}".format(len(outSkinClusterL),len(meshCacheObjL) ) )
        # for i in noSkinL:
        #     self.printF("    No skin on: {0}".format(i) )
        # # --------------------------
        # if  result :
        #     boolResult = False
        # self.pBar_upd(step= 1,)



        # # 2 cleanUnusedInfluence (meshCacheObjL)
        # result,totalSkinClusterL,deletedDict = jpZ.cleanUnusedInfluence(inObjL=meshCacheObjL)
        # # prints -------------------
        # self.printF("cleanUnusedInfluance()", st="t")
        # self.printF(result, st="r")
        # self.printF ( "total cleaned skinCluster: {0}/{1}".format( len(deletedDict), len(totalSkinClusterL) ) )
        # for i,j in deletedDict.iteritems():
        #     self.printF ( "influance Deleted on {0}: {1}".format( i.ljust(15),j ) )
        # # --------------------------
        # if not result :
        #     boolResult = False
        # self.pBar_upd(step= 1,)



        # # 3 setSmoothness (meshCacheObjL)
        # result,debugD = jpZ.setSmoothness(inObjL=allTransL, mode=0)
        # # prints -------------------
        # self.printF("setSmoothness()", st="t")
        # self.printF(result, st="r")
        # self.printF ( " error on: {0}/{1}".format( len(debugD.keys()),len(allTransL) ) )
        # for i,j in debugD.iteritems():
        #     self.printF ( "     - {0}: {1}".format( i.ljust(15),j ) )
        # # --------------------------
        # if not result :
        #     boolResult = False
        # self.pBar_upd(step= 1,)



        # # 4 disableShapeOverrides (allTransL)
        # result,debugD = jpZ.disableShapeOverrides(inObjL=allTransL)
        # # prints -------------------
        # self.printF("disableShapeOverrides()", st="t")
        # self.printF(result, st="r")
        # self.printF ( " error on: {0}/{1}".format( len(debugD.keys()),len(allTransL), ) )
        # for i,j in debugD.iteritems():
        #     self.printF ( "     - {0}: {1}".format( i.ljust(15),j ) )
        # # --------------------------
        # if not result:
        #     boolResult = False
        # self.pBar_upd(step= 1,)



        # 5 checkSRT (geoTransformList)
        result,debugD = jpZ.checkSRT(inObjL = geoTransformList, )
        # prints -------------------
        self.printF("checkSRT()", st="t")
        self.printF(result, st="r")
        self.printF ( " not zero total: {0}/{1}".format( len(debugD.keys()),len(geoTransformList), ) )
        for i,j in debugD.iteritems():
            self.printF ( "    - {0} : {1}".format( i.ljust(15), " ".join(j) ) )
        # --------------------------
        if not result:
            boolResult = False
        self.pBar_upd(step= 1,)



        # 6 cleanKeys (controlObjL)
        result,cleanedL,debugD = jpZ.cleanKeys(inObjL=controlObjL,verbose=True)
        if not result:
            # prints -------------------
            self.printF("cleanKeys()", st="t")
            self.printF(result, st="r")
            self.printF ( " Cleaned : {0}/{1}".format( len(cleanedL),len(controlObjL), ) )
            self.printF ( " error on: {0}/{1}".format( len(debugD.keys()),len(controlObjL), ) )
            for i,j in debugD.iteritems():
                self.printF ( "     - {0}: {1}".format( i.ljust(15),j.values() ) )
            # --------------------------
            boolResult = False
        self.pBar_upd(step= 1,)



        # 7 checkKeys (controlObjL)
        result,debugD = jpZ.checkKeys(inObjL=controlObjL,verbose=True)
        # prints -------------------
        self.printF("checkKeys()", st="t")
        self.printF(result, st="r")
        self.printF ( " error on: {0}/{1}".format( len(debugD.keys()),len(controlObjL), ) )
        for i,j in debugD.iteritems():
            self.printF ( "     - {0}: {1}".format( i.ljust(15),j.keys() ) )
        # --------------------------
        if not result :
            boolResult = False
        self.pBar_upd(step= 1,)



        # 8 resetSRT (controlObjL)
        result,debugD = jpZ.resetSRT(inObjL=controlObjL)
        # prints -------------------
        self.printF("resetSRT()", st="t")
        self.printF(result, st="r")
        self.printF ( " Reseted : {0}/{1}".format( len(debugD["resetedL"]),len(controlObjL), ) )
        self.printF ( " error on: {0}/{1}".format( len(debugD["errors"]),len(controlObjL), ) )
        for j in debugD["errors"]:
            self.printF ( "     on : {0}".format( j.ljust(15) ) )
        # --------------------------
        if not result :
            boolResult = False
        self.pBar_upd(step= 1,)


        # 9 checkSRT (controlObjL)
        if not jpZ.checkSRT(inObjL =controlObjL, verbose=True)[0] :
            boolResult = False
        self.pBar_upd(step= 1,)

        # colors
        print "*btn_CleanObjects:",boolResult
        self.colorBoolControl(controlL=[controlN], boolL=[boolResult], labelL=[""], )

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


    def btn_cleanAll(self,  *args, **kwargs):
        print "btn_cleanAll()"
        

        boolResult = True
        if not self.btn_preClean(controlN=self.BpreClean, ):
            boolResult = False
        if not self.btn_checkStructure(controlN=self.BcheckStructure, ):
            boolResult = False
        print "*1",boolResult
        if not self.btn_CleanScene(controlN=self.BCleanScene, ):
            boolResult = False
        print "*2",boolResult
        if not self.btn_CleanObjects(controlN=self.BCleanObjects, ):
            boolResult = False
        
        # colors
        print "*3",boolResult
        self.colorBoolControl(controlL=[self.BCleanAll], boolL=[boolResult], labelL=[""],)
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
    def colorBoolControl(self, controlL=[], boolL=[],labelL=[""],  *args, **kwargs):
        # color the controlL depending on the given Bool
        if self.GUI:
            
            for i,j,label in zip(controlL,boolL,labelL):
                    if j in [True,1]:
                        cmds.button(i, e=1, backgroundColor=self.trueColor, ebg=self.ebg)
                    else:
                        cmds.button(i, e=1, backgroundColor=self.falseColor, ebg=self.ebg)


    def pBar_upd (self, step=0,maxValue=10,e=False, *args, **kwargs):
        # print "pBar_upd()",step
        if self.GUI:
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
        self.BCleanAll = cmds.button("CLEAN-CHECK ALL",c= partial(self.btn_cleanAll),en=1)

        self.BpreClean = cmds.button("pre-Clean",)
        cmds.button(self.BpreClean,e=1,c= partial( self.btn_preClean,self.BpreClean))

        self.BcheckStructure = cmds.button("checkStructure", )
        cmds.button(self.BcheckStructure,e=1,c= partial( self.btn_checkStructure,self.BcheckStructure) )

        self.BCleanScene = cmds.button("CleanScene",)
        cmds.button(self.BCleanScene,e=1,c= partial( self.btn_CleanScene,self.BCleanScene))

        self.BCleanObjects = cmds.button("CleanObjects",)
        cmds.button(self.BCleanObjects,e=1,c= partial( self.btn_CleanObjects,self.BCleanObjects) )
        
        self.BValidationPBar = cmds.progressBar(maxValue=3,s=1 )

        self.BDebugBoardF= cmds.frameLayout("DebugBoard",cll=True,cl=True)
        self.BDebugBoard = cmds.scrollField(w=250,h=300,)
        
        cmds.setParent("..")
        self.BClearAll = cmds.button("clear",c= self.btn_clearAll,)
  
        

#----------------------------------------------------------------------------------------------------------
#--------------------- EXEC -------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------

# Z2K_Pcheck = checkModule(GUI=True )
# Z2K_Pcheck.insertLayout( parent="" )