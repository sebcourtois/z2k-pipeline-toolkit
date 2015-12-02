#!/usr/bin/python
# -*- coding: utf-8 -*-
########################################################
# Name    : Z2K_ReleaseTool
# Version : v100
# Description : Create previz maya file in .mb with some cleaning script called inside
# Comment : BASE SCRIPT OUT OF Z2K in v002
# Author : Jean-Philippe Descoins
# Date : 2015-26-08
# Comment : wip
#
# TO DO:
#   WIP add comment from version for now it's alway the edited version wich is alway a public n+1 version (auto increment probleme)
#   - add release and unLock btn
#   - finish integrating aladin_lamp swith here
#   x Make it contextual (add mode contextual) this is done outside in the ReleaseTool_ALADIN_LAMP.py
#   aboard: add type chooser (previz_ref/anim_ref/previz_scene/anim_scene) et enlevé le ref c est de toute facon pour le release
#   x add seeRef 
#   x add cat chooser to the GUI, "set/env/char/prop"
#   x handle module import style
#   x Unlockink the edited file if not saved
#   x Dockable
#   x debug/advanced mode
#   - add save debug file
#   - add filter ability for big menu list
#   
########################################################





# getLockOwner()



import os
import maya.cmds as cmds
from functools import partial
import dminutes.Z2K_wrapper as Z2K
reload(Z2K)

import dminutes.jipeLib_Z2K as jpZ
reload(jpZ)
# import dminutes.Z2K_Batchator.Z2K_Release_Batch_CONFIG as Batch_CONFIG
# reload(Batch_CONFIG)
# from dminutes.Z2K_Batchator.Z2K_Release_Batch_CONFIG import *

# import   constant
import dminutes.Z2K_ReleaseTool.modules as ini
reload(ini)
from dminutes.Z2K_ReleaseTool.modules import *


import dminutes.Z2K_ReleaseTool.modules.Z2K_Previz_PROP_checks as Z2K_Pcheck_PROP
reload(Z2K_Pcheck_PROP)
import dminutes.Z2K_ReleaseTool.modules.Z2K_Previz_CHAR_checks as Z2K_Pcheck_CHAR
reload(Z2K_Pcheck_CHAR)
import dminutes.Z2K_ReleaseTool.modules.Z2K_Previz_SET_checks as Z2K_Pcheck_SET
reload(Z2K_Pcheck_SET)



