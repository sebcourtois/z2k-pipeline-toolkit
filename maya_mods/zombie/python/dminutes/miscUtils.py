import maya.cmds as mc
import pymel.core as pm
import os
import re
import subprocess
import datetime


def getAllTransfomMeshes(inParent = "*", inType = "mesh", recursive = False):
    """
    list all the transforms meshes , under de given 'inParent', 
    by default '*' means that any unreferenced transform mesh in the scene will be listed
        - inParent (string) : long name of the parent 
        - return (list) : allTransMesh
    """ 
    oParent = mc.ls(inParent, l =True)
    if not oParent:
        raise ValueError("#### error 'getAllTransfomMeshes': No '"+str(inParent)+"' found")
    elif len(oParent)>1 and recursive:
        oParent = oParent
    elif inParent != "*":
        oParent = oParent[0]
    else:
        oParent = "*"
        
    allGeoShapeList = mc.ls(mc.listRelatives(oParent, allDescendents = True, fullPath = True, type = inType), noIntermediate = True, l=True)

    geoShapeList =[]
    instancedGeoShapeList =[]

    for each in allGeoShapeList:
        if len(mc.listRelatives(each,allParents =True))>1:
            instancedGeoShapeList.append(each)
        else:
            geoShapeList.append(each)

    transMeshL = mc.listRelatives (geoShapeList, parent = True, fullPath = True, type = "transform")
    InstanciedtransMeshL = mc.listRelatives (instancedGeoShapeList, allParents = True, fullPath = True, type = "transform")


    if transMeshL is None: transMeshL = []
    if InstanciedtransMeshL is None: InstanciedtransMeshL = []

    return transMeshL, InstanciedtransMeshL


def pathJoin(*args):
    return normPath(os.path.join(*args))

def normPath(p):
    return os.path.normpath(p).replace("\\",'/')



def createUserWorkspace():
    try:
        davosUser = os.environ["DAVOS_USER"]
    except:
        raise ValueError("#### Error: DAVOS_USER environement variable is not defined, please log to davos")

    if davosUser not in mc.workspace(listWorkspaces = True):

        workspaceDir = os.path.split(normPath(mc.workspace( 'default',q=True, dir=True )))[0]
        projectPath = (normPath(os.path.join(workspaceDir, davosUser)))
        if not os.path.isdir(projectPath):
            print "#### Info: create project: "+projectPath
            mc.workspace( davosUser, newWorkspace=True)

            os.mkdir(projectPath)
            os.makedirs(normPath(os.path.join(projectPath,"cache","nCache","fluid")))
            os.makedirs(normPath(os.path.join(projectPath,"data")))
            os.makedirs(normPath(os.path.join(projectPath,"images")))
            os.makedirs(normPath(os.path.join(projectPath,"sourceimages","3dPaintTextures")))
            os.makedirs(normPath(os.path.join(projectPath,"scripts")))
            os.makedirs(normPath(os.path.join(projectPath,"movies")))
            os.makedirs(normPath(os.path.join(projectPath,"scenes")))
            os.makedirs(normPath(os.path.join(projectPath,"scenes","edits")))
            os.makedirs(normPath(os.path.join(projectPath,"autosave")))
            os.makedirs(normPath(os.path.join(projectPath,"sound")))
            os.makedirs(normPath(os.path.join(projectPath,"renderData")))
            os.makedirs(normPath(os.path.join(projectPath,"clips")))
            os.makedirs(normPath(os.path.join(projectPath,"assets")))
            os.makedirs(normPath(os.path.join(projectPath,"cache","bifrost")))
            os.makedirs(normPath(os.path.join(projectPath,"renderData","fur","furShadowMap")))
            os.makedirs(normPath(os.path.join(projectPath,"renderData","shaders")))
            os.makedirs(normPath(os.path.join(projectPath,"renderData","fur","furFiles")))
            os.makedirs(normPath(os.path.join(projectPath,"renderData","fur","furEqualMap")))
            os.makedirs(normPath(os.path.join(projectPath,"renderData","fur","furImages")))
            os.makedirs(normPath(os.path.join(projectPath,"renderData","iprImages")))
            os.makedirs(normPath(os.path.join(projectPath,"cache","particles")))
            os.makedirs(normPath(os.path.join(projectPath,"renderData","depth")))
            os.makedirs(normPath(os.path.join(projectPath,"renderData","fur","furAttrMap")))    
            pm.mel.setProject(projectPath)
    
    print "#### Info: set project: "+ davosUser
    pm.workspace( davosUser, openWorkspace = True )

        
