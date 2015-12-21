#!/usr/bin/python
# -*- coding: utf-8 -*-
################################################################
# Name    : Z2K_connect_BS_Tertiaire
# Version : 004
# Description : Apply et connect les blendShapes des chr tertiaires en fonction des parametres lus dans le fichier .bsd associe a chaque .ma
#               contenant les blendshapes concernees.
# Author : Jean-Philippe Descoins
# Date : 2014-12-01
# Comment : a executer une fois le .ma contenant les blendShapes importe dans la scene sans namespace.
# TO DO : Fixe bug delettre old BS, ligne 153
################################################################
#    ! Toute utilisation de ce se script sans autorisation     #
#                         est interdite !                      #
#    ! All use of this script without authorization is         #
#                           forbidden !                        #
#                                                              #
#                                                              #
#                 © Jean-Philippe Descoins                     #
################################################################




# table pour blendShape Tertiaire
############### Importing other LIBS ####################
import maya.cmds as cmds
import ast,os
import maya.mel as mel
#########################################################
# TO DO
# x doit marcher sur plusisuers objs avec differents param de inbetween or not


# dictL = [
#     {
#     "squ_001":{
#         "attrN":"L_brow_upDown",
#         "attrParamL": ["double",-2, 0, 2, True, False],
#         "drivenMesh": {
#             "geo_bodyDefault"   : ["bs_body",[ (-1,"L_brows_up"),(1,"L_brows_down")  ] ],
#             "geo_eyebrowscouette":["bs_eyeBrows",[ (-1,"L_eyebrows_up"),(1,"L_eyebrows_down")  ] ],
#                     },      
#                 },
#             },
#     {
#     "squ_001":{
#         "attrN":"R_brow_upDown",
#         "attrParamL": ["double",-2, 0, 2, True, False],
#         "drivenMesh": {
#             "geo_bodyDefault"   : ["bs_body",[ (-1,"R_brows_up"),(1,"R_brows_down")  ] ],
#             "geo_eyebrowscouette":["bs_eyeBrows",[ (-1,"L_eyebrows_up"),(1,"L_eyebrows_down")  ] ],
#                     },      
#                 },
#             },
#     {
#     "squ_001":{
#         "attrN":"mouth_upDown",
#         "attrParamL": ["double",-2, 0, 2, True, False],
#         "drivenMesh": {
#             "geo_bodyDefault"   : ["bs_body",[ (-1,"lips_up"),(1,"lips_down")  ] ],
            
#                     },      
#                 },
#             },
#     {
#     "squ_001":{
#         "attrN":"lips_kiss",
#         "attrParamL": ["double",-2, 0, 2, True, False],
#         "drivenMesh": {
#             "geo_bodyDefault"   : ["bs_body",[ (1,"lips_kiss")  ] ],
            
#                     },      
#                 },
#             },
  
  

                
                
#     # "AttribName": {
#     #     "attrHodler": "squ_001",
#     #     "attrParamL": ["double",min, defaultValue, max, keyable, lock],
#     #     "drivenMesh": {
#     #         "targetObj": ["targetBS",[ (1,"targetShape1"), (-1,"targetShape2"),etc...  ] ],
#     #                  }
#     #     }

# ]


def jipe_multiAttr_BSConnector(tableD={},importNS="BS",connectTargetShapeOnly=False,connectAttrToBsOnly=False, *args, **kwargs):
    """ Description: Connect les Objs et BlendShapes selon les parametres donnés dans le dictionnaire tableD
        Return : -
        Dependencies : cmds - 
    """
    

    # loop in tableD
    #for attrN,dico in tableD.iteritems():
    for attrHodlerD in tableD:  
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

                    


                    # delete all not connected old BS ------------------------- FOIREUX BUG bUG

                    # construct current BS attr Dict
                    bsAttrL = cmds.aliasAttr( BS_Node, query=True )
                    bsAttrD = {}
                    if bsAttrL:
                        for a,i in zip( bsAttrL[::2], bsAttrL[1::2] ):
                            bsAttrD[a] = int(i.split("[",1)[-1].split("]",1)[0] )
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

                    #-----------------------------------------------------------
                    print "BS PART ----------------------------------"
                    # create the BS node if it doesn t exists
                    if not cmds.objExists(BS_Node):
                        cmds.blendShape(drivenMesh, name=BS_Node)
                    # enable negative values on BS node
                    cmds.setAttr( BS_Node+ ".supportNegativeWeights", 1)

                    
                    # get the total index length, this isthe indice where to plug the new blendShape
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
        


# getFile and read
filename = cmds.fileDialog2(fileMode=1, caption="Select the BS_setting_file", fileFilter="", dialogStyle=1, okc="OPEN")[0]
print "filename=", filename

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
    
    # apply the connection dict
    jipe_multiAttr_BSConnector(tableD=bsDictL, importNS="BS")