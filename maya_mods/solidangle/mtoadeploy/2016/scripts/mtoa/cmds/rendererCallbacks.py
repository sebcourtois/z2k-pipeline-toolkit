import maya.cmds as cmds
import maya.mel as mel
import mtoa.utils as utils
from mtoa.ui.nodeTreeLister import aiHyperShadeCreateMenu_BuildMenu, createArnoldNodesTreeLister_Content
import mtoa.ui.ae.templates as templates
import ctypes
import types
import pymel.core as pm

try:
    import mtoa.utils as utils
    from mtoa.ui.globals.common import createArnoldRendererCommonGlobalsTab, updateArnoldRendererCommonGlobalsTab
    from mtoa.ui.globals.settings import createArnoldRendererGlobalsTab, updateArnoldRendererGlobalsTab
    from mtoa.ui.globals.settings import createArnoldRendererDiagnosticsTab, updateArnoldRendererDiagnosticsTab, createArnoldRendererSystemTab, updateArnoldRendererSystemTab
    from mtoa.ui.aoveditor import createArnoldAOVTab, updateArnoldAOVTab
except:
    import traceback
    traceback.print_exc(file=sys.__stderr__) # goes to the console
    raise

global arnoldAOVCallbacks

try:
    import maya.app.renderSetup.model.rendererCallbacks as rendererCallbacks
    import mtoa.core as core

    class ArnoldRenderSettingsCallbacks(rendererCallbacks.RenderSettingsCallbacks):
    
        # Create the default Arnold nodes
        def createDefaultNodes(self):
            core.createOptions()

    arnoldRenderSettingsCallbacks = ArnoldRenderSettingsCallbacks()
except:
    arnoldRenderSettingsCallbacks = None