def deleteUnknownNodes(GUI = True):
    resultB = True
    logL = []
    
    mentalRayNodeList = [u'mentalrayGlobals',u'mentalrayItemsList',u'miDefaultFramebuffer',u'miDefaultOptions',u'Draft',u'DraftMotionBlur',u'DraftRapidMotion',u'Preview',
                            u'PreviewCaustics',u'PreviewFinalGather',u'PreviewGlobalIllum',u'PreviewImrRayTracyOff',u'PreviewImrRayTracyOn',u'PreviewMotionblur',
                            u'PreviewRapidMotion',u'Production',u'ProductionFineTrace',u'ProductionMotionblur',u'ProductionRapidFur',u'ProductionRapidHair',
                            u'ProductionRapidMotion',u'miContourPreset']
    turtleNodeList = [u'TurtleDefaultBakeLayer',u'TurtleBakeLayerManager',u'TurtleRenderOptions',u'TurtleUIOptions']

    deLightNodeList = [u'delightRenderGlobals']

    mentalRayNodeList = mc.ls(mentalRayNodeList)
    turtleNodeList= mc.ls(turtleNodeList)
    deLightNodeList= mc.ls(deLightNodeList)
    mentalRayDeletedNodeList = []
    turtleDeletedNodeList = []
    delightDeletedNodeList = []

    for each in mentalRayNodeList:
        try:
            mc.lockNode(each,lock = False)
            mc.delete(each)
            mentalRayDeletedNodeList.append(each)
        except:
            logMessage = "#### {:>7}: 'deleteUnknownNodes' {} Mental Ray node could not be deleted".format("Warning", each)
            logL.append(logMessage)
            if GUI == True: print logMessage

    for each in turtleNodeList:
        try:
            mc.lockNode(each,lock = False)
            mc.delete(each)
            turtleDeletedNodeList.append(each)
        except:
            logMessage = "#### {:>7}: 'deleteUnknownNodes' {} Turtle node could not be deleted".format("Warning", each)
            logL.append(logMessage)
            if GUI == True: print logMessage

    for each in deLightNodeList:
        try:
            mc.lockNode(each,lock = False)
            mc.delete(each)
            delightDeletedNodeList.append(each)
        except:
            logMessage = "#### {:>7}: 'deleteUnknownNodes' {} 3dlight node could not be deleted".format("Warning", each)
            logL.append(logMessage)
            if GUI == True: print logMessage

    unknownNodes = mc.ls(type = "unknown")
    if unknownNodes:
        logMessage = "#### {:>7}: 'deleteUnknownNodes'  {} unknown node has been found in the scene: {}".format("Warning", len(unknownNodes), unknownNodes)
        logL.append(logMessage)
        if GUI == True: print logMessage

    if mentalRayDeletedNodeList:
        logMessage = "#### {:>7}: 'deleteUnknownNodes'  {} Mental Ray node(s) deteled: '{}'".format("Info", len(mentalRayDeletedNodeList), mentalRayDeletedNodeList)
        logL.append(logMessage)
        if GUI == True: print logMessage

    if delightDeletedNodeList:
        logMessage = "#### {:>7}: 'deleteUnknownNodes'  {} 3delight node(s) deteled: '{}'".format("Info", len(delightDeletedNodeList), delightDeletedNodeList)
        logL.append(logMessage)
        if GUI == True: print logMessage

    if turtleDeletedNodeList:
        logMessage = "#### {:>7}: 'deleteUnknownNodes'  {} Turtle node(s) deteled: '{}".format("Info", len(turtleDeletedNodeList), turtleDeletedNodeList)
        logL.append(logMessage)
        if GUI == True: print logMessage

    if not turtleDeletedNodeList and not mentalRayDeletedNodeList:
        logMessage =  "#### {:>7}: 'deleteUnknownNodes'  no Turtle or Mental Ray node deteled".format("Info")
        logL.append(logMessage)
        if GUI == True: print logMessage

    mc.flushUndo()
    mc.refresh()
    try:
        mc.unloadPlugin("Turtle",force = True)
        mc.unknownPlugin( "Turtle", r=True )
    except:
        pass
        
    def unloadMr():
        import maya.cmds as mc
        pm.mel.eval("global proc mrRemoveItemsFromCreateLightMenu(){}")
        try:
            mc.unloadPlugin('Mayatomr',force = True)
            #print "mr off loaded"
        except:
            #print "failed to off load mr"
            pass
    
    try:
        mc.evalDeferred(unloadMr)
        mc.unknownPlugin( "Mayatomr", r=True )
    except:
        pass

    try:
        mc.unloadPlugin("3delight_for_maya2016",force = True)
        mc.unknownPlugin( "3delight_for_maya2016", r=True )
    except:
        pass
        
    return resultB, logL



        


