import maya.cmds as mc
import pymel.core as pm
from mtoa import aovs

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
        self.visDmnToonS = [] # set name gathering the dmnToon of all the visible object in the layer

        self.initRndItem()
        self.scriptJobManager(delete = False, create = True)

        # self.rndLayerD = {}
        # for each in mc.ls("*",type="renderLayer"):
        #     if each!='defaultRenderLayer':
        #         self.rndLayerD[mc.getAttr(each+".identification")]=each



    def initRndItem(self, rndItemL = None):
        self.log.funcName ="'initRndItem' "

        self.allRndObjL = mc.ls("geo_*", type="transform") + mc.ls("*:geo_*", type="transform") + mc.ls("*:*:geo_*", type="transform") + mc.ls("vol_*", type="transform") + mc.ls("*:vol_*", type="transform") + mc.ls("*:*:vol_*", type="transform")+ mc.ls("col_*", type="transform") + mc.ls("*:col_*", type="transform") + mc.ls("*:*:col_*", type="transform")
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
                            "set_lyrID"+layerIdS+"_primaryRayOff"
                            ]
        self.visDmnToonS = "set_lyrID"+layerIdS+"_visDmnToon"
        self.layerMemberL = mc.editRenderLayerMembers(layerNameS,q=True, fullNames =True)

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
        if mc.ls("template",type="displayLayer"):
            mc.delete("template")

        if setBlackMatteOnL and setPrimaryRayOffL:
            setBlackMatteOnMemberL = mc.sets(setBlackMatteOnL[0], q=True)
            setPrimaryRayOffMemberL= mc.sets(setPrimaryRayOffL[0], q=True)
        else:
            txt = "No 'set_lyrIDx_blackMatteOn' or 'set_lyrIDx_primaryRayOff' found, cannot update display layers"
            self.log.printL("w", txt)
            return
        # if setTemplateMemberL:
        #     setTemplateMemberL= mc.sets(setTemplateL[0], q=True)


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

        self.layerMemberL = mc.editRenderLayerMembers(self.layerNameS,q=True, fullNames =True)





    def duplicateLayer(self, layerName= "", rndItemL = None):
        self.log.funcName ="'duplicateLayer'"
        if not layerName:
            layerName = self.layerNameS+"_copy"

        layerContentOrigL = self.layerMemberL
        layerSetOrigL = self.layerSetL
        layerIdOrigI = self.layerIdI
        layerNameOrigS = self.layerNameS


        if not self.layerNameS:
            txt = "'{}' cannot be duplicated".format(layerName)
            self.log.printL("i", txt)
            return dict(resultB=self.log.resultB, logL=self.log.logL)

        if layerName in mc.ls("*",type="renderLayer"):
            txt = "'{}' render layer already exist".format(layerName)
            self.log.printL("e", txt)
            return dict(resultB=self.log.resultB, logL=self.log.logL)

        allPartitionL = mc.ls(type="partition")
        partitionOrigS = ""
        for each in allPartitionL:
            setL =  mc.partition( each, q=True )
            if setL == layerSetOrigL:
                partitionOrigS = each
                break

        mc.createRenderLayer( layerContentOrigL, noRecurse=True, name=layerName, makeCurrent=True )
        self.initLayer()


        layerIdS = str(mc.getAttr(self.layerNameS+".identification"))

        toDeleteL= mc.ls("par_lyrID"+layerIdS)+ mc.ls(self.layerSetL)
        if toDeleteL:
            mc.delete(toDeleteL)
            print "deleting:",toDeleteL

        mc.partition( name="par_lyrID"+layerIdS)
        mc.duplicate(layerSetOrigL[0],  name=self.layerSetL[0], inputConnections = True)
        mc.duplicate(layerSetOrigL[1],  name=self.layerSetL[1], inputConnections = True)
        mc.duplicate(layerSetOrigL[2],  name=self.layerSetL[2], inputConnections = True)

        print "switch to ", layerNameOrigS
        mc.editRenderLayerGlobals( currentRenderLayer=layerNameOrigS )
        mc.editRenderLayerAdjustment(self.layerSetL[1]+".aiOverride", remove=True)
        mc.editRenderLayerAdjustment(self.layerSetL[2]+".aiOverride", remove=True)
        mc.editRenderLayerGlobals( currentRenderLayer=layerName )
        print "switch to ", layerName

        mc.setAttr(self.layerSetL[1]+".aiOverride", 0)
        mc.editRenderLayerAdjustment(self.layerSetL[1]+".aiOverride")
        mc.setAttr(self.layerSetL[1]+".aiOverride", 1)

        mc.setAttr(self.layerSetL[2]+".aiOverride", 0)
        mc.editRenderLayerAdjustment(self.layerSetL[2]+".aiOverride")
        mc.setAttr(self.layerSetL[2]+".aiOverride", 1)

        for eachSet in self.layerSetL:
            outConnectionL = mc.listConnections( eachSet+".partition", d=True, s=False, plugs=True)
            if outConnectionL:
                for eachConnection in outConnectionL:
                    mc.disconnectAttr (eachSet+".partition", eachConnection)

        mc.partition(self.layerSetL, add= "par_lyrID"+layerIdS)


        txt = "'{}' duplicated to {}".format(layerNameOrigS, layerName)
        self.log.printL("i", txt)
        return dict(resultB=self.log.resultB, logL=self.log.logL)


    def createLightPass(self):
        self.log.funcName ="'createLightPass' "

        layerNameS = "lyr_" + self.layerNameS.split("_")[1] + "_lgp"
        layerNameOrigS = self.layerNameS
        self.duplicateLayer(layerName= layerNameS)

        if not self.layerNameS:
            txt = "'{}' cannot be duplicated".format(layerName)
            self.log.printL("i", txt)
            return dict(resultB=self.log.resultB, logL=self.log.logL)

        setVisibleL = mc.ls(self.layerSetL[0], type = "objectSet")
        if setVisibleL:
            setVisibleMemberL= mc.sets(setVisibleL[0], q=True)
        else:
            txt = "no 'set_lyrX_visible' set found for layer '{}'".format(self.layerNameS)
            self.log.printL("e", txt)

        dmnToonL = []
        for eachGeo in setVisibleMemberL:
            shdGroupL = mc.ls(mc.listHistory(eachGeo,future = True),type="shadingEngine")
            if "eye" in eachGeo or "outline" in eachGeo:
                pass
            else:
                if mc.getAttr(eachGeo+".aiSelfShadows")!=1:
                    mc.editRenderLayerAdjustment(eachGeo+".aiSelfShadows")
                    mc.setAttr(eachGeo + ".aiSelfShadows", 1)
                if mc.getAttr(eachGeo+".castsShadows")!=1:
                    mc.editRenderLayerAdjustment(eachGeo+".castsShadows")
                    mc.setAttr(eachGeo+".castsShadows",1)

            for eachSG in shdGroupL:
                aiShaderL = mc.listConnections(eachSG+'.aiSurfaceShader',connections = False,  source =True, destination = False)
                if aiShaderL:
                    if mc.nodeType(aiShaderL[0]) == "dmnToon":
                        dmnToonL.append(aiShaderL[0])
                    else:
                        txt = "'{}' is not the right type, should be a 'dmnToon'".format(aiShaderL[0])
                        self.log.printL("e", txt)

        toDeleteL= mc.ls(self.visDmnToonS)
        if toDeleteL:
            mc.delete(toDeleteL)
            print "deleting:",toDeleteL

        mc.sets(name=self.visDmnToonS, empty=True)

        if dmnToonL:
            mc.sets(dmnToonL, forceElement=self.visDmnToonS)
            for each in dmnToonL:
                connectL = mc.listConnections(each + ".selfShadows", plugs=True, source=True, destination=False)
                if connectL:               
                    for eachConnection in connectL:
                        mc.editRenderLayerAdjustment(each + ".selfShadows")
                        mc.disconnectAttr (eachConnection, each + ".selfShadows")
                    mc.setAttr(each + ".selfShadows", 1)
                if mc.getAttr(each + ".selfShadows") != 1:
                    mc.editRenderLayerAdjustment(each + ".selfShadows")
                    mc.setAttr(each + ".selfShadows", 1)

        mc.addAttr(self.visDmnToonS, shortName='output', longName='output', attributeType="enum", enumName= "composite:final_layout:toon:rim_toon:contour:shadow_mask:incidence:lambert:occlusion:diffuse:ambient:specular:reflection:refraction:lightpass:diffuse_bounces:glossy_bounce")
        mc.setAttr(self.visDmnToonS+".output", 14)
        mc.setAttr(self.visDmnToonS+".aiOverride", 0)
        mc.editRenderLayerAdjustment(self.visDmnToonS+".aiOverride")
        mc.setAttr(self.visDmnToonS + ".aiOverride", 1)
        if mc.getAttr("defaultArnoldRenderOptions.aovMode") == True :
            mc.editRenderLayerAdjustment("defaultArnoldRenderOptions.aovMode")
            mc.setAttr("defaultArnoldRenderOptions.aovMode", 0)
        else:
            pass
        txt = "Created '{}' light pass from '{}'".format(layerNameS, layerNameOrigS)
        self.log.printL("i", txt)
        return dict(resultB=self.log.resultB, logL=self.log.logL)

    def createFxsPass(self):
        self.log.funcName = "'createFxsPass' "

        layerNameS = "lyr_" + self.layerNameS.split("_")[1] + "_fxs"
        layerNameOrigS = self.layerNameS
        self.duplicateLayer(layerName=layerNameS)

        if not self.layerNameS:
            txt = "'{}' cannot be duplicated".format(layerName)
            self.log.printL("i", txt)
            return dict(resultB=self.log.resultB, logL=self.log.logL)

        setVisibleL = mc.ls(self.layerSetL[0], type="objectSet")
        if setVisibleL:
            setVisibleMemberL = mc.sets(setVisibleL[0], q=True)
        else:
            txt = "no 'set_lyrX_visible' set found for layer '{}'".format(self.layerNameS)
            self.log.printL("e", txt)

        dmnToonL = []
        for eachGeo in setVisibleMemberL:
            shdGroupL = mc.ls(mc.listHistory(eachGeo, future=True), type="shadingEngine")
            if "eye" in eachGeo or "outline" in eachGeo:
                pass
            else:
                if mc.getAttr(eachGeo + ".selfShadows") != 1:
                    mc.editRenderLayerAdjustment(eachGeo + ".selfShadows")
                    mc.setAttr(eachGeo + ".selfShadows", 1)
                if mc.getAttr(eachGeo + ".castsShadows") != 1:
                    mc.editRenderLayerAdjustment(eachGeo + ".castsShadows")
                    mc.setAttr(eachGeo + ".castsShadows", 1)

            for eachSG in shdGroupL:
                aiShaderL = mc.listConnections(eachSG + '.aiSurfaceShader', connections=False, source=True, destination=False)
                if aiShaderL:
                    if mc.nodeType(aiShaderL[0]) == "dmnToon":
                        dmnToonL.append(aiShaderL[0])
                    else:
                        txt = "'{}' is not the right type, should be a 'dmnToon'".format(aiShaderL[0])
                        self.log.printL("e", txt)

        toDeleteL = mc.ls(self.visDmnToonS)
        if toDeleteL:
            mc.delete(toDeleteL)
            print "deleting:", toDeleteL

        mc.sets(name=self.visDmnToonS, empty=True)

        if dmnToonL:
            mc.sets(dmnToonL, forceElement=self.visDmnToonS)
            for each in dmnToonL:
                connectL = mc.listConnections(each + ".aiSelfShadows", plugs=True, source=True, destination=False)
                if connectL:
                    for eachConnection in connectL:
                        mc.editRenderLayerAdjustment(each + ".aiSelfShadows")
                        mc.disconnectAttr (eachConnection, each + ".aiSelfShadows")
                    mc.setAttr(each + ".aiSelfShadows", 1)
                if mc.getAttr(each + ".aiSelfShadows") != 1:
                    mc.editRenderLayerAdjustment(each + ".aiSelfShadows")
                    mc.setAttr(each + ".aiSelfShadows", 1)

