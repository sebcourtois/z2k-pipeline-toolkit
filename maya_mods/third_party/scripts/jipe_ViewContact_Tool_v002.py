#!/usr/bin/python
# -*- coding: utf-8 -*-
########################################################
# Name    : jipe_ViewContact_Tool
# Version : 002
# Description : Parameter the viewport to viewport 2.0 with occlusion to handle contacts
# Author : Jean-Philippe Descoins
# Date : 2014-06-10
# Comment : WIP
# contact : jp_oim@hotmail.com                                 
#                                                              
#    ! Toute utilisation de ce se script sans autorisation     
#                         est interdite !                      
#    ! All use of this script without authorization is         
#                           forbidden !                        
#                                                              
#                                                              
#                 © Jean-Philippe Descoins                     
################################################################

# x: adapte to maya 20016 basically on viewport 2.0

import maya.cmds as cmds
import maya.mel as mel
import dminutes.jipeLib_Z2K as jpZ
reload(jpZ)
from dminutes import miscUtils
reload (miscUtils)
class ViewportSwitch(object):

    VERSION = "_v001"

    def __init__(self,*args,**kwargs):

        self.theEditor = ""
        self.oldRenderMode = ""
        self.stateString = ""
        self.occluAmout = 2.5
        self.occluRadius = 16
        self.occluFilter = 8

        # anti aliasing
        self.lineAAEnable = 0
        self.multiSampleEnable = 0
        self.multiSampleCount = 4
        self.curSe = jpZ.GetSel()

    def getEditor( self,*args,**kwargs):
        print "getEditor()"
        theEdito = cmds.playblast(activeEditor=True)
        print "\t",theEdito
        if len(theEdito)<1 :
            self.errorMsg( title='Get Viewport ERROR', msg='Please click on the CAMERA VIEW')
        print "*",self.curSe
        return theEdito


    def getRenderMode( self,*args,**kwargs):
        print "getRenderMode()"
        return cmds.modelEditor(self.theEditor, q=True, rnm = True )


    def getModelEditorSetting( self, theEditor="", *args, **kwargs ):
        print "getModelEditorSetting()"
        # get model editor state
        stateString = cmds.modelEditor(theEditor, q=1, stateString=True )
        stateString = stateString.replace("$editorName", theEditor)
        print "\t ",theEditor
        return stateString


    def setBackViewport( self, theEditor="", stateString="", oldRenderMode="", *args, **kwargs ):
        print "setModelEditorSetting()"
        
        # set back the model editor state
        mel.eval(stateString)

        # set back old render mode
        cmds.modelEditor(theEditor, e=True, rnm = oldRenderMode )

    def ifexist(self,attr,*args,**kwargs):
        if cmds.objExists(attr):
            return True
        else:
            return False

    def Viewport20_Settings(self, theEditor="", occlu=True, *args, **kwargs):
        print "\t HD"
        # viewPort 2.0 settings
        try:
            cmds.ActivateViewport20()
            cmds.modelEditor(theEditor, edit=True, displayAppearance="smoothShaded")
            cmds.modelEditor(theEditor, edit=True, displayTextures = True, textureSampling=1, textureMaxSize= 2048)
            cmds.modelEditor(theEditor, edit=True, shadows = True, transpInShadows = True, transparencyAlgorithm="perPolygonSort" )
            cmds.modelEditor(theEditor, edit=True, displayLights="default") # all, none, default

            # occlusion settings
            cmds.setAttr("hardwareRenderingGlobals.ssaoEnable", occlu)
            cmds.setAttr ("hardwareRenderingGlobals.ssaoFilterRadius", self.occluFilter)
            cmds.setAttr ("hardwareRenderingGlobals.ssaoRadius", self.occluRadius)
            cmds.setAttr ("hardwareRenderingGlobals.ssaoAmount", self.occluAmout)
            
            # Anti aliasing settings
            if cmds.objExists("hardwareRenderingGlobals.lineAAEnable"):
                cmds.setAttr("hardwareRenderingGlobals.lineAAEnable", self.lineAAEnable )
            
            cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", self.multiSampleEnable )
            cmds.setAttr("hardwareRenderingGlobals.multiSampleCount", self.multiSampleCount )

            # transparency setting
            cmds.setAttr("hardwareRenderingGlobals.transparencyAlgorithm", 3 )
        except Exception,err:
            jpZ.UnikName(err)
            print err,Exception



    # -------------------- executing func -------------------------------------
    def goToV20(self,*args,**kwargs):

        # get current editor
        self.theEditor = self.getEditor()

        # get old model editor and render setting
        self.oldRenderMode = self.getRenderMode()
        print "oldRenderMode=", self.oldRenderMode
        self.stateString = self.getModelEditorSetting(theEditor=self.theEditor)
        print jpZ.getCatL()

        # apply 2.0 settings
        self.Viewport20_Settings (theEditor= self.theEditor , occlu=True )

    def goBack(self,*args,**kwargs):

        self.setBackViewport(theEditor=self.theEditor, stateString=self.stateString, oldRenderMode=self.oldRenderMode)
        self.Viewport20_Settings (theEditor= self.theEditor , occlu=False )
    