def setAttrC(*args, **kwargs):
    try:
        mc.setAttr(*args, **kwargs)
        return True
    except:
        return False




def removeAllNamespace ( NSexclusionL = [""], limit = 100, verbose = False, emptyOnly=False, *args,**kwargs):
        """ Description: Delete all NameSpace appart the ones in the NSexclusionL
            Return : nothing
            Dependencies : cmds - 
        """
        mc.refresh()
        tab= "    "
        #print "removeAllNamespace()"
        toReturnB = True
        delNameSpaceL = []
        # "UI","shared" NS are used by maya itself
        NS_exclusionBL=["UI","shared"]
        NS_exclusionBL.extend(NSexclusionL)
        # set the current nameSpace to the root nameSpace
        mc.namespace(setNamespace = ":")
        # get NS list
        nsL = mc.namespaceInfo(listOnlyNamespaces=True)# list content of a namespace  
        

        for loop in range(len(nsL)+2):
            nsL = mc.namespaceInfo(listOnlyNamespaces=True)
            for ns in nsL:
                if ns not in NS_exclusionBL:
                    if emptyOnly == False:
                        if verbose: print tab+"ns:",ns
                        mc.namespace( removeNamespace =ns, mergeNamespaceWithRoot=True)
                        delNameSpaceL.append(ns)
                    else:
                        if not mc.namespaceInfo(ns,  listOnlyDependencyNodes= True):
                            if verbose: print tab+"ns:",ns
                            mc.namespace( removeNamespace =ns, mergeNamespaceWithRoot=True)
                            delNameSpaceL.append(ns)

        # recursive
        if emptyOnly==False:
            count = 0
            nsLFin = mc.namespaceInfo(listOnlyNamespaces=True)
            while len(nsLFin)>2:
                removeAllNamespace(NSexclusionL = NSexclusionL, emptyOnly = emptyOnly, verbose= verbose)
                count += 1
                if count > limit:
                    break
        mc.refresh()
        return [toReturnB, delNameSpaceL]


def getShape(objectList =  [], failIfNoShape = False):
        shapeList = []
        for eachObject in objectList:
            if not mc.objectType(eachObject,isAType = "shape"):
                eachObjectShapes = mc.ls(mc.listRelatives(eachObject, noIntermediate = True, shapes = True, fullPath = True),l=True)
                if not eachObjectShapes and failIfNoShape:
                    raise ValueError("'{}' has no shape".format(eachObject))
                if len(eachObjectShapes)>1: 
                    raise ValueError("'{}' has several shapes".format(eachObject))
                shapeList.append(eachObjectShapes[0])
            else:
                shapeList.append(mc.ls(eachObject,l=1))
        return shapeList if shapeList != [] else  None


