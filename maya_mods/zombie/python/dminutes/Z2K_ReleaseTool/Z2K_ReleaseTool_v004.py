#!/usr/bin/python
# -*- coding: utf-8 -*-
########################################################
# Name    : Z2K_ReleaseTool
# Version : v004
# Description : Create previz maya file in .mb with some cleaning script called inside
# Comment : BASE SCRIPT OUT OF Z2K in v002
# Author : Jean-Philippe Descoins
# Date : 2015-26-08
# Comment : wip
#
# TO DO:
#       wip handle module import style


########################################################





# getLockOwner()



import os
import maya.cmds as cmds
import dminutes.jipeLib_Z2K as Z2K
reload(Z2K)
import dminutes.Z2K_ReleaseTool.modules.Z2K_Asset_Previz_checks_v007 as Z2K_PcheckD
reload(Z2K_PcheckD)
print"zoo"
Z2K_Pcheck = Z2K_PcheckD.AssetPrevizMod()


class Z2K_ReleaseTool (object):
    
    version = "_v0.04"            
    name = "Z2K_ReleaseTool" + str(version)
    width = 250
    def __init__(self, sourceAsset="", SourceAssetType="previz_scene", destinationAsset = "", destinationAssetType= "previz_ref", 
                projConnectB= True,theProject="zombtest", *args, **kwargs):
        print "__init__"
        self.cf = "Z2K_ReleaseTool"

        self.assetL = self.getAssetL(theDir=r"P:/zombtest/asset/chr")
        self.sourceAsset = sourceAsset
        self.sourceAssetType = SourceAssetType
        self.destinationAsset = destinationAsset
        self.destinationAssetType = destinationAssetType
        print "**** projConnectB = ", projConnectB
        if projConnectB :
            self.proj=Z2K.projConnect(theProject=theProject)
        else:
            print "**** NO projConnectB = ", projConnectB

            self.proj=""

        self.path_private_toEdit = ""


        # self.createWin()



    # ------------------------ JIPE_LIL Functions ------------------------------------
    def jipeExec(self, filepath, mode="file", *args):  
            # use : historyswitchmode() ,
            print ("/" * 150 + "\n" + "/" * 150 + "\n")
            try:
                filetoread = open(filepath, 'rU')
                scrtxt = filetoread.read()
                print "*file*",scrtxt
                ns = {}
                if filepath.find (".mel") not in [False,-1] :
                    print "MEL *******"
                    mel.eval(scrtxt) in ns
                
                else :
                    exec (scrtxt) in ns
            except Exception as erreur:
                print "ERREUR jipeExec() : ", type(erreur), erreur.args, erreur



    # ------------------------ OS/Z2K Functions ------------------------------------
    def openAsset(self,sourceAsset="chr_aurelien_manteau",SourceAssetType="previz_scene",*args,**kwargs):
        curLeadAsset = sourceAsset
        
        path_public,path_private = Z2K.getPath(proj=self.proj, assetName=curLeadAsset,pathType=SourceAssetType)
        path_private_toEditC = Z2K.editFile(proj=self.proj, Path_publish_public=path_public)
        path_private_toEdit = path_private_toEditC.absPath()
        print "path_private_toEdit=", path_private_toEdit

        cmds.file(path_private_toEdit,open=True,f=True)

        return path_private_toEdit

    def getAssetL (self,theDir=r"P:/zombtest/asset/chr",*args,**kwargs):

        assetL = os.listdir(theDir)

        for a in assetL:
            print 
        return assetL


    def release_Asset(self,destinationAsset="chr_aurelien_manteau", destinationAssetType = "previz_ref", *args, **kwargs):
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
        exportedFileZ2K = Z2K.publishFile(proj=self.proj, path_private_toPublish=path_private_toPublish, comment="test the cashbah moda foka!")

        # re open the publish file for checking
        cmds.file(os.path.normpath(exportedFileZ2K), open=True,f=True)


# Z2K_OpenA=Z2K_ReleaseTool(sourceAsset="chr_aurelien_manteau", SourceAssetType="previz_scene",
#                         destinationAsset="chr_aurelien_manteau", destinationAssetType= "previz_ref",
#                          projConnectB= 1)




##########################################################################################################
#                                          _____        _   _        _  
#                                         /  ___|      | | | |      | | 
#                                         | |          | | | |      | | 
#                                         | |  _       | | | |      | | 
#                                         | |_| |      | |_| |      | | 
#                                         \_____/      \_____/      |_| 
###########################################################################################################


class Z2K_ReleaseTool_Gui (Z2K_ReleaseTool):
    def __init__(self,sourceAsset,SourceAssetType, destinationAsset, destinationAssetType, projConnectB,theProject,*args, **kwargs):
        # self = Z2K_ReleaseTool
        Z2K_ReleaseTool.__init__(self,sourceAsset,SourceAssetType, destinationAsset, destinationAssetType, projConnectB,theProject)
        
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