try:
    import maya.app.renderSetup.model.renderSetup as renderSetup
    import maya.app.renderSetup.model.rendererCallbacks as rendererCallbacks
    import maya.app.renderSetup.model.typeIDs as typeIDs
    import maya.app.renderSetup.model.selector as selector
    from maya.app.renderSetup.model.selection import Selection
    import maya.app.renderSetup.model.undo as undo
    import maya.app.renderSetup.model.utils as renderSetupUtils
    from mtoa.aovs import AOVInterface
    import mtoa.core as core
    import mtoa.ui.aoveditor as aoveditor
    import json
    import maya.api.OpenMaya as OpenMaya

    class ArnoldAOVChildSelector(selector.Selector):
        kTypeId = typeIDs.arnoldAOVChildSelector
        kTypeName = 'arnoldAOVChildSelector'
        aAOVNodeName = OpenMaya.MObject()

        @classmethod
        def initializer(cls):
            cls.inheritAttributesFrom(selector.Selector.kTypeName)

            # The Arnold AOV Node Name is the name of the aiAOV node for a particular AOV name.
            # It is attached to an aiAOVDriver and aiAOVFilter.
            default = OpenMaya.MFnStringData().create('')
            attr = OpenMaya.MFnTypedAttribute()
            cls.aAOVNodeName = cls.createInput(attr,["arnoldAOVNodeName", "ann", OpenMaya.MFnData.kString, default])
            cls.addAttribute(cls.aAOVNodeName)
            cls.affectsOutput(cls.aAOVNodeName)

        def contentType(self):
            return selector.Selector.kNonDagOnly

        def isAbstractClass(self):
            return False

        def __init__(self):
            super(ArnoldAOVChildSelector, self).__init__()
            self._cache = set()

        # ACCESSORS / MUTATORS / QUERIES
        def _getInputAttr(self, attr, dataBlock=None):
            return dataBlock.inputValue(attr) if dataBlock else OpenMaya.MPlug(self.thisMObject(), attr)

        def getAOVNodeName(self, dataBlock=None):
            return self._getInputAttr(self.aAOVNodeName, dataBlock).asString()

        def setAOVNodeName(self, val):
            if val != self.getAOVNodeName():
                with undo.NotifyCtxMgr(selector.kSet % (self.name(), 'arnoldAOVNodeName', val), self.selectionChanged):
                    cmds.setAttr( self.name() + '.arnoldAOVNodeName', val, type='string')

        def acceptsType(self, typeName, dataBlock=None):
            return typeName in ["aiAOV", "aiAOVDriver", "aiAOVFilter"]

        def _update(self, dataBlock):
            self._cache = set()
            aovNodeName = self.getAOVNodeName(dataBlock)
            # If the aovNodeName does not exist because we don't have an AOV 
            # associated with the aovNodeName, then we should empty the cache.
            if(cmds.objExists(aovNodeName)):
                self._cache.add(aovNodeName)
                outputsAttr = aovNodeName + ".outputs"
                numOutputs = cmds.getAttr(outputsAttr, size=True)
                for i in range(numOutputs):
                    outputIndex = outputsAttr + "[" + str(i) + "]"
                    for outputType in [".filter", ".driver"]:
                        output = cmds.listConnections(outputIndex + outputType)[0]
                        self._cache.add(output)
            else:
                self._cache = set()

        def selection(self):
            names = self.names()
            if not self._selection:
                self._selection = Selection(names)
            return self._selection

        @selector.Selector.synced
        def names(self):
            return self._cache

        @selector.Selector.synced
        def nodes(self):
            return self.selection().nodes()

        def _encodeProperties(self, dict):
            encoders = [(self.aAOVNodeName,  self.getAOVNodeName)]
            for attr, encode in encoders:
                dict[OpenMaya.MPlug(self.thisMObject(), attr).partialName(useLongNames=True)] = encode()
            
        def _decodeProperties(self, dict):
            decoders = [(self.aAOVNodeName,  self.setAOVNodeName)]
            for attr, decode in decoders:
                name = OpenMaya.MPlug(self.thisMObject(), attr).partialName(useLongNames=True)
                if name in dict:
                    decode(dict[name])

        def onNodeAdded(self, **kwargs):
            if OpenMaya.MFnDependencyNode(kwargs['obj']).typeName in ["aiAOV", "aiAOVDriver", "aiAOVFilter"] and not self.isDirty():
                self.selectionChanged()
        
        def onNodeRemoved(self, **kwargs):
            if OpenMaya.MFnDependencyNode(kwargs['obj']).typeName in ["aiAOV", "aiAOVDriver", "aiAOVFilter"] and not self.isDirty():
                self.selectionChanged()
        
        def onNodeRenamed(self, **kwargs):
            if OpenMaya.MFnDependencyNode(kwargs['obj']).typeName in ["aiAOV", "aiAOVDriver", "aiAOVFilter"] and not self.isDirty():
                self.selectionChanged()
   
        def onConnectionChanged(self, **kwargs):
            if cmds.nodeType(kwargs['srcPlug']) == "aiAOV" and cmds.nodeType(kwargs['dstPlug']) in ["aiAOVDriver", "aiAOVFilter"]:
                self.selectionChanged()


    class ArnoldAOVCallbacks(rendererCallbacks.AOVCallbacks):
        DEFAULT_ARNOLD_DRIVER_NAME = "defaultArnoldDriver"
        DEFAULT_ARNOLD_FILTER_NAME = "defaultArnoldFilter"
    
        def encode(self):
            aovsJSON = {}
            basicNodeExporter = rendererCallbacks.BasicNodeExporter()

            outputs = []
            aovs = []
            drivers = []
            filters = []
            uniqueDrivers = set()
            uniqueFilters = set()

            try:
                aovNodes = AOVInterface().getAOVNodes()
            except Exception:
                pass
            else:
                # Iterate over our aovNodes (aiAOV nodes)
                for aovNode in aovNodes:
                    aovNodeName = aovNode.name()
                    numOutputs = cmds.getAttr(aovNodeName + ".outputs", size=True)
                    currentOutputs = []
                    
                    # Iterate over our output connections which have driver and filter connections
                    for outputNum in range(0, numOutputs):
                        driver = cmds.listConnections(aovNodeName + ".outputs[" + str(outputNum) + "].driver")[0]
                        filter = cmds.listConnections(aovNodeName + ".outputs[" + str(outputNum) + "].filter")[0]

                        # If we don't have this driver yet, add it to the list
                        if not driver in uniqueDrivers:
                            uniqueDrivers.add(driver)
                            basicNodeExporter.setNodes([driver])
                            drivers.append({driver : basicNodeExporter.encode()})

                        # If we don't have this filter yet, add it to the list
                        if not filter in uniqueFilters:
                            uniqueFilters.add(filter)
                            basicNodeExporter.setNodes([filter])
                            filters.append({filter : basicNodeExporter.encode()})
                        
                        # Append our current aovNode's driver and filter to the currentOutputs
                        currentOutputs.append( { "driver" : driver, "filter" : filter } )
                        
                    # Set the outputs for the specified node name.
                    outputs.append({ aovNodeName : currentOutputs })

                    # Set the AOV information for the current AOV node name.
                    basicNodeExporter.setNodes([aovNodeName])
                    aovs.append( { aovNodeName : basicNodeExporter.encode() })

            # Set the AOV, filters, drivers, and outputs values
            aovsJSON["aovs"] = aovs
            aovsJSON["filters"] = filters
            aovsJSON["drivers"] = drivers
            aovsJSON["outputs"] = outputs
            return aovsJSON
         
        def decode(self, aovsJSON, decodeType):
            
            core.createOptions()

            # We're doing a replace, so remove all previous AOVs
            if decodeType == self.DECODE_TYPE_OVERWRITE:
                AOVInterface().removeAOVs(AOVInterface().getAOVs())

            basicNodeExporter = rendererCallbacks.BasicNodeExporter()

            outputs = aovsJSON["outputs"]
            filterNewNameMap = {} # Used when we're doing a merge
            driverNewNameMap = {} # Used when we're doing a merge
            for output in outputs:
                for key, value in output.iteritems():

                    # If we're doing a merge, we need to delete the nodes that overlap with the nodes we are importing.
                    aovName = key[len('aiAOV_'):] # Remove aiAOV_ from the start of the string
                    if decodeType == self.DECODE_TYPE_MERGE and AOVInterface().getAOVNode(aovName) != None:
                        AOVInterface().removeAOV(aovName)

                    # Create a new aov node with the given aov name
                    aovNode = AOVInterface().addAOV(aovName)
                    
                    # Iterate over the output's value indexes
                    for outputIndex in range(0, len(value)):
                        filterName = value[outputIndex]["filter"]
                        driverName = value[outputIndex]["driver"]
                        
                        # Try to create a filter with the provided name, but we might end up getting a different name back.
                        # So store a mapping between the old filter name and our new name if they are different.
                        newFilterName = filterName
                        if filterName != self.DEFAULT_ARNOLD_FILTER_NAME:
                            newFilterName = cmds.createNode("aiAOVFilter", name=filterName)
                            if newFilterName != filterName:
                                filterNewNameMap[filterName] = newFilterName

                        # Try to create a driver with the provided name, but we might end up getting a different name back.
                        # So store a mapping between the old driver name and our new name if they are different.
                        newDriverName = driverName
                        if driverName != self.DEFAULT_ARNOLD_DRIVER_NAME:
                            newDriverName = cmds.createNode("aiAOVDriver", name=driverName)
                            if newDriverName != driverName:
                                driverNewNameMap[driverName] = newDriverName
                                
                        # Setup our filter and driver connections.
                        for outputType, outputName, newOutputName in ["filter", filterName, newFilterName], ["driver", driverName, newDriverName]:
                            if outputIndex > 0 or cmds.listConnections(key + ".outputs[" + str(outputIndex) + "]." + outputType)[0] != outputName:
                                cmds.connectAttr(newOutputName + ".message", key + ".outputs[" + str(outputIndex) + "]." + outputType, force=True)

            # Iterate over our AOVs and decode them
            aovs = aovsJSON["aovs"]
            for aov in aovs:
                for aovName, aovJSON in aov.iteritems():
                    basicNodeExporter.decode(aovJSON)

            # Iterate over our filters/drivers and decode them
            for outputType, outputNewNameMap in ["filters", filterNewNameMap], ["drivers", driverNewNameMap]:
                outputs = aovsJSON[outputType]
                for output in outputs:
                    for outputName, outputJSON in output.iteritems():
                        # If you have an existing scene of AOV nodes and are doing a merge import,
                        # then you may have a name collision as the saved out node names may be
                        # the same as nodes existing in the scene. In this case the nodes we are
                        # importing need to be renamed to the unique node name that is assigned to
                        # them on creation.
                        if outputName in outputNewNameMap:
                            outputJSON = json.loads(json.dumps(outputJSON).replace(outputName, outputNewNameMap[outputName]))
                        basicNodeExporter.decode(outputJSON)
            
            # Rebuild Arnold AOV tab as it has changed.
            aoveditor.refreshArnoldAOVTab()

        # Displays the AOV unifiedRenderGlobalsWindow tab. This is needed as each renderer stores its AOVs in a unique location.
        def displayMenu(self):
            mel.eval('unifiedRenderGlobalsWindow')
            mel.eval('setCurrentTabInRenderGlobalsWindow(\"AOVs\")')
            mel.eval('fillSelectedTabForCurrentRenderer')
            
        # Given an aovNode (aiAOV, aiAOVFilter, or aiAOVDriver type node), returns the aovName.
        def getAOVName(self, aovNode):
            try:
                nodeType = cmds.nodeType(aovNode)
            except:
                return aovNode[len('aiAOV_'):]
            if nodeType == "aiAOV":
                return cmds.getAttr(aovNode + ".name")
            else:
                # The first item in the returned list of connections should be the attached aiAOV node.
                aiAOVNode = cmds.listConnections(aovNode)[0]
                nodeType = cmds.nodeType(aiAOVNode)
                if nodeType == "aiAOV":
                    return self.getAOVName(aiAOVNode)
                else:
                    raise ValueError('The attached item is not an aiAOV node as required.')

        # Creates a selector for the AOV Collection that selects all aovNodes (aiAOV, aiAOVDriver, aiAOVFilter nodes)
        def getCollectionSelector(self, selectorName):
            returnSelectorName = cmds.createNode(selector.SimpleSelector.kTypeName, name=selectorName, skipSelect=True)
            currentSelector = renderSetupUtils.nameToUserNode(returnSelectorName)
            currentSelector.setPattern("*")
            currentSelector.setFilterType(selector.Filters.kCustom)
            currentSelector.setCustomFilterValue("aiAOV aiAOVDriver aiAOVFilter")
            return returnSelectorName

        # Creates a selector for the AOV Child Collection for a particular AOV name. Retrieves the AOV node (aiAOV) from
        # the AOV name and then uses a custom selector to find aiAOVFilter and aiAOVDriver nodes from the aiAOV node.
        def getChildCollectionSelector(self, selectorName, aovName):
            returnSelectorName = cmds.createNode(ArnoldAOVChildSelector.kTypeName, name=selectorName, skipSelect=True)
            currentSelector = renderSetupUtils.nameToUserNode(returnSelectorName)
            aovNodeName = "aiAOV_" + aovName
            currentSelector.setAOVNodeName(aovNodeName)
            return returnSelectorName

        # This function returns the child selector AOV node name from the provided dictionary
        def getChildCollectionSelectorAOVNodeFromDict(self, d):
            return d["selector"]["arnoldAOVChildSelector"]["arnoldAOVNodeName"]

    renderSetup.registerNode(ArnoldAOVChildSelector)
    arnoldAOVCallbacks = ArnoldAOVCallbacks()