def deleteAllColorSet(inParent = "*",GUI = True):
    resultB = True
    logL = []
    sTransList, sSnstanceList = getAllTransfomMeshes(inParent = inParent)
    sMeshList = mc.ls(sTransList, type='mesh')
    nbOfDeleteDone=0
    for each in sTransList:
        if mc.polyColorSet(each, query=True, allColorSets=True):       
            mc.polyColorSet(each, delete=True)
            nbOfDeleteDone +=1
    logMessage = "#### {:>7}: 'deleteAllColorSet' color sets have been deleted on  {} objects".format("Info",nbOfDeleteDone )
    logL.append(logMessage)
    if GUI == True: print logMessage
    return resultB, logL


def h264ToProres(inSeqList = ['sq0230', 'sq0150'], shotStep = '01_previz'):
    """
    There are 4 profiles that exist within Prores: Proxy, LT, SQ and HQ (and then optionally 4444). In ffmpeg these profiles are assigned numbers (0 is Proxy and 3 is HQ)
    """
    ffmpegCommand = os.path.normpath(os.path.join(os.environ["Z2K_LAUNCH_SCRIPT"].split("launchers")[0],"movSplitter","ffmpeg","bin","ffmpeg.exe"))
    shotDir = os.path.normpath(os.path.join(os.environ["ZOMB_SHOT_LOC"],"zomb","shot"))
    montageDir = "//Zombiwalk/z2k/11_EXCHANGE_MONTAGE"
    sSeqShotDict = {}


    if shotStep == "01_previz" or shotStep == "02_layout":
        profile = 0
        shotExt = shotStep.split("_")[-1]
    else:
        raise ValueError("'{}' shotStep is not valid".format(shotStep))

    for eachSeq in os.listdir(shotDir):
        if re.match('^sq[0-9]{4}$', eachSeq) and (eachSeq in inSeqList or not inSeqList):
            for eachShot in os.listdir(os.path.normpath(os.path.join(shotDir,eachSeq))):
                if re.match('^sq[0-9]{4}_sh[0-9]{4}a$', eachShot):
                    #sSeqShotDict[eachSeq].append(eachShot)
                    sSeqShotDict.setdefault(eachSeq,[]).append(eachShot)

    for each in inSeqList:
        if each not in sSeqShotDict.keys():
            raise ValueError("'{}' sequence could not be found".format(each))

    tempBatFile = os.path.normpath(os.path.join(os.environ["temp"],"conv2prores.bat"))
    print "#### {:>7}: writing temp batch file: '{}'".format("Info",tempBatFile )
    conv2prores_obj = open(tempBatFile, "w")

    for seqName, shotNameList in sSeqShotDict.items():
        oDate = datetime.datetime.today()
        sDate = str(oDate.year)+"-"+str(oDate.month)+"-"+str(oDate.day)
        outDir = os.path.normpath(os.path.join(montageDir, shotStep, seqName, sDate))

        conv2prores_obj.write("\n")

        if  not os.path.isdir(outDir):
            #print "#### {:>7}: Create directory: '{}'".format("Info",outDir )
            os.makedirs(outDir)

        for shotName in shotNameList:
            inDir = os.path.normpath(os.path.join(shotDir, seqName, shotName, shotStep,"_version"))
            if  not os.path.isdir(inDir):
                raise ValueError("Directory could not be found: '{}'".format(inDir))
            videoList = []
            for each in os.listdir(inDir):
                if re.match('^sq[0-9]{4}_sh[0-9]{4}[a-z]{1}_[a-zA-Z0-9\-]{1,24}.mov$', each):
                    videoList.append(each)
            if len (videoList) < 2:
                print "#### {:>7}: no video found in directory: '{}'".format("Warning",inDir )
                continue
            videoList.sort()
            inFile = os.path.normpath(os.path.join(inDir,videoList[-1]))
            outFile = os.path.normpath(os.path.join(outDir,videoList[-1]))
            finalCommand = "{0} -i {1} -c:v prores_ks -profile:v {2} {3}".format(ffmpegCommand,inFile,profile,outFile)
            conv2prores_obj.write(finalCommand+"\n")

    conv2prores_obj.write("\n")
    conv2prores_obj.write("pause\n")
    conv2prores_obj.close()

    #subprocess.call([tempBatFile])

