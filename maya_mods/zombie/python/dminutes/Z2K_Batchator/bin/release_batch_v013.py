#!/usr/bin/python
# -*- coding: utf-8 -*-
################################################################
# Name    : Z2K_Batchator
# Version : 013
# Description : Script to batch z2k assets (Publish/release/SHOTGUN/prepublish_Scripts/prerelease_Scripts/locks)
# Author : Jean-Philippe Descoins
# Date : 2014-04-01
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



# TO DO
# x secure same way pre_textOUTL
# x convert to class to integrate the debug file path inside it
# wip clean launch
# x add publish inside batch
# - clean and separate the publish and release process
# - think about gui
# - 
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# MAYAPI LAUNCHER FOR Z2K-----------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------


import os,sys
# add Z2K custom environ before launching mayapy
# path="C:/Golaem/GolaemCrowd-4.2.0.1-Maya2016/plug-ins;C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/Toonkit_module/Maya2016/plug-ins;C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/solidangle/mtoadeploy/2016/plug-ins;C:/Program Files/Autodesk/Maya2016/bin/plug-ins;C:/Program Files/Autodesk/Maya2016/plug-ins/substance/plug-ins;C:/Program Files/Autodesk/Maya2016/plug-ins/xgen/plug-ins;C:/Program Files/Autodesk/Maya2016/plug-ins/bifrost/plug-ins;C:/Program Files/Autodesk/Maya2016/plug-ins/fbx/plug-ins;"
# os.environ["MAYA_PLUG_IN_PATH"] = path

# curproj ="zombillenium"  # "zombtest" / "zombillenium" 
# if curproj in ["zombillenium"]:
#     theFolder= "zomb"
# if curproj in ["zombtest"]:
#     theFolder= "zombtest"

# ENVS = {
#         "ZOMB_ASSET_PATH":"\\\\ZOMBIWALK\\Projects\\"+theFolder+"\\asset",
#         "ZOMB_SHOT_PATH":"\\\\ZOMBIWALK\\Projects\\"+theFolder+"\\shot",
#         "ZOMB_OUTPUT_PATH":"\\\\ZOMBIWALK\\Projects\\"+theFolder+"\\output",
#         "ZOMB_TOOL_PATH":"\\\\ZOMBIWALK\\Projects\\"+theFolder+"\\tool",

#         "PRIV_ZOMB_PATH":"\\\\ZOMBIWALK\\Projects\\private\\$DAVOS_USER\\"+theFolder,
#         "DAVOS_INIT_PROJECT":curproj,
#         "DAVOS_CONF_PACKAGE":'zomblib.config',
#         "MAYA_MODULE_PATH":"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods",
#         "Z2K_PYTHON_SITES:":"C:/jipe_Local/z2k-pipeline-toolkit/python/mayapy-2016",

#         }

# for i,j in ENVS.iteritems():
#     os.environ[i]=j