except ImportError:
    arnoldAOVCallbacks = None

def aiHyperShadePanelBuildCreateMenuCallback() :
    if cmds.pluginInfo('mtoa', query=True, loaded=True) :
        aiHyperShadeCreateMenu_BuildMenu()
        cmds.menuItem(divider=True)

def aiHyperShadePanelBuildCreateSubMenuCallback() :  
    return "rendernode/arnold"

def aiRenderNodeClassificationCallback() :
    return "rendernode/arnold"

def aiCreateRenderNodePluginChangeCallback(classification) :
    return classification.startswith("rendernode/arnold")

def aiCreateRenderNodeSelectNodeCategoriesCallback(nodeTypesFlag, renderNodeTreeLister) :
    if (nodeTypesFlag == "allWithArnoldUp") :
        cmds.treeLister(renderNodeTreeLister, edit=True, selectPath="arnold")

def aiBuildRenderNodeTreeListerContentCallback(renderNodeTreeLister, postCommand, filterString) :
    filterClassArray = filterString
    createArnoldNodesTreeLister_Content(renderNodeTreeLister, postCommand, filterClassArray)

def aiProvideClassificationStringsForFilteredTreeListerCallback(classification) :
    return "rendernode/arnold/shader/surface"

def aiNodeCanBeUsedAsMaterialCallback(nodeId, nodeOwner ) :
    if nodeOwner == "Arnold":
        return 1
    else:
        return 0

