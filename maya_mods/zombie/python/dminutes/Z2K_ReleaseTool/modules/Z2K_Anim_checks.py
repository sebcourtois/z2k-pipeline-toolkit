#!/usr/bin/python
# -*- coding: utf-8 -*-
########################################################
# Name    : Z2K_Chr_Previz_checks
# Version : v010
# Description : Create previz maya file in .mb with some cleaning one the leadAsset
# Comment : BASE SCRIPT OUT OF Z2K in v002
# Author : Jean-Philippe Descoins
# Date : 2015-26-08
# Comment : wip
# TO DO:
#       - add set all dynamic OFF
#       x connect shape visibility to a control -> btn_specialSettings
#       x Add debug file in input of th e class ; a reporter sur les check des autres
#       x add turttle check
#       x Handle versioning problems if edti it's incremented/ if readonly it's not (if edit and if not publish add please publish edited)
#       WIP mettage en lIB et nouveau path and names
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


from dminutes import miscUtils

reload (miscUtils)

from dminutes import assetconformation
reload(assetconformation)




class checkModule(object):
    name = "AssetPreviz_Module"
    cf = name

    basePath = jpZ.getBaseModPath()
    ICONPATH = Z2K_ICONPATH + "Z2K_ANIM_LOGO_A3.bmp"
    upImg= basePath + ICONPATH


    def __init__(self, GUI=True, parent="", debugFile ="", *args, **kwargs):
        print "init"
        self.GUI=GUI
        self.parent = parent
        self.ebg = True
        self.DebugPrintFile = debugFile
        self.trueColor = self.colorLum( [0,0.75,0],-0.2 )
        self.falseColor =  self.colorLum(  [0.75,0,0] , -0.2)
        self.warnColor = self.colorLum(  [1,0.7,0] , -0.0)
        # trickage pour le batch mode goret
        print "GUI=",self.GUI
        if self.GUI in [False,0]:
            self.BcheckStructure=""
            self.BCleanScene=""
            self.BCleanObjects=""
            self.BSpecialSettings =""
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
    def btn_checkStructure(self, controlN="", *args, **kwargs):
        boolResult=True
        boolResultL = []
        warnB = False
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
            boolResultL.append(boolResult)
        self.pBar_upd(step= 1,)


        # 2   checkAssetStructure()
        result,debugD = jpZ.checkAssetStructure(assetgpN="asset", expectedL=["grp_rig","grp_geo"],
        additionalL=["grp_placeHolders","grp_light"])
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
            boolResultL.append(boolResult)
        self.pBar_upd(step= 1,)



        # 3   isSet_meshCache_OK()
        result,details = jpZ.isSet_meshCache_OK ()
        # prints -------------------
        self.printF("isSetMeshCacheOK()", st="t")
        self.printF(result, st="r")
        self.printF(details)
        # --------------------------
        if not result:
            boolResult = False
            boolResultL.append(boolResult)
        self.pBar_upd(step= 1,)


        # 4   isHiddenObjInSet()
        result,details = jpZ.isHiddenObjInSet (theSet="set_meshCache")
        # prints -------------------
        self.printF("isHiddenObjInSet(set_meshCache)", st="t")
        self.printF(result, st="r")
        for i in details:
            self.printF("-" + i)
        # --------------------------
        if not result:
            boolResult = False
            warnB = True
        self.pBar_upd(step= 1,)
        
        if boolResultL.count(False)>0:
            warnB=False


        # colors
        print "*btn_checkStructure:",boolResult,
        self.colorBoolControl(controlL=[controlN], boolL=[boolResult], labelL=[""], warning=warnB )
        
        return boolResult

    @jpZ.waiter
    def btn_CleanScene(self, controlN="", *args, **kwargs):
        boolResult=True
        boolResultL = []
        warnB=False
        # set progress bar
        self.pBar_upd(step=1, maxValue=10, e=True)

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



        # 5 cleanDisplayLayerWithSet()
        result,debugL = jpZ.cleanDisplayLayerWithSet(setL=["set_meshCache","set_control"],layerL=["geometry","control"])
        # prints -------------------
        self.printF("cleanDisplayLayerWithSet()", st="t")
        self.printF(result, st="r")
        for i in debugL:
            self.printF(i)
        # --------------------------
        if not result :
            boolResult = False
        self.pBar_upd(step= 1,)



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

        # 10 ----- chr_delete_BS_active_group ()
        result,debugL = jpZ.chr_delete_BS_active_group()
        # prints -------------------
        self.printF("chr_delete_BS_active_group()", st="t")
        self.printF(result, st="r")
        self.printF(debugL)
        # --------------------------
        # --------------------------
        if not result :
            boolResult = False
        self.pBar_upd(step= 1,) 
        

        




        # colors
        print "*btn_CleanScene:",boolResult
        self.colorBoolControl(controlL=[controlN], boolL=[boolResult], labelL=[""],warning=warnB )
        
        return boolResult
        
    @jpZ.waiter
    def btn_CleanObjects(self, controlN="", *args, **kwargs):
        boolResult=True

        # set progress bar
        self.pBar_upd(step=1, maxValue=9, e=True)

        meshCacheObjL = jpZ.getSetContent(inSetL=["set_meshCache"] )
        controlObjL = jpZ.getSetContent(inSetL=["set_control"] )

        # steps



        # 1 isSkinned (meshCacheObjL)
        result,outSkinClusterL,noSkinL = jpZ.isSkinned(inObjL= meshCacheObjL,)
        # prints -------------------
        self.printF("isSkinned()", st="t")
        self.printF(result, st="r")
        self.printF("skinned_object = {0} / {1}".format(len(outSkinClusterL),len(meshCacheObjL) ) )
        for i in noSkinL:
            self.printF("    No skin on: {0}".format(i) )
        # --------------------------
        if not result :
            boolResult = False
        self.pBar_upd(step= 1,)



        # 2 cleanUnusedInfluence (meshCacheObjL)
        result,totalSkinClusterL,deletedDict = jpZ.cleanUnusedInfluence(inObjL=meshCacheObjL)
        # prints -------------------
        self.printF("cleanUnusedInfluance()", st="t")
        self.printF(result, st="r")
        self.printF ( "total cleaned skinCluster: {0}/{1}".format( len(deletedDict), len(totalSkinClusterL) ) )
        for i,j in deletedDict.iteritems():
            self.printF ( "{2} influances Deleted on {0}: {1}".format( i.ljust(15), j, str(len(j) ).zfill(2) ) )
        # --------------------------
        if not result :
            boolResult = False
        self.pBar_upd(step= 1,)



        # 3 setSmoothness (meshCacheObjL)
        result,debugD = jpZ.setSmoothness(inObjL=meshCacheObjL, mode=0)
        # prints -------------------
        self.printF("setSmoothness()", st="t")
        self.printF(result, st="r")
        self.printF ( " error on: {0}/{1}".format( len(debugD.keys()),len(meshCacheObjL) ) )
        for i,j in debugD.iteritems():
            self.printF ( "     - {0}: {1}".format( i.ljust(15),j ) )
        # --------------------------
        if not result :
            boolResult = False
        self.pBar_upd(step= 1,)



        # 4 disableShapeOverrides (meshCacheObjL)
        result,debugD = jpZ.disableShapeOverrides(inObjL=meshCacheObjL)
        # prints -------------------
        self.printF("disableShapeOverrides()", st="t")
        self.printF(result, st="r")
        self.printF ( " error on: {0}/{1}".format( len(debugD.keys()),len(meshCacheObjL), ) )
        for i,j in debugD.iteritems():
            self.printF ( "     - {0}: {1}".format( i.ljust(15),j ) )
        # --------------------------
        if not result:
            boolResult = False
        self.pBar_upd(step= 1,)



        # 5 checkSRT (meshCacheObjL)
        result,debugD = jpZ.checkSRT(inObjL = meshCacheObjL, )
        # prints -------------------
        self.printF("checkSRT()", st="t")
        self.printF(result, st="r")
        self.printF ( " not zero total: {0}/{1}".format( len(debugD.keys()),len(meshCacheObjL), ) )
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



        # 8 resetCTR (controlObjL)
        result,debugD = jpZ.resetCTR(inObjL=controlObjL, userDefined=True, SRT=True)
        # prints -------------------
        self.printF("resetCTR()", st="t")
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

    @jpZ.waiter
    def btn_specialSettings(self, controlN="", *args, **kwargs):
        print "btn_specialSettings()"
        boolResult=True

        # set progress bar
        self.pBar_upd(step=1, maxValue=19, e=True)


        # 1 connectVisibility ()
        self.printF("connectVisibility()", st="t")
        result,debugS = jpZ.connectVisibility()
        # prints -------------------
        self.printF(result, st="r")
        # --------------------------
        if not result :
            boolResult = False
        self.pBar_upd(step= 1,) 


        # 2 ----- fixTKFacialRig_EyeBrow_Middle ()
        self.printF("fixTKFacialRig_EyeBrow_Middle()", st="t")
        result,debugL = jpZ.chr_fixTKFacialRig_EyeBrow_Middle()
        # prints -------------------
        self.printF(result, st="r")
        for i in debugL:
            self.printF(i)
        # --------------------------
        # --------------------------
        if not result :
            boolResult = False
        self.pBar_upd(step= 1,) 


        # 3 ----- fixTKFacialRig_EyeBrow_Middle ()
        self.printF("chr_facialUnlockSRT()", st="t")
        result,debugL = jpZ.chr_UnlockForgottenSRT()
        # prints -------------------
        self.printF(result, st="r")
        self.printF( "total updated= ".format(len(debugL) ) )
        # --------------------------
        # --------------------------
        if not result :
            boolResult = False
        self.pBar_upd(step= 1,) 

        # 4 ----- fixTKFacialRig_EyeBrow_Middle ()
        self.printF("set_grp_geo_SmoothLevel()", st="t")
        result,debugL = jpZ.set_grp_geo_SmoothLevel()
        # prints -------------------
        self.printF(result, st="r")
        # --------------------------
        # --------------------------
        if not result :
            boolResult = False
        self.pBar_upd(step= 1,) 

        
        # 5 ----- chr_rename_Teeth_BS_attribs ()
        self.printF("chr_rename_Teeth_BS_attribs()", st="t")
        result,debugL = jpZ.chr_rename_Teeth_BS_attribs()
        # prints -------------------
        self.printF(result, st="r")
        for debug in debugL:
            self.printF(debug)
        # --------------------------
        # --------------------------
        if not result :
            boolResult = False
        self.pBar_upd(step= 1,)



        # 6 ----- chr_TeethFix ()
        resultL,debugL = jpZ.chr_TeethFix()
        self.printF("chr_TeethFix()", st="t")
        # prints -------------------
        self.printF(result, st="r")
        for debug in debugL:
            self.printF(debug)
        # --------------------------
        # --------------------------
        if False in[resultL] :
            boolResult = False
        self.pBar_upd(step= 1,)

    
        # 7 ----- chr_chinEarsFix ()
        self.printF("chr_chinEarsFix()", st="t")
        resultL,debugL = jpZ.chr_chinEarsFix()
        # prints -------------------
        self.printF(result, st="r")
        for debug in debugL:
            self.printF(debug)
        # --------------------------
        # --------------------------
        if False in [resultL] :
            boolResult = False
        self.pBar_upd(step= 1,)

        # 8 ----- chr_changeCtrDisplays ()
        self.printF("chr_changeCtrDisplays()", st="t")
        result,debugL = jpZ.chr_changeCtrDisplays()
        # prints -------------------
        self.printF(result, st="r")
        for debug in debugL:
            self.printF(debug)
        # --------------------------
        # --------------------------
        if not result :
            boolResult = False
        self.pBar_upd(step= 1,)
        

        # # 09 neck bulge factor to zero
        self.printF("chr_neckBulge_Factor_to_zero()", st="t")
        result = jpZ.chr_neckBulge_Factor_to_zero()
        # prints -------------------
        self.printF(result, st="r")
        
        # --------------------------
        # --------------------------
        if not result :
            boolResult = False
        self.pBar_upd(step= 1,)



        # 10 ----- chr_TongueFix () COULD BE BETTER
        self.printF("chr_TongueFix()", st="t")
        result,debugL = jpZ.chr_TongueFix()
        # prints -------------------
        self.printF(result, st="r")
        for debug in debugL:
            self.printF(debug)
        # --------------------------
        # --------------------------
        if not result :
            boolResult = False
        self.pBar_upd(step= 1,)



        # 11 ----- chr_fixeLatticeParams () 
        self.printF("chr_fixeLatticeParams()", st="t")
        result,debugL = jpZ.chr_fixeLatticeParams()
        # prints -------------------
        self.printF(result, st="r")
        for debug in debugL:
            self.printF(debug)
        # --------------------------
        # --------------------------
        if not result :
            boolResult = False
        self.pBar_upd(step= 1,)



        # 12 ----- chr_hideCurveAiAttr () 
        self.printF("chr_hideCurveAiAttr()", st="t")
        result,debugL = jpZ.chr_hideCurveAiAttr()
        # prints -------------------
        self.printF(result, st="r")
        self.printF("-cleaned_Ctr = {0}".format(debugL))
        # --------------------------
        # --------------------------
        if not result :
            boolResult = False
        self.pBar_upd(step= 1,)




        # 13 ----- chr_clean_set_control_bad_members ()
        result,debugL = jpZ.chr_clean_set_control_bad_members()
        # prints -------------------
        self.printF("chr_clean_set_control_bad_members()", st="t")
        self.printF(result, st="r")
        if len(debugL):
            for i in debugL:
                self.printF("    -"+i+" removed from set_control")
        # --------------------------
        # --------------------------
        if not result :
            boolResult = False
        self.pBar_upd(step= 1,) 


        
        # 14 ----- chr_replace_chr_vis_Exp_System () 
        self.printF("chr_replace_chr_vis_Exp_System()", st="t")
        result,debug = jpZ.chr_replace_chr_vis_Exp_System()
        # prints -------------------
        self.printF(result, st="r")
        self.printF("-"+str(debug)+ " expressions replaced")
        # --------------------------
        # --------------------------
        if not result :
            boolResult = False
        self.pBar_upd(step= 1,)



         # 15 ----- chr_reArrangeCtr_displayLevel () 
        self.printF("chr_reArrangeCtr_displayLevel()", st="t")
        result,debug = jpZ.chr_reArrangeCtr_displayLevel()
        # prints -------------------
        self.printF(result, st="r")
        # --------------------------
        # --------------------------
        if not result :
            boolResult = False
        self.pBar_upd(step= 1,)
        

        # 16 chr_setVis_Params (chr_setVis_Params)
        if not jpZ.chr_setVis_Params()[0] :
            boolResult = False
        self.pBar_upd(step= 1,)


        # je ne veux plus importer les lights dans les refs de persos a cause de crash lors de rendu arnold
        # OK
        # 17   import light rig"
        # self.printF("assetconformation: import light rig", st="t")
        # resultD = assetconformation.importGrpLgt(lgtRig = "lgtRig_character", gui=False, hideLgt = True)
        # # prints -------------------
        # self.printF(resultD["resultB"], st="r")
        # for each in resultD["logL"]:
        #     self.printF( each )
        # # --------------------------
        # if not resultD["resultB"]:
        #     boolResult = False
        # self.pBar_upd(step= 1,)



        # 17 ----- chr_Fix_LookAt () 
        self.printF("chr_Fix_LookAt()", st="t")
        result,debugL = jpZ.chr_Fix_LookAt()
        # prints -------------------
        self.printF(result, st="r")
        if debugL:
            for i in debugL:
                self.printF("  -",i)
        # --------------------------
        # --------------------------
        if not result :
            boolResult = False
        self.pBar_upd(step= 1,)
        

        # 18 ----- chr_fix_mirror_parameters () 
        self.printF("chr_fix_mirror_parameters()", st="t")
        result,debugL = jpZ.chr_fix_mirror_parameters()
        # prints -------------------
        self.printF(result, st="r")
        if debugL:
            for i in debugL:
                self.printF("  -",i)
        # --------------------------
        # --------------------------
        if not result :
            boolResult = False
        self.pBar_upd(step= 1,)


        # 19 ----- chr_fixCornerNeutralsRotation () 
        self.printF("chr_fixCornerNeutralsRotation()", st="t")
        result,debugL = jpZ.chr_fixCornerNeutralsRotation()
        # prints -------------------
        self.printF(result, st="r")
        if debugL:
            for i in debugL:
                self.printF("  -",i)
        # --------------------------
        # --------------------------
        if not result :
            boolResult = False
        self.pBar_upd(step= 1,)







        # colors
        print "*btn_specialSettings:",boolResult
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
        cmds.button(self.BSpecialSettings, e=1, bgc= defCol)

    def btn_cleanAll(self,  *args, **kwargs):
        print "btn_cleanAll()"
        

        boolResult = True
        if not self.btn_checkStructure(controlN=self.BcheckStructure, ):
            boolResult = False
        
        if not self.btn_CleanScene(controlN=self.BCleanScene, ):
            boolResult = False
        
        if not self.btn_CleanObjects(controlN=self.BCleanObjects, ):
            boolResult = False
        if not self.btn_specialSettings(controlN=self.BSpecialSettings, ):
            boolResult = False
        
        # colors
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
    def colorBoolControl(self, controlL=[], boolL=[],labelL=[""], warning=False,  *args, **kwargs):
        # color the controlL depending on the given Bool
        if self.GUI:
            
            for i,j,label in zip(controlL,boolL,labelL):
                    if j in [True,1]:
                        cmds.button(i, e=1, backgroundColor=self.trueColor, ebg=self.ebg)
                    else:
                        if warning:
                            cmds.button(i, e=1, backgroundColor=self.warnColor, ebg=self.ebg)
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

        self.BcheckStructure = cmds.button("checkStructure", )
        cmds.button(self.BcheckStructure,e=1,c= partial( self.btn_checkStructure,self.BcheckStructure) )

        self.BCleanScene = cmds.button("CleanScene",)
        cmds.button(self.BCleanScene,e=1,c= partial( self.btn_CleanScene,self.BCleanScene))

        self.BCleanObjects = cmds.button("CleanObjects",)
        cmds.button(self.BCleanObjects,e=1,c= partial( self.btn_CleanObjects,self.BCleanObjects) )
        
        self.BSpecialSettings = cmds.button("Apply Special_Settings",)
        cmds.button(self.BSpecialSettings,e=1,c= partial( self.btn_specialSettings,self.BSpecialSettings) )
        
        

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