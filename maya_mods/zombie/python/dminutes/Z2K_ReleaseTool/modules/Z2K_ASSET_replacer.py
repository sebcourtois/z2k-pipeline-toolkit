#!/usr/bin/python
# -*- coding: utf-8 -*-
################################################################
# Name    : Z2K_ASSET_replacer
# Version : 002
# Description : replace current scene with a custom selected file
# Author : Jean-Philippe Descoins
# Date : 2015_09_24
# Comment : WIP
# TO DO :
#   x Add publish asset button
#   x remember last path in get
#   x add publish SG
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
import dminutes.Z2K_wrapper as Z2K
reload(Z2K)


ICONPATH = "/zombie/python/dminutes/Z2K_ReleaseTool/icons/Z2K_ReleaseTool/Z2K_REPLACE_LOGO_A1.bmp"

class Z2K_ASSET_replacer(object):

    name = "Z2K_ASSET_replacer"
    version = "_v001"
    OVcurDir = "Z2K_ASSET_replacer_CurDir"
    def __init__(self, theProject="zombtest",currentSceneP="", replacingSceneP="",*args, **kwargs):
        print "init"
        self.theProject = theProject
        self.replacingSceneP = replacingSceneP
        self.currentSceneP = currentSceneP
        if self.currentSceneP in [""]:
            self.currentSceneP,self.currentScene = self.getCurrentScene()
        else:
            self.currentScene = os.normpath( self.currentSceneP).rsplit(os.sep,1)[-1]

        self.theProj=Z2K.projConnect(theProject=self.theProject)

        self.memorisedPath =self.getOV(var=self.OVcurDir)

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


    def getOV(self, var="jipeTmpVar", *args, **kwargs):
        mem =cmds.optionVar( q=var )
        if not mem:
            mem = "c:"
        return mem

    def setOV(self, var="jipeTmpVar",val=0, *args, **kwargs):
        
        print "var type = %s  %s" %( var, type(val) )
        if isinstance(val,int):
                cmds.optionVar( intValue=[ var, val])

        elif isinstance(val,float):
                cmds.optionVar( floatValue=[ var, val])
                
        # all rest go to str
        elif isinstance(val,unicode):
                cmds.optionVar( stringValue=[ var, val])

        elif isinstance(val, str):
                cmds.optionVar( stringValue=[ var, val])

        else :
            print "not registred"

    # ----------------------------------- function ----------------------------------------------
    def getCurrentScene(self,*args, **kwargs):
        # get currentScene name
        currentSceneP,currentScene = cmds.file(q=1,sceneName=True),cmds.file(q=1,sceneName=True,shortName=True)
        print "currentScene=", currentScene
        return [currentSceneP,currentScene]

    def replace(self, currentSceneP="", replacingSceneP="",*args, **kwargs):
        print "replace()"
        print "    -currentSceneP  =",currentSceneP
        print "    -replacingSceneP=", replacingSceneP

        outBool = False
        # check names


        # open the replacing file rename it and save it over the replaced
        try:
            cmds.undoInfo(openChunk=True)
            cmds.file( replacingSceneP, open=True, f=True)
            newName = cmds.file (rename = currentSceneP)
            cmds.file(save=True,f=True)
            cmds.undoInfo(closeChunk=True)
            msg = str(newName)
            icon = "information"
            outBool = True
        except Exception,err:
            print "ERROR IN REPLACING FILE: re-open source file",err
            outBool=False
            cmds.undoInfo(closeChunk=True)
            # re-open old scene and re save
            cmds.file( currentSceneP, open=True, f=True)
            newName = cmds.file (rename = currentSceneP)
            cmds.file(save=True,f=True)
            msg = str(err)
            icon = "warning"

        return outBool,[msg,icon]


    def publishScene(self, pathType="scene_previz", comment="Auto_Release_rockTheCasbah", sgTask="Rig", *args, **kwargs):
        print 'publishScene()'

        PublishedFile_absPath = "None"
        theAssetN,rawType = self.currentScene.rsplit("-v",1)[0].rsplit("_",1)
        print "  -theAssetN=", theAssetN
        print "  -rawType=", rawType

        # publishing for real
       
        PublishedMrc = self.theProj.publishEditedVersion(self.currentSceneP, comment=comment, autoLock=True,sgTask=sgTask)[0]
        print "PublishedMrc=", PublishedMrc
        PublishedFile_absPath = PublishedMrc.absPath()
        print "  -PublishedFile_absPath=", PublishedFile_absPath
            
        

        return PublishedFile_absPath
# save replacingScene as currentScene in the private



