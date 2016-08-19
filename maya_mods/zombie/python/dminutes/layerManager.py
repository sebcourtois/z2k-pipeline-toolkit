import maya.cmds as mc


# import os
# import re
# import shutil
import maya.mel
# import pymel.core as pm

from dminutes import miscUtils
reload (miscUtils)








class LayerManager:
    def __init__(self, gui = True):     
        self.gui=gui
        self.log = miscUtils.LogBuilder(gui=gui, logL = [], resultB = True)

        self.allRndObjL = []    # all renderable objects
        self.envRndObjL = []    # evironement renderable objects
        self.astRndObjL = []    # asset renderable objects (basically all renderable except environement)

        self.rndItemL = []      # renderable item to be manipulated (for instance, add or remove to a set or layer)

        self.layerIdI = 0       # is the id of the layer to work on, '0' by default for the current layer, 0 for 'defaultRenderLayer' 
        self.layerSetL = []     # '_visible', '_blackMatteOn'... set names for the current layer
        self.layerMemberL = [] #  layer members list
        self.layerNameS = ""


        # self.rndLayerD = {}
        # for each in mc.ls("*",type="renderLayer"):
        #     if each!='defaultRenderLayer':
        #         self.rndLayerD[mc.getAttr(each+".identification")]=each



    def initRndItem(self, rndItemL = None):
        self.log.funcName ="'initRndItem' "

        self.allRndObjL = mc.ls("geo_*",type="transform")+mc.ls("*:geo_*",type="transform")+mc.ls("*:*:geo_*",type="transform")
        for each in self.allRndObjL:
            if "env_" in each:
                self.envRndObjL.append(each)
            else:
                self.astRndObjL.append(each)

        if rndItemL is None:
            selectionL = mc.ls(selection=True)
            if not selectionL:
                txt = "Nothing selected".format(layerSetL[layerIdI])
                self.log.printL("w", txt)
                rndItemL = []
            else:
                rndItemL = mc.listRelatives(selectionL, allDescendents = True, type = "transform")

        self.rndItemL = []
        for each in rndItemL:
            if each in self.allRndObjL:
                self.rndItemL.append(each)


    def initLayer(self, layerNameS = ""):
        self.log.funcName ="'initLayer' "

        if not layerNameS:
            layerNameS = mc.editRenderLayerGlobals( query=True, currentRenderLayer=True )
        else:
            if not mc.ls(layerNameS,type="renderLayer"):
                txt = "'{}' layer doesn't exist".format(layerNameS)
                self.log.printL("e", txt)
                raise ValueError(txt)

        layerIdI = mc.getAttr(layerNameS+".identification")
        if layerIdI == 0:
            txt = "'{}' active layer is the 'defaultRenderLayer', please pick an other one".format(layerNameS)
            self.log.printL("e", txt)
            self.layerIdI = 0
            self.layerNameS = ""
            raise ValueError(txt)
        else:
            self.layerIdI = layerIdI
            self.layerNameS = layerNameS

        layerIdS = str(layerIdI)
        self.layerSetL =[   "set_lyrID"+layerIdS+"_visible",
                            "set_lyrID"+layerIdS+"_blackMatteOn",
                            "set_lyrID"+layerIdS+"_primaryRayOff"]
        self.layerMemberL = mc.editRenderLayerMembers(layerNameS,q=True)

        txt = "layer '{}' initialised".format(layerNameS)
        self.log.printL("i", txt)




    def createRndlayer(self, layerName="lyr_default_name", layerContentL=None, layerPosition = 0):
        self.log.funcName ="'createRndlayer' "

        if layerContentL is None:
            layerContentL=self.astRndObjL


        if layerName in mc.ls("*",type="renderLayer"):
            txt = "'{}' render layer already exist".format(layerName)
            self.log.printL("e", txt)
            return dict(resultB=self.log.resultB, logL=self.log.logL)

        mc.createRenderLayer( layerContentL, noRecurse=True, name=layerName, makeCurrent=True )
        maya.mel.eval("layerEditorMoveRenderItem RenderLayerTab "+str(layerPosition))
        layerIdS = str(mc.getAttr(layerName+".identification"))
        #mc.editRenderLayerGlobals( currentRenderLayer=layerName )
        self.initLayer()

        miscUtils.createPartitionSets(setL = self.layerSetL ,partitionS = "par_lyrID"+layerIdS,gui = self.gui)
        mc.sets(layerContentL, forceElement=self.layerSetL[0])

        mc.addAttr(self.layerSetL[1], shortName='aiMatte', longName='aiMatte', attributeType='bool')
        mc.editRenderLayerAdjustment(self.layerSetL[1]+".aiMatte")
        mc.setAttr(self.layerSetL[1]+".aiMatte", 1)

        mc.addAttr(self.layerSetL[2], shortName='primaryVisibility', longName='primaryVisibility', attributeType='bool')
        mc.editRenderLayerAdjustment(self.layerSetL[2]+".primaryVisibility")
        mc.setAttr(self.layerSetL[2]+".primaryVisibility", 0)

        return dict(resultB=self.log.resultB, logL=self.log.logL)



    def addItemToSet(self, rndItemL = None, setTypeI = 0 ):
        self.log.funcName ="'addItemToSet' "
        """
        setTypeI : int: according to the 'layerSetL', 0 --> "_visible", 1 --> "_blackMatteOn" etc ..
        """
        if rndItemL is None:
            rndItemL = self.rndItemL

        mc.sets(rndItemL, forceElement=self.layerSetL[setTypeI])
        txt = "'{}' added to '{}': {}".format(len(rndItemL),self.layerSetL[setTypeI],rndItemL)
        self.log.printL("i", txt)

        return dict(resultB=self.log.resultB, logL=self.log.logL)



    def layerMemberModifier(self, rndItemL = None, mode="add"):
        self.log.funcName ="'addItemToLayer' "

        if rndItemL is None:
            rndItemL = self.rndItemL

        if mode == "add":
            itemToAddL = list(set(rndItemL) - set(self.layerMemberL))
            if itemToAddL:
                mc.editRenderLayerMembers(self.layerMemberL, itemToAddL, remove= False, noRecurse=True)
                mc.sets(itemToAddL, forceElement=self.layerSetL[0])
                self.log.printL("i", "added {} items to layer'{}': {}".format(len(itemToAddL), self.layerNameS, itemToAddL))
            else:
                self.log.printL("i", "nothing to add to layer'{}'".format(self.layerNameS))
        else:
            itemToRemoveL = list(set(rndItemL) & set(self.layerMemberL))
            if itemToRemoveL:
                mc.editRenderLayerMembers(self.layerMemberL, itemToRemoveL, remove= True, noRecurse=True)
                for eachSet in self.layerSetL:
                    mc.sets(itemToRemoveL, remove=eachSet)
                self.log.printL("i", "removed {} items from layer'{}': {}".format(len(itemToRemoveL), self.layerNameS, itemToRemoveL))
            else:
                self.log.printL("i", "nothing to remove from layer'{}'".format(self.layerNameS))

        self.layerMemberL = mc.editRenderLayerMembers(self.layerNameS,q=True)