def getShapeOrig(TransformS = ""):
    shapeOrigList=[]
    shapeL = mc.ls(mc.listRelatives(TransformS, allDescendents = True, fullPath = True, type = "mesh"), noIntermediate = False, l=False)
    for each in shapeL:
        if mc.getAttr(each+".intermediateObject") == 1 and not mc.listConnections( each+".inMesh",source=True) and "ShapeOrig" in each:
            shapeOrigList.append(each)
    return shapeOrigList


def cleanLayout():
    panelL = mc.getPanel( visiblePanels=True )
    panelToCloseL=["hyperShadePanel","polyTexturePlacementPanel"]
    for each in panelL:
        for eachPanel in panelToCloseL:
            if eachPanel in each:
                mc.deleteUI(each, panel = True)
    myPanelL = mc.getPanel(type="modelPanel")
    for each in myPanelL:
        try:
            mc.modelEditor(each, e=1, displayAppearance="wireframe")
        except:
            pass




def listColHD(public = False):

    def subScan( path = ""):
        print ""
        print "########"
        print "######################  {}  ######################".format( path)
        print "########"
        chrDirS = pathJoin(assetDirS,"chr")
        if not os.path.isdir(chrDirS):
            return
        allChrL = os.listdir(chrDirS)
        allChrL.sort()
        myChrL = []
        
        for each in allChrL:
            texturePathS = pathJoin(chrDirS,each,"texture")
            if os.path.isdir(texturePathS):
                print "#### {:>7}: Scanning: {}".format("Info", texturePathS)
                allFileL = os.listdir(texturePathS)
                for each in allFileL:
                    if each.split(".")[-1].lower()=="jpg" and each.split(".")[0].split("_")[-1].lower() == "colhd":
                        print "#### {:>7}: ----------> {}".format("Info", each)
                        
    if public == True:
        assetDirS = os.environ["ZOMB_ASSET_PATH"]
        subScan(path = assetDirS)
    else:
        privDirS = pathJoin(os.environ["ZOMB_PRIVATE_LOC"],"private")
        allFileL = os.listdir(privDirS)
        for each in allFileL:
            assetDirS = pathJoin(privDirS,each,"zomb","asset")
            if os.path.isdir(assetDirS):
                subScan(path = assetDirS)
        




class LogBuilder():
    
    def __init__(self,gui=True, funcName ="", logL = None, resultB = True, logFile = ""):
        self.gui = gui
        if not logL:
            logL = []
        self.funcName = funcName
        self.logL = logL
        self.resultB = resultB
        self.logFile = logFile
        if self.funcName:
            self.funcName = "'"+self.funcName+"' "

        if self.logFile:
            print "toto"

    def printL(self,style = "i",msg = "", guiPopUp = False ):
        self.style = style
        self.msg = msg

        if not self.gui:
            self.guiPopUp = False
        else:
            self.guiPopUp = guiPopUp

      
        if self.style == "t":
            self.formMsg = '\n----------- '+self.msg    
        elif self.style == "e":
            self.formMsg = "#### {:>7}: {}{}".format("Error",self.funcName,self.msg)
            if self.guiPopUp: mc.confirmDialog( title='Error: '+self.funcName, message=self.msg, button=['Ok'], defaultButton='Ok' )
            self.resultB = False
        elif self.style == "w":
            self.formMsg = "#### {:>7}: {}{}".format("Warning",self.funcName,self.msg)
            if self.guiPopUp: mc.confirmDialog( title='Warning: '+self.funcName, message=self.msg, button=['Ok'], defaultButton='Ok' )
        elif self.style == "i":
            self.formMsg = "#### {:>7}: {}{}".format("Info",self.funcName,self.msg)
            if self.guiPopUp: mc.confirmDialog( title='Info: '+self.funcName, message=self.msg, button=['Ok'], defaultButton='Ok' )
        else:
            self.formMsg = "{}{}".format(self.funcName,self.msg)


        print self.formMsg



        self.logL.append(self.formMsg)
    


        



