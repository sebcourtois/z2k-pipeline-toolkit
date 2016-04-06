#!/usr/bin/python
# -*- coding: utf-8 -*-
################################################################
# Name    : Z2K_BS_Tertiaire_Tool
# Version : 001
# Description : Tool facilitant le travail de connexion des blendShapes sur les personnages tertiaires
# Author : Jean-Philippe Descoins
# Date : 2015-12-11
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

import os,sys,ast
from functools import partial
import maya.cmds as cmds
import dminutes.jipeLib_Z2K as jpZ
reload(jpZ)
import dminutes.Z2K_wrapper as Z2K
reload(Z2K)

from davos.core import damproject
from davos.core.damtypes import DamAsset

import dminutes.Z2K_BS_Tertiaire_Connect as BS_connect
reload(BS_connect)

import dminutes.Z2K_BS_Tertiaire_Check_mayaFile as BS_check
reload(BS_check)


# BS_check.checkDialog()
# BS_connect.connectDialog()



class Z2K_BS_Tertiaire_Tool_GUI (object):
    WNAME = "Z2K_BS_Tertiaire_Tools"
    version = "001"
    def __init__(self,*args, **kwargs):
        print "GUI_init"
        # get zomb project
        theProject = os.environ.get("DAVOS_INIT_PROJECT")
        print theProject
        self.curproj = Z2K.projConnect(theProject=theProject)

    # def jipeFileDialog(self,*args, **kwargs):
    #     print "jipeFileDialog()"
    #     # getFile and read
    #     filename=""
    #     startDir =cmds.optionVar( q="Z2K_BS_tertiairePathBS" )
    #     if not startDir:
    #         startDir = "c:"

    #     result = cmds.fileDialog2(dir= startDir, fileMode=1, caption="Select the '.ma' BleandShape file", fileFilter="*.ma", dialogStyle=1, okc="OPEN")
    #     if result:
    #         filename = result[0]
    #     return filename

    def getBSD_File(self, pathType="pathType", *args, **kwargs):
        print "getBSD_File()"
        currentSceneP,currentScene = cmds.file(q=1,sceneName=True),cmds.file(q=1,sceneName=True,shortName=True)
        assetN = os.path.normpath(currentScene).rsplit(os.sep,1)[-1].rsplit("-v",1)[0]
        print assetN.rsplit("_",1)[0]

        pathPublic= Z2K.getPath(proj=self.curproj, assetName= assetN.rsplit("_",1)[0], pathType= pathType )[0]
        print "pathPublic=", pathPublic
        return pathPublic

    def checkNameCorrespondance(self, GUI=True, filename="", *args, **kwargs):
        print "checkNameCorrespondance()"
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

    def jipe_multiAttr_BSConnector(self, tableDL={}, importNS="BS",connectTargetShapeOnly=False, connectAttrToBsOnly=False, *args, **kwargs):
        """ Description: Connect les Objs et BlendShapes selon les parametres donnés dans le dictionnaire tableDL
            Return : -
            Dependencies : cmds - 
        """
        # importNS : not implemented
        # connectTargetShapeOnly: not implemented
        # connectAttrToBsOnly : not implemented
        print "jipe_multiAttr_BSConnector()"
        result =True
        BS_NodeL = []
        # pre-loop check for connected Target BS:
        allreadyTestedL=[]
        for attrHodlerD in tableDL: 
            for attrHodler,dico in attrHodlerD.iteritems():
                drivenMeshD = dico.get("drivenMesh",{"defaultObj":[]})
                try:
                    for drivenMesh,valL in drivenMeshD.iteritems():
                            print "        drivenMesh:",drivenMesh
                            BS_Node = valL[0]
                            print "# ",BS_Node
                            if cmds.objExists(BS_node):
                                if not BS_Node in BS_NodeL:
                                    BS_NodeL.append(BS_Node)
                            # check for connected targets
                            if BS_Node not in allreadyTestedL:
                                objTargetD = jpZ.get_BS_TargetObjD(BS_Node=BS_Node)
                                print "    objTargetD=",objTargetD
                                allreadyTestedL.append(BS_Node)

                                if len(objTargetD):
                                    result = cmds.confirmDialog( title='bsd check: {0}'.format(BS_Node), message="Some Blend_Shape Targets are allready connected,\n Please clean your BS_node! \n{0}".format(objTargetD.values()),
                                            button=["ABOARD"], defaultButton='ABOARD', cancelButton='ABOARD', dismissString='ABOARD' )
                                    

                                    # delete old BSO if user decided
                                    if result in ["ABOARD"]:
                                        result = False
                                        return result


                                    else:
                                        return
                                        # delete BUGGED
                                        # for drivenMesh,valL in drivenMeshD.iteritems():
                                        
                                

                except Exception,err:
                    print "ERROR=",Exception
                    pass
               
        print "BS_NodeL=",BS_NodeL
        if len(BS_NodeL):
            # delete BUGGED
            # for drivenMesh,valL in drivenMeshD.iteritems():
            result = cmds.confirmDialog( title='REPLACE_ALL BS_NODE', message="There is existing BS_NODE:\n  {0}\nDO YOU WANT TO DELETE ALL old BS_Node ?".format(BS_NodeL),
                button=["YES","KEEP","ABOARD"], defaultButton='ABOARD', cancelButton='ABOARD', dismissString='ABOARD' )
            if result in ["YES"]:
                cmds.delete(BS_NodeL)
                print "BS_NODE DELETED"

            if result in ["ABOARD"]:
                sys.exit()

        # loop in tableDL ------------------------------------------------
        #for attrN,dico in tableDL.iteritems():
        for attrHodlerD in tableDL:  
            print "attrHodler=", attrHodlerD  

            for attrHodler,dico in attrHodlerD.iteritems():
                attrN= dico.get("attrN", "BS_default" )
                attrParamL = dico.get("attrParamL",["float",0,1,1,True,False] )
                drivenMeshD = dico.get("drivenMesh",{"defaultObj":[]})
                attrT = attrParamL[0] #type
                attrMin = attrParamL[1] # minimum val
                attrDv = attrParamL[2] # default val
                attrMax = attrParamL[3] # maximun val
                attrK = attrParamL[4] # keyable
                attrL = attrParamL[5] # lock

                print "    attrHodler=", attrHodler
                print "    attrN=", attrN
                print "    attrParamL=", attrParamL
                print "    drivenMeshD=", drivenMeshD

                # Attrib part --------------------------------------------------------------------------------------
                # delete old attrib
                try:
                    print "            DELETING:" ,attrHodler
                    cmds.setAttr(attrHodler + "."+attrN, l=False)
                    cmds.deleteAttr( attrHodler, at=attrN, )
                except Exception,err:
                    print err
                    pass
                # add attr to control object
                print  "            CREATING:" ,attrHodler+"."+attrN
                if attrT in ["enum"]:
                    print "enum"
                    cmds.addAttr( attrHodler, longName=attrN, attributeType= attrT, en=attrDv,
                                        keyable=attrK,) 
                    cmds.setAttr(attrHodler + "."+attrN, l=attrL, cb=True)
                else:
                    print "normal"
                    cmds.addAttr( attrHodler, longName=attrN, attributeType= attrT, min=attrMin,dv= attrDv, max= attrMax,
                                            keyable=attrK,) 


                    # BS part -------------------------------------------------------------------------------------------
                    for drivenMesh,valL in drivenMeshD.iteritems():
                        print "        drivenMesh:",drivenMesh
                        
                        BS_Node = valL[0]
                        targetShapeParamL = valL[1]
                        print "            BS_Node:",BS_Node
                        print "            targetShapeParamL:",targetShapeParamL
                        print "            len(targetShapeParamL):",len(targetShapeParamL)

                        

                        # create the BS node if it doesn t exists
                        if not cmds.objExists(BS_Node):
                            cmds.blendShape(drivenMesh, name=BS_Node,foc=True)
                        # enable negative values on BS node
                        cmds.setAttr( BS_Node+ ".supportNegativeWeights", 1)


                        # delete all not connected old BS ------------------------- FOIREUX BUG bUG
                        # mel.eval("blendShapeDeleteTargetGroup {0} {1}".format(BS_Node,i) )

                       
                        #     if 

                        #     cmds.blendShape (BS_Node, e=1, remove=True, t= ( drivenMesh,  bsAttrD[name]  ,  objTargetD[i],0)

                            # print taget shape table
                            # for tName,wi in bsAttrD.iteritems():
                            #     print tName,"->",wi
                            
                            # # delete BSattr  bugged
                            # for a,i in bsAttrD.iteritems():
                            #     print "deleting:",a,i
                            #     if tmp_Count in [0]:
                            #         try:
                            #             print "   deconect",BS_Node+"."+targetShapeParamL[-1][-1]
                            #             mel.eval ("CBdeleteConnection {0}".format(BS_Node+"."+targetShapeParamL[-1][-1]))
                            #             print "   del", targetShapeParamL[-1][-1],i,a

                            #             cmds.blendShape (BS_Node, e=1, remove=True, t= ( targetShapeParamL[-1][-1],i,a,0)  )
                            #         except Exception,err:
                            #             print "*",err
                            #         tmp_Count +=1

                            # delete BSattr  
                            # for a,i in bsAttrD.iteritems():
                            #     print BS_Node,drivenMesh,a,i
                            #     try:

                            #         cmds.blendShape (BS_Node, e=1, remove=True, t= (drivenMesh,i,a,0)  )
                            #     except Exception,err:
                            #         print "*",err
                            # cmds.blendShape (BS_Node, e=1, remove=True, t= (drivenMesh,bsAttrD[targetShapeParamL[-1][-1] ],targetShapeParamL[-1][-1],0)  )
                        
                        # get the total index length, this is the indice where to plug the new blendShape
                        index = len( cmds.getAttr(BS_Node+"."+"w")[0] )+1
                        print "            index=", index

                        # connection TO BS NODE
                        print "            simple BS connect"
                        # simple blend shape
                        targetShapeObj = targetShapeParamL[0][1]
                        value = targetShapeParamL[0][0]
                        cmds.blendShape (BS_Node, e=1, ib=False, t = [drivenMesh, index, targetShapeObj, value ] )
                        
                        
                        # inbetweened blend shape
                        if len(targetShapeParamL)>1:
                            print "            inbetween BS connect"
                            for targetShapeParam in targetShapeParamL[1:]:
                                print "            targetShapeParam=", targetShapeParam

                                inBetweenTargetShapeObj = targetShapeParam[1]
                                value = targetShapeParam[0]
                                cmds.blendShape (BS_Node, e=1, ib=True, t = [drivenMesh, index, inBetweenTargetShapeObj, value ] )

                                

                        # connect attrN on BS targetShape attr

                        print "connecting:",index, attrHodler + "."+attrN,"->", BS_Node + ".w["+ str(index) + "]"
                        cmds.connectAttr( attrHodler + "."+attrN, BS_Node + ".w["+ str(index) + "]", f=1)


                    # finally set the attr default value and the lock state
                    cmds.setAttr(attrHodler + "."+attrN, attrDv)
                    cmds.setAttr(attrHodler + "."+attrN, l=attrL)
                    


            print "Connection is fucking DONE! :)"
        return result
        

    def readConnexionDictL(self, filename="",*args, **kwargs):
        print "readConnexionDict()"
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
                        print k,l
        return bsDictL



   
    def btn_check_NameCorespondance(self, GUI=True,*args, **kwargs):
        print "btn_check_NameCorespondance()"
        result = self.getBSD_File(pathType="blendShape_bsd")
        print "result=", result
        if result:
            filename = result
            if ".bsd" in filename:
                print "filename=", filename
                resultL = self.checkNameCorrespondance(GUI=GUI, filename=filename)
                return resultL[0]
            else:
                print "Execution aboarded: bad file type selected, please select a .bsd file!"
                cmds.confirmDialog( title='', message="Execution aboarded: bad file type selected, please select a .bsd file!",
                                             button=['OK'], defaultButton='OK', cancelButton='OK', dismissString='OK' )
        else:
            print "Execution aboarded!" 
            cmds.confirmDialog( title='', message="Execution aboarded",
                                             button=['OK'], defaultButton='OK', cancelButton='OK', dismissString='OK' )

    def importClean_underGP(self, GPName="imported_gp",*args, **kwargs):
        print "importClean_underGP()"

        if not cmds.objExists(GPName):
            pathPublic= self.getBSD_File(pathType="blendShape_scene")
            print "pathPublic=", pathPublic

            # import in scene with the good configuration of NS etc
            if os.path.isfile(pathPublic):
                curRef=cmds.file( pathPublic, groupReference=True, groupName=GPName ,i=True)
                print "curRef=", curRef
            else:
                print "No valid File found"
        else:
            cmds.confirmDialog( title='Warning', message="BlendShape file allready imported,\n Please clean you scene before importing again",
                                             button=['OK'], defaultButton='OK', cancelButton='OK', dismissString='OK',
                                             icon= "information")

    def btn_jipe_multiAttr_BSConnector(self, *args, **kwargs):
        print "connectDialog()"
        # getFile and read
        filename=""
        startDir =cmds.optionVar( q="Z2K_BS_tertiairePath" )
        if not startDir:
            startDir = "c:"

        result = self.getBSD_File(pathType="blendShape_bsd")
        if result:
            filename = result
            if ".bsd" in filename:
                print "filename=", filename
                bsDictL= self.readConnexionDictL(filename=filename)
                cmds.optionVar( stringValue=[ "Z2K_BS_tertiairePath", filename])
                # check nameCorrespondance:
                chResultL = self.checkNameCorrespondance(GUI= False, filename=filename) 
                print "chResultL[0]=", chResultL[0]
                print "chResultL[0]=", chResultL[-1]
                if chResultL[0]:   
                    # apply the connection dict
                    result = self.jipe_multiAttr_BSConnector(tableDL=bsDictL, importNS="BS") 
                    if result:
                        cmds.confirmDialog( title='', message="The blendShapes are successfully CONNECTED\n        Don't apply it again !",
                                             button=['OK'], defaultButton='OK', cancelButton='OK', dismissString='OK' )
                    else:

                        cmds.confirmDialog( title='bsd check', message="Connection failed, some problems occured!",
                                             button=['OK'], defaultButton='OK', cancelButton='OK', dismissString='OK' )
                else:
                    cmds.confirmDialog( title='bsd check', message="Connection IMPOSSIBLE, Name Correspondance ERROR:\nNot found: {0}".format(chResultL[1]),
                                             button=['OK'], defaultButton='OK', cancelButton='OK', dismissString='OK' )
                    print "Name Correspondance ERROR:/n {0}".format(chResultL[1])

            else:
                print "Execution aboarded: bad file type selected, please select a .bsd file!"
        else:
            print "Execution aboarded!"


    def createWin(self,*args,**kwargs):
        if cmds.window(self.WNAME, exists=True):
            cmds.deleteUI(self.WNAME)
        #create the window
        cmds.window(self.WNAME, title=self.WNAME+" v"+str(self.version), w=50,h=20, sizeable=1, tlb=0, mnb=True)
        #create layout
        cmds.frameLayout(lv=0)
        cmds.separator(3)
        cmds.text(self.WNAME.replace("_"," ")+":",font="boldLabelFont")
        cmds.tabLayout(tabsVisible=0,borderStyle="full")
        cmds.columnLayout(adj=1)
        
        cmds.columnLayout(adj=1)

        cmds.rowLayout(nc=2,adj=2)
        cmds.text("  BS_File    : ")
        cmds.setParent("..")

        cmds.tabLayout(tabsVisible=0,borderStyle="full")
        cmds.button("Check Naming correspondance with .bsd file".ljust(50),c= partial(self.btn_check_NameCorespondance,True ) )
        cmds.setParent("..")

        cmds.rowLayout(nc=2,adj=2)
        cmds.text("  Asset_file    : ")
        cmds.setParent("..")

        cmds.tabLayout(tabsVisible=0,borderStyle="full")
        cmds.columnLayout(adj=1)
        cmds.button("import blendShape_File in current scene".ljust(50), c= partial(self.importClean_underGP ,"imported_gp")  )
        cmds.separator(3)
        cmds.button("Connect imported BS to current asset".ljust(50),c= self.btn_jipe_multiAttr_BSConnector,  )
        cmds.setParent("..")
        cmds.setParent("..")
        cmds.text("Cleaner la scene")
        
        # cmds.text(" info: Browse for the corresponding '.bsd' file ",)
        # show Window
        cmds.showWindow()


Z2K_BS_Tertiaire_Tool_GUII=Z2K_BS_Tertiaire_Tool_GUI()
Z2K_BS_Tertiaire_Tool_GUII.createWin()