#!/usr/bin/python
# -*- coding: utf-8 -*-
################################################################
# Name    : infoSetExp
# Version : 001
# Description : Export to a file les coordonnées des global et local SRT des set d'une scene
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







import maya.cmds as cmds
import os
import dminutes.jipeLib_Z2K as jpZ
reload(jpZ)


class infoSetExp(object):
    def __ini__(self,*args, **kwargs):
        print "__init__()"

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
        camFileN = damShot.getPath("private","infoSet_file")
        print "camFileNA=", camFileN
        camFileN = os.path.abspath(os.path.normpath(camFileN))
        print "camFileNB=", camFileN
        return camFileN


    def constructDico(self,inCTRL=["BigDaddy","set*:Global_SRT","set*:Local_SRT"],*args, **kwargs):

        # construct output dict
        CTRL = cmds.ls(inCTRL)
        infoDict ={}

        for i in CTRL:
            infoDict[i] = {}
            print i
            infoDict[i]["translate"] = cmds.xform(i,q=1,t=True)
            infoDict[i]["rotate"] = cmds.xform(i,q=1,t=True)
            infoDict[i]["scale"] = cmds.xform(i,q=1,r=1,s=True)
            print "    t=",infoDict[i]["translate"]
            print "    r=",infoDict[i]["rotate"]
            print "    s=",infoDict[i]["scale"]


# get private path
 outPath=self.getDataCamFilePath( theProj=theProj, currentScene=sceneName)
print "*outPath=", outPath
# write the file


# publish the file
# get shot version 
shotVersion = cmds.file(q=1,sceneName=True,shortName=True).split("-",1)[1][:4]
if shotVersion[0]  in ["v"] and not len(shotVersion)in [4]:
    print "* bad version"
    shotVersion = "UNKNWON"
# publish Davos from private exported file
result=self.publishCamFile( theProj=theProj, currentScene=sceneName, comment= "From "+shotVersion)
print "result=", result