import maya.cmds as mc
import maya.OpenMaya as om
import re
import os
import string 
import subprocess
import miscUtils


def connectedToSeveralSG(myNode = ""):
    """
    return "True" if the node is connected to several shading group
    """
    upStreamShadingGroupList = []
    upStreamNodeList = mc.listHistory (myNode,future = True)
    for item in upStreamNodeList:
        if mc.nodeType(item) == "shadingEngine":
            upStreamShadingGroupList.append(item)
    if len(upStreamShadingGroupList) >1:
        print "####    error: '"+myNode+"' is connected to several shading groups  -->   "+str(upStreamShadingGroupList)
        return True
    else:
        return False



def conformShaderName(shadEngineList = "selection", selectWrongShadEngine = True ):
    """
    shadEngineList : selection, all
    conform the shading tree attached to the selected shading engine , or all the shading trees , depending on the shadEngineList value.
    The initial shading engines are skipped so the ones that do not follow the proper 
    naming convention:  'sgr_materialName' where is composed of 24 alphanumeric characters maximum"
    the shading tree is splited in 2 parts:
        - surfaceShader SG input: this shading tree describes the shader for preview, these nodes will recieve a 'pre_' prefix
        - aiSurfaceShader SG input: his shader tree is dedicated o arnold renders and wil recieve a 'mat_' prefix
    all the nodes will be renamed : 'mat_materialName_nodeType' or 'pre_materialName_nodeType'
    'materialName' part comes from the shading engine name and 'nodeType' is the node's type
    """
    print ""
    print "#### {:>7}: running conformShaderName(shadEngineList = {}, selectWrongShadEngine = {} )".format("info",shadEngineList, selectWrongShadEngine)

    correctShadEngine =[]
    wrongShadEngine = []

    permitted_preview_shader_type = ["lambert","surfaceShader"]
    permitted_render_shader_type = ["aiStandard", "dmnToon"]

    if shadEngineList == "all":
        shadEngineList = mc.ls(":*",type = "shadingEngine")
        shadEngineList.remove("initialParticleSE")
        shadEngineList.remove("initialShadingGroup")
        if not shadEngineList :
            print "#### {:>7}: no shading engine to conform".format("info")
            return

    elif shadEngineList == "selection":
        shadEngineList = mc.ls(selection = True,type = "shadingEngine")
        if "initialParticleSE" in shadEngineList: shadEngineList.remove("initialParticleSE")
        if "initialParticleSE" in shadEngineList: shadEngineList.remove("initialParticleSE")
        if not shadEngineList : 
            print "#### {:>7}: no shading engine selected".format("info")
            return

    for each in shadEngineList:
        #check shading group name convention
        if not re.match('^sgr_[a-zA-Z0-9]{1,24}$', each):
            wrongShadEngine.append((each,"does not match naming convention 'sgr_materialName' where is composed of 24 alphanumeric characters maximum"))
        else:
            #check that 2 different2 shading nodes are plugged into the surfaceShader and aiSurfaceShader input of the SG node
            correctShadEngine.append(each)
            materialName = each.split("sgr_")[-1]
            preview_shader =  mc.listConnections(each+'.surfaceShader',connections = True)
            render_shader =  mc.listConnections(each+'.aiSurfaceShader',connections = True)
            if not preview_shader or not render_shader:
                wrongShadEngine.append((each,"the preview_shader or render_shader is missing: "))
                continue
            else:
                preview_shader = preview_shader[-1]
                render_shader = render_shader[-1]
                 
            if preview_shader == render_shader:
                wrongShadEngine.append((each,"surfaceShader and aiSurfaceShader connected to the same node: "+preview_shader))
                continue
            #check that the type of the preview and render nodes is permitted
            preview_shader_type = mc.nodeType(preview_shader)
            render_shader_type = mc.nodeType(render_shader)
            if preview_shader_type not in permitted_preview_shader_type:
                wrongShadEngine.append((each,preview_shader+" unauthorized preview shader node type: "+preview_shader_type+" should be one of the following: "+str(permitted_preview_shader_type)))
                continue

            for item in mc.listHistory (preview_shader):
                if "dagNode" in mc.nodeType(item, inherited=True):
                    continue
                if connectedToSeveralSG (item):
                    return
                preview_shader_type = mc.nodeType(item)
                if not re.match('pre_'+materialName+'_'+preview_shader_type+'[0-9]{0,3}$',preview_shader):
                    preview_shader = mc.rename(item,'pre_'+materialName+'_'+preview_shader_type)
                
            for item in mc.listHistory (render_shader):
                if "dagNode" in mc.nodeType(item, inherited=True):
                    continue
                if connectedToSeveralSG (item):
                    return
                render_shader_type = mc.nodeType(item)
                if not re.match('mat_'+materialName+'_'+render_shader_type+'[0-9]{0,3}$',render_shader):
                    render_shader = mc.rename(item,'mat_'+materialName+'_'+render_shader_type)
        print "#### {:>7}: {:^28} tree has been conformed properly".format("info", each)

    if  wrongShadEngine != []:
        if selectWrongShadEngine == True: mc.select(clear = True)
        for each in wrongShadEngine:
            print "#### {:>7}: {:^28} {}".format("warning", each[0], each[1])
            if selectWrongShadEngine == True: mc.select(each[0], ne = True, add = True)
        print "####    info: problematics shading engines have been selected"
    return wrongShadEngine if wrongShadEngine != [] else  None


