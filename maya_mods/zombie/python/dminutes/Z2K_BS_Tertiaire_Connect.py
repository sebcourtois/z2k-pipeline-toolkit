#!/usr/bin/python
# -*- coding: utf-8 -*-
################################################################
# Name    : Z2K_connect_BS_Tertiaire
# Version : 004
# Description : Apply et connect les blendShapes des chr tertiaires en fonction des parametres lus dans le fichier .bsd associe a chaque .ma
#               contenant les blendshapes concernees.
# Author : Jean-Philippe Descoins
# Date : 2014-12-01
# Comment : a executer une fois le .ma contenant les blendShapes imported dans la scene sans namespace.
# TO DO : Fixe bug delette old BS, ligne 153
#         - give option to delete totally old BS node option
#         - incorporate jpm function to z2K_lib
################################################################
#    ! Toute utilisation de ce se script sans autorisation     #
#                         est interdite !                      #
#    ! All use of this script without authorization is         #
#                           forbidden !                        #
#                                                              #
#                                                              #
#                 © Jean-Philippe Descoins                     #
################################################################





############### Importing other LIBS ####################
import maya.cmds as cmds
import ast,os
import maya.mel as mel
#########################################################
import dminutes.Z2K_BS_Tertiaire_Check_mayaFile as BS_check
reload(BS_check)
import dminutes.jipeLib_Z2K as jpZ
reload(jpZ)

def jipe_multiAttr_BSConnector(tableDL={},importNS="BS",connectTargetShapeOnly=False, connectAttrToBsOnly=False, *args, **kwargs):
    """ Description: Connect les Objs et BlendShapes selon les parametres donnés dans le dictionnaire tableDL
        Return : -
        Dependencies : cmds - 
    """
    # importNS : not implemented
    # connectTargetShapeOnly: not implemented
    # connectAttrToBsOnly : not implemented
    result =True
    
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

                        # check for connected targets
                        if BS_Node not in allreadyTestedL:
                            objTargetD = jpZ.get_BS_TargetObjD(BS_Node=BS_Node)
                            print "    ",objTargetD
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
                                    
                            

            except:
                pass
           

    

    


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
                        cmds.blendShape(drivenMesh, name=BS_Node)
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
        

def readConnexionDictL(filename="",*args, **kwargs):
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

def connectDialog(*args, **kwargs):
    print "connectDialog()"
    # getFile and read
    filename=""
    startDir =cmds.optionVar( q="Z2K_BS_tertiairePath" )
    if not startDir:
        startDir = "c:"

    result = cmds.fileDialog2(dir= startDir, fileMode=1, caption="Select the '.bsd' BS_setting_file", fileFilter="*.bsd", dialogStyle=1, okc="OPEN")
    if result:
        filename = result[0]
        if ".bsd" in filename:
            print "filename=", filename
            bsDictL= readConnexionDictL(filename=filename)
            cmds.optionVar( stringValue=[ "Z2K_BS_tertiairePath", filename])
            # check nameCorrespondance:
            chResultL = BS_check.checkNameCorrespondance(GUI= False, filename=filename) 
            print "chResultL[0]=", chResultL[0]
            print "chResultL[0]=", chResultL[-1]
            if chResultL[0]:   
                # apply the connection dict
                result = jipe_multiAttr_BSConnector(tableDL=bsDictL, importNS="BS") 
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