def castSelf(selfid):
    # Can't pass self as an object.
    # It's cast to id(self) by the caller
    # and we convert it back to a python object here
    if isinstance(selfid,str):
        return ctypes.cast( int(selfid), ctypes.py_object ).value
    else:
        return selfid
      
def aiExportFrame( self, frame, objFilename ):
    # Export a single mental ray archive frame.
    cmds.currentTime( frame )

    cmds.arnoldExportAss(f=objFilename+".ass.gz", s=True, c=True, bb=True, mask=56)
    #cmds.Mayatomr( 	mi=True, exportFilter=7020488, 
    #            active=True, binary=True, compression=9, 
    #            fragmentExport=True, fragmentChildDag =True, passContributionMaps =True, 
    #            assembly=True, assemblyRootName="obj", exportPathNames="n", 
    #            file=objFilename + ".mi" )
    self.log( "assExport " + objFilename + ".ass.gz")

def aiExportAppendFile( self, assFilename, material, obj, lod ):
    lodList = self.tweakLodAppend( self.curFiles, lod  )
    for l in lodList:
        self.addArchiveFile( "ass", assFilename, material, "", l, 3 )
        
def aiExport( self, objs, filename, lod, materialNS ):
    filename = self.nestFilenameInDirectory( filename, "ass" )
    
    lastProgress = self.progress
    self.splitProgress( len(objs) )
    
    self.log( "assExport " + filename + lod )
    
    # force units to centimeters when exporting mi.
    #prevUnits = cmds.currentUnit( query=True, linear=True, fullName=True )
    #cmds.currentUnit( linear="centimeter" )
    
    prevTime = cmds.currentTime( query=True )

    for obj in objs:
        objFilename = filename + "_" + obj.replace("|", "_").replace(":", "_") + lod
        cmds.select( obj, r=True )

        filenames = []
        # Choose to export single file or a sequence.
        frameToken = ""
        if self.startFrame != self.endFrame:
            frameToken =".${FRAME}"

            dummyFrameFile = open( objFilename + frameToken + ".ass.gz", "wt" )
            dummyFrameFile.write( "STARTFRAME=%4.4d\nENDFRAME=%4.4d\n" % (int( self.startFrame), int(self.endFrame) ) )
            dummyFrameFile.close()

            for curFrame in range( int(self.startFrame), int(self.endFrame)+ 1 ):
                aiExportFrame( self, curFrame, objFilename + ".%4.4d" % int(curFrame) )
        else:
            aiExportFrame( self, self.startFrame, objFilename )
        
        if self.curFiles != None:
            materials = self.getSGsFromObj( obj )
            if materials and len(materials)>0 :
                assFilename = objFilename + frameToken + ".ass.gz"
                aiExportAppendFile( self, assFilename, materialNS+materials[0], obj, lod )
        self.incProgress()
    
    #cmds.currentUnit( linear=prevUnits )
    cmds.currentTime( prevTime )
    
    self.progress = lastProgress