class Z2K_ASSET_replacer_GUI(Z2K_ASSET_replacer):
    basePath =  os.environ.get("MAYA_MODULE_PATH").split(";")[0]
    upImg= basePath + ICONPATH


    def __init__(self, theProject="zombtest", currentSceneP="", replacingSceneP="",sgTask="sgTask",*args, **kwargs):
        Z2K_ASSET_replacer.__init__(self, theProject=theProject, currentSceneP=currentSceneP, replacingSceneP=replacingSceneP)

        print self.name,self.version
        self.cf = self.name + self.version
        print "theProject=", self.theProject
        self.pComment = "Auto_Release_rockTheCasbah"
        self.sgTask = sgTask
        
    def getInterfaceValues(self,*args, **kwargs):
        print "getInterfaceValues()"
        self.pComment = cmds.textField(self.BComment,q=1,text=1)


    def btn_getFile(self,*args, **kwargs):
        print ("btn_getFile()")
        outStr =""
        # open dialog box
        theFileP = self.GetFileDialog(jtitle="Select replacing file", OkButtName="Ok", jfileMode=1, jdialogStyle=1, baseDir= self.memorisedPath )
        self.setOV(var=self.OVcurDir, val=theFileP)
        if len(theFileP):
            theFileN =os.path.normpath( theFileP )
            print "*",theFileN.rsplit(".",1)[-1]
            if theFileN.rsplit(".",1)[-1]  in ["ma","mb"]:
                # outStr = theFileN.rsplit(os.sep,1)[-1]
                self.replacingSceneP = theFileN
                outStr = theFileN

                print "yes",outStr
            else:
                outStr = "BAD SCENE TYPE"
        # " update field"
        cmds.textField(self.BFileName,e=1,text=outStr)


    def btn_replaceScene(self,*args, **kwargs):
        print ("btn_replaceScene()")
        self.currentSceneP,self.currentScene = self.getCurrentScene()
        outBool,infoL = self.replace(currentSceneP=self.currentSceneP, replacingSceneP= self.replacingSceneP)

        if not outBool:
            cmds.confirmDialog(title="replace_Info", message=infoL[0], messageAlign="center", icon=infoL[1])


    def btn_publishScene(self,*args, **kwargs):
        print "btn_publishScene()"
        self.getInterfaceValues()
        try: 
            PublishedFile_absPath = self.publishScene(pathType="scene_previz", comment=self.pComment, sgTask=self.sgTask)
            cmds.confirmDialog(title= "PUBLISH info",message="PUBLISH DONE :\r"+PublishedFile_absPath, button="OK", messageAlign="center", icon="information" )
        
        except Exception,err:
            msg= str(err)
            cmds.confirmDialog(title= "PUBLISH info",message= "ERROR : \r"+msg,button="OK", messageAlign="center", icon="warning")


    
    # -------------------------------------- interface -------------------------------------------
    def createWin(self, *args,**kwargs):
        # test si la windows exist / permet d'avoir plusieurs windows grace a var "cf" de la class
        if cmds.window(self.cf, q=True, exists=True):
            cmds.deleteUI(self.cf, window=True)
        #create la window et rename apres
        self.cf = cmds.window(self.cf ,rtf=True, tlb=True, t=self.cf + " " +self.theProject)
        outputW = cmds.window(self.cf, e=True, sizeable=True, )
        
        # show window
        cmds.showWindow(self.cf)
        return outputW


    def insertLayout(self, parent="",*args, **kwargs):

        if parent in [""]:
            parent = self.createWin()

        cmds.setParent(parent)
        self.bigDadL = cmds.frameLayout(label=self.name.center(50), fn="boldLabelFont", lv=0)
        self.layoutImportModule = cmds.columnLayout("layoutImportModule",adj=True)
        cmds.columnLayout(adjustableColumn=True, columnOffset= ["both",5],)
        cmds.tabLayout(tabsVisible=0,borderStyle="full")
        cmds.columnLayout("layoutModule",columnOffset= ["both",0],adj=True,)

        cmds.image(image=self.upImg)
        cmds.columnLayout("layoutImportModule",columnOffset= ["both",0],adj=True,)

        cmds.rowLayout(nc=3,adj=2,manage = 1)
        cmds.text("Replacing File:")
        self.BFileName = cmds.textField()
        self.BgetFile = cmds.button("Get",c= self.btn_getFile,en=1)
        cmds.setParent("..")
        self.BreplaceScene = cmds.button("replace_current_Scene",c= self.btn_replaceScene)
        self.BPublishScene = cmds.button("PUBLISH",c= self.btn_publishScene)
        
        cmds.separator()
        cmds.text("ShotGun Task: {0}".format(self.sgTask),align="left",)
        cmds.rowLayout(nc=2,adj=2)
        cmds.text("Comment:",align="left",)
        
        self.BComment = cmds.textField(text= self.pComment,font="obliqueLabelFont")
        cmds.setParent("..")



# exec
# Z2K_ASSET_replacer_GUIA.insertLayout(parent="")
# Z2K_ASSET_replacer_GUIA = Z2K_ASSET_replacer_GUI(replacingScene="")