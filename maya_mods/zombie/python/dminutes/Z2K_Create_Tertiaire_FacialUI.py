#!/usr/bin/python
# -*- coding: utf-8 -*-
################################################################
# Name    : Z2K_Create_Tertiaire_FacialUI
# Version : 003
# Description : create automatically an UI in viewport for the facial of third character, and connect the BS holderto it.(head)
# Author : Jean-Philippe Descoins
# Date : 2016-08-18
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





import dminutes.jipeLib_Z2K as jpZ
reload(jpZ)
import maya.cmds as cmds


class Create_Third_FacialUI(object):
    # must exist var
    THEPARENTFOLDER= "asset|grp_rig"
    THEHEAD= "Head_FK"
    OBROWSAL = ["Brows"]
    OEYESAL = ["Eyes"]
    OMOUTHAL = ["Mouth_central","Mouth_side"]
    THEVISHOLDER="VisHolder_Main_Ctrl"
    THEVISLVL = "Controls_2"
    # new var
    BROWS_HOLDER= "facialUI_brows"
    EYES_HOLDER= "facialUI_eyes"
    MOUTH_HOLDER= "facialUI_mouth"
    UI_DADDY = "facialUI_gp"
    CADRE_NAME = "facialUI_cadre"
    browL,mouthL,eyesL=[],[],[]
    start, addBrow,addMouth,addEye=0,0,0,0

    def __init__(self,*args, **kwargs):
        print "init()"

    def overideColor(self,theColor=[0,1,0], mode="normal",TheSel = None, *args):
        ''' Description : Override the color of the selected obj
                options: mode: "normal"/"default"
                         theColor: color index or RGB color
                Return : theColor
                Dependencies : cmds - GetSel()
        '''
        print "theColor=", theColor
        colorMode= "index"
        if type (theColor) in [tuple,list]:
            colorMode = "RGB"
        # Override la color de la shape de l'obj selected
        if mode in ["normal"]:
            EnableSwith = True
        if mode in ["default"]:
            EnableSwith = False
        cursel =list(TheSel)

        for obj in cursel:
            shapeNodes = cmds.listRelatives(obj, shapes=True, path=True)
            if type(shapeNodes) is not list:
                shapeNodes = [shapeNodes]
             
            for shape in shapeNodes:
                try:
                    if shape in [ None,"None" ]:
                        shape = obj
                    cmds.setAttr("%s.overrideEnabled" % (shape), EnableSwith)

                    if colorMode in ["RGB"]:
                        cmds.setAttr("%s.overrideRGBColors" % (shape), EnableSwith)
                        cmds.setAttr("%s.overrideColorRGB" % (shape), *theColor)#1,0.37,0)
                    
                    elif colorMode in ["index"]:
                        cmds.setAttr("%s.overrideEnabled" % (shape), EnableSwith)
                        cmds.setAttr("%s.overrideColor" % (shape), theColor)

                except Exception, err:
                    print "erreur :", Exception, err
        # print "theColor = ",theColor
        return theColor

    def replaceConnectAttr(self,theObj, attrHolder, theAttr):
        print "replaceConnectAttr()",theObj,attrHolder,theAttr
        
        # delete oldAttr if found
        if  cmds.objExists(attrHolder+"."+theAttr):
            cmds.deleteAttr(attrHolder+"."+theAttr)
  
        # get orignal values
        theType= cmds.addAttr(theObj+"."+theAttr, q=1, attributeType=True, )
        theMin= cmds.addAttr(theObj+"."+theAttr, q=1, min=True, )
        theDv= cmds.addAttr(theObj+"."+theAttr, q=1, dv=True, )
        theMax= cmds.addAttr(theObj+"."+theAttr, q=1, max=True, )

        theKeya = cmds.getAttr(theObj+"."+theAttr, k=True, )
        print 'theKeya=',theKeya
        theLock = cmds.getAttr(theObj+"."+theAttr, lock=1,)
        theCbDisp = cmds.getAttr(theObj+"."+theAttr, channelBox=1,)

        theEnum = "//"
        if theType in ["enum"]:
            theEnum= cmds.addAttr(theObj+"."+theAttr, q=1, en=True, )

        # print "**", theObj+"."+theAttr
        # print "  theType=", theType
        # print "  theMin=", theMin
        # print "  theMax=", theMax
        # print "  theDv=", theDv
        # print "  theKeya=", theKeya
        # print "  theLock=", theLock
        # print "  theCbDisp=", theCbDisp
        # print "  theEnum=", theEnum
        if not theLock:
            # add and connect
            cmds.addAttr(attrHolder, longName=theAttr, attributeType=theType, min=theMin, dv=theDv, max=theMax,keyable=theKeya,en=theEnum)
            cmds.setAttr(attrHolder+'.'+theAttr,lock=theLock)
            if not theKeya:
                cmds.setAttr(attrHolder+'.'+theAttr,channelBox=theCbDisp)
            cmds.connectAttr(attrHolder+"."+theAttr, theObj+"."+theAttr)

            # hide old ones
            cmds.setAttr(theObj+'.'+theAttr,k=False)

    def createUi(self,*args, **kwargs):
        print ("createUi()")
        if not cmds.objExists(self.MOUTH_HOLDER):

            # creation pure
            cadre = cmds.curve (d=1, p=[ (0.8851,0.001,-0.6884),(0.8851,0.001,-0.7376),(0.836,0.001,-0.836),(0.7376,0.001,-0.8851),(0.6884,0.001,-0.8851),(0,0.001,-0.8851),(-0.6884,0.001,-0.8851),(-0.7376,0.001,-0.8851),(-0.836,0.001,-0.836),(-0.8851,0.001,-0.7376),(-0.8851,0.001,-0.6884),(-0.8851,0.001,0.6884),(-0.8851,0.001,0.7376),(-0.836,0.001,0.836),(-0.7376,0.001,0.8851),(-0.6884,0.001,0.8851),(-0,0.001,0.8851),(0.6884,0.001,0.8851),(0.7376,0.001,0.8851),(0.836,0.001,0.836),(0.8851,0.001,0.7376),(0.8851,0.001,0.6884),(0.8851,0.001,0),(0.8851,0.001,-0.6884),])
            R_eye = cmds.curve (d=1, p=[ (0.3351,0.0027,-0.4428),(0.2551,0.0027,-0.4428),(0.095,0.0027,-0.6029),(0.095,0.0027,-0.683),(0.095,0.0027,-0.6029),(-0.0651,0.0027,-0.4428),(-0.1452,0.0027,-0.4428),(-0.0651,0.0027,-0.4428),(0.095,0.0027,-0.2828),(0.095,0.0027,-0.2027),(0.095,0.0027,-0.2828),(0.2551,0.0027,-0.4428),(0.3351,0.0027,-0.4428),])
            eye = cmds.curve (d=1, p=[ (0.3351,0.0027,0.4428),(0.2551,0.0027,0.4428),(0.095,0.0027,0.2828),(0.095,0.0027,0.2027),(0.095,0.0027,0.2828),(-0.0651,0.0027,0.4428),(-0.1452,0.0027,0.4428),(-0.0651,0.0027,0.4428),(0.095,0.0027,0.6029),(0.095,0.0027,0.683),(0.095,0.0027,0.6029),(0.2551,0.0027,0.4428),(0.3351,0.0027,0.4428),])
            cmds.parent( cmds.listRelatives(R_eye,c=1,s=1,ni=0)[0], eye, shape=1,r=1)

            R_brow = cmds.curve (d=1, p=[ (0.4987,0.001,-0.7267),(0.4919,0.001,-0.7267),(0.4784,0.001,-0.711),(0.4717,0.001,-0.6794),(0.4717,0.001,-0.6636),(0.4717,0.001,-0.4428),(0.4717,0.001,-0.1151),(0.4717,0.001,-0.1069),(0.4784,0.001,-0.0906),(0.4919,0.001,-0.0824),(0.4987,0.001,-0.0824),(0.6874,0.001,-0.0824),(0.6941,0.001,-0.0824),(0.7076,0.001,-0.0906),(0.7143,0.001,-0.1069),(0.7143,0.001,-0.1151),(0.7143,0.001,-0.4428),(0.7143,0.001,-0.6636),(0.7143,0.001,-0.6794),(0.7076,0.001,-0.711),(0.6941,0.001,-0.7267),(0.6874,0.001,-0.7267),(0.593,0.001,-0.7267),(0.4987,0.001,-0.7267),])
            brow = cmds.curve (d=1, p=[ (0.4987,0.001,0.7267),(0.4919,0.001,0.7267),(0.4784,0.001,0.711),(0.4717,0.001,0.6794),(0.4717,0.001,0.6636),(0.4717,0.001,0.4428),(0.4717,0.001,0.1151),(0.4717,0.001,0.1069),(0.4784,0.001,0.0906),(0.4919,0.001,0.0824),(0.4987,0.001,0.0824),(0.6874,0.001,0.0824),(0.6941,0.001,0.0824),(0.7076,0.001,0.0906),(0.7143,0.001,0.1069),(0.7143,0.001,0.1151),(0.7143,0.001,0.4428),(0.7143,0.001,0.6636),(0.7143,0.001,0.6794),(0.7076,0.001,0.711),(0.6941,0.001,0.7267),(0.6874,0.001,0.7267),(0.593,0.001,0.7267),(0.4987,0.001,0.7267),])
            cmds.parent( cmds.listRelatives(R_brow,c=1,s=1,ni=0)[0], brow, shape=1,r=1)

            mouth= cmds.curve (d=1, p=[ (-0.6379,0.001,-0.7249),(-0.6484,0.001,-0.7249),(-0.6695,0.001,-0.7131),(-0.6801,0.001,-0.6895),(-0.6801,0.001,-0.6777),(-0.6801,0.001,-0.0073),(-0.6801,0.001,0.6879),(-0.6801,0.001,0.6997),(-0.6695,0.001,0.7233),(-0.6484,0.001,0.7351),(-0.6379,0.001,0.7351),(-0.3423,0.001,0.7351),(-0.3317,0.001,0.7351),(-0.3106,0.001,0.7233),(-0.3001,0.001,0.6997),(-0.3001,0.001,0.6879),(-0.3001,0.001,-0.0073),(-0.3001,0.001,-0.6777),(-0.3001,0.001,-0.6895),(-0.3106,0.001,-0.7131),(-0.3317,0.001,-0.7249),(-0.3423,0.001,-0.7249),(-0.4901,0.001,-0.7249),(-0.6379,0.001,-0.7249),])

            # renaming
            cmds.rename(cadre,self.CADRE_NAME)
            cmds.rename(brow,self.BROWS_HOLDER)
            cmds.rename(eye,self.EYES_HOLDER)
            cmds.rename(mouth,self.MOUTH_HOLDER)

            # clean
            cmds.group(name=self.UI_DADDY,em=True)
            cmds.parent([self.MOUTH_HOLDER,self.EYES_HOLDER,self.BROWS_HOLDER,],self.CADRE_NAME)
            cmds.parent(self.CADRE_NAME,self.UI_DADDY)
            cmds.delete(R_brow)
            cmds.delete(R_eye)

        # sett attr
        attrL = ["translateX", "translateY", "translateZ",
                  "rotateX", "rotateY", "rotateZ",
                  "scaleX", "scaleY", "scaleZ"]
        for i in [self.MOUTH_HOLDER,self.EYES_HOLDER,self.BROWS_HOLDER,]:
            for j in attrL:
                cmds.setAttr(i+"."+j,k=0,l=1)
                cmds.setAttr(i+".v",k=0)

        # cadre
        for j in attrL:
                cmds.setAttr(self.CADRE_NAME+"."+j,k=0,cb=1)
        cmds.setAttr(self.CADRE_NAME+".v",k=0)

        # color
        self.overideColor(theColor=(1,0.37,0), mode="normal",TheSel = [self.MOUTH_HOLDER,self.EYES_HOLDER,self.BROWS_HOLDER,self.CADRE_NAME] )


    def alignBase(self,target,obj):
        print "alignBase()"
        jpZ.matchByXformMatrix(cursel=[target,obj], mode=0 )
        # get BBox 

        # bboxAX,bboxAY,bboxAZ = cmds.getAttr(target + ".boundingBoxMaxX" ) - cmds.getAttr(target + ".boundingBoxMinX" ),cmds.getAttr(target + ".boundingBoxMaxY" )- cmds.getAttr(target + ".boundingBoxMinY" ),cmds.getAttr(target + ".boundingBoxMaxZ") - cmds.getAttr(target + ".boundingBoxMinZ" )
        # bboxBX,bboxBY,bboxBZ = cmds.getAttr(obj    + ".boundingBoxMaxX" ) - cmds.getAttr(obj    + ".boundingBoxMinX" ),cmds.getAttr(obj    + ".boundingBoxMaxY" )- cmds.getAttr(obj    + ".boundingBoxMinY" ),cmds.getAttr(obj    + ".boundingBoxMaxZ") - cmds.getAttr(obj    + ".boundingBoxMinZ" )
        # cmds.move( ( bboxAX  )*0.5 , ( bboxAY) * 0.5 , (bboxAZ ) *0.5, obj, r=1,  )
        
        bboxA = cmds.exactWorldBoundingBox(target)
        bboxB = cmds.exactWorldBoundingBox(obj)


        diffX=( bboxB[3] - bboxB[0]  ) -( bboxA[3] - bboxA[0] ) 



        baseX= ( bboxB[3] - bboxB[0]  )

        print "baseX=", baseX
        # print "xdiff=", xdiff
        # cmds.move( ( bboxA[3] - bboxA[0] )*0.5 , -( bboxA[4] - bboxA[1] ) * 0.25 , (bboxA[5] - bboxA[2]) *1, obj, r=1, os=1, )
        cmds.xform(obj,relative=True, translation=( (bboxA[3] - bboxA[0] )/2.0 + diffX - baseX*1.66 , ( bboxB[4] - bboxB[1] ) /2 , (bboxA[5] - bboxA[2]) *0.33)  )


    def cleaningBeaver (self,*args, **kwargs):
        print "connectToDisplLevel()"
        # visholder connect
        jpZ.chr_applyVisLevel(objL=[self.CADRE_NAME,self.MOUTH_HOLDER,self.BROWS_HOLDER,self.EYES_HOLDER],curLvl=self.THEVISLVL,GUI=False,)
        # add ctrs to ctr set
        cmds.sets([self.MOUTH_HOLDER,self.BROWS_HOLDER,self.EYES_HOLDER,self.CADRE_NAME], add="set_control")
        # add to displ layer
        jpZ.cleanDisplayLayerWithSet()

        # parent the rigFolder inside the char
        cmds.parent(self.UI_DADDY,self.THEPARENTFOLDER)

    def generate(self,*args, **kwargs):
        print 'generate()'

        debug = ""
        thisThirtCHRB =True
        thisThirtCHRBL = []
        for i in [self.THEHEAD,self.THEHEAD+"."+self.OBROWSAL[0], self.THEHEAD+"."+self.OEYESAL[0],self.THEHEAD+"."+self.OMOUTHAL[0]]:
            if not cmds.objExists(i):
                print i,"doesn't exists!"
                thisThirtCHRBL.append(False)
        if False in thisThirtCHRBL:
            thisThirtCHRB =False
        if not thisThirtCHRB:
            debug="It's not a Third Character: nothing Done"
            print debug
        else:
            debug = "applying custom Facial for Third CHR"
            # get userDefined attr and filter in 3 cat
            udAttrL = cmds.listAttr(self.THEHEAD, ud=1, )
            if udAttrL:
                for attr in udAttrL:
                    print attr
                    if attr in self.OBROWSAL:
                        self.start=1
                    if self.start:
                        if attr in self.OBROWSAL:
                            print "********self.addBrow"
                            self.addBrow=1
                            self.addMouth =0
                            self.addEye =0
                        elif attr in self.OEYESAL:
                            print "********self.addEye"
                            self.addBrow=0
                            self.addMouth =0
                            self.addEye =1
                        elif attr in self.OMOUTHAL:
                            print "********self.addMouth" 
                            self.addBrow=0
                            self.addMouth =1
                            self.addEye =0

                        # create listRelatives
                        if self.addBrow:
                            self.browL.append(attr)
                        elif self.addEye:
                            self.eyesL.append(attr)
                        elif self.addMouth:
                            self.mouthL.append(attr)
                            
                        

            print self.browL
            print self.eyesL
            print self.mouthL

            # create obj, addAttr,Connect
            self.createUi()

            # add to it and connect
            if len(self.browL):
                attrHolder = self.BROWS_HOLDER
                for i in self.browL:
                    self.replaceConnectAttr(self.THEHEAD,attrHolder,i)
                    
                    
            if len(self.eyesL):
                attrHolder = self.EYES_HOLDER
                for i in self.eyesL:
                    self.replaceConnectAttr(self.THEHEAD,attrHolder,i)
                    
            if len(self.mouthL):
                attrHolder = self.MOUTH_HOLDER
                for i in self.mouthL:
                    self.replaceConnectAttr(self.THEHEAD,attrHolder,i)
                    

            # align with head
            self.alignBase(self.THEHEAD, self.UI_DADDY  )

            # constrain to head
            cmds.parentConstraint(self.THEHEAD, self.UI_DADDY,mo=1)
            cmds.scaleConstraint(self.THEHEAD, self.UI_DADDY,mo=1)

            # cleaning Beaver
            self.cleaningBeaver()

            # end
        return True,debug

# launch
# Ctf= Create_Third_FacialUI()
# Ctf.generate()

thirdC= Create_Third_FacialUI()
result,debug = thirdC.generate()