def aiPreventDeletionFromCleanUpSceneCommandCallback(shader, plug, connection) :
    if (plug == "defaultArnoldRenderOptions"):
        return True
    else:
        return False
               
def aiCreateRenderNodeCommandCallback(postCommand, type):
    if cmds.getClassification(type, sat="rendernode/arnold"):
        return "python(\"import mtoa.core as core ; core.createArnoldNode(\\\"" + type + "\\\")\")"

def aiRenderSettingsBuiltCallback(currentRenderer):
    pm.renderer('arnold', edit=True, addGlobalsTab=('Common',
                                                    utils.pyToMelProc(createArnoldRendererCommonGlobalsTab, useName=True),
                                                    utils.pyToMelProc(updateArnoldRendererCommonGlobalsTab, useName=True)))
    pm.renderer('arnold', edit=True, addGlobalsTab=('Arnold Renderer',
                                                    utils.pyToMelProc(createArnoldRendererGlobalsTab, useName=True),
                                                    utils.pyToMelProc(updateArnoldRendererGlobalsTab, useName=True)))
    pm.renderer('arnold', edit=True, addGlobalsTab=('System', 
                                                    utils.pyToMelProc(createArnoldRendererSystemTab, useName=True), 
                                                    utils.pyToMelProc(updateArnoldRendererSystemTab, useName=True)))
    pm.renderer('arnold', edit=True, addGlobalsTab=('AOVs', 
                                                    utils.pyToMelProc(createArnoldAOVTab, useName=True), 
                                                    utils.pyToMelProc(updateArnoldAOVTab, useName=True)))
    pm.renderer('arnold', edit=True, addGlobalsTab=('Diagnostics', 
                                                    utils.pyToMelProc(createArnoldRendererDiagnosticsTab, useName=True), 
                                                    utils.pyToMelProc(updateArnoldRendererDiagnosticsTab, useName=True)))