#        mc.addAttr(self.visDmnToonS, shortName='output', longName='output', attributeType="enum", enumName="composite:final_layout:toon:rim_toon:contour:shadow_mask:incidence:lambert:occlusion:diffuse:ambient:specular:reflection:refraction:lightpass:diffuse_bounces:glossy_bounce")
#        mc.setAttr(self.visDmnToonS + ".output", 14)
#        mc.setAttr(self.visDmnToonS + ".aiOverride", 0)
#        mc.editRenderLayerAdjustment(self.visDmnToonS + ".aiOverride")
#        mc.setAttr(self.visDmnToonS + ".aiOverride", 1)

        txt = "Created '{}' light pass from '{}'".format(layerNameS, layerNameOrigS)
        self.log.printL("i", txt)
        return dict(resultB=self.log.resultB, logL=self.log.logL)


def createCryptomatteLayer():
    ## Add assets ##
    pm.select('|shot|grp_character', '|shot|grp_prop', '|shot|grp_set', '|shot|grp_prop')

    ## Create custom layer and make current ##
    pm.createRenderLayer(n='lyr_utl0_bty_16')
    pm.editRenderLayerGlobals(currentRenderLayer='lyr_utl0_bty_16')

def setCryptoAov():
    ''''
        Special aov for cryptomatte to use in an extra layer
    '''
    ## Set dmnToon output mode to lambert ##
