#!/usr/bin/python
# -*- coding: utf-8 -*-
################################################################
# Name    : Z2K_replaceWithCustomFile
# Version : 001
# Description : replace current scene with a custom selected file
# Author : Jean-Philippe Descoins
# Date : 2015_09_24
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

import sys,os
import maya.cmds as cmds





class Z2K_replaceWithCustomFile(object):

    name = "Z2K_replaceWithCustomFile"
    version = "_v001"
    def __init__(self,replacingScene="",*args, **kwargs):
        print "init"
        self.replacingScene = replacingScene
        self.currentSceneP,self.currentScene = self.getCurrentScene()


    # ------------------------ jipe functions ---------------------------------
    def GetFileDialog(self, jtitle="Open File", OkButtName="Ok", jfileMode=1, jdialogStyle=1, jfileFilter="*", baseDir="c://",*args,**kwargs):
        # moved to mayaFunc because of the cmds use
        ''' Description : ouvre un dialog pour choisir un fichier
                    Return : str : filePath
                    Dependencies :  cmds - 
        '''
        try:
            filename = cmds.fileDialog2(fileMode=jfileMode, caption=jtitle, dialogStyle=jdialogStyle, okc=OkButtName, startingDirectory=baseDir)
            print "FilePath = %s" % filename[0]
        except Exception as erreur:
            print "GetFileDialog(ERROR!):", type(erreur), erreur.args, erreur
            filename = [""]
            sys.exit()
        return filename[0]


    def getCurrentScene(self,*args, **kwargs):
        # get currentScene name
        currentSceneP,currentScene = cmds.file(q=1,sceneName=True),cmds.file(q=1,sceneName=True,shortName=True)
        print "currentScene=", currentScene
        return [currentSceneP,currentScene]

    def replace(self, replacingSceneP="",*args, **kwargs):
        print "replace()"
        print "    currentSceneP  =",self.currentSceneP
        print "    replacingSceneP=",replacingSceneP

        # check names


        # open the replacing file rename it and save it over the replaced
        cmds.file( replacingSceneP, open=True, f=True)
        newName = cmds.file (rename = self.currentSceneP)
        cmds.file(save=True,f=True)
# save replacingScene as currentScene in the private



class Z2K_replaceWithCustomFile_GUI(Z2K_replaceWithCustomFile):
    basePath =  os.environ.get("MAYA_MODULE_PATH").split(";")[0]
    upImg= basePath +"/zombie/python/dminutes/Z2K_ReleaseTool/icons/Z2K_ReleaseTool/Z2K_REPLACE_LOGO_A1.bmp"
    def __init__(self,replacingScene="",*args, **kwargs):
        Z2K_replaceWithCustomFile.__init__(self, replacingScene="")

        print self.name,self.version
        self.cf = self.name + self.version





    def btn_getFile(self,*args, **kwargs):
        print ("btn_getFile()")
        outStr =""
        # open dialog box
        theFileP = self.GetFileDialog(jtitle="Select replacing file", OkButtName="Ok", jfileMode=1, jdialogStyle=1, baseDir= self.currentScene)

        if len(theFileP):
            theFileN =os.path.normpath( theFileP )
            print "*",theFileN.rsplit(".",1)[-1]
            if theFileN.rsplit(".",1)[-1]  in ["ma","mb"]:
                outStr = theFileN.rsplit(os.sep,1)[-1]
                self.replacingSceneP = theFileN
                print "yes",outStr
            else:
                outStr = "BAD SCENE TYPE"
        # " update field"
        cmds.textField(self.BFileName,e=1,text=outStr)


    def btn_replaceScene(self,*args, **kwargs):
        print ("btn_replaceScene()")

        self.replace(replacingSceneP= self.replacingSceneP)

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
        self.BgetFile = cmds.button("get file",c= self.btn_getFile,en=1)

        cmds.rowLayout(nc=2,adj=2,manage = 1)
        cmds.text("FileName:")
        self.BFileName = cmds.textField()
        cmds.setParent("..")
        self.BreplaceScene = cmds.button("replace_current_Scene",c= self.btn_replaceScene)
        cmds.setParent("..")



# exec
# Z2K_replaceWithCustomFile_GUIA.insertLayout(parent="")
# Z2K_replaceWithCustomFile_GUIA = Z2K_replaceWithCustomFile_GUI(replacingScene="")