class Z2K_ReleaseTool (object):
    
    version = "_v010"            
    name = "Z2K_ReleaseTool"
    categoryL = jpZ.getCatL()

    def __init__(self, sourceAsset="", assetCat = "chr", SourceAssetType="previz_scene", destinationAsset = "", destinationAssetType= "previz_ref", 
        projConnectB= True,theProject="zombtest",theComment= "auto rock the casbah release !", debug=False, *args, **kwargs):
        print "__init__"
        

        self.debug = debug
        self.assetCat = assetCat
        self.sourceAsset = sourceAsset
        self.sourceAssetType = SourceAssetType
        self.destinationAsset = destinationAsset
        self.destinationAssetType = destinationAssetType
        self.theProject = theProject
        self.theComment = theComment
        self.SceneInfoDict = {}
        print "**** projConnectB = ", projConnectB
        if projConnectB :
            self.proj=Z2K.projConnect(theProject=theProject)
        else:
            print "**** NO projConnectB = ", projConnectB
            self.proj=""

        self.path_private_toEdit = ""

        self.assetL = jpZ.getAssetL ( assetCat= self.assetCat )

        # self.createWin()



    # ------------------------ JIPE_LIB Functions ------------------------------------


        

    def openAsset(self, sourceAsset="chr_aurelien_manteau", SourceAssetType="previz_scene", readOnly=False, autoUnlock=True, seeRef=False, *args,**kwargs):

        # get char from mayascene
        assetN=""
        sceneN = cmds.file(q=1,sceneName=True)
        # lock handling
        if len(sceneN)>0:
            assetN = os.path.normpath(sceneN).rsplit(os.sep,1)[-1].rsplit("-v",1)[0]
            print "assetN=", assetN
            print "*",assetN.rsplit("_",1)[0]
            print "*",assetN.rsplit("_",1)[-1] + "_" + SourceAssetType.rsplit("_",1)[-1]
            try:
                drcF=Z2K.getDrcF(proj=self.proj, assetName=assetN.rsplit("_",1)[0], pathType= self.sourceAssetType )
                print "drcF=", drcF
                theLock=Z2K.getLock(drcF)
                print "theLock=", theLock
                if len(theLock)>0:
                    if not autoUnlock:
                        booboo=cmds.confirmDialog(message="Current Asset : {0} \ris LOCKED by :'{1}' \rDo you want to UNLOCK it before loading?!".format(assetN,theLock),
                                                    messageAlign="center", defaultButton="YES", cancelButton="NO" , b="YES", button="NO",
                                                    icon="warning")
                        print "booboo=",booboo
                        if booboo in ["YES"]:
                            Z2K.unlock(drcF)
                        else:
                            print assetN + " not unlocked"
                    else:
                        Z2K.unlock(drcF)
            except Exception,err:
                print "the file in not really a nice clean Z2K file Dude!",err
                


        #  opening asset
        if seeRef:
            SourceAssetType = SourceAssetType.rsplit("_",1)[0] + "_ref"
            
        path_public,path_private = Z2K.getPath(proj=self.proj, assetName=sourceAsset,pathType=SourceAssetType)
        if os.path.isfile(path_public):

            if readOnly :
                print "/readOnly"
                path_private_toEdit = Z2K.openFileReadOnly(proj=self.proj, Path_publish_public=path_public)
            else:
                print "/edit"
                path_private_toEditC = Z2K.editFile(proj=self.proj, Path_publish_public=path_public)
                path_private_toEdit = path_private_toEditC.absPath()
            print "path_private_toEdit=", path_private_toEdit

        
            cmds.file(path_private_toEdit,open=True,f=True)
        else:
            raise IOError("Tout le monde n'aime pas le boudin, mais cette scene n'existe pas!")

        return path_private_toEdit


    def release_Asset(self, destinationAsset="chr_aurelien_manteau", destinationAssetType = "previz_ref",
        theComment= "auto rock the casbah release !", autoUnlock = False,
        *args, **kwargs):
        print "release_Asset()"
        
        print "***//",destinationAsset, destinationAssetType
        path_public,path_private = Z2K.getPath(proj=self.proj, assetName=destinationAsset, pathType=destinationAssetType)
        path_private_toPublish = Z2K.editFile(proj=self.proj, Path_publish_public=path_public)
        path_private_toPublishAbs= path_private_toPublish.absPath()
        print "path_private_toPublish=", path_private_toPublishAbs
        
        # check if current file is published
        path_public,path_private = Z2K.getPath(proj=self.proj, assetName=self.sourceAsset, pathType=self.sourceAssetType)
        print "path_public=", path_public
        print "path_private=", path_private
        #pubFile is a MrcFile
        pubFile_Version = "v" + str(self.proj.entryFromPath(path_public).currentVersion).zfill(3)
        curVersion = jpZ.infosFromMayaScene()["version"]
        print "pubFile_Version=",pubFile_Version
        print "current_Version=",curVersion

        if pubFile_Version == curVersion:

            # get scene form SG feed
            print "******",
            scenePathSG = cmds.file(q=1,sceneName=True)
            print "scenePathSG=", scenePathSG

            # save file with Maya at the supposed place
            newName = cmds.file (rename = path_private_toPublishAbs)
            exportedFileM= cmds.file ( save=True, force=True, options= "v=0", type= "mayaBinary", preserveReferences=False,  )

            # auto comment DAVOS if not given
            if theComment in ["",None]:
                thecomment = "released From " + curVersion

            # feeding SG #1
            
            curVersFile = self.proj.versionFileFromPrivatePath(scenePathSG)
            print "curVersFile=", curVersFile
            curSgVers = curVersFile.getSgVersion()
            print "curSgVers=", curSgVers
            # publishing this file to the public
            exportedFileZ2K = Z2K.publishFile(proj=self.proj, path_private_toPublish=path_private_toPublish, comment=theComment)
            
            # feeding SG #2
            rlsVersFile = self.proj.versionFileFromPrivatePath(exportedFileZ2K)
            print "rlsVersFile=", rlsVersFile
            rlsSgVers = rlsVersFile.getSgVersion()
            print "rlsSgVers=", rlsSgVers

            # feeding SG #3 (final step)
            self.proj.updateSgEntity(curSgVers,sg_current_release_version=rlsSgVers, sg_released=True)

            # re open the publish file for checking
            cmds.file(os.path.normpath(exportedFileZ2K), open=True,f=True)
        else:
            print "Not RELEAZED: Edited version was not published!"
            exportedFileZ2K = "NOT RELEAZED: Edited version was not published before release!"

        return exportedFileZ2K