def referenceShadingCamera(cameraName = "cam_shading_default", fileType=".ma"):
    """
    reference a camera for shading purpose. This tools is not to use for shot bulding.
        cameraName (string): the camera name you want to reference
        fileType(string): specify if the '.ma' or '.mb' file is to reference
    """
    zombie_asset_dir =  os.environ["ZOMB_ASSET_PATH"]
    shading_cam_filename =  os.path.join("$ZOMB_ASSET_PATH", "cam",cameraName,cameraName+fileType)
    
    
    if cameraName in  str(mc.file(query=True, list=True, reference = True)):
        print "#### info 'referenceShadingCamera': a camera '"+cameraName+"' is already referenced in this scene, operation canceled"
    else:
        mc.file(shading_cam_filename, reference = True, namespace = cameraName+"00", ignoreVersion  = True,  groupLocator = True, mergeNamespacesOnClash = False)
              



def conformTexturePath(inVerbose = True, inConform = False, inCopy =False, inAuthorizedFormat=["jpg","tga"]):
    """
    checks all the unreferenced file nodes. 
    in : inVerbose (boolean) : log info if True
         inConform (boolean) : modify path of file nodes when requiered.
         inCopy (boolean) : allow a copy of the texture to be made from the initial path to the final path before modifiying the path value 
         inAuthorizedFormat (list): a list of texture extention that are considered as correct
    out: outNoMapFileNodeList (list) : list of all the file nodes that need to be modified in order to get conform. 
    """ 
    print ""
    print "#### info: runing shading.conformMapPath( inVerbose = {}, inConform = {}, inCopy = {}, inAuthorizedFormat = {} )".format(inVerbose , inConform , inCopy, inAuthorizedFormat)
    if mc.ls("|asset"):        
        mainFilePath = mc.file(q=True, list = True)[0]
        mainFilePathElem = mainFilePath.split("/")
        if  mainFilePathElem[-4] == "asset":
            finalMapdir = miscUtils.pathJoin("$PRIV_ZOMB_TEXTURE_PATH",mainFilePathElem[-3],mainFilePathElem[-2],"texture")
            #finalMapdir = miscUtils.pathJoin("$PRIV_ZOMB_TEXTURE_PATH","asset",mainFilePathElem[-3],mainFilePathElem[-2],"texture")
            #finalMapdirExpand = miscUtils.pathJoin(os.environ["PRIV_ZOMB_TEXTURE_PATH"],"asset",mainFilePathElem[-3],mainFilePathElem[-2],"texture")
            finalMapdirExpand = os.path.expandvars(finalMapdir)
        else:
            raise ValueError("#### Error: you are not working in an 'asset' structure directory")
    else :
        raise ValueError("#### Error: no '|asset' could be found in this scene")
        

    fileNodeList = mc.ls("*",type ="file")
    outWrongFileNodeList = []
    
    for eachFileNode in fileNodeList:
        wrongFileNode = False
        mapFilePath = mc.getAttr(eachFileNode+".fileTextureName")
        mapFilePathExpand = os.path.expandvars(mapFilePath)
        mapPath = os.path.split(mapFilePath)[0]
        fileName = os.path.split(mapFilePath)[1]       
        finalMapFilePathExpanded = miscUtils.pathJoin(finalMapdirExpand,fileName)
        finalMapFilePath = miscUtils.pathJoin(finalMapdir,fileName)


        #tests the texture extention
        mapExtention = (os.path.split(mapFilePath))[-1].split(".")[-1]
        if mapExtention  not in inAuthorizedFormat:
            if inVerbose == True: print "#### warning: '{0:^24}' the file extention :'.{1}'  is not conform, only {2} are allowed".format(eachFileNode,mapExtention,inAuthorizedFormat)
            outWrongFileNodeList.append(eachFileNode)
            continue
        #tests if used path match the finalMapDir and if the texture exists
        elif mapPath == finalMapdir: 
            if os.path.isfile(mapFilePathExpand) == True:
                if inVerbose == True: print "#### info: '{0:^24}' file and path corect :'{1}'".format(eachFileNode,mapFilePath)  
                continue
            else:
                if inVerbose == True: print "#### warning: '{0:^24}' the file :'{1}' doesn't exist".format(eachFileNode,mapFilePath)       
                outWrongFileNodeList.append(eachFileNode)
                continue
        #tests if the texture exists in the finalMapDir, and modify the path if inConform = True
        elif os.path.isfile(finalMapFilePathExpanded) is True:
            if inConform is True: 
                mc.setAttr(eachFileNode+".fileTextureName", finalMapFilePath, type = "string")
                if inVerbose == True: print "#### Info: '{0:^24}' the file path changed to {1}".format(eachFileNode,finalMapFilePath)
                continue
            else:
                if inVerbose == True: print "#### warning: '{0:^24}' wrong path file :'{1}'".format(eachFileNode,mapFilePath)       
                outWrongFileNodeList.append(eachFileNode)
                continue
        #tests if the texture file exists at the initial file path and copy it if required to the finalMapDir
        elif os.path.isfile(mapFilePath) is True:
            if inCopy is True:
                print "#### Info: copy file: "+mapFilePath+" --> "+finalMapFilePathExpanded
                shutil.copyfile(mapFilePath, finalMapFilePathExpanded)
                if os.path.isfile(finalMapFilePathExpanded) == False: 
                    print "#### Error: "+eachFileNode+" file could not be found: "+finalMapFilePathExpanded
                    outWrongFileNodeList.append(eachFileNode)
                    continue
                mc.setAttr(eachFileNode+".fileTextureName", finalMapFilePath, type = "string")
                if inVerbose == True: print "#### Info: '{0:^24}' the file path changed to {1}".format(eachFileNode,finalMapFilePath)                        
                continue
        else:
            if inVerbose == True: print "#### warning: '{0:^24}' the file must be moved to {1}".format(eachFileNode,finalMapFilePath)                         
            outWrongFileNodeList.append(eachFileNode)
            continue

    if outWrongFileNodeList: 
        print "#### warning: {} file node(s) have wrong file path settings".format(len(outWrongFileNodeList))
        if inVerbose == True: 
            mc.select(outWrongFileNodeList)
            print "#### info: the wrong file nodes have been selected"
    return outWrongFileNodeList if outWrongFileNodeList != [] else  None



