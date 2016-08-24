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

        self.initRndItem()
        self.scriptJobManager(delete = False, create = True)

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
                self.log.printL("w", "Nothing selected")
                rndItemL = []
            else:
                allDescendentL= mc.listRelatives(selectionL, allDescendents = True, type = "transform")
                if allDescendentL is None:
                    allDescendentL = []
                rndItemL = allDescendentL + selectionL

        self.rndItemL = []
        for each in rndItemL:
            if each in self.allRndObjL:
                self.rndItemL.append(each)
        return self.rndItemL


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
            self.layerSetL = []
            self.layerMemberL = []
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




    def initLayerDisplay(self):
        self.log.funcName ="'initLayerDisplay' "

        setBlackMatteOnL = mc.ls(self.layerSetL[1], type = "objectSet")
        setPrimaryRayOffL = mc.ls(self.layerSetL[2], type = "objectSet")

        if mc.ls("primaryRayOff",type="displayLayer"):
            mc.delete("primaryRayOff")
        if mc.ls("blackMatteOn",type="displayLayer"):
            mc.delete("blackMatteOn")

        if setBlackMatteOnL and setPrimaryRayOffL:
            setBlackMatteOnMemberL = mc.sets(setBlackMatteOnL[0], q=True)
            setPrimaryRayOffMemberL= mc.sets(setPrimaryRayOffL[0], q=True)
        else:
            txt = "No 'set_lyrIDx_blackMatteOn' or 'set_lyrIDx_primaryRayOff' found, cannot update display layers"
            self.log.printL("w", txt)
            return


        if setPrimaryRayOffMemberL:
            mc.createDisplayLayer(setPrimaryRayOffMemberL,number=1, empty=False, noRecurse=False, name="primaryRayOff")
            mc.setAttr("primaryRayOff.shading", 0)
            mc.setAttr("primaryRayOff.color", 7)
        if setBlackMatteOnMemberL:
            mc.createDisplayLayer(setBlackMatteOnMemberL,number=1, empty=False, noRecurse=False, name="blackMatteOn")
            mc.setAttr("blackMatteOn.color", 4)



    def scriptJobManager(self, delete = False, create = True):
        self.log.funcName ="'scriptJobManager' "
        scriptJobL = mc.scriptJob( listJobs =True)
        existingScriptJobNumb = 0
        for each in scriptJobL:
            if "protected=True, event=['renderLayerManagerChange', 'from dminutes import layerManager" in each:
                existingScriptJobNumb+=1
                if delete:
                    jobId = int(each.split(":")[0])
                    mc.scriptJob( kill=jobId, force=True)
                    self.log.printL("i", "'renderLayerManagerChange' scriptjob number '{}' deleted".format(jobId) )
        if not existingScriptJobNumb and create:
            jobId = mc.scriptJob( event= ['renderLayerManagerChange','from dminutes import layerManager ;lm=layerManager.LayerManager(); lm.initLayer(); lm.initLayerDisplay()'], protected=True)
            self.log.printL("i", "'renderLayerManagerChange' scriptjob number '{}' created".format(jobId) )




    def createRndlayer(self, layerName="lyr_default_name", layerContentL=None, disableLayer = False):
        self.log.funcName ="'createRndlayer' "

        if layerContentL is None:
            layerContentL=self.astRndObjL


        if layerName in mc.ls("*",type="renderLayer"):
            txt = "'{}' render layer already exist".format(layerName)
            self.log.printL("e", txt)
            return dict(resultB=self.log.resultB, logL=self.log.logL)

        mc.createRenderLayer( layerContentL, noRecurse=True, name=layerName, makeCurrent=True )
        #maya.mel.eval("layerEditorMoveRenderItem RenderLayerTab "+str(layerPosition))  #deactive car le 'layerPosition' decale le layer vers le haut ou le bas de la pile en fonction de sa valeur (0 ou 1). il ne s'agit pas d'un d'une position
        layerIdS = str(mc.getAttr(layerName+".identification"))
        #mc.editRenderLayerGlobals( currentRenderLayer=layerName )
        self.initLayer()

        toDeleteL= mc.ls("par_lyrID"+layerIdS)+ mc.ls(self.layerSetL)
        if toDeleteL:
            mc.delete(toDeleteL)

        miscUtils.createPartitionSets(setL = self.layerSetL ,partitionS = "par_lyrID"+layerIdS,gui = self.gui)
        mc.sets(layerContentL, forceElement=self.layerSetL[0])

        mc.addAttr(self.layerSetL[1], shortName='aiMatte', longName='aiMatte', attributeType='bool')
        mc.setAttr(self.layerSetL[1]+".aiMatte", 1)
        mc.setAttr(self.layerSetL[1]+".aiOverride", 0)
        mc.editRenderLayerAdjustment(self.layerSetL[1]+".aiOverride")
        mc.setAttr(self.layerSetL[1]+".aiOverride", 1)

        mc.addAttr(self.layerSetL[2], shortName='primaryVisibility', longName='primaryVisibility', attributeType='bool')
        mc.setAttr(self.layerSetL[2]+".primaryVisibility", 0)
        mc.setAttr(self.layerSetL[2]+".aiOverride", 0)
        mc.editRenderLayerAdjustment(self.layerSetL[2]+".aiOverride")
        mc.setAttr(self.layerSetL[2]+".aiOverride", 1)

        if disableLayer:
            mc.setAttr(layerName+".renderable", 0)

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
                mc.editRenderLayerMembers(self.layerNameS, itemToAddL, remove= False, noRecurse=True)
                mc.sets(itemToAddL, forceElement=self.layerSetL[0])
                self.log.printL("i", "added {} items to layer'{}': {}".format(len(itemToAddL), self.layerNameS, itemToAddL))
            else:
                self.log.printL("i", "nothing to add to layer'{}'".format(self.layerNameS))
        else:
            itemToRemoveL = list(set(rndItemL) & set(self.layerMemberL))
            if itemToRemoveL:
                mc.editRenderLayerMembers(self.layerNameS, itemToRemoveL, remove= True, noRecurse=True)
                for eachSet in self.layerSetL:
                    mc.sets(itemToRemoveL, remove=eachSet)
                self.log.printL("i", "removed {} items from layer'{}': {}".format(len(itemToRemoveL), self.layerNameS, itemToRemoveL))
            else:
                self.log.printL("i", "nothing to remove from layer'{}'".format(self.layerNameS))

        self.layerMemberL = mc.editRenderLayerMembers(self.layerNameS,q=True)