# Z2K_OpenA=Z2K_ReleaseTool(sourceAsset="chr_aurelien_manteau", SourceAssetType="previz_scene",
#                         destinationAsset="chr_aurelien_manteau", destinationAssetType= "previz_ref",
#                          projConnectB= 1,)


##########################################################################################################
#                                          _____        _   _        _  
#                                         /  ___|      | | | |      | | 
#                                         | |          | | | |      | | 
#                                         | |  _       | | | |      | | 
#                                         | |_| |      | |_| |      | | 
#                                         \_____/      \_____/      |_| 
###########################################################################################################


class Z2K_ReleaseTool_Gui (Z2K_ReleaseTool):
    layoutImportModule=""

    basePath = jpZ.getBaseModPath()
    ICONPATH = Z2K_ICONPATH + "Z2K_RELEAZE_LOGO_A1.bmp"
    upImg= basePath + ICONPATH
        
    
    def __init__(self, sourceAsset="", assetCat="", SourceAssetType="", destinationAsset="", destinationAssetType="", projConnectB="",theProject="",theComment="",debug="",*args, **kwargs):
        # self = Z2K_ReleaseTool
        Z2K_ReleaseTool.__init__(self,sourceAsset,assetCat,SourceAssetType, destinationAsset, destinationAssetType, projConnectB,theProject,theComment,debug)
        # self.sourceAsset = sourceAsset
        # self.sourceAssetType = SourceAssetType
        # self.destinationAsset = destinationAsset
        # self.destinationAssetType = destinationAssetType
        # self.projConnectB = projConnectB
        # self.theProject = theProject
        # self.theComment = theComment
        # self = Z2K_ReleaseTool(*args, **kwargs)
        print "theProject = ", self.proj
        print self.name,self.version
        self.cf = self.name + self.version
        self.dc = self.cf+"_Dock" +"_" +self.theProject
        self.width = 315


    # --------------interface functions-----------------------------------------------
    def getInterfaceValues( self,*args,**kwargs):
        print "getInterfaceValues()"
        self.sourceAsset = cmds.textField(self.BsourceAsset, q=1,text=True)
        self.sourceAssetType = cmds.textField(self.BsourceAssetType, q=1,text=True)

        self.destinationAsset = cmds.textField(self.BdestinationAsset, q=1,text=True)
        self.destinationAssetType = cmds.textField(self.BdestinationAssetType, q=1,text=True)

        self.theComment =  cmds.textField(self.BtheComment, q=1,text=True)

        print self.sourceAsset,"->",self.destinationAsset, self.sourceAssetType,"->",self.destinationAssetType
    
    def refreshOptionMenu(self, theOptMenuL=[], inList=[], *args, **kwargs):
        print "refreshOptionMenu()"
        for theOptMenu in theOptMenuL:
            items = cmds.optionMenu(theOptMenu, query=True, itemListShort=True)
            for item in items:
                cmds.deleteUI(item)

            for item in inList:
                cmds.menuItem(theOptMenu + "_" + item, label= item, parent=theOptMenu)

    def btn_categoryMenu (self,*args, **kwargs):
        print "btn_categoryMenu()"
        self.assetCat = cmds.optionMenu(self.BcategoryMenu,q=1,v=1)
        self.assetL = jpZ.getAssetL( assetCat=self.assetCat)

        # cascade
        self.refreshOptionMenu(theOptMenuL=[self.BsourceAssetMenu,self.BdestinationAssetMenu], inList=self.assetL)
        self.btn_sourceAssetMenu()

    def btn_sourceAssetMenu( self,*args,**kwargs):
        print "btn_assetMenu()"
        curAsset= cmds.optionMenu(self.BsourceAssetMenu,q=1,v=True)
        cmds.textField(self.BsourceAsset,e=1, text=curAsset)
        cmds.textField(self.BdestinationAsset,e=1, text=curAsset)
        cmds.optionMenu( self.BdestinationAssetMenu, e=1, v= curAsset )

    def btn_destinationAssetMenu( self,*args,**kwargs):
        print "btn_assetMenu()"
        curAsset= cmds.optionMenu(self.BdestinationAssetMenu,q=1,v=True)
        cmds.textField(self.BdestinationAsset,e=1, text=curAsset)

    def btn_open_Asset( self,*args,**kwargs):
        print "btn_open_Asset()"
        self.getInterfaceValues()
        self.sourceAssetPath = self.openAsset(sourceAsset= self.sourceAsset, SourceAssetType=self.sourceAssetType,readOnly=False,autoUnlock=False, seeRef=False)
        cmds.textField(self.BdestinationAsset,e=1, text=self.sourceAsset)
        cmds.optionMenu(self.BdestinationAssetMenu ,e=True, value=self.sourceAsset)

        # update UI with current scene informations
        self.updateUI()

    def btn_open_Asset_readOnly(self, *args, **kwargs):
        print "btn_open_Asset_readOnly()"
        self.getInterfaceValues()
        self.readOnlyAssetPath = self.openAsset(sourceAsset= self.sourceAsset, SourceAssetType=self.sourceAssetType,readOnly=True,autoUnlock=False, seeRef=False)
        cmds.textField(self.BdestinationAsset,e=1, text=self.sourceAsset)
        cmds.optionMenu(self.BdestinationAssetMenu ,e=True, value=self.sourceAsset)

        # update UI with current scene informations
        self.updateUI()

    def btn_see_Ref(self, *args, **kwargs):
        print "btn_see_Ref()"
        self.getInterfaceValues()
        self.readOnlyAssetPath = self.openAsset(sourceAsset= self.sourceAsset, SourceAssetType=self.sourceAssetType,readOnly=True,autoUnlock=False, seeRef=True)
        cmds.textField(self.BdestinationAsset,e=1, text=self.sourceAsset)
        cmds.optionMenu(self.BdestinationAssetMenu ,e=True, value=self.sourceAsset)




    def btn_release_Asset( self, force=False, *args,**kwargs):
        print "btn_release_Asset()",force
        self.getInterfaceValues()

        # check if the context of the UI is the same as the scene
        curCTX = jpZ.infosFromMayaScene()
        if curCTX == self.SceneInfoDict or force:
            print "CONTEXT IS OK"


            print "X",self.sourceAsset,"->",self.destinationAsset, self.sourceAssetType,"->",self.destinationAssetType
            try :
                exportedFileZ2K = self.release_Asset( destinationAsset= self.destinationAsset ,destinationAssetType = self.destinationAssetType,
                                        theComment= self.theComment)
                cmds.confirmDialog(title= "ASSET RELEASE DONE",message= exportedFileZ2K,button="OK", messageAlign="center", icon="information")

                # disable l'UI, elle ne peut etre reactived que avec le boutton get_context
                # cmds.layout(self.layToEn,e=1,en=0)
                cmds.layout(self.layToEnB,e=1,en=0)

            except Exception,err:
                msg= str(err)
                cmds.confirmDialog(title= "ERROR",message= msg,button="OK", messageAlign="center", icon="warning")

            

        else:
            msg= "BAD CONTEXT ! \n do a get_context"
            print msg
            cmds.confirmDialog(title= "ERROR",message= msg,button="OK", messageAlign="center", icon="warning")

        



    def updateUI(self, *args, **kwargs):
        # cascade
        if self.assetCat  in self.categoryL:
            cmds.optionMenu(self.BcategoryMenu ,e=True, value=self.assetCat)
        self.refreshOptionMenu(theOptMenuL=[self.BsourceAssetMenu,self.BdestinationAssetMenu], inList=self.assetL)
        
        cmds.optionMenu(self.BsourceAssetMenu ,e=True, value=self.sourceAsset)
        cmds.textField(self.BsourceAsset,e=1, text=self.sourceAsset)
        cmds.textField(self.BsourceAssetType, e=1, text=self.sourceAssetType)

        cmds.optionMenu(self.BdestinationAssetMenu ,e=True, value=self.destinationAsset)
        cmds.textField(self.BdestinationAsset,e=1, text=self.destinationAsset)
        cmds.textField(self.BdestinationAssetType, e=1, text=self.destinationAssetType)

        cmds.textField(self.BtheComment,e=1,text=self.theComment, )
        # unparent or delete old test layout
        toDel = cmds.layout(self.layoutImportModule,q=1,childArray=1)
        print "toDel=", toDel
        try:
            cmds.deleteUI(toDel[0])
        except Exception,err:
            print "deleteUI():",err


    def btn_get_context(self, *args, **kwargs):
        print "btn_get_context"
        # get scene info
        self.SceneInfoDict = jpZ.infosFromMayaScene()
        infoDict = self.SceneInfoDict
        print "infoDict=", infoDict 
        if infoDict and not "Ref" in infoDict["assetType"][-3:] :
            # set inReleaseTool context
            self.assetCat = infoDict["assetCat"]
            self.sourceAsset =infoDict["assetName"]
            self.sourceAssetType =infoDict["assetType"]+"_scene"
            self.destinationAsset =infoDict["assetName"]
            self.destinationAssetType = infoDict["assetType"]+"_ref"
            self.theComment = "released From " + infoDict["version"] 
            self.assetL = jpZ.getAssetL ( assetCat= self.assetCat )

            # update UI with current scene informations
            self.updateUI()

            

            # parent the new good one
            Z2K_Pcheck="NADA"
            print 'self.assetCat=',self.assetCat
            # THIS IS FOR NOW ONLY OK FOR THE PREVIZ, IT DOESN'T TEST infoDict["assetType"] but only infoDict["assetCat"]
            tab = "    "
            if  self.assetCat in ["chr"]:
                print "It' is a CHAR test"
                if self.sourceAssetType in ["modeling_scene"]:
                    print tab, "modeling, test not ready"
                    # set DEBUG FILE here
                    theDebugFile  = DEBUGFILE_MODELING_CHR

                elif self.sourceAssetType in ["render_scene"]:
                    print tab, "render, test not ready"
                    # set DEBUG FILE here
                    theDebugFile  = DEBUGFILE_RENDER_CHR

                elif self.sourceAssetType in ["previz_scene"]:
                    print tab, "previz"
                    Z2K_Pcheck = Z2K_Pcheck_CHAR
                    # set DEBUG FILE here
                    theDebugFile  = DEBUGFILE_PREVIZ_CHR

                elif self.sourceAssetType in ["anim_scene"]:
                    print tab, "anim-> same as props"
                    Z2K_Pcheck = Z2K_Pcheck_PROP
                    # set DEBUG FILE here
                    theDebugFile  = DEBUGFILE_ANIM_CHR

                else:
                    print tab, "unknown test or not specific test ready"



            elif  self.assetCat in ["prp","vhl","c2d","env","fxp"]:
                print "It' is a PROP test"
                if self.sourceAssetType in ["modeling_scene"]:
                    print tab, "modeling, test not ready"
                    # set DEBUG FILE here
                    theDebugFile  = DEBUGFILE_MODELING_PRP

                elif self.sourceAssetType in ["render_scene"]:
                    print tab, "render, test not ready"
                    # set DEBUG FILE here
                    theDebugFile  = DEBUGFILE_RENDER_PRP

                elif self.sourceAssetType in ["previz_scene"]:
                    print tab, "previz"
                    # set DEBUG FILE here
                    theDebugFile  = DEBUGFILE_PREVIZ_PRP
                    Z2K_Pcheck = Z2K_Pcheck_PROP

                elif self.sourceAssetType in ["anim_scene"]:
                    print tab, "anim"
                    # set DEBUG FILE here
                    theDebugFile  = DEBUGFILE_ANIM_PRP
                    Z2K_Pcheck = Z2K_Pcheck_PROP
                    
                
            elif  self.assetCat in ["set"]:
                print "It' is a SET test"
                if self.sourceAssetType in ["modeling_scene"]:
                    print tab, "modeling, test not ready"
                    # set DEBUG FILE here
                    theDebugFile  = DEBUGFILE_MODELING_SET

                elif self.sourceAssetType in ["render_scene"]:
                    print tab, "render, test not ready"
                    # set DEBUG FILE here
                    theDebugFile  = DEBUGFILE_RENDER_SET

                elif self.sourceAssetType in ["previz_scene"]:
                    print tab, "previz"
                    # set DEBUG FILE here
                    theDebugFile  = DEBUGFILE_PREVIZ_SET
                    Z2K_Pcheck = Z2K_Pcheck_SET
                    
                elif self.sourceAssetType in ["anim_scene"]:
                    print tab, "anim, test not ready"
                    # set DEBUG FILE here
                    theDebugFile  = DEBUGFILE_ANIM_SET

                


            if Z2K_Pcheck in ["NADA"]:
                raise Exception("PAS DE MODULE DE CHECK POUR CET ASSET")
            else:
                print "Z2K_Pcheck=", Z2K_Pcheck
                Z2K_Pcheck = Z2K_Pcheck.checkModule(GUI=True, parent=self.layoutImportModule, debugFile = theDebugFile )

            # Enable l'UI, 
            cmds.layout(self.layToEn,e=1,en=1)
            cmds.layout(self.layToEnB,e=1,en=1)
            # cmds.button(self.Brelease_Asset,e=1,en=1) 

        else:
            msg= "THIS SCENE IS NOT RELEASABLE! "
            print msg
            cmds.confirmDialog(title= "ERROR",message= msg,button="OK", messageAlign="center", icon="warning")
            # raise Exception(msg)

    # --------------Window-----------------------------------------------
    def deleteUIandpref(self,*args, **kwargs):
        print "deleteUIandpref()"
        # if cmds.dockControl(self.dc, q=1,exists=True ):
        #     # cmds.deleteUI( self.cf,window=True)
        #     # cmds.deleteUI( self.dc,ctl=True)
        #     # cmds.evalDeferred('cmds.deleteUI("{0}")'.format(self.cf))
        #     cmds.evalDeferred('cmds.deleteUI("{0}")'.format(self.dc))
        
        # print cmds.windowPref( self.cf, q=True ,w=1)
        # cmds.windowPref( self.cf, e=True ,w=1000,h=50,te=400,le=800)
        # print cmds.windowPref( self.cf, q=True ,wh=1)

    def createWin(self,*args,**kwargs):
        textF_w = 120

        # test si la windows exist / permet d'avoir plusieurs windows grace a var "cf" de la class
        # if cmds.window(self.cf, q=True, exists=True):
        #     cmds.deleteUI(self.cf, window=True)
        #create la window et rename apres
        print "DOCK MAMI BOUSIN:",cmds.dockControl(self.dc, q=True, exists=True)
        if cmds.dockControl(self.dc, q=True, exists=True):
            cmds.deleteUI(self.dc)
        if cmds.window(self.cf, q=True, exists=True):
            cmds.deleteUI(self.cf)

        cmds.window(self.cf, rtf=True, tlb=True, t= self.cf, width=self.width,)
        cmds.window(self.cf, e=True, sizeable=True, t= self.cf, h=50,w=50)
        #BIG TAB ------------------------------------------------------------------------------------------------
        cmds.frameLayout(marginHeight=2, marginWidth=2,lv=0)
        # cmds.tabLayout(tabsVisible=0,borderStyle="full")
        cmds.frameLayout("Bigframe", marginHeight=0, marginWidth=0, labelVisible=False, fn="tinyBoldLabelFont", cll=False,w=self.width)
        cmds.columnLayout(adjustableColumn=True, columnOffset= ["both",5],)
        cmds.columnLayout(adjustableColumn=True,)
        cmds.image( image=self.upImg )
        # cmds.setParent("..")
        
        # cmds.frameLayout(lv=1, mh=5, mw=5,l="OPEN:",cll=1)
        cmds.columnLayout(adj=1,rs=2)
        cmds.button("GET CONTEXT", ann="Rub the Lamp and make a wish'",h=30,c=self.btn_get_context )
        cmds.setParent("..")
        self.layToEn = cmds.tabLayout(tabsVisible=0,borderStyle="full")
        cmds.columnLayout(adj=1,rs=2)
        
        
        
        # category menu
        self.BcategoryMenu = cmds.optionMenu("categoy", label='Category:', ann="", changeCommand=self.btn_categoryMenu )
        for cat in self.categoryL  :
            cmds.menuItem( label=cat )
        if self.assetCat  in self.categoryL:
            cmds.optionMenu(self.BcategoryMenu ,e=True, value=self.assetCat)

        # Source_Asset menu
        self.BsourceAssetMenu = cmds.optionMenu("Source_Asset_List", label='Source_Asset:', ann="", changeCommand=self.btn_sourceAssetMenu )
        for asset in sorted(self.assetL)  :
            cmds.menuItem( label=asset )
        if self.sourceAsset  in self.assetL:
            cmds.optionMenu(self.BsourceAssetMenu ,e=True, value=self.sourceAsset)

        # source advanced rowL
        self.sourceRowL = cmds.rowLayout(nc=4,adj=1, manage = 1)
        self.BsourceAsset = cmds.textField("sourceAssetName",text=self.sourceAsset,w=textF_w,manage=1)
        self.BsourceAssetType = cmds.textField("sourceAssetType",text=self.sourceAssetType, w=95,manage=1)
        cmds.setParent("..")
        
        cmds.rowLayout(nc=4,adj=3,manage = 1)
        self.Bopen_Asset = cmds.button("EDIT ASSET",ann="EDIT ASSET",c= self.btn_open_Asset,w=round(self.width/3)-10)
        self.Bopen_Asset_ReadOnly = cmds.button("SEE ASSET",ann="SEE ASSET",c= self.btn_open_Asset_readOnly,w=round(self.width/3)-10) 
        self.Bsee_Ref_ReadOnly = cmds.button("SEE REF",ann="SEE REF",c= self.btn_see_Ref,w=round(self.width/3)-10,enable=1) 

        cmds.setParent("..")
        
        cmds.setParent("..")
        cmds.setParent("..")
        cmds.setParent("..")

        # cmds.separator(  style='out' )


        # layout import module SPACE -----------------------------------------------------------------
        # self.layoutImportModule = cmds.tabLayout(tabsVisible=0,borderStyle="full")
        self.layoutImportModule = cmds.frameLayout(lv=0)
        
        # Z2K_Pcheck.insertLayout(parent=self.layoutImportModule )




        # destination asset menu -------------------------------------------------------------------
        # cmds.setParent("..")
        cmds.setParent("..")

        self.layToEnB= cmds.tabLayout(tabsVisible=0,borderStyle="full")
        cmds.columnLayout(adj=1,rs=2)
        # cmds.separator(  style='out' )

        self.BdestinationAssetMenu = cmds.optionMenu("Destination_Asset_List", label='Destination_Asset:', ann="", changeCommand=self.btn_destinationAssetMenu )
        for asset in self.assetL  :
            cmds.menuItem( label=asset )
        if self.sourceAsset  in self.assetL:
            cmds.optionMenu(self.BdestinationAssetMenu ,e=True, value=self.sourceAsset)
        
        # source advanced rowL
        # cmds.setParent("..")

        self.destiRowL= cmds.rowLayout(nc=4, adj=1, manage=1)
        self.BdestinationAsset = cmds.textField("destinationAssetName",text=self.destinationAsset,w=textF_w,manage=1)
        self.BdestinationAssetType = cmds.textField("sourceAssetType",text=self.destinationAssetType, w=95,manage=1)
        
        # release button
        cmds.setParent("..")
        self.Brelease_Asset  = cmds.button("RELEASE ASSET",c= self.btn_release_Asset)
        self.BforceRelease = cmds.button("FORCE RELEASE ASSET",c= partial(self.btn_release_Asset,True) )
        # comment
        self.commentRowL= cmds.rowLayout(nc=4, adj=2, manage=1)
        cmds.text("Comment:")
        self.BtheComment= cmds.textField("releaseComment",text=self.theComment, w=85, manage=1,)


        # debug options
        if  not  self.debug:

            cmds.rowLayout(self.sourceRowL, e=1, enable=0)
            cmds.optionMenu(self.BcategoryMenu,e=1,m=0)
            cmds.optionMenu(self.BsourceAssetMenu,e=1,m=0)

            cmds.rowLayout(self.destiRowL, e=1, enable=0)
            cmds.optionMenu(self.BdestinationAssetMenu,e=1,m=0)

            cmds.button(self.BforceRelease,e=1,m=0)
            cmds.rowLayout(self.commentRowL,e=1,  enable=0)
        # show the window
        # cmds.showWindow(self.cf)
        

        # dockable control
        allowedAreas = ['right', 'left']
        self.dc=cmds.dockControl(self.dc,l=self.dc, area='right', content=self.cf, allowedArea=allowedAreas, r=True, floating=True,
                                cc=self.deleteUIandpref,retain=False,splitLayout="horizontal",fixedWidth=True,w=self.width+5 )


        # disable l'UI, elle ne peut etre reactived que avec le boutton get_context
        cmds.layout(self.layToEn,e=1,en=0)
        cmds.layout(self.layToEnB,e=1,en=0)
        
        # self.btn_get_context()




# Z2K_ReleaseTool_GuiI = Z2K_ReleaseTool_Gui(sourceAsset="chr_aurelien_manteau", assetCat = "chr", SourceAssetType="previz_scene",
#                       destinationAsset="chr_aurelien_manteau", destinationAssetType= "previz_ref",
#                       projConnectB= True, theProject="zombtest",debug=False,
#                       theComment= "auto rock the casbah release !")


# Z2K_ReleaseTool_GuiI.createWin()




    