#    dmnToonOutput = pm.ls(type='dmnToon')
#    [pm.setAttr(out + '.output', 7) for out in dmnToonOutput]

    ## Create and set the Cryptomatte aov ##
    defRenderOpt = pm.PyNode('defaultArnoldRenderOptions')
    if pm.objExists('alCryptoShader') == True:
        pm.delete('alCryptoShader')
        print 'Delete alCryptoShader !'

    if not pm.objExists('alCryptoShader') == True:
        pm.shadingNode('alSurface', asShader=True, name='alCryptoShader')
        pm.setAttr('alCryptoShader.standardCompatibleAOVs', 0)
        pm.setAttr('alCryptoShader.specular1Strength', 0)
        maya.mel.eval('hookShaderOverride(\"lyr_utl0_bty_16\", \"\", \"alCryptoShader\");')

    else:
        pass

    aovs.AOVInterface()
    #myAovs.addAOV("crypto_object", aovType='rgb')
    aovsL = defRenderOpt.aovs.get()
    [aov.attr('enabled').set(False) for aov in aovsL if aov.attr('name').get() == 'crypto_object']
    pm.editRenderLayerAdjustment('aiAOV_*.enabled')
    [aov.attr('enabled').set(False) for aov in aovsL]
    [aov.attr('enabled').set(True) for aov in aovsL if aov.attr('name').get() == 'crypto_object']


