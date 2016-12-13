#!/usr/bin/python
# -*- coding: utf-8 -*-
################################################################
# Name    : BATZ_COULD_TO_PATH
# Version : 001
# Description :
# Author : Jean-Philippe Descoins
# Date : 2016-01-12
# Comment : First release
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
import dminutes.jipeLib_Z2K as jpZ
reload(jpZ)


class connectToPathGUI (object):
    def __init__(self,*args, **kwargs):
        print "connectToPathGUI"
        self.name = "connectToPathGUI"
        self.cf =  self.name
        self.createdSet = ""
        self.folderBigDaddy = "RIG_TO_PATH_bigDaddy"

    def connectToPath(self, NsObjSource="",objL=[],thePath="", followAxis="z", upAxis= "y", drivingAttrP="ctrl_head.PATH", 
        globalScaleAttrP="ctrl_head.globalScale",stretchOnPathAttrP="ctrl_head.StretchOnPath", startValue=0.001,worldUpOrientObj="UpV_orient_001",
        CTRtoBeAlignedToStartOfPath= "Global_SRT",):
        print "objL=",objL
        print "thePath=", thePath
        print "NsObjSource=", NsObjSource
        createdNodeL=[]
        moPathOld=""   
        moPath = "" 
        UpObject = "Global_SRT"
        NS=""
        totalDist = 0.0
        totalRealDist = 0.0
        self.setName = "set_RIG_TO_PATH#"
        
        # handling eventuals NS in selection
        if ":" in NsObjSource :
            NS=NsObjSource.split(":",1)[0] + ":"
        stretchOnPathAttrP = NS + stretchOnPathAttrP
        drivingAttrP = NS+ drivingAttrP
        worldUpOrientObj = NS+ worldUpOrientObj
        objL = [NS+x for x in objL]
        maxVal=cmds.addAttr(drivingAttrP ,max=1,q=1)

        # general group
        self.curDaddyGroup = cmds.group(em=1,name= self.setName[4:] + thePath +  "_gp")
        createdNodeL.append (self.curDaddyGroup)
        # mini debug
        if  not len(thePath):
            return False,"ERROR: SELECT A CURVE"
        else:

            # get length of the curve
            curveInfoN= cmds.arclen(thePath,ch=1)
            createdNodeL.append (curveInfoN)
            curveLen = cmds.getAttr (curveInfoN + ".arcLength" )
            print "   curveLen=",curveLen

            # set start value
            cmds.setAttr (drivingAttrP,startValue)

            # get distance original
            distL= [0]
            for i in xrange( len(objL) ) :
                objA = objL[i]
                if i < len(objL)-1:
                    objB = objL[i+1]
                else:
                    objB = objA
                # get realdistance in between all original objects
                print "Mesure:",objA,"<->",objB
                        
                tmpDistN = cmds.createNode("distanceBetween", name= "tmpDistN" )
                cmds.connectAttr(objA + ".worldMatrix", tmpDistN + ".inMatrix1")
                cmds.connectAttr(objB + ".worldMatrix", tmpDistN + ".inMatrix2")
                theDistAB= cmds.getAttr(tmpDistN + ".distance")

                print "  theDistAB=",theDistAB
                cmds.delete( tmpDistN) 

                totalDist+=theDistAB
                
                distL.append(theDistAB) 

            # normalise total Dist
            print "distL=", distL
            print "totalDist=",totalDist
            totalRealDist = totalDist/curveLen
            print "-> totalRealDist=", totalRealDist

            # total real dist real time 
            totalRealDistNode = cmds.createNode("multiplyDivide", name= "totalRealDistNode_{0}".format(objA) )
            createdNodeL.append (totalRealDistNode)
            cmds.setAttr (totalRealDistNode + ".operation",2)
            cmds.setAttr (totalRealDistNode + ".input1X",totalDist)
            cmds.connectAttr( curveInfoN + ".arcLength" ,totalRealDistNode + ".input2X",f=1) 
            for i in xrange( len(objL) ) :
                objA = objL[i]

                # get position objA at start of the path
                curLoc = cmds.spaceLocator(name="LocOnPath_{0}##".format(objA) )[0]
                curLocZero= cmds.group (curLoc,relative=1,name= curLoc+ "_zero")
                createdNodeL.append (curLocZero)
                cmds.parent ( curLocZero,self.curDaddyGroup)
                # constrain to path theLoc
                moPathOld = str(moPath)
                moPath = cmds.pathAnimation( curLocZero, c=thePath, fractionMode=True, follow=True,
                                            followAxis=followAxis, upAxis=upAxis, worldUpType="objectrotation",worldUpObject= worldUpOrientObj,
                                            inverseUp=False, inverseFront=False, bank=False )
                createdNodeL.append (moPath)
                # get the dist between A(current point) and B next current point
                print "distL[i]=", distL[i],objA
                curRealDist = distL[i] / curveLen
                # convertit curRealDist pour les cas de 0 ou de 1 qui bug le motion path
                # if round(curRealDist,4) in [0.0000]:
                #     print "ZERO"
                #     curRealDist=0.0001
                # elif  round(curRealDist,4) in [1.000]:
                #     print "ONE"
                #     curRealDist=0.9999


                # calcul du ratio rapport au length du path la dist / la taille courante du path
                divideNodeCurRealDist = cmds.createNode("multiplyDivide", name= "multiNodeCurRealDist_{0}".format(objA) )
                createdNodeL.append (divideNodeCurRealDist)
                cmds.setAttr (divideNodeCurRealDist + ".operation",2)
                cmds.setAttr (divideNodeCurRealDist + ".input1X",distL[i])
                cmds.connectAttr( curveInfoN + ".arcLength" ,divideNodeCurRealDist + ".input2X",f=1) 

                # ajout d un factor de stretching sur le path
                # multiN_StretchedRealDist = cmds.createNode("multiplyDivide", name= "multiN_StretchedRealDist_{0}".format(objA) )
                # cmds.connectAttr( stretchOnPathAttrP, multiN_StretchedRealDist +".input2X",f=1)


                # cmds.connectAttr( divideNodeCurRealDist + ".outputX", multiN_StretchedRealDist +".input1X",f=1)
                # print "  curRealDist = ",cmds.getAttr (divideNodeCurRealDist + ".outputX")
                # ---> multiN_StretchedRealDist est la distance d offset relative au arclen total


                stretchOnPathAttrPDiv = cmds.createNode("multiplyDivide", name= "stretchOnPathAttrPDiv_{0}".format(objA) )
                createdNodeL.append (stretchOnPathAttrPDiv)
                cmds.setAttr (stretchOnPathAttrPDiv + ".operation",2)
                cmds.setAttr (stretchOnPathAttrPDiv + ".input2X",maxVal/5) #10

                # add a connection to replace the fied val on input 2 of stretchOnPathAttrPDiv
                stretchOnPathAttrPDivinput2 = cmds.createNode("multiplyDivide", name= "stretchOnPathAttrPDiv_{0}".format(objA) )
                createdNodeL.append (stretchOnPathAttrPDivinput2)
                cmds.setAttr (stretchOnPathAttrPDivinput2 + ".operation",1)
                cmds.setAttr (stretchOnPathAttrPDivinput2 + ".input1X",distL[i]) #maxVal
                cmds.connectAttr( drivingAttrP, stretchOnPathAttrPDivinput2 + ".input2X",f=1)
                cmds.connectAttr(  stretchOnPathAttrPDivinput2 + ".outputX",stretchOnPathAttrPDiv + ".input2X", f=1)

                print "stretchOnPathAttrPDivinput2=", stretchOnPathAttrPDivinput2
                # ---------------------------------------------------

                cmds.connectAttr( stretchOnPathAttrP, stretchOnPathAttrPDiv +".input1X",f=1)

                multiN_Stretch = cmds.createNode("multiplyDivide", name= "multiN_StretchedRealDist_{0}".format(objA) )
                createdNodeL.append (multiN_Stretch)
                # create stretching factor node
                tweakStretchValue = cmds.createNode("reverse", name= "tweakStretchValue_{0}".format(objA) )
                createdNodeL.append (tweakStretchValue)


                cmds.connectAttr( stretchOnPathAttrPDiv + ".outputX", tweakStretchValue +".inputX",f=1)
                cmds.connectAttr(tweakStretchValue + ".outputX", multiN_Stretch +".input2X",f=1)
                
                # without tweakStretchValue
                # cmds.connectAttr( stretchOnPathAttrP, multiN_Stretch +".input2X",f=1)

                
                if not len(moPathOld):
                    print "FIRST"
                     # handling offset
                    offsetBaseNode = cmds.createNode( "addDoubleLinear", name= "offsetBaseNode_{0}".format(objA) )
                    createdNodeL.append (offsetBaseNode)
                    # cmds.setAttr ( offsetBaseNode + ".input2", totalRealDist)
                    cmds.connectAttr( totalRealDistNode + ".outputX",offsetBaseNode + ".input2",f=1)

                    multiNode = cmds.createNode("multiplyDivide", name= "multiplyFactor_{0}".format(objA) )
                    createdNodeL.append (multiNode)
                    cmds.setAttr (multiNode + ".operation",2)
                    
                    cmds.setAttr (multiNode + ".input2X",maxVal)
                    cmds.connectAttr( drivingAttrP ,multiNode + ".input1X",f=1)
                    # cmds.connectAttr( multiNode + ".outputX" ,moPath + ".uValue",f=1) 


                    # # intercallage base offset
                    cmds.connectAttr(multiNode + ".outputX", offsetBaseNode+".input1",f=1)
                    cmds.connectAttr( offsetBaseNode + ".output" ,moPath + ".uValue",f=1) 

                    # # intercallage stretch offset
                    # cmds.connectAttr(offsetBaseNode + ".output", multiN_Stretch+".input1X",f=1)
                    # cmds.connectAttr( multiN_Stretch + ".outputX" ,moPath + ".uValue",f=1) 

                    

                    # intercallage base offset
                    # cmds.connectAttr(multiNode + ".outputX", multiN_Stretch+".input1X",f=1)
                    # cmds.connectAttr( offsetBaseNode + ".output" ,moPath + ".uValue",f=1) 

                    # intercallage stretch offset
                    # cmds.connectAttr(multiN_Stretch + ".outputX", offsetBaseNode+".input1",f=1)
                    # cmds.connectAttr( offsetBaseNode + ".output" ,moPath + ".uValue",f=1) 




                else:
                     # handling offset
                    offsetBaseNode = cmds.createNode( "addDoubleLinear", name= "offsetBaseNode_{0}".format(objA) )
                    createdNodeL.append (offsetBaseNode)
                    # cmds.setAttr ( offsetBaseNode + ".input2", curRealDist * -2)

                    # multiply -2
                    mutliTwoN = cmds.createNode( "multiplyDivide", name= "mutliTwoN_{0}".format(objA) )
                    createdNodeL.append (mutliTwoN)
                    cmds.setAttr ( mutliTwoN + ".input2X",  -2)
                    cmds.connectAttr( divideNodeCurRealDist + ".outputX",mutliTwoN + ".input1X")
                    cmds.connectAttr( mutliTwoN + ".outputX",offsetBaseNode + ".input2")



                    addNode = cmds.createNode("addDoubleLinear", name= "addDist_{0}".format(objA) )
                    createdNodeL.append (addNode)
                    # cmds.setAttr(addNode+".input2", curRealDist)
                    cmds.connectAttr(divideNodeCurRealDist+".outputX", addNode+".input2",f=1)

                    cmds.connectAttr(moPathOld + ".uValue", addNode+".input1",f=1)


                    # # intercallage base offset OLD
                    # cmds.connectAttr(addNode + ".output", offsetBaseNode+".input1",f=1)
                    # # cmds.connectAttr( offsetBaseNode+".output", moPath + ".uValue",f=1)
                    # # intercallage stretch offset
                    # cmds.connectAttr(offsetBaseNode + ".output", multiN_Stretch+".input1X",f=1)
                    # cmds.connectAttr( multiN_Stretch + ".outputX" ,moPath + ".uValue",f=1) 

                    # intercallage base offset
                    cmds.connectAttr(addNode + ".output", multiN_Stretch+".input1X",f=1)
                    # cmds.connectAttr( offsetBaseNode + ".output" ,moPath + ".uValue",f=1) 

                    # intercallage stretch offset
                    cmds.connectAttr(multiN_Stretch + ".outputX", offsetBaseNode+".input1",f=1)
                    cmds.connectAttr( offsetBaseNode + ".output" ,moPath + ".uValue",f=1) 
                      
                # constraint each original object to the loc on curve
                theCstP = cmds.parentConstraint(curLoc,objA,mo=0)[0]
                theCstS = cmds.scaleConstraint(curLoc,objA,mo=1)[0]

                createdNodeL.append (theCstP)
                createdNodeL.append (theCstS)
       


        # align the CTRtoBeAlignedToStartOfPath to the start of the path
     
        # theCstTmp = cmds.parentConstraint(objL[0], NS+ CTRtoBeAlignedToStartOfPath,mo=0)[0]
        # cmds.delete( theCstTmp)
        jpZ.matchByXformMatrix ( cursel= [objL[0], NS+ CTRtoBeAlignedToStartOfPath],mode=0 )

        # parent to the mega master group for all eventuals path and set the attr_name of the sets
        if not cmds.objExists(self.folderBigDaddy):
            self.curDaddyGroup=cmds.group  (self.curDaddyGroup,name= self.folderBigDaddy)
            # createdNodeL.append (self.folderBigDaddy)
        else:
            cmds.parent (self.curDaddyGroup,self.folderBigDaddy)


        # create a set with all new nodes
        self.createdSet = cmds.sets(  createdNodeL, name=self.setName)

        # add the created set to the history attr
        self.AddHistoric(targetObj=self.folderBigDaddy, targetAttr="setL", text=self.createdSet, sep=", ",debug=False,)

        

        # re activate undo
        # cmds.undoInfo( closeChunk=True)


        # reselect the driver object at the end
        cmds.select(drivingAttrP.split(".",1)[0])

    def AddHistoric(self,targetObj="RIG", targetAttr="HIST", text="", sep=", ",debug=False,  *args, **kwargs):
        """ Description: handle an historical writen on an attribute
            Return : [list] - the implemented list
            Dependencies : cmds - 
        """
        # var
        newStep = text
        HATTR = targetObj + "." + targetAttr
        outText =""

        # test / create
        if not cmds.objExists(HATTR):
            cmds.addAttr(HATTR.split(".")[0], longName=HATTR.split(".")[-1], dt = "string")

        # get old value    
        curval= cmds.getAttr(HATTR)

        # create new value
        if curval in [None,"","None"]:
            curval = ""
            outText = newStep
        else :
            outText = curval + sep + newStep

        # fianelly set the Attr
        cmds.setAttr(HATTR, outText, type="string",)
        curL = curval.split(sep)
        # print current state
        if debug in [True,1]:
            for count,j in zip( xrange( len(curL)),curL ) :
                print count,j
        return curL

    def getSetContent (self, inSetL=[], *args, **kwargs):
        """
        description : return the objL in a setlist
        Return : [list]
        """
        outL = []
        objL = []
        otherL= []
        for i in inSetL:
            # print "i=", i
            if cmds.objExists(i):
                # print "  set exists"
                objL = cmds.listConnections(i + "." + "dagSetMembers", source=1,d=0)
                otherL = cmds.listConnections(i + "." + "dnSetMembers", source=1,d=0)
                # print "    otherL=", otherL
                # print "    objL=", objL
                if objL:
                    outL.extend(objL)
                if otherL:
                    outL.extend(otherL)

        return outL


    # ------------------------------------------- UI FONCTIONS -----------------------------------------------------------

    def getUIV (self,*args, **kwargs):
        print "getUIV()"
    def btn_connectToPath(self,*args, **kwargs):

        if not len(cmds.ls(sl=1) )>=2:
            text= "Por favor, select the BATZ CLOUD Global_SRT and them a Path !"
            cmds.confirmDialog( title='Error', message=(text), button=['OK'], defaultButton='OK')
        else:
            self.connectToPath( NsObjSource=cmds.ls(os=1)[0], objL=['ctrl_head_pathHook', 'ctrl_headMid_pathHook', 'ctrl_tailMid_pathHook', 'ctrl_tail_pathHook'],thePath=cmds.ls(os=1)[-1],
                            followAxis="z", upAxis= "y", drivingAttrP="ctrl_head.PATH", stretchOnPathAttrP="ctrl_head.StretchOnPath", startValue=0.0001, worldUpOrientObj="path_UpOrient",
                                globalScaleAttrP="ctrl_head.globalScale", CTRtoBeAlignedToStartOfPath= "Global_SRT",
                            )
            
    def btn_deleteAllConnectionRig (self,*args, **kwargs):
        print "btn_deleteConnections"

        if cmds.objExists (self.folderBigDaddy+".setL"):
            setsToDelL = cmds.getAttr (self.folderBigDaddy+".setL").split (",")
            objToDelL = self.getSetContent(setsToDelL)
            # print "objToDelL=", objToDelL
            for i in objToDelL:
                # print "deleting=", i
                if cmds.objExists(i):
                    cmds.delete (i)
        # finally delete the big group
        if cmds.objExists (self.folderBigDaddy):
            cmds.delete(self.folderBigDaddy)

    def createWindow (self,*args, **kwargs):

        if cmds.window (self.cf, q=True, exists=True):
            print " {0} allready exists".format(self.cf)
            cmds.deleteUI(self.cf, window=True)
        #create la window e permet d avoir plusieurs windows
        cmds.window(self.cf, rtf=True, tlb=0,   t=(self.name  ),)
        print "WINDOW NAME=",self.cf
       

        #BIG TAB ------------------------------------------------------------------------------------------------
        cmds.frameLayout("Bigframe", marginHeight=5, marginWidth=5,l="        Connect Batz to Path:", labelVisible=True, fn="smallBoldLabelFont", cll=False,)
        cmds.columnLayout (adj=1,rs=5)
        cmds.text  ("1: Select the global_SRT".ljust(30))
        cmds.text  ("2: Select the bezier curve".ljust(30))
        cmds.button  ("connect_to_path",ann="Attach the select batz_cloud to the selected curve by a motion path", c=self.btn_connectToPath)
        cmds.button  ("deleteAll",l="Delete All motions paths rig",ann="Delete all motion path and additive rig", c=self.btn_deleteAllConnectionRig)

        # show windos
        cmds.showWindow()


ctpI=connectToPathGUI()
ctpI.createWindow()