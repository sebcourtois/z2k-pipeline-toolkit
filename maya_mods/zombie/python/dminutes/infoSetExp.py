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







import os

import dminutes.jipeLib_Z2K as jpZ
reload(jpZ)
import dminutes.Z2K_wrapper as Z2K
reload(Z2K)
import json

from davos.core.damtypes import DamShot

import maya.cmds as cmds
from functools import partial


class infoSetExp(object):
    def __init__(self, *args, **kwargs):
        print "__init__()"
        self.curproj = os.environ.get("DAVOS_INIT_PROJECT")
        self.proj = Z2K.projConnect(theProject=self.curproj)


    def getDataInfoSetFilePath(self, currentScene="sq6660_sh6660", *args, **kwargs):
        """ Description: Recupere from damas le path private pour sauver le fichier cam exported
                         from maya. Ce fichier est ensuite published avec le publish Damas qui gere increment
                         et commentaire.
            Return : camFileName
            Dependencies : os - 
        """

        print "getDataInfoSetFilePath()"
        print "theProj=", self.proj
        outFileName = ""
        damShot = DamShot(self.proj, name=currentScene)
        print "damShot=", damShot
        # outFileName = damShot.getPath("public","camera_scene")
        outFileName = damShot.getPath("private", "infoSet_file")
        print "outFileNameA=", outFileName
        outFileName = os.path.abspath(os.path.normpath(outFileName))
        print "outFileNameB=", outFileName
        return outFileName

    def publishInfoSetFile(self, currentScene="sq6660_sh6660", comment="", **kwargs):
        """ Description: Publish la camera exported avant à partir du meme private path
            Return : [publicFile,versionFile]
            Dependencies : -
        """

        damShot = DamShot(self.proj, name=currentScene)
        dataDir = damShot.getResource("public", "data_dir")
        topublish = damShot.getPath("private", "infoSet_file")

        pubFile, versionFile = dataDir.publishFile(topublish, autoLock=True, autoUnlock=True, comment=comment)
        print "pubFile,versionFile=", pubFile, versionFile
        return pubFile, versionFile

    def constructDico(self, inCTRL=["set_*:BigDaddy", "set_*:Global_SRT", "set_*:Local_SRT"], GUI=True, *args, **kwargs):
        # construct output dict
        errmsg = "UNKNWON"
        CTRL = cmds.ls(inCTRL)
        infoDict = {}
        if len(CTRL):
            for i in CTRL:
                infoDict[i] = {}
                print i
                infoDict[i]["translate"] = cmds.xform(i, q=1, t=True)
                infoDict[i]["rotate"] = cmds.xform(i, q=1, ro=True)
                infoDict[i]["scale"] = cmds.xform(i, q=1, r=1, s=True)
                print "    t=", infoDict[i]["translate"]
                print "    r=", infoDict[i]["rotate"]
                print "    s=", infoDict[i]["scale"]
        else:
            errmsg = "Nothing to export in this scene,CHECK your REFERENCES!"

        return infoDict

    def export(self, sceneName="", *args, **kwargs):
        # get private path
        outPath = self.getDataInfoSetFilePath(currentScene=sceneName)
        print "*outPath=", outPath
        # write the file

        # check si le dossier d export exist et le cree si false
        pathToCheck = os.path.normpath(outPath).rsplit(os.sep, 1)[0]
        print "pathToCheck=", pathToCheck
        if not os.path.isdir(pathToCheck):
            print "creating dir:", pathToCheck
            os.makedirs(pathToCheck)

        # write file std
        with open(outPath, "w") as f:
            f.write(str(self.constructDico()))

        # get shot version
        # scnFilename = os.path.basename(cmds.file(q=1, l=1)[0])
        scnFilename = pymel.core.sceneName() 
        shotVersion = scnFilename.split("-", 1)[1][:4]
        fromTxt = scnFilename.split(".", 1)[0].rsplit("_", 1)[-1]
        if shotVersion[0]  in ["v"] and not len(shotVersion)in [4]:
            print "* bad version"
            shotVersion = "UNKNWON"
        print "shotVersion=", shotVersion

        # publish Davos from private exported file
        sComment = "From " + fromTxt
        sAddComment = kwargs.pop("comment", "")
        if sAddComment:
            sComment = "{}: {}".format(sComment, sAddComment)

        result = self.publishInfoSetFile(currentScene=sceneName, comment=sComment)
        print "result=", result

# test de la class
if __name__ in ["__main__"]:
    infoSetExpI = infoSetExp()
    infoSetExpI.export(sceneName=jpZ.getShotName())