def setUtlAovs() :
    aovs.AOVInterface()
    defRenderOpt = pm.PyNode('defaultArnoldRenderOptions')
    aovsL = defRenderOpt.aovs.get()

    if pm.objExists('alUtls') == True:
        pm.delete('alUtls')
        print 'Delete AiUtls !'

    if not pm.objExists('alUtls') == True:
        pm.shadingNode('aiUtility', asShader=True, name='alUtls')
        pm.setAttr('alUtls.shadeMode', 2)
        pm.setAttr('alUtls.colorMode', 5)

    else:
        pass

    pm.connectAttr('alUtls.outColor', 'aiAOV_uvs.defaultValue', force=True)

    if pm.objExists('aiAOVDriverP32') == True:
        pm.delete('aiAOVDriverP32')
        print 'Delete aiAOVDriverP32 !'

    if not pm.objExists('aiAOVDriverP32') == True:
        pm.createNode('aiAOVDriver', n='aiAOVDriverP32', skipSelect=True)
        pm.setAttr('aiAOVDriverP32.autocrop', 1)

    else:
        pass

    pm.connectAttr('aiAOVDriverP32.aiTranslator', 'aiAOV_P.outputs[0].driver', f=True)
    pm.connectAttr('defaultArnoldFilter.aiTranslator', 'aiAOV_Pref.outputs[0].filter', f=True)

def setUtl32Aovs() :
    aovs.AOVInterface()
    defRenderOpt = pm.PyNode('defaultArnoldRenderOptions')
    #pm.editRenderLayerAdjustment('aiAOV_*.enabled')
    if not pm.objExists('aiAOVDriverP32') == True:
        pm.createNode('aiAOVDriver', n='aiAOVDriverP32', skipSelect=True)
        pm.setAttr('aiAOVDriverP32.autocrop', 1)

    else:
        pass

    pm.connectAttr('defaultArnoldFilter.aiTranslator', 'aiAOV_Pref.outputs[0].filter', f=True)
    aovsL = defRenderOpt.aovs.get()

    [aov.attr('enabled').set(False) for aov in aovsL if aov.attr('name').get() == 'crypto_object' and aov.attr('enabled').get() == 1]
    #[aov.attr('enabled').set(False) for aov in aovsL if aov.attr('name').get() == 'P' and aov.attr('enabled').get() == 1]
    pm.editRenderLayerAdjustment('aiAOV_*.enabled')
    [aov.attr('enabled').set(False) for aov in aovsL]
    [aov.attr('enabled').set(True) for aov in aovsL if aov.attr('name').get() == 'P']
    pm.connectAttr('defaultArnoldFilter.aiTranslator', 'aiAOV_P.outputs[0].filter', f=True)

    #[aov.attr('enabled').set(False) for aov in aovsL if aov.attr('name').get() == 'crypto_object']
    #pm.editRenderLayerAdjustment('defaultArnoldDriver.halfPrecision')
    #pm.setAttr('defaultArnoldDriver.halfPrecision', 0)