# --------------interface functions-----------------------------------------------
    def getInterfaceValues( self,*args,**kwargs):
        print "getInterfaceValues()"
        self.sourceAsset = cmds.textField(self.BsourceAsset,q=1,text=True)
        self.destinationAsset = cmds.textField(self.BdestinationAsset,q=1,text=True)

        self.sourceAssetType = "previz_scene"
        self.destinationAssetType = "previz_ref"

        print self.sourceAsset,"->",self.destinationAsset, self.sourceAssetType,"->",self.destinationAssetType


    def btn_sourceAssetMenu( self,*args,**kwargs):
        print "btn_assetMenu()"
        curAsset= cmds.optionMenu(self.BsourceAssetMenu,q=1,v=True)
        cmds.textField(self.BsourceAsset,e=1, text=curAsset)

    def btn_destinationAssetMenu( self,*args,**kwargs):
        print "btn_assetMenu()"
        curAsset= cmds.optionMenu(self.BdestinationAssetMenu,q=1,v=True)
        cmds.textField(self.BdestinationAsset,e=1, text=curAsset)

    def btn_open_Asset( self,*args,**kwargs):
        print "btn_open_Asset()"
        self.getInterfaceValues()
        self.sourceAssetPath = self.openAsset(sourceAsset= self.sourceAsset, SourceAssetType=self.sourceAssetType)
        cmds.textField(self.BdestinationAsset,e=1, text=self.sourceAsset)
        cmds.optionMenu(self.BdestinationAssetMenu ,e=True, value=self.sourceAsset)

    # def btn_check_Asset( self,*args,**kwargs):
    #     print "btn_check_Asset()"
    #     self.getInterfaceValues()
    #     self.jipeExec ("C:/jipe_Local/00_JIPE_SCRIPT/PythonTree/Z2K_WORKGROUP/Asset_Previz_checks_v001.py")

    # def btn_clean_Asset( self,*args,**kwargs):
    #     print "btn_clean_Asset()"
    #     self.getInterfaceValues()
    #     self.jipeExec ("C:/jipe_Local/00_JIPE_SCRIPT/PythonTree/Z2K_WORKGROUP/Asset_Previz_checks_v001.py")

    def btn_release_Asset( self,*args,**kwargs):
        print "btn_release_Asset()"
        self.getInterfaceValues()
        print "X",self.sourceAsset,"->",self.destinationAsset, self.sourceAssetType,"->",self.destinationAssetType
        self.release_Asset( destinationAsset= self.destinationAsset ,destinationAssetType = self.destinationAssetType)


# --------------Window-----------------------------------------------

    def createWin(self,*args,**kwargs):
        # test si la windows exist / permet d'avoir plusieurs windows grace a var "cf" de la class
        if cmds.window(self.cf, q=True, exists=True):
            cmds.deleteUI(self.cf, window=True)
        #create la window et rename apres
        self.cf = cmds.window(self.cf ,rtf=True, tlb=False, t=(self.cf + " : " + str(self.cf)), width=self.width)
        cmds.window(self.cf, e=True, sizeable=True, t=(self.cf + " : " + str(self.cf)))
        #BIG TAB ------------------------------------------------------------------------------------------------
        cmds.frameLayout(marginHeight=2, marginWidth=2,lv=0)

        cmds.frameLayout("Bigframe", marginHeight=0, marginWidth=0, labelVisible=False, fn="tinyBoldLabelFont", cll=False)
        cmds.columnLayout(adjustableColumn=True)
        
        # cmds.frameLayout(lv=1, mh=5, mw=5,l="OPEN:",cll=1)
        
        # source asset menu
        self.BsourceAssetMenu = cmds.optionMenu("Source_Asset_List", label='Source_Asset:', ann="", changeCommand=self.btn_sourceAssetMenu )
        for asset in self.assetL  :
            cmds.menuItem( label=asset )
        cmds.optionMenu(self.BsourceAssetMenu ,e=True, value=self.sourceAsset)

        cmds.rowLayout(nc=4,adj=1,)
        self.BsourceAsset = cmds.textField("sourceAssetName",text=self.sourceAsset,w=170)
        self.BsourceAssetType = cmds.textField("sourceAssetType",text=self.sourceAssetType, w=85)

        cmds.setParent("..")
        self.Bopen_Asset = cmds.button("OPEN ASSET",c= self.btn_open_Asset)
        
        cmds.setParent("..")
        cmds.separator(  style='out' )


        # layout import module SPACE -----------------------------------------------------------------
        self.layoutImportModule = cmds.frameLayout("layoutImportModule",lv=0)
        
        
        Z2K_Pcheck.insertLayout(parent=self.layoutImportModule )

        # destination asset menu -------------------------------------------------------------------
        cmds.setParent("..")
        cmds.separator(  style='out' )

        self.BdestinationAssetMenu = cmds.optionMenu("Destination_Asset_List", label='Destination_Asset:', ann="", changeCommand=self.btn_destinationAssetMenu )
        for asset in self.assetL  :
            cmds.menuItem( label=asset )
        cmds.optionMenu(self.BdestinationAssetMenu ,e=True, value=self.sourceAsset)
        
        cmds.rowLayout(nc=4,adj=1,)
        self.BdestinationAsset = cmds.textField("destinationAssetName",text=self.destinationAsset,w=170)
        self.BdestinationAssetType = cmds.textField("sourceAssetType",text=self.destinationAssetType, w=85)

        cmds.setParent("..")
        self.Brelease_Asset  = cmds.button("RELEASE ASSET",c= self.btn_release_Asset)
        
        # show the window
        cmds.showWindow(self.cf)






Z2K_ReleaseTool_GuiI = Z2K_ReleaseTool_Gui(sourceAsset="chr_aurelien_manteau", SourceAssetType="previz_scene",
                        destinationAsset="chr_aurelien_manteau", destinationAssetType= "previz_ref",
                         projConnectB= True, theProject="zombtest")


Z2K_ReleaseTool_GuiI.createWin()




    