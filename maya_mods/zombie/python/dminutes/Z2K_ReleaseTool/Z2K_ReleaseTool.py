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
#   x add seeRef 
#   - add type chooser (previz_ref/anim_ref/previz_scene/anim_scene) et enlevé le ref c est de toute facon pour le release
#   x add cat chooser to the GUI, "set/env/char/prop"
#   x handle module import style
#   x Unlockink the edited file if not saved
#   x Dockable
#   x debug/advanced mode
#   - add save debug file
#   - add filter ability for big menu list
#   - ass see REF button
########################################################





# getLockOwner()



import os
import maya.cmds as cmds

# import dminutes.Z2K_ReleaseTool.Z2K_Asset_Previz_checks as Z2K_PcheckD
# reload(Z2K_PcheckD)
# import dminutes.Z2K_ReleaseTool._versions.Z2K_Asset_Previz_checks_v007 as Z2K_PcheckD
# Z2K_Pcheck = Z2K_PcheckD.AssetPrevizMod()
import dminutes.Z2K_wrapper as Z2K
reload(Z2K)
import dminutes.jipeLib_Z2K as jpm
reload(jpm)




class Z2K_ReleaseTool (object):
    
    version = "_v010"            
    name = "Z2K_ReleaseTool"
    categoryL = ["chr","prp", "set"]

    basePath = [x for x in os.environ.get("MAYA_MODULE_PATH").split(";") if "maya_mods" in x][0]
    upImg= basePath +"/zombie/python/dminutes/Z2K_ReleaseTool/icons/Z2K_ReleaseTool/Z2K_RELEAZE_LOGO_A1.bmp"

    baseAssetPath =  os.environ.get("ZOMB_ASSET_PATH")
    print baseAssetPath
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
        print "**** projConnectB = ", projConnectB
        if projConnectB :
            self.proj=Z2K.projConnect(theProject=theProject)
        else:
            print "**** NO projConnectB = ", projConnectB
            self.proj=""

        self.path_private_toEdit = ""

        self.assetL = self.getAssetL( theDir=os.path.normpath(self.baseAssetPath ) , assetCat=self.assetCat )

        # self.createWin()



    # ------------------------ JIPE_LIB Functions ------------------------------------




    # ------------------------ OS/Z2K Functions ------------------------------------
    def getAssetL (self,theDir=r"P:/zombtest/asset/", assetCat="chr",*args,**kwargs):
        theDir = os.path.normpath(theDir) + os.sep + assetCat
        print "theDir=", theDir
        if os.path.isdir(theDir):
            assetL = sorted(os.listdir(theDir) )
            if not len(assetL):
                assetL=["Empty Folder"]
            
        else:
            assetL=["Invalide folder"]

        return assetL


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


    def release_Asset(self,destinationAsset="chr_aurelien_manteau", destinationAssetType = "previz_ref",
        theComment= "auto rock the casbah release !",
        *args, **kwargs):
        print "release_Asset()"

        print "***//",destinationAsset, destinationAssetType
        path_public,path_private = Z2K.getPath(proj=self.proj, assetName=destinationAsset, pathType=destinationAssetType)
        path_private_toPublish = Z2K.editFile(proj=self.proj, Path_publish_public=path_public)
        path_private_toPublishAbs= path_private_toPublish.absPath()
        print "path_private_toPublish=", path_private_toPublishAbs
        
        # save file with Maya at the supposed place
        newName = cmds.file (rename = path_private_toPublishAbs)
        exportedFileM= cmds.file ( save=True, force=True, options= "v=0", type= "mayaBinary", preserveReferences=False,  )

        # publishing this file to the public
        exportedFileZ2K = Z2K.publishFile(proj=self.proj, path_private_toPublish=path_private_toPublish, comment=theComment)

        # re open the publish file for checking
        cmds.file(os.path.normpath(exportedFileZ2K), open=True,f=True)

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
    def __init__(self, sourceAsset="", assetCat="", SourceAssetType="", destinationAsset="", destinationAssetType="", projConnectB="",theProject="",*args, **kwargs):
        # self = Z2K_ReleaseTool
        Z2K_ReleaseTool.__init__(self,sourceAsset,assetCat,SourceAssetType, destinationAsset, destinationAssetType, projConnectB,theProject)
        # self.sourceAsset = sourceAsset
        # self.SourceAssetType = SourceAssetType
        # self.destinationAsset = destinationAsset
        # self.destinationAssetType = destinationAssetType
        # self.projConnectB = projConnectB
        # self.theProject = theProject

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
        self.assetL = self.getAssetL(theDir=os.path.normpath(self.baseAssetPath ) , assetCat=self.assetCat)

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


    def btn_open_Asset_readOnly(self,*args, **kwargs):
        print "btn_open_Asset_readOnly()"
        self.getInterfaceValues()
        self.readOnlyAssetPath = self.openAsset(sourceAsset= self.sourceAsset, SourceAssetType=self.sourceAssetType,readOnly=True,autoUnlock=False, seeRef=False)
        cmds.textField(self.BdestinationAsset,e=1, text=self.sourceAsset)
        cmds.optionMenu(self.BdestinationAssetMenu ,e=True, value=self.sourceAsset)

    def btn_see_Ref(self,*args, **kwargs):
        print "btn_see_Ref()"
        self.getInterfaceValues()
        self.readOnlyAssetPath = self.openAsset(sourceAsset= self.sourceAsset, SourceAssetType=self.sourceAssetType,readOnly=True,autoUnlock=False, seeRef=True)
        cmds.textField(self.BdestinationAsset,e=1, text=self.sourceAsset)
        cmds.optionMenu(self.BdestinationAssetMenu ,e=True, value=self.sourceAsset)

    def btn_release_Asset( self,*args,**kwargs):
        print "btn_release_Asset()"
        self.getInterfaceValues()
        print "X",self.sourceAsset,"->",self.destinationAsset, self.sourceAssetType,"->",self.destinationAssetType
        try :
            exportedFileZ2K = self.release_Asset( destinationAsset= self.destinationAsset ,destinationAssetType = self.destinationAssetType)
            cmds.confirmDialog(title= "ASSET RELEASE DONE",message= exportedFileZ2K,button="OK", messageAlign="center", icon="information")

        except Exception,err:
            msg= str(err)
            cmds.confirmDialog(title= "ERROR",message= msg,button="OK", messageAlign="center", icon="warning")

    


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
        print "MAMI BOUSIN:",cmds.dockControl(self.dc, q=True, exists=True)
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
        
        
        cmds.tabLayout(tabsVisible=0,borderStyle="full")
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
        self.BsourceAssetType = cmds.textField("sourceAssetType",text=self.sourceAssetType, w=85,manage=1)
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

        cmds.tabLayout(tabsVisible=0,borderStyle="full")
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
        self.BdestinationAssetType = cmds.textField("sourceAssetType",text=self.destinationAssetType, w=85,manage=1)
        
        # release button
        cmds.setParent("..")
        self.Brelease_Asset  = cmds.button("RELEASE ASSET",c= self.btn_release_Asset)
        
        
        # debug options
        if not self.debug:
            cmds.rowLayout(self.sourceRowL, e=1, manage=0)
            # cmds.textField(self.BsourceAsset, e=1, manage=0)
            # cmds.textField(self.BsourceAssetType, e=1, manage=0)
            cmds.rowLayout(self.destiRowL, e=1, manage=0)
            # cmds.textField(self.BdestinationAsset, e=1, manage=0)
            # cmds.textField(self.BdestinationAssetType, e=1, manage=0)

        # show the window
        # cmds.showWindow(self.cf)
        

        # dockable control
        allowedAreas = ['right', 'left']
        self.dc=cmds.dockControl(self.dc,l=self.dc, area='right', content=self.cf, allowedArea=allowedAreas, r=True, floating=True,
                                cc=self.deleteUIandpref,retain=False,splitLayout="horizontal",fixedWidth=True,w=self.width+5 )



        

# Z2K_ReleaseTool_GuiI = Z2K_ReleaseTool_Gui(sourceAsset="chr_aurelien_manteau", assetCat = "chr", SourceAssetType="previz_scene",
#                       destinationAsset="chr_aurelien_manteau", destinationAssetType= "previz_ref",
#                       projConnectB= True, theProject="zombtest",debug=False,
#                       theComment= "auto rock the casbah release !")


# Z2K_ReleaseTool_GuiI.createWin()




    