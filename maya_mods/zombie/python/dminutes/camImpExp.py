#!/usr/bin/python
# -*- coding: utf-8 -*-
################################################################
# Name    : camImpExp
# Version : 003
# Description : Class permettant l'import et l'export de la camera d'un shot en utisant les ressource de davos
# Author : Jean-Philippe Descoins
# Date : 2014-11-01
# Comment : WIP
# TO DO:
# wip securiser l'export, en cas d'erreur remettre la scene intact
# x gerer import (replace / add to scene)
# x import hecker les problemes de NS
# x import add
# x import mergeRef option
# - Export implementer  checkExported
# x Add import from other scene -> Done in davos asset manager
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

import dminutes.jipeLib_Z2K as jpZ
reload(jpZ)
import dminutes.Z2K_wrapper as Z2K
reload(Z2K)


from davos.core.damtypes import DamShot

import maya.cmds as cmds
from functools import partial




class camImpExp(object):

    def __init__(self,*args, **kwargs):
        print "__init__()"
        # proj inst
        self.curproj = os.environ.get("DAVOS_INIT_PROJECT")
        self.proj=Z2K.projConnect(theProject=self.curproj)
        self.camBigDaddy_grp ="grp_camera"
        self.shot_grp = "shot"
        self.animaticNS = "cam_animatic" 
        self.camNS_prefix ="cam_"



    def getDataCamFilePath(self, theProj="", currentScene="sq6660_sh6660",*args, **kwargs):
        """ Description: Recupere from damas le path private pour sauver le fichier cam exported
                         from maya. Ce fichier est ensuite published avec le publish Damas qui gere increment
                         et commentaire.
            Return : camFileName
            Dependencies : os - 
        """
        
        print "getDataCamFilePath()"
        print "theProj=", theProj
        camFileN =""
        damShot = DamShot(theProj, name=currentScene)
        print "damShot=", damShot
        # camFileN = damShot.getPath("public","camera_scene")
        camFileN = damShot.getPath("private","camera_scene")
        print "camFileNA=", camFileN
        camFileN = os.path.abspath(os.path.normpath(camFileN))
        print "camFileNB=", camFileN
        return camFileN

    def publishCamFile(self,theProj="", currentScene="sq6660_sh6660",comment="", **kwargs):
        """ Description: Publish la camera exported avant à partir du meme private path
            Return : [publicFile,versionFile]
            Dependencies : -
        """
        
        damShot = DamShot(theProj, name=currentScene)
        dataDir = damShot.getResource("public","data_dir")
        topublish = damShot.getPath("private","camera_scene")

        pubFile,versionFile= dataDir.publishFile(topublish, autoLock=True, autoUnlock=True,comment=comment)
        print "pubFile,versionFile=", pubFile,versionFile
        return pubFile,versionFile

    def exportCam(self, theProj="", sceneName="",   checkExported=False, GUI=True, *args, **kwargs):
        """ Description: export la camera de la scene courante ds le data de sceneName
            Return : BOOL
            Dependencies : cmds - getDataCamFilePath() - publishCamFile()
        """
        print "exportCam()"
        errored = False
        errmsg = "UNKNWON"
        print "sceneName OK =", sceneName
        pathToReturn=None
        try:
            cmds.undoInfo( openChunk=True)

            # get output scenepath from Davos
            outPath=self.getDataCamFilePath( theProj=theProj, currentScene=sceneName)
            print "*outPath=", outPath
            
            # check if the scene is conform for unparenting and export

            if not "|"+self.camBigDaddy_grp in cmds.ls(assemblies=1):
                

                if cmds.objExists(self.shot_grp+"|"+self.camBigDaddy_grp):
                    try:
                        
                        # get parent for verification
                        oldParent = cmds.listRelatives(self.camBigDaddy_grp,type="transform",p=1)
                        if oldParent:
                            oldParent = oldParent[0]
                        else:
                            oldParent =""
                        print "CAM Parent_GP=", oldParent
                        if oldParent  in [self.shot_grp]:

                            # unparent group
                            cmds.parent(self.camBigDaddy_grp, world=True)

                            # select gp
                            cmds.select(self.camBigDaddy_grp)

                            # check si le dossier d export exist et le cree si false
                            pathToCheck = os.path.normpath(outPath).rsplit(os.sep,1)[0]
                            print "pathToCheck=", pathToCheck
                            if not os.path.isdir(pathToCheck):
                                print "creating dir:",pathToCheck
                                os.makedirs(pathToCheck)

                            # export to specified data folder
                            print "exporting"
                            pathToReturn = cmds.file(outPath, exportSelected=True, type="mayaAscii",force=True)
                        
                            # reparent group
                            cmds.parent(self.camBigDaddy_grp, oldParent)
                        else:
                            errored=True
                            errmsg = "Bad hierarchy!"
                            raise Exception(errmsg)
                            pathToReturn = None

                    except Exception,err:
                        errored=True
                        errmsg = err
                        print errmsg
                        pathToReturn = None
                        

                    # get shot version 
                    shotVersion = cmds.file(q=1,sceneName=True,shortName=True).split("-",1)[1][:4]
                    if shotVersion[0]  in ["v"] and not len(shotVersion)in [4]:
                        print "* bad version"
                        shotVersion = "UNKNWON"
                    # publish Davos from private exported file
                    result=self.publishCamFile( theProj=theProj, currentScene=sceneName,comment= "From "+shotVersion)
                    print "result=", result

                else:
                    errored=True
                    errmsg = "camera_grp not found!"
                    print errmsg
                # check exported content
                # pas forcement necessaire
                # return
            else:
                errored=True
                errmsg = "there is already a '{0}' in the scene root! Rename it or remove it".format(self.camBigDaddy_grp)
                print errmsg
                pathToReturn = None

            if GUI and not errmsg in ["UNKNWON"]:
                cmds.confirmDialog( title='Error', message='Export impossible mon pote!\n{0}'.format(errmsg), button=['ok'], 
                                    defaultButton='ok', cancelButton='ok', dismissString='ok',icon="warning" )

            cmds.undoInfo( closeChunk=True)
        except:
            cmds.undoInfo( closeChunk=True)


        return pathToReturn


    def importCam(self, theProj="", sceneName="",replaceCam=True, GUI=False, MergeRef=True,refDigit=3, *args, **kwargs):
        """ Description: import la camera de sceneName dans la scene courante
            Return : BOOL
            Dependencies : cmds - getDataCamFilePath()
        """
        print "importCam()"
        impIncr = 1
        camNS= self.camNS_prefix + sceneName
        impNS= sceneName + "_" +str(impIncr).zfill(refDigit)
        print "impNS=", impNS
        addNS = "Z2K_CAM_added"
        tmp_prefixe = "TMP_ORIGINAL_CAM_"
        camExists= False

        # get inPath scene from Davos
        inPath=self.getDataCamFilePath( theProj=theProj, currentScene=sceneName)
        print "*inPath=", inPath

        # check if there is allready imported camera and import NS
        if cmds.namespace(exists=impNS):
            print "impNS=", impNS
            print " allready existing import_NS: incrementing"
            # cmds.namespace( removeNamespace =impNS, mergeNamespaceWithRoot=True)
            impNS = impNS[:-refDigit] + str( int(impNS[-refDigit:])+1).zfill(refDigit)
            print "impNS=", impNS
            

        if replaceCam:
            print "replacing camera"
            # check si il exist deja la camera du shot
            if cmds.objExists(self.shot_grp+ "|"+self.camBigDaddy_grp):
                camExists = True
        
            
            # rename Original if exists
            if camExists:
                print "renaming Original NS"
                original_animaticNS_tmp = tmp_prefixe+self.animaticNS
                cmds.namespace(rename=[self.animaticNS, original_animaticNS_tmp])
                original_camNS_tmp = tmp_prefixe+camNS
                cmds.namespace(rename=[camNS,original_camNS_tmp])
                # rename camGP from scene if present
                print self.shot_grp+ "|"+self.camBigDaddy_grp
                print tmp_prefixe + self.camBigDaddy_grp
                original_Cam_tmp = cmds.rename(self.shot_grp+ "|"+self.camBigDaddy_grp, tmp_prefixe + self.camBigDaddy_grp )

            
            # import in scene with the good configuration of NS etc
            curRef=cmds.file( inPath,namespace=impNS ,reference=True)
            print "curRef=", curRef

            # import ref in the scene for real
            if MergeRef :
                cmds.file(curRef,importReference=True)

            # parent imported cam to base group
            cmds.parent(impNS+":"+self.camBigDaddy_grp, self.shot_grp)
            
            # delete original renamed camGP if replace true
            if replaceCam:
                print "replacing camera"
                if camExists:
                    # delete tmp cam and NS
                    cmds.delete(original_Cam_tmp)
                    cmds.namespace( removeNamespace =original_animaticNS_tmp, mergeNamespaceWithRoot=True)
                    cmds.namespace( removeNamespace =original_camNS_tmp, mergeNamespaceWithRoot=True)
                else:
                    try:
                        # deleting original camNS and animatic NS
                        cmds.namespace( removeNamespace = self.animaticNS, mergeNamespaceWithRoot=True)
                        cmds.namespace( removeNamespace = camNS, mergeNamespaceWithRoot=True)
                    except:
                        pass
                        print "no namespace to delete"
                cmds.namespace( removeNamespace =impNS, mergeNamespaceWithRoot=True)
        
        else:
            print "adding camera"
            # import in scene with the good configuration of NS etc
            curRef=cmds.file( inPath,namespace=impNS ,reference=True)
            print "curRef=", curRef
            
           # import ref in the scene for real
            if MergeRef :
                cmds.file(curRef,importReference=True)
            

    # ----------- GUI -----------------------------------------------

    def btn_exportCam(self,*args, **kwargs):
        print "btn_exportCam()"
        res = cmds.confirmDialog( title='Confirm', message='Are you sure?', button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
        if res == "Yes":
            self.exportCam (theProj=self.proj, sceneName=jpZ.getShotName(), )

    def btn_importCamReplace(self,*args, **kwargs):
        print "btn_importCamReplace()"
        res = cmds.confirmDialog( title='Confirm', message='Are you sure?', button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
        if res == "Yes":
            self.importCam (theProj=self.proj, sceneName=jpZ.getShotName(), replaceCam=True, GUI=True, MergeRef=True )
    
    def btn_importCamAdd(self,*args, **kwargs):
        print "btn_importCamAdd()"
        res = cmds.confirmDialog( title='Confirm', message='Are you sure?', button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
        if res == "Yes":
            self.importCam (theProj=self.proj, sceneName=jpZ.getShotName(), replaceCam=False, GUI=True, MergeRef=False )


    def createWindow(self,*args, **kwargs):
        windName = "Z2K_camImpExp_GUI"
        if cmds.window(windName, q=True, exists=True):
            cmds.deleteUI(windName)

        cmds.window(windName)
        cmds.tabLayout(tabsVisible=0,borderStyle="full")
        cmds.frameLayout(lv=0)
        cmds.text("Import Export Camera :")
        cmds.tabLayout(tabsVisible=0,borderStyle="full",)
        cmds.columnLayout(adj=1,rs=2)
        cmds.button("Export_cam", c= self.btn_exportCam )
        cmds.button("Import_cam(replace current)", c= self.btn_importCamReplace )
        cmds.button("Import_cam(add reference)  ", c= self.btn_importCamAdd )
        cmds.showWindow()

# test de la class
if __name__ in ["__main__"]:
    camImpExpI = camImpExp()
    camImpExpI.createWindow()



##################################################################
# using the class
##################################################################

# # intanciate the class
# camImpExpI = camImpExp()
# # import et remplace dans la hierarchy
# self.importCam (theProj=self.proj, sceneName=jpZ.getShotName(), replaceCam=True, GUI=True, MergeRef=True )

# # import et ajoute la camera en reference
# self.importCam (theProj=self.proj, sceneName=jpZ.getShotName(), replaceCam=False, GUI=True, MergeRef=False )

# # export la cam de la scene
# self.exportCam (theProj=self.proj, sceneName=jpZ.getShotName(), )