# append all sys path including the one loaded whith the modules
mayaSysPath= ["C:/Program Files/Autodesk/Maya2016/bin",
"C:/jipe_Local/z2k-pipeline-toolkit/python/pypeline-tool-devkit",
"C:/jipe_Local/z2k-pipeline-toolkit/python/davos-dev",
"C:/jipe_Local/z2k-pipeline-toolkit/python/mayapy-2016-site/pillow-3.0.0.dev0-py2.7-win-amd64.egg",
"C:/jipe_Local/z2k-pipeline-toolkit/python",
"C:/Program Files/Autodesk/Maya2016/plug-ins/bifrost/scripts/presets",
"C:/Program Files/Autodesk/Maya2016/plug-ins/bifrost/scripts",
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/Toonkit_module/Maya2016/scripts",
"C:/Program Files/Autodesk/Maya2016/plug-ins/fbx/scripts",
"C:/Golaem/GolaemCrowd-4.2.0.1-Maya2016/scripts",
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/solidangle/mtoadeploy/2016/scripts",
"C:/Program Files/Autodesk/Maya2016/plug-ins/substance/scripts",
"C:/Program Files/Autodesk/Maya2016/plug-ins/xgen/scripts/cafm",
"C:/Program Files/Autodesk/Maya2016/plug-ins/xgen/scripts/xgenm",
"C:/Program Files/Autodesk/Maya2016/plug-ins/xgen/scripts/xgenm/ui",
"C:/Program Files/Autodesk/Maya2016/plug-ins/xgen/scripts/xgenm/xmaya",
"C:/Program Files/Autodesk/Maya2016/plug-ins/xgen/scripts/xgenm/ui/brushes",
"C:/Program Files/Autodesk/Maya2016/plug-ins/xgen/scripts/xgenm/ui/dialogs",
"C:/Program Files/Autodesk/Maya2016/plug-ins/xgen/scripts/xgenm/ui/fxmodules",
"C:/Program Files/Autodesk/Maya2016/plug-ins/xgen/scripts/xgenm/ui/tabs",
"C:/Program Files/Autodesk/Maya2016/plug-ins/xgen/scripts/xgenm/ui/util",
"C:/Program Files/Autodesk/Maya2016/plug-ins/xgen/scripts/xgenm/ui/widgets",
"C:/Program Files/Autodesk/Maya2016/plug-ins/xgen/scripts",
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/zombie/scripts",
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/zombie/python",
"C:/Program Files/Autodesk/Maya2016/bin/python27.zip",
"C:/Program Files/Autodesk/Maya2016/Python/DLLs",
"C:/Program Files/Autodesk/Maya2016/Python/lib",
"C:/Program Files/Autodesk/Maya2016/Python/lib/plat-win",
"C:/Program Files/Autodesk/Maya2016/Python/lib/lib-tk",
"C:/Program Files/Autodesk/Maya2016/bin",
"C:/Program Files/Autodesk/Maya2016/Python",
"C:/Program Files/Autodesk/Maya2016/Python/lib/site-packages",
"C:/Program Files/Autodesk/Maya2016/Python/lib/site-packages/win32",
"C:/Program Files/Autodesk/Maya2016/Python/lib/site-packages/win32/lib",
"C:/Program Files/Autodesk/Maya2016/Python/lib/site-packages/Pythonwin",
"C:/jipe_Local/z2k-pipeline-toolkit/python/mayapy-2016-site",
"C:/Program Files/Autodesk/Maya2016/bin/python27.zip/lib-tk",
"C:/Users/jipe/Documents/maya/2016/prefs/scripts",
"C:/Users/jipe/Documents/maya/2016/scripts",
"C:/Users/jipe/Documents/maya/scripts",
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/Toonkit_module/Maya2016/scripts/../Python/lib/site-packages",
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/Toonkit_module/Maya2016/scripts/../../Python/Oscar",
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/Toonkit_module/Maya2016/scripts",
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/solidangle/mtoadeploy/2016/extensions",
"C:/jipe_Local/00_JIPE_SCRIPT/PythonTree/",
]

for p in mayaSysPath:
    sys.path.append(p)

import maya.standalone
maya.standalone.initialize(name='python')

# load pour de vrai tout les sys pasth deja present dans le os .env mais pas dans sys path
# for p in os.environ["PYTHONPATH"].split(";"):

#     if os.path.normpath(p) not in os.environ:
#         sys.path.append(p)
#     else:
#         print "all ready"










# load all plugins
# cmds.loadPlugin( allPlugins=True)


# ---------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------
#  releaze tool batch -------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------
# set python path for special lib in custom python path
execfile(r"C:/jipe_Local/00_JIPE_SCRIPT/PythonTree/Maya_jipeLib_Setter_v0.3.py")

#  import
# import RIG_WORKGROUP.jipe_lib.lib.mayaFunc as jpm
# reload (jpm)
# import RIG_WORKGROUP.jipe_lib.lib.jipe_IO as jpIO
# reload (jpIO)





from davos.core import damproject
from davos.core.damtypes import DamAsset
import os
import dminutes.Z2K_ReleaseTool.Z2K_ReleaseTool_batchable as Z2KR
reload (Z2KR)