def aiRendererAddOneTabToGlobalsWindowCreateProcCallback(createProc):
    createProcs = ['createArnoldRendererCommonGlobalsTab',
                   'createArnoldRendererGlobalsTab',
                   'createArnoldRendererSystemTab',
                   'createArnoldRendererDiagnosticsTab']

    if createProc in createProcs:
        pm.mel.eval(createProc)
        
def xgaiArchiveExport(selfid) :
    self = castSelf(selfid)
    aiExport( self, self.invokeArgs[0], self.invokeArgs[1], self.invokeArgs[2], self.invokeArgs[3] )
    
def xgaiArchiveExportInfo(selfid) :
    self = castSelf(selfid)
    self.archiveDirs.append( "ass" )
    self.archiveLODBeforeExt.append( ".${FRAME}.ass" )
    self.archiveLODBeforeExt.append( ".${FRAME}.ass.gz" )
    self.archiveLODBeforeExt.append( ".ass" )
    self.archiveLODBeforeExt.append( ".ass.gz" )
    
#def xgaiArchiveExportInit(selfid) :
#    print "##### xgaiArchiveExportInit ",selfid
 

try:
    import xgenm as xg
    xg.registerCallback( "ArchiveExport", "mtoa.cmds.rendererCallbacks.xgaiArchiveExport" )
    xg.registerCallback( "ArchiveExportInfo", "mtoa.cmds.rendererCallbacks.xgaiArchiveExportInfo" )
    #xg.registerCallback( "ArchiveExportInit", "mtoa.cmds.rendererCallbacks.xgaiArchiveExportInit" )
