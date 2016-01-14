#!/usr/bin/python
# -*- coding: utf-8 -*-
################################################################
# Name    : Z2K_BS_Tertiaire_Check_mayaFile
# Version : 001
# Description :
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




# check maya file, for consistency with .bsd file

import maya.mel as mel
import os,ast
import maya.cmds as cmds

def checkNameCorrespondance(GUI=True, filename="", *args, **kwargs):
    # return: Bool,debugList
    # getFile and read
    print "GUI=", GUI
    theResult = False
    print "filename=", filename
    WrongObjNameL =[]
    if os.path.isfile(filename):
        print"read"
        content=""
        with open(filename, 'rU') as f:
            for line in f.readlines():
                if "#" not in line[0]:
                    content+= line.strip()
        print ( content )
        bsDictL = ast.literal_eval(content)

        for i in bsDictL:
            for k,l in i.iteritems():
                #print k,l
                dicoTmp= l.get('drivenMesh',l["attrN"])
                if not isinstance(dicoTmp,str):
                    for i,j in dicoTmp.iteritems():
                       for listTmp in j[1:]:
                           for pair in listTmp:
                               obj= pair[-1]
                               if not cmds.objExists(obj):
                                   WrongObjNameL.append(obj)
                               
    if len(WrongObjNameL):
        theResult = False
        for k in WrongObjNameL:
            print "Not found:",k
        print "GUI=", GUI
        if GUI:
            cmds.confirmDialog( title='bsd check', message="The blendShape Names are NOT conform with the selected .bsd file\n    {0}".format(WrongObjNameL),
                                 button=['OK'], defaultButton='OK', cancelButton='OK', dismissString='OK' )
    else:
        theResult = True
        if GUI:
            cmds.confirmDialog( title='bsd check', message="The blendShape Names are conform with the selected .bsd file",
                                button=['OK'], defaultButton='OK', cancelButton='OK', dismissString='OK' )
 
    
    return theResult,WrongObjNameL

def checkDialog(GUI=True,*args, **kwargs):
    print "checkDialog()"
    # getFile and read
    filename=""
    startDir =cmds.optionVar( q="Z2K_BS_tertiairePath" )
    if not startDir:
        startDir = "c:"

    result = cmds.fileDialog2(dir= startDir, fileMode=1, caption="Select the '.bsd' BS_setting_file", fileFilter="*.bsd", dialogStyle=1, okc="OPEN")
    print "result=", result
    if result:
        filename = result[0]
        if ".bsd" in filename:
            print "filename=", filename
            resultL = checkNameCorrespondance(GUI=GUI,filename=filename)
            return resultL[0]
        else:
            print "Execution aboarded: bad file type selected, please select a .bsd file!"
            cmds.confirmDialog( title='', message="Execution aboarded: bad file type selected, please select a .bsd file!",
                                         button=['OK'], defaultButton='OK', cancelButton='OK', dismissString='OK' )
    else:
        print "Execution aboarded!" 
        cmds.confirmDialog( title='', message="Execution aboarded",
                                         button=['OK'], defaultButton='OK', cancelButton='OK', dismissString='OK' )