import dminutes.Z2K_wrapper as Z2K
reload(Z2K)
import dminutes.jipeLib_Z2K as jpZ
reload(jpZ)

import maya.cmds as cmds
import maya.mel as mel


import dminutes.Z2K_Batchator.Z2K_Release_Batch_CONFIG_v13 as Batch_CONFIG
reload(Batch_CONFIG)
from dminutes.Z2K_Batchator.Z2K_Release_Batch_CONFIG_v13 import *

print "DEBUGFILE=", DEBUGFILE

# --------------------------------------------------------------------


curproj = os.environ.get("DAVOS_INIT_PROJECT")
print "curproj=", curproj

class Z2K_ReleaseBatch(object):

    def __init__(self,
        sceneL =[] , openInMaya=True, readOnly=True, publishMayaFile=False, releaseMayaFile =False,forceReleaseDude=False, backupfiles=True, unlockFile = True,
        preRelease_pyScriptL=[], prePublish_pyScriptL=[], backupSuffix= "_backup", deleteBackuped=True,
        sourceAssetType="previz_scene", assetCat = "chr",
        destinationAssetType= "previz_ref",
        projConnectB= True, theProject="zombtest",
        theComment= "Auto_Release_rockTheCasbah !",
        sgTask = "Rig_Previz",
        debug= False, debugFile = "",
        userConfirm = True,
        *args, **kwargs
        ):
        print "Z2K_ReleaseBatch(INIT)"
        # debug file delete handling
        if os.path.isfile(debugFile):
            os.remove(debugFile)

        # wrap all var inside class
        self.sceneL= sceneL
        self.openInMaya= openInMaya
        self.readOnly= readOnly
        self.publishMayaFile= publishMayaFile
        self.releaseMayaFile= releaseMayaFile
        self.forceReleaseDude = forceReleaseDude
        self.backupfiles= backupfiles
        self.unlockFile= unlockFile
        self.preRelease_pyScriptL= preRelease_pyScriptL
        self.prePublish_pyScriptL= prePublish_pyScriptL
        self.backupSuffix= backupSuffix
        self.deleteBackuped= deleteBackuped
        self.sourceAssetType= sourceAssetType
        self.assetCat= assetCat
        self.destinationAssetType= destinationAssetType
        self.projConnectB= projConnectB
        self.theProject= theProject
        self.theComment= theComment
        self.sgTask= sgTask
        self.debug= debug
        self.debugFile= debugFile

        

        self.counter = 0
        self.outputD = {}
        self.okL = []
        self.preRelease_text = []
        self.failL=[]
        self.publishedL = []
        self.releasedL=[]

        self.preRelease_result = False
        self.prePublish_result = False

        self.finalOKL = []

        # # intantiate class Release tool
        # self.Z2K_ReleaseToolI = Z2KR.Z2K_ReleaseTool(sourceAsset="", sourceAssetType=self.sourceAssetType, assetCat =self.assetCat,
        #                         destinationAsset="", destinationAssetType= self.destinationAssetType,
        #                         projConnectB= self.projConnectB, theProject=self.theProject,
        #                         theComment= self.theComment,
        #                         debug= self.debug ,
        #                         )
        
        
        if userConfirm:                
            self.userVerify()
        self.batch()


    #----------------------------- jipe func ------------------
    def userVerify(self,*args, **kwargs):
        print " "
        print "#"*120
        print "#        userVerify()"
        print "#"*120
        print " "

        # print all verifiying important information in a readable way
        print "SceneL:"
        for l in self.sceneL:
            print "  -",l
        print "  TOTAL: %s" % len(self.sceneL)
        print "-"*120

        theDict={"theProject":self.theProject,
                "publishMayaFile":self.publishMayaFile,
                "releaseMayaFile":self.releaseMayaFile,
                "unlockFile":self.unlockFile,
                "theComment":self.theComment,
                "debugFile":self.debugFile,
                "assetCat": self.assetCat,
                "sgTask" : self.sgTask,
                    }
        
        
        # print
        for i,j in theDict.iteritems():
            print i.ljust(15),"=",j

        # print si les paths de script sont ok
        print "Script List:"

        for i in self.preRelease_pyScriptL:
            print "****",i
            print"  -{0} : {1}".format( os.path.normpath(i).rsplit(os.sep,1)[-1],  os.path.isfile(i) )
        for i in self.prePublish_pyScriptL:
            print "****",i
            print"  -{0} : {1}".format( os.path.normpath(i).rsplit(os.sep,1)[-1],  os.path.isfile(i) )

        print " "
        print "#"*120
        print " "
        
        # put script in pause waiting for enter press
        raw_input("PRESS ENTER TO START the BATCH")

    def printF(self, texta="",openMode = "a",printN=True,*args,**kwargs):
        with open(self.debugFile, openMode) as the_file:
                the_file.write( str(texta)+ u"\r" )
        if printN:
            print  str(texta)


    def jipeExec(self, scriptPath="",*args,**kwargs):
        # exec file function
        # scriptPath = os.path.normpath(scriptPath)

        with open(scriptPath) as f:
            fData =f.read()
        
        # executing as mel script or python script
        ns = {}
        if ".mel" in scriptPath[-4:]:
            print "\t","# MEL script mode"
            mel.eval(fData) in ns
        
        if ".py" in scriptPath[-3:]:
            print "\t","# PYTHON script mode"
            exec (fData) in ns
            # execfile(scriptPath)

        return ns

    #---------------------------- Motor --------------------

    def batch(self,*args, **kwargs):


        # BATCH loop --------------------------------------------------------------------------------
        for scene in self.sceneL:
            # self.outputD[scene]= {}
            self.counter +=1
            coun = str(self.counter)
            
            self.outputD[scene]= {}

            result=False
            print "\n\n","*"*80,"\n","scene = %s" %( scene ),"\n","*"*80,"\n",

            # # get scene info /context WIP a remplacer par un check sur le filePath et non a partir de la maya command
            # infoDict = jpZ.infosFromMayaScene()
            # print "infoDict=", infoDict 
            # # 
            # if not infoDict and not "Ref" in infoDict["assetType"][-3:] :
            #     printF("THIS SCENE IS NOT RELEASABLE! ") 
            # else:

            #     # # intantiate class Release tool
            #     Z2K_ReleaseToolI = z2kR.Z2K_ReleaseTool(sourceAsset=infoDict["assetName"], sourceAssetType=infoDict["assetType"]+"_scene", assetCat = infoDict["assetCat"],
            #                     destinationAsset=infoDict["assetName"], destinationAssetType= infoDict["assetType"]+"_ref",
            #                     projConnectB= self.projConnectB, theProject=self.theProject,
            #                     theComment= "released From " + infoDict["version"] ,
            #                     debug=self.debug,
            #                     )
            # intantiate class Release tool
            self.Z2K_ReleaseToolI = Z2KR.Z2K_ReleaseTool(sourceAsset=scene, sourceAssetType=self.sourceAssetType, assetCat =self.assetCat,
                        destinationAsset="", destinationAssetType= self.destinationAssetType,
                        projConnectB= self.projConnectB, theProject=self.theProject,
                        theComment= self.theComment,
                        debug= self.debug ,
                        )

            # opening the file or not -----------------------------------------------
            if self.openInMaya in [True,1]:
                try:
                    # open file / edit
                    path_private_toEdit=self.Z2K_ReleaseToolI.openAsset(sourceAsset=scene, sourceAssetType=self.sourceAssetType, readOnly=self.readOnly, autoUnlock=True)
                    self.printF(texta="@@@@@@@@@@@@@@@@@@@@@@ OPENED: "+scene +" @@@@@@@@@@@@@@@@@@@@@@@@@@@@", openMode="a")
                    self.outputD[scene]["Opened"]=True
                except Exception,err:
                    self.printF(texta="ERROR_openInMaya: \r\t{0}".format(err), openMode="a", printN=True)
                    self.outputD[scene]["ERROR_openInMaya"]= "\r\t{0}".format(err)


            # backup handling to another folder  ------------------------------------
            if self.backupfiles in [True,1]:
                print "\t","self.backupfiles: TRUE"
                BACKUP_tmp_file = path_private_toEdit + self.backupSuffix 
                shutil.copy(path_private_toEdit, BACKUP_tmp_file )
                self.outputD[scene]["Backuped"]=True


            # ----------------------------------------------------------------------------------------------------------------------------
            # execution des PRE-PUBLISH SCRIPTS  WIP--------------------------------------------------------------------------------------
            # ----------------------------------------------------------------------------------------------------------------------------
            try:
                self.scrTextOUTL = []
                self.prePublish_result = False
                scrResultL=[]
                self.outputD[scene]["prePublish_ScriptL"]=self.prePublish_pyScriptL
                for script in self.prePublish_pyScriptL:
                    try:
                        self.printF( texta="-"*40 )
                        self.printF( texta="@ scriptName= {0}".format( os.path.normpath( script ).rsplit(os.sep,1)[-1])  )
                        
                        execOutputResultD = self.jipeExec(scriptPath=script)
                        # self.printF(texta="      exec_Output_ResultD={0}".format(execOutputResultD), openMode="a", printN=True)
                        tmpResult = execOutputResultD["result"]
                        scrResultL.append(tmpResult)
                        # print "    ->result=",tmpResult, script.rsplit(os.sep,1)[-1]
                        self.printF( texta="@---->result={0}".format(tmpResult) )
                    except Exception,err:
                        scrResultL.append(False)
                        tmpResult = "ERROR:"+str(err)
                        self.printF(texta=tmpResult, openMode="a", printN=True)
                        self.scrTextOUTL.append( tmpResult )
                    self.outputD[scene]["    -"+script]= tmpResult

                if not False in scrResultL:
                    self.prePublish_result =True


                else:
                    self.prePublish_result= False
            except Exception,err:
                self.prePublish_result =False
                self.scrTextOUTL.append( "ERROR:"+str(err) ) 
                self.failL.append(scene) 


            self.printF( texta="*"*80 )
            self.printF( texta="    prePublish SCRIPTS RESULT= {0}".format(self.prePublish_result) )
            self.printF( texta="*"*80 )
            self.printF( texta="*"*80 )

            self.outputD[scene]["prePublish_RESULT"]=self.prePublish_result        
            self.outputD[scene]["prePublish_RESULT_detail"]= self.scrTextOUTL

            # publish  file ---------------------------------------------------------
            print "self.prePublish_result=", self.prePublish_result
            if self.prePublish_result :
                try:
                    if self.publishMayaFile in [True,1]:
                        print "\n","* PUBLISHING"
                        # Z2KR.publishScene(pathType=self.destinationAssetType , comment=self.theComment, sgTask=self.sgTask)
                        self.printF(texta="PUBLISHING SCENE:{0}".format(scene), openMode="a")
                        outfile = Z2K.publishEditedVersionSG(proj=self.Z2K_ReleaseToolI.proj, path_private_toPublish=path_private_toEdit, comment=self.theComment, 
                                                    sgTask=self.sgTask,)
                        self.publishedL.append(scene)
                        self.outputD[scene]["published"]= True 
                        self.outputD[scene]["published_file"]= outfile 
                        print "********************* PUBLISHED *********************"
                
                except Exception,err:
                    print "ERRRRROR OCCURED IN PUBLISH"
                    self.printF(texta="ERROR_publish: \r\t{0}".format(err), openMode="a", printN=True)
                    self.outputD[scene]["ERROR_publish"]=  "\r\t{0}".format(err)

            # ----------------------------------------------------------------------------------------------------------------------------
            # execution des PRE-RELEASE SCRIPTS ------------------------------------------------------------------------------------------
            # ----------------------------------------------------------------------------------------------------------------------------

            try:
                self.scrTextOUTL = []
                scrResultL=[]
                self.preRelease_result = False
                self.outputD[scene]["preRelease_ScriptL"]=self.preRelease_pyScriptL
                for script in self.preRelease_pyScriptL:
                    try:
                        self.printF( texta="-"*40 )
                        self.printF( texta="@ scriptName= {0}".format( os.path.normpath( script ).rsplit(os.sep,1)[-1])  )
                        
                        execOutputResultD = self.jipeExec(scriptPath=script)
                        # self.printF(texta="      exec_Output_ResultD={0}".format(execOutputResultD), openMode="a", printN=True)
                        tmpResult = execOutputResultD["result"]
                        scrResultL.append(tmpResult)
                        # print "    ->result=",tmpResult, script.rsplit(os.sep,1)[-1]
                        self.printF( texta="@---->result={0}".format(tmpResult) )
                        
                    except Exception,err:
                        scrResultL.append(False)
                        tmpResult = "ERROR:"+str(err)
                        self.printF(texta=tmpResult, openMode="a", printN=True)
                        self.scrTextOUTL.append( tmpResult )
                    self.outputD[scene]["    -"+script]= tmpResult

                if not False in scrResultL:
                    self.preRelease_result =True
                    self.okL.append(scene)
                else:


                    self.preRelease_result= False  
                    self.failL.append(scene) 

            except Exception,err:
                print "ERRRRROR OCCURED IN PRE-RELEASE"
                self.preRelease_result =False
                self.scrTextOUTL.append( "ERROR:"+str(err) )
                self.failL.append(scene) 


            self.printF( texta="*"*80 )
            self.printF( texta="    preRelease_RESULT= {0}".format(self.preRelease_result) )
            self.printF( texta="*"*80 )
            self.outputD[scene]["preRelease_RESULT"]=self.preRelease_result
            self.outputD[scene]["preRelease_detail"]= self.scrTextOUTL

            #---------------------------------------------------------------------------------------------------------------

            # Release file ---------------------------------------------------------
            # if (pubres == 1 and relres==1) or (pub ==0 and relres==1):
            # if self.prePublish_result and self.preRelease_result:
            ReleaseAssetB = False
            if self.forceReleaseDude in [True,1]:
                ReleaseAssetB =True
                print "********************* YOU ARE FORCING DA RELEASE DUDE *********************\n\n"
            else:
                if (self.prePublish_result in [True,1] and self.preRelease_result in [True,1]) or (self.publishMayaFile in [False,0] and self.preRelease_result in [True,1]):
                    self.finalOKL.append(scene)
                    ReleaseAssetB =True

            if ReleaseAssetB:
                try:
                    # releasing
                    if self.releaseMayaFile in [True,1]:
                        print "\n","* RELEASING"
                        self.printF(texta="RELEASING SCENE:{0}".format(scene), openMode="a")


                        outfile = self.Z2K_ReleaseToolI.release_Asset( destinationAsset=scene, destinationAssetType = self.destinationAssetType,
                                                        theComment="",sgTask=self.sgTask)
                        self.releasedL.append(scene)
                        self.outputD[scene]["released"]= True
                        self.outputD[scene]["released_file"]= outfile  
                        self.outputD[scene]["sgTask"]= self.sgTask     
                        print "********************* RELEASED *********************"
                        
                        
                except Exception, err:
                    print "ERRRRROR OCCURED IN RELEASE"
                    # print "    *", self.sourceAsset, self.sourceAssetType
                    print "    *", scene, self.destinationAssetType, self.theComment
                    print "    ", Exception, err
                    self.printF(texta="ERROR_release: \r\t{0}".format(err), openMode="a", printN=True)
                    self.outputD[scene]["ERROR_release"]=  "\r\t{0}".format(err)



            # deleting the backuped_File
            if self.deleteBackuped in [True,1]:
                print "\t","DELETING Backuped File"
                if os.path.isfile(BACKUP_tmp_file):
                    os.remove( BACKUP_tmp_file )
                    self.outputD[scene]["backup_deleted"]=True   


            # unLocking the file
            if self.unlockFile :
                assetName=scene
                print "assetName",assetName
                print "self.sourceAssetType=", self.sourceAssetType
                drcF=Z2K.getDrcF(proj=self.Z2K_ReleaseToolI.proj, assetName=assetName, pathType= self.sourceAssetType )
                print "drcF=", drcF
                theLock=Z2K.getLock(drcF)
                self.printF(texta="UNLOCKING SCENE:{0}".format(scene), openMode="a")
                print "theLock=", theLock
                Z2K.unlock(drcF)
                theLock=Z2K.getLock(drcF)
                if theLock in [""]:
                    theLock = "UNLOCKED"
                print "theLock=", theLock
                self.outputD[scene]["lock_state"]=theLock

        # print "scrResultL=", scrResultL

        self.printF(texta="@"*120 ,openMode="a")
        self.printF(texta="@"*120 ,openMode="a")
        self.printF(texta="@"*120 ,openMode="a")
        self.printF(texta=" " ,openMode="a")
        self.printF ( texta="@ FINAL_RESULT = {0} / {1}   -published: {2}    -released:{3}".format( len(self.finalOKL),self.counter,len(self.publishedL),len(self.releasedL), ) )
        self.printF(texta=" " ,openMode="a")
        self.printF(texta="@"*120 ,openMode="a")

        for i,dico in sorted( self.outputD.iteritems() ):
            self.printF(texta="* "+i, openMode="a")
            for k,l in sorted( dico.iteritems() ):
                self.printF(texta="    {0} = {1}".format(k.ljust(20),l) ,openMode="a")

        self.printF(texta=" " ,openMode="a")
        self.printF(texta="@"*120 ,openMode="a")


        self.printF(texta=" " ,openMode="a")
        self.printF ( texta="- failL:{0} -{1}".format( len(self.failL),self.failL ), openMode="a")
        self.printF ( texta="- publishedL:{0} -{1}".format( len(self.publishedL),self.publishedL ), openMode="a")
        self.printF ( texta="- releasedL:{0} -{1}".format( len(self.releasedL),self.releasedL ), openMode="a")