# -------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------ GUI --------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------

class ViewportSwitch_UI(ViewportSwitch):

    WindowN = "jipe_ViewContact_Tool" 

    def __init__(self,*args,**kwargs):
        
        super(ViewportSwitch_UI,self,).__init__(*args, **kwargs)
        # play_in_context.__init__(self,*args, **kwargs)

        self.enableTeakers = False

    def getInterfaceValues(self,*args,**kwargs):
        self.occluAmout = cmds.floatSlider(self.BOccluAmount,q=1,v=True)    
        self.occluRadius = cmds.floatSlider(self.BOccluRadius,q=1,v=True)    

    def btn_occluSlider(self,*args,**kwargs):
        self.getInterfaceValues(self.curSe)
        cmds.setAttr ("hardwareRenderingGlobals.ssaoAmount", self.occluAmout)
        cmds.setAttr ("hardwareRenderingGlobals.ssaoRadius", self.occluRadius)

        # set the representing fields
        cmds.floatField(self.BOccluAmountField,e=1,v= self.occluAmout)
        cmds.intField(self.BOccluRadiusField,e=1,v= self.occluRadius)
    
    def btn_goToV20(self,*args,**kwargs):

        self.goToV20(jpZ.getAssetTypeL())
        self.enableTeakers = True
        for curControl in [self.RowA,self.RowB]:
            print "curControl=",curControl
            cmds.control(curControl, e=1, enable = self.enableTeakers)    

    def createWindow(self,*args,**kwargs):

        self.WindowN = self.WindowN + self.VERSION
        if cmds.window(self.WindowN, exists=True):
            cmds.deleteUI(self.WindowN)

        #create the window
        cmds.window(self.WindowN, title= self.WindowN , sizeable=True,tlb=False,mnb=True,)

        #create LAYOUT
        cmds.frameLayout(borderStyle = "etchedIn",lv=0, mh=5, mw=5)
        cmds.columnLayout(adj=True,rowSpacing=5)
        cmds.text(l="ViewContact_Tool :", align="center",fn="boldLabelFont")
        cmds.frameLayout(borderStyle = "etchedIn", l="", lv=0,mh=5,mw=5 )
        DadLayout = cmds.columnLayout (adj=True)

        # buttons
        cmds.rowLayout(numberOfColumns=2, adjustableColumn=2,)
        cmds.button(l="View Contacts",ann="go to Viewport 2.0 with occlusion to see contacts",c=self.btn_goToV20)
        cmds.button(l="goBack",c=self.goBack )
        cmds.setParent("..")

        # occlu amount slider
        self.RowA = cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, en = self.enableTeakers )
        cmds.text(" occlu Amount : ")
        self.BOccluAmount = cmds.floatSlider( min=0, max=3, value=self.occluAmout, step=0.1, dragCommand= self.btn_occluSlider,)
        self.BOccluAmountField = cmds.floatField(v=self.occluAmout, w=25 ,pre=1 ,ed=False)
        # occlu spread  slider
        cmds.setParent("..")
        self.RowB = cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, en = self.enableTeakers )
        cmds.text(" occlu Radius  : ")
        self.BOccluRadius = cmds.floatSlider( min=1, max=64, value=self.occluRadius, step=1, dragCommand= self.btn_occluSlider,)
        self.BOccluRadiusField = cmds.intField(v=self.occluRadius, w=25 ,ed=False)

        # finally show Window
        cmds.showWindow()


# ViewportSwitch_UI_I = ViewportSwitch_UI()
# ViewportSwitch_UI_I.createWindow()