except:
    pass
 

# Add the callbacks
def registerCallbacks():
    if cmds.about(batch=True):
        return
        
    if arnoldAOVCallbacks is not None:
        rendererCallbacks.registerCallbacks("arnold", rendererCallbacks.CALLBACKS_TYPE_AOVS, arnoldAOVCallbacks)
        
    if arnoldRenderSettingsCallbacks is not None:
        rendererCallbacks.registerCallbacks("arnold", rendererCallbacks.CALLBACKS_TYPE_RENDER_SETTINGS, arnoldRenderSettingsCallbacks)

    cmds.callbacks(addCallback=aiHyperShadePanelBuildCreateMenuCallback,
                   hook="hyperShadePanelBuildCreateMenu",
                   owner="arnold")

    cmds.callbacks(addCallback=aiHyperShadePanelBuildCreateSubMenuCallback,
                   hook="hyperShadePanelBuildCreateSubMenu",
                   owner="arnold")

    cmds.callbacks(addCallback=aiCreateRenderNodeSelectNodeCategoriesCallback,
                   hook="createRenderNodeSelectNodeCategories",
                   owner="arnold")
               

    # FIXME: Maya doc is wrong
    #cmds.callbacks(addCallback=aiRenderNodeClassificationCallback,
    #               hook="addToRenderNodeTreeLister",
    #              owner="arnold")
    # Should be this instead

    cmds.callbacks(addCallback=aiRenderNodeClassificationCallback,
                   hook="renderNodeClassification",
                   owner="arnold")

    cmds.callbacks(addCallback=aiBuildRenderNodeTreeListerContentCallback,
                   hook="buildRenderNodeTreeListerContent",
                   owner="arnold")

    cmds.callbacks(addCallback=aiCreateRenderNodePluginChangeCallback,
                   hook="createRenderNodePluginChange",
                   owner="arnold")

    cmds.callbacks(addCallback=templates.loadArnoldTemplate,
                   hook="AETemplateCustomContent",
                   owner="arnold")

    cmds.callbacks(addCallback=aiProvideClassificationStringsForFilteredTreeListerCallback,
                   hook="provideClassificationStringsForFilteredTreeLister",
                   owner="arnold")

    cmds.callbacks(addCallback=aiNodeCanBeUsedAsMaterialCallback,
                   hook="nodeCanBeUsedAsMaterial",
                   owner="arnold")

    cmds.callbacks(addCallback=aiPreventDeletionFromCleanUpSceneCommandCallback,
                   hook="preventMaterialDeletionFromCleanUpSceneCommand",
                   owner="arnold")
               
    cmds.callbacks(addCallback=aiCreateRenderNodeCommandCallback,
                   hook="createRenderNodeCommand",
                   owner="arnold")   

    cmds.callbacks(addCallback=aiRenderSettingsBuiltCallback,
                   hook="renderSettingsBuilt",
                   owner="arnold")

    # This callback is new for Maya 2018.
    cmds.callbacks(addCallback=aiRendererAddOneTabToGlobalsWindowCreateProcCallback,
                   hook="rendererAddOneTabToGlobalsWindowCreateProc",
                   owner="arnold")

def clearCallbacks():
    if cmds.about(batch=True):
        return
    try:
        cmds.callbacks(clearAllCallbacks=True, owner="arnold")
    except:
        pass

    if not arnoldAOVCallbacks is None:
        rendererCallbacks.unregisterCallbacks("arnold", rendererCallbacks.CALLBACKS_TYPE_AOVS)
        renderSetup.unregisterNode(ArnoldAOVChildSelector)