#--------------------------------------------------------------------------------------------------------------------
# ----------------- EXEC --------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------


print "!!!!!!!!!!!!!!!!!!!!!!!!!! curproj=", curproj
# get asset list from batch CONFIG file
assetToReleaseL= BATCH_ASSET_LIST
for k in assetToReleaseL:
    print "* ",k


# launch the batch
# DON'T FORGET TO SET WELL THE PROJECT AND OPTIONS
# launcher
Z2K_ReleaseBatchI = Z2K_ReleaseBatch(  
    sceneL =assetToReleaseL , 
    projConnectB= True, theProject=curproj,
    assetCat = ASSETCAT, #"chr","set","prp"
    sourceAssetType= SOURCE_ASSET_TYPE, 
    destinationAssetType= DESTINATION_ASSET_TYPE,
    sgTask = SGTASK, # wip not in use "Rig Auto"
    theComment= THECOMMENT, #"Auto_Release_rockTheCasbah !","First_publish_RockTheCasbah"
    openInMaya= OPENINMAYA, readOnly= READONLY, 
    publishMayaFile= PUBLISHMAYAFILE, 
    releaseMayaFile = RELEASEMAYAFILE,  
    forceReleaseDude = FORCERELEASE,
    unlockFile = UNLOCKFILE,
    backupfiles=0, backupSuffix= "_backup", deleteBackuped=0,
    prePublish_pyScriptL = PREPUBLISH_PYSCRIPTL,
    preRelease_pyScriptL= PRERELEASE_PYSCRIPTL,
    debugFile = DEBUGFILE,# CHANGE THIS PATH ALSO DANS   DEBUGFILE_PREVIZ_SET
    userConfirm = True,

    )


# ATTENTION LE LAUNCH DU BATCH PREND AUJOURD HUI LE STARTPU DE SEB DONC TOUJOURS DANS LE PROJET ZOMBILLENIUM
# TEST SUR chr_devTeam_testing