def createLowResJpg(nodeList, lod = "4", jpgQuality = "70"):
    """
    This function creates a low resolution jpg file given texture file.
    it also switch off the mipmap fitering, and set the given file node so it point toward this new low res jgp
     - nodeList : (list) a list of texture file node
     - lod : (string) 0..19 of pyramid map, largest is 0
     - jpgQuality : (string) 1...100 highest is 100
    """
    mentalRayBin = os.path.normpath(os.environ['MAYA_LOCATION'].replace("Maya","mentalrayForMaya")).replace("\\", "/")
    imfCopyCommand = mentalRayBin+"/bin/imf_copy"
    tempDir = os.getenv ("TMPDIR")
    tempDir = tempDir.rstrip("/")
    
    tempImageFormat = "tif"
    
    if not os.path.isdir(tempDir):
        print "#### error: "+tempDir+" is not a valid directory"
        return


    fileNodeList = []
    for each in nodeList:
        if mc.nodeType(each) == "file":
            fileNodeList.append(each)
    if not fileNodeList:
        print "#### error: No node to process. Please specify at least one Node"
    if not os.path.isdir(mentalRayBin):
        print "#### error: could not find the following directory: "+mentalRayBin
        return

    
    for eachFileNode in fileNodeList:
        textureFileName = mc.getAttr(eachFileNode+".fileTextureName")
        textureFileName_exp  = pathExpand (textureFileName)
        tempFile = textureFileName_exp.replace(os.path.dirname(textureFileName_exp),tempDir)+"."+tempImageFormat
        lowResFileName  = textureFileName.split(".")[0]+"_lowRes"+textureFileName.replace(textureFileName.split(".")[0],"")+".jpg"
        lowResFileName_exp = pathExpand (lowResFileName)
        print "---------"
        
        if os.path.isfile(textureFileName_exp):
            
            image = om.MImage()
            image.readFromFile(textureFileName_exp)
            util = om.MScriptUtil()
            widthUtil = om.MScriptUtil()
            heightUtil = om.MScriptUtil()
            widthPtr = widthUtil.asUintPtr()
            heightPtr = heightUtil.asUintPtr()
            image.getSize(widthPtr, heightPtr)
            width = util.getUint(widthPtr)
            height = util.getUint(heightPtr)
            image.resize( width/2**int(lod), height/2**int(lod) )
            image.writeToFile( tempFile, tempImageFormat)
            subprocess.call([imfCopyCommand, "-vq",jpgQuality, tempFile,lowResFileName_exp])
            os.remove(tempFile)
            

            statinfo = os.stat(textureFileName_exp)
            imageSize = string.ljust(str(statinfo.st_size/1024)+" Kb",10," ")
            textureWidth = string.ljust(str(width),5," ")
            textureHeight = string.ljust(str(height),5," ")
            
            statinfo_lowRes = os.stat(lowResFileName_exp)
            fastJpgImageSize = string.ljust(str(statinfo_lowRes.st_size/1024)+" Kb",10," ")
            textureWidthLowRes = string.ljust(str(width/2**int(lod)),5," ")
            textureHeightLowRes = string.ljust(str(height/2**int(lod)),5," ")

            print "#### info: resize (LOD "+lod+") and convert to jpg (quality = "+jpgQuality+ ") and adjust '"+eachFileNode+"' file node attributes"
            print "#### info: "+textureFileName+"             -->  width: "+textureWidth+"  height: "+textureHeight+"  size: "+imageSize
            print "#### info: "+lowResFileName+"  -->  width: "+textureWidthLowRes+"  height: "+textureHeightLowRes+"  size: "+fastJpgImageSize
            mc.setAttr(eachFileNode+".filterType", 0)
            mc.setAttr(eachFileNode+".preFilter", 0)
            mc.setAttr(eachFileNode+".fileTextureName",lowResFileName, type = "string")

        else:
            print "#### error: lowRes jpg creation is not possible, the following texture file do not exist: "+textureFileName_exp
            continue
            
            