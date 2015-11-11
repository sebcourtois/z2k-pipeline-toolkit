import maya.cmds as mc
import pymel.core as pm
import maya.OpenMaya as om
import re
import os
import string 
import subprocess
import miscUtils
import modeling


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
        #print "####    error: '"+myNode+"' is connected to several shading groups  -->   "+str(upStreamShadingGroupList)
        return True
    else:
        return False



def conformShaderName(shadEngineList = "selection", selectWrongShadEngine = True, verbose = True, gui = True ):
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
    if verbose == True: print ""
    if verbose == True: print "#### {:>7}: running conformShaderName(shadEngineList = {}, selectWrongShadEngine = {} )".format("info",shadEngineList, selectWrongShadEngine)

    correctShadEngine =[]
    wrongShadEngine = []

    permitted_preview_shader_type = ["lambert","surfaceShader"]
    permitted_render_shader_type = ["aiStandard", "dmnToon"]

    if shadEngineList == "all":
        shadEngineList = mc.ls(":*",type = "shadingEngine")
        shadEngineList.remove("initialParticleSE")
        shadEngineList.remove("initialShadingGroup")
        if not shadEngineList :
            print "#### {:>7}: no shading engine to conform".format("Warning")
            return

    elif shadEngineList == "selection":
        shadEngineList = mc.ls(selection = True,type = "shadingEngine")
        if "initialParticleSE" in shadEngineList: shadEngineList.remove("initialParticleSE")
        if "initialShadingGroup" in shadEngineList: shadEngineList.remove("initialShadingGroup")
        shadEngineListTemp = shadEngineList
        for each in shadEngineListTemp:
            if ":" in each: shadEngineList.remove(each) 
        if not shadEngineList : 
            print "#### {:>7}: no shading engine selected".format("Warning")
            return
    elif isinstance(shadEngineList, (basestring)):
            shadEngineList = [shadEngineList]

    if not isinstance(shadEngineList, (list,tuple,set)):
        print "#### {:>7}: shadEngineList must be a list. shadEngineList: {}".format("Error", shadEngineList)
        return
    if shadEngineList == []: 
        print "#### {:>7}: No shading engine to process, shadEngineList is empty".format("Error")
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
                materialParticule = str(materialName)
                if "dagNode" in mc.nodeType(item, inherited=True):
                    continue
                if connectedToSeveralSG (item):
                    materialParticule = "shared"
                preview_shader_type = mc.nodeType(item)
                if not re.match('pre_'+materialParticule+'_'+preview_shader_type+'[0-9]{0,3}$',preview_shader) and  not mc.lockNode(item, q=True)[-1] and not mc.ls(item, defaultNodes = True):
                    preview_shader = mc.rename(item,'pre_'+materialParticule+'_'+preview_shader_type)
                
            for item in mc.listHistory (render_shader):
                materialParticule = str(materialName)
                if "dagNode" in mc.nodeType(item, inherited=True):
                    continue
                if connectedToSeveralSG (item):
                    materialParticule = "shared"
                render_shader_type = mc.nodeType(item)
                if not re.match('mat_'+materialParticule+'_'+render_shader_type+'[0-9]{0,3}$',render_shader) and  not mc.lockNode(item, q=True)[-1] and not mc.ls(item, defaultNodes = True):
                    render_shader = mc.rename(item,'mat_'+materialParticule+'_'+render_shader_type)
            if verbose == True: print "#### {:>7}: {:^28} tree has been conformed properly".format("Info", each)

    if  wrongShadEngine != [] and selectWrongShadEngine == True:
        mc.select(clear = True)
        for each in wrongShadEngine:
            print "#### {:>7}: {:^28} {}".format("Error", each[0], each[1])
            if selectWrongShadEngine == True: 
                mc.select(each[0], ne = True, add = True)
        print "#### {:>7}: Problematics shading engines have been selected".format("Error")
        if gui == True:
            mc.confirmDialog( title = 'Shader Name Error', message = 'Some shaders are not conform, please read the log to get more information', button = ['Ok'], defaultButton = 'Ok' )
    return wrongShadEngine if wrongShadEngine != [] else  None


def referenceShadingCamera(cameraName = "cam_shading_default", fileType=".ma", remove = False):
    """
    reference a camera for shading purpose. This tools is not to use for shot bulding.
        cameraName (string): the camera name you want to reference
        fileType(string): specify if the '.ma' or '.mb' file is to reference
    """
    if mc.ls("|asset"):        
        mainFilePath = mc.file(q=True, list = True)[0]
        mainFilePathElem = mainFilePath.split("/")
        if  mainFilePathElem[-4] == "asset":
            privateMapdir = miscUtils.normPath(miscUtils.pathJoin("$PRIV_ZOMB_TEXTURE_PATH",mainFilePathElem[-3],mainFilePathElem[-2],"texture"))
            privateMapdirExpand = miscUtils.normPath(os.path.expandvars(os.path.expandvars(privateMapdir)))
            publicMapdir = miscUtils.normPath(miscUtils.pathJoin("$ZOMB_TEXTURE_PATH",mainFilePathElem[-3],mainFilePathElem[-2],"texture"))
            publicMapdirExpand = miscUtils.normPath(os.path.expandvars(os.path.expandvars(privateMapdir)))
        else:
            raise ValueError("#### Error: you are not working in an 'asset' structure directory")
    else :
        raise ValueError("#### Error: no '|asset' could be found in this scene")


    zombie_asset_dir =  os.environ["ZOMB_ASSET_PATH"]
    shading_cam_filename =  os.path.join("$ZOMB_ASSET_PATH", "cam",cameraName,cameraName+fileType)
    
    if remove == False:
        if cameraName in  str(mc.file(query=True, list=True, reference = True)):
            print "#### info 'referenceShadingCamera': a camera '"+cameraName+"' is already referenced in this scene, operation canceled"
        else:
            mc.currentTime(1)
            if mc.ls("|asset|*",type = "orientConstraint"):
                mc.delete(mc.ls("|asset|*",type = "orientConstraint"))
            #mc.makeIdentity ("|asset",apply= False, n=0, pn=1)
            pm.disconnectAttr("|asset.rotateX")
            pm.disconnectAttr("|asset.rotateY")
            pm.disconnectAttr("|asset.rotateZ")
            mc.setAttr ("|asset.rotateX", 0)
            mc.setAttr ("|asset.rotateY", 0)
            mc.setAttr ("|asset.rotateZ", 0)
            cameraNewNodes = mc.file(shading_cam_filename, reference = True, namespace = cameraName+"00", ignoreVersion  = True,  groupLocator = True, mergeNamespacesOnClash = False, returnNewNodes = True)
            for each in cameraNewNodes:
                if ":" in each:
                    cameraNameSpace = each.split(":")[0]
                    break
            #mc.orientConstraint( cameraNameSpace+':crv_trunAround','|asset',name = "asset2crvTrurnAround_orientConstraint")
            mc.connectAttr(cameraNameSpace+":crv_trunAround.rotate", '|asset.rotate', force =True)
        if not mc.listConnections('defaultArnoldRenderOptions.background',connections = False):
            #myAiRaySwitch = mc.shadingNode("aiRaySwitch", asShader=True)
            #mc.setAttr(myAiRaySwitch+".camera", 0.5,0.5,0.5, type = "double3")
            #mc.setAttr(myAiRaySwitch+".refraction", 0.5,0.5,0.5, type = "double3")
            myAiRaySwitch = cameraNameSpace+":env_aiRaySwitch"
            mc.connectAttr(myAiRaySwitch+".message", 'defaultArnoldRenderOptions.background', force =True)


    else:
        if "cam_shading_" in  str(mc.file(query=True, list=True, reference = True)):
            mc.currentTime(1)
            for each in  mc.file(query=True, list=True, reference = True):
                if "cam_shading_" in each:
                    mc.file(each, removeReference = True)
                    if mc.ls("|asset|*",type = "orientConstraint"):
                        mc.delete(mc.ls("|asset|*",type = "orientConstraint"))
                    pm.disconnectAttr("|asset.rotateX")
                    pm.disconnectAttr("|asset.rotateY")
                    pm.disconnectAttr("|asset.rotateZ")
                    mc.setAttr ("|asset.rotateX", 0)
                    mc.setAttr ("|asset.rotateY", 0)
                    mc.setAttr ("|asset.rotateZ", 0)
                    #mc.makeIdentity ("|asset",apply= False, n=0, pn=1)
                    print "#### info 'referenceShadingCamera': remove camera '"+each+""
        else:
            print "#### info 'referenceShadingCamera': no 'cam_shading_*' to remove"
        try:    
            mc.delete(mc.listConnections('defaultArnoldRenderOptions.background',connections = False))
        except:
            pass




def conformTexturePath(inVerbose = True, inConform = False, inCopy =False, inAuthorizedFormat=["jpg","tga"], returnMapPath = False):
    """
    checks all the unreferenced file nodes. 
    in : inVerbose (boolean) : log info if True
         inConform (boolean) : modify path of file nodes when requiered.
         inCopy (boolean) : allow a copy of the texture to be made from the initial path to the final path before modifiying the path value 
         inAuthorizedFormat (list): a list of texture extention that are considered as correct
    out: outNoMapFileNodeList (list) : list of all the file nodes that need to be modified in order to get conform. 
         outMapPathForPublishList (list)
    """ 
    if inVerbose == True: print ""
    if inVerbose == True: print "#### info: runing shading.conformTexturePath( inVerbose = {}, inConform = {}, inCopy = {}, inAuthorizedFormat = {} , returnMapPath = {})".format(inVerbose , inConform , inCopy, inAuthorizedFormat, returnMapPath)

    if mc.ls("|asset"):        
        mainFilePath = mc.file(q=True, list = True)[0]
        mainFilePathElem = mainFilePath.split("/")
        if  mainFilePathElem[-4] == "asset":
            privateMapdir = miscUtils.normPath(miscUtils.pathJoin("$PRIV_ZOMB_TEXTURE_PATH",mainFilePathElem[-3],mainFilePathElem[-2],"texture"))
            privateMapdirExpand = miscUtils.normPath(os.path.expandvars(os.path.expandvars(privateMapdir)))
            publicMapdir = miscUtils.normPath(miscUtils.pathJoin("$ZOMB_TEXTURE_PATH",mainFilePathElem[-3],mainFilePathElem[-2],"texture"))
            publicMapdirExpand = miscUtils.normPath(os.path.expandvars(os.path.expandvars(publicMapdir)))
        else:
            raise ValueError("#### Error: you are not working in an 'asset' structure directory")
    else :
        raise ValueError("#### Error: no '|asset' could be found in this scene")
        


    fileNodeList = mc.ls("*",type ="file")
    outWrongFileNodeList = []
    outMapPathForPublishList = []
    if inVerbose == True: print "#### info: Expanded working directory: '{}'".format(os.path.normpath(privateMapdirExpand))


    for eachFileNode in fileNodeList:
        wrongFileNode = False
        mapFilePath = miscUtils.normPath(mc.getAttr(eachFileNode+".fileTextureName"))
        mapFilePathExpand = miscUtils.normPath(os.path.expandvars(os.path.expandvars(mapFilePath)))
        mapPath = os.path.split(mapFilePath)[0]
        fileName = os.path.split(mapFilePath)[1]       
        privateMapFilePathExpanded = miscUtils.normPath(miscUtils.pathJoin(privateMapdirExpand,fileName))
        privateMapFilePath = miscUtils.normPath(miscUtils.pathJoin(privateMapdir,fileName))
        publicMapFilePathExpanded = miscUtils.normPath(miscUtils.pathJoin(publicMapdirExpand,fileName))
        publicMapFilePath = miscUtils.normPath(miscUtils.pathJoin(publicMapdir,fileName))


        uvTilingMode = mc.getAttr(eachFileNode+".uvTilingMode")



        #tests the texture extention
        mapExtention = (os.path.split(mapFilePath))[-1].split(".")[-1]
        if mapExtention  not in inAuthorizedFormat:
            if inVerbose == True: print "#### {:>7}: '{:^30}' the file extention :'.{}'  is not conform, only {} are allowed".format("Warning",eachFileNode,mapExtention,inAuthorizedFormat)
            outWrongFileNodeList.append(eachFileNode)
            continue
        #tests if used path match the privateMapdir and if the texture exists
        elif mapPath == privateMapdirExpand: 
            if os.path.isfile(mapFilePathExpand) == True:
                if ".1001." in os.path.split(mapFilePath)[-1] and mapFilePath.split(".")[-1] == "jpg":
                    if inVerbose == True: print "#### {:>7}: '{:^30}' {:^30} '{}'".format("Warning",eachFileNode,"Udim not allowed for jpg:", mapFilePath)       
                    outWrongFileNodeList.append(eachFileNode)
                    continue
                elif ".1001." in os.path.split(mapFilePath)[-1] and uvTilingMode != 3:
                    if inConform is True:
                        uvTilingMode = 3
                        mc.setAttr(eachFileNode+".uvTilingMode",uvTilingMode)
                        if inVerbose == True:print "#### {:>7}: '{:^30}' {:^30} ".format("Info",eachFileNode,"uvTilingMode set to 3 ")
                    else:
                        if inVerbose == True:print "#### {:>7}: '{:^30}' {:^30} ".format("Info",eachFileNode,"uvTilingMode must be set to 3 ")

                elif ".1001." in os.path.split(mapFilePath)[-1]:
                    udimNb = 1002
                    while udimNb < 1010:
                        udimMapFilePath = mapFilePath.replace(".1001.","."+str(udimNb)+".")
                        udimMapFilePath_exp = miscUtils.normPath(os.path.expandvars(os.path.expandvars(udimMapFilePath)))
                        if os.path.isfile(udimMapFilePath_exp) == True:
                            outMapPathForPublishList.append(udimMapFilePath)
                        udimNb=udimNb+1
                if inVerbose == True: print "#### {:>7}: '{:^30}' {:^30} '{}'".format("Info",eachFileNode,"File and filepath correct: ",mapFilePath)  
                outMapPathForPublishList.append(mapFilePath)
                continue
            else:
                if inVerbose == True: print "#### {:>7}: '{:^30}' {:^30} '{}' ".format("Warning",eachFileNode,"The file doesn't exist: ",mapFilePath)      
                outWrongFileNodeList.append(eachFileNode)
                continue

        #tests if used path match the privateMapdirExpand and if the texture exists
        elif mapPath == publicMapdir: 
            if os.path.isfile(publicMapFilePathExpanded) == True:
                if inVerbose == True: print "#### {:>7}: '{:^30}' {:^30} '{}'".format("Info",eachFileNode,"Published File: ", mapFilePath)  
                continue
            else:
                if inVerbose == True: print "#### {:>7}: '{:^30}' {:^30} '{}' ".format("Warning",eachFileNode,"The file doesn't exist: ",mapFilePath)       
                outWrongFileNodeList.append(eachFileNode)
                continue

        #tests if the texture exists in the privateMapdirExpand, and modify the path if inConform = True
        elif os.path.isfile(privateMapFilePathExpanded) is True:
            if inConform is True:
                if  uvTilingMode != 0: mc.setAttr(eachFileNode+".uvTilingMode",0)
                mc.setAttr(eachFileNode+".fileTextureName", privateMapFilePathExpanded, type = "string")
                if  uvTilingMode != 0: mc.setAttr(eachFileNode+".uvTilingMode",uvTilingMode)
                if inVerbose == True: print "#### {:>7}: '{:^30}' {:^30} '{}'".format("Info",eachFileNode,"The file path changed to: ", privateMapFilePathExpanded)
                continue
            else:
                if inVerbose == True: print "#### {:>7}: '{:^30}' {:^30} '{}'".format("Warning",eachFileNode,"Wrong path file: ", mapFilePath)       
                outWrongFileNodeList.append(eachFileNode)
                continue
        #tests if the texture file exists at the initial file path and copy it if required to the privateMapdirExpand
        elif os.path.isfile(mapFilePath) is True:
            if inCopy is True:
                print "#### {:>7}: copy file: "+mapFilePath+" --> "+privateMapFilePathExpanded
                shutil.copyfile(mapFilePath, privateMapFilePathExpanded)
                if os.path.isfile(privateMapFilePathExpanded) == False: 
                    print "#### Error: "+eachFileNode+" file could not be found: "+privateMapFilePathExpanded
                    outWrongFileNodeList.append(eachFileNode)
                    continue
                if  uvTilingMode != 0: mc.setAttr(eachFileNode+".uvTilingMode",0)
                mc.setAttr(eachFileNode+".fileTextureName", privateMapFilePathExpanded, type = "string")
                if  uvTilingMode != 0: mc.setAttr(eachFileNode+".uvTilingMode",uvTilingMode)
                if inVerbose == True: print "#### {:>7}: '{:^30}' {:^30} '{}'".format("Info",eachFileNode,"The file path changed to: ",privateMapFilePathExpanded)                        
                continue
        else:
            if inVerbose == True: print "#### {:>7}: '{:^30}' {:^30} '{}'".format("Warning",eachFileNode,"File must be moved to: ",privateMapFilePathExpanded)                         
            outWrongFileNodeList.append(eachFileNode)
            continue




    if outWrongFileNodeList: 
        print "#### {:>7}: {} file node(s) have wrong file path settings".format("Warning",len(outWrongFileNodeList))
        if inVerbose == True: 
            mc.select(outWrongFileNodeList)
            print "#### Info: the wrong file nodes have been selected"
    if not returnMapPath:
        return outWrongFileNodeList if outWrongFileNodeList else  None
    elif returnMapPath and (not outWrongFileNodeList):
        return outMapPathForPublishList if outMapPathForPublishList else  None
    else:
        return None


    



def imageResize(inputFilePathName = "", outputFilePathName = "", lod = 4, jpgQuality = 90, updateOnly = False, openImageMentalRay = True):
    """
    This function creates a resized jpg image
    it also switch off the mipmap fitering, and set the given file node so it point toward this new low res jgp
     - inputFilePathName : (string) an image to resize
     - outputFilePathName : (string) a jpg image file path name
     - lod : (int) 0..19 of pyramid map, largest is 0, width and height wil be divided by lod*lod
     - jpgQuality : (int) 1...100 highest is 100
    """

    if not isinstance(inputFilePathName,basestring):
        print "#### {:>7}: 'inputFilePathName' is not a string".format("Error")
        return

    if not isinstance(outputFilePathName,basestring):
        print "#### {:>7}: 'outputFilePathName' is not a string".format("Error")
        return

    inputFilePathName_exp = os.path.expandvars(os.path.expandvars(inputFilePathName))
    outputFilePathName_exp = os.path.expandvars(os.path.expandvars(outputFilePathName))

    if inputFilePathName == "" :
        print "#### {:>7}: no 'inputFilePathName' given".format("Error")
        return
    elif not os.path.isfile(inputFilePathName_exp):
        print "#### {:>7}: Missing file : {} given".format("Error", inputFilePathName_exp)
        return

    if outputFilePathName == "" :
        outputFilePathName = inputFilePathName.replace(inputFilePathName.split(".")[-1],"jpg")
        outputFilePathName_exp = inputFilePathName_exp.replace(inputFilePathName.split(".")[-1],"jpg")
    elif not os.path.isdir(os.path.split(outputFilePathName)[0]):
        print "#### {:>7}: Missing directory : {} given".format("Error", os.path.split(outputFilePathName))
        return
    elif not outputFilePathName.split(".")[-1] == "jpg":
        print "#### {:>7}: 'outputFilePathName'must be a '.jpg' file: {}".format("Error", outputFilePathName)
        return

    if os.path.isfile(outputFilePathName_exp) and updateOnly == True:
        inStatInfo = os.stat(inputFilePathName_exp)
        outStatInfo = os.stat(outputFilePathName_exp)
        if inStatInfo.st_mtime <= outStatInfo.st_ctime:
            print "#### {:>7}: {}  -->  is up to date".format("Info", outputFilePathName)
            return
        else:
            os.remove(outputFilePathName_exp)
    elif os.path.isfile(outputFilePathName_exp):
        os.remove(outputFilePathName_exp)

        
    if openImageMentalRay == True:
        #open image/mentalray method
        #mentalRayBin = os.path.normpath(os.environ['MAYA_LOCATION'].replace("Maya","mentalrayForMaya")).replace("\\", "/")
        imfCopyCommand = miscUtils.normPath(os.environ["ZOMB_TOOL_PATH"])+"/binaries/imf_copy"
        #imfCopyCommand = "/Applications/Autodesk/mentalrayForMaya2016_old/bin/imf_copy"
        tempDir = os.getenv ("TMPDIR")
        tempDir = tempDir.rstrip("/")
        tempImageFormat = "tga"
        tempFile = inputFilePathName_exp.replace(os.path.dirname(inputFilePathName_exp),tempDir)+"."+tempImageFormat
        if not os.path.isdir(tempDir):
            print ""
            print "#### error: "+tempDir+" is not a valid directory"
            return
        
        image = om.MImage()
        image.readFromFile(inputFilePathName_exp)
        util = om.MScriptUtil()
        widthUtil = om.MScriptUtil()
        heightUtil = om.MScriptUtil()
        widthPtr = widthUtil.asUintPtr()
        heightPtr = heightUtil.asUintPtr()
        image.getSize(widthPtr, heightPtr)
        width = util.getUint(widthPtr)
        height = util.getUint(heightPtr)
        image.resize( width/2**lod, height/2**lod )
        image.writeToFile( tempFile, tempImageFormat)
        subprocess.call([imfCopyCommand, "-vq",str(jpgQuality), tempFile,outputFilePathName_exp])
        os.remove(tempFile)     

    else:
        print "--NA---"


    statinfo = os.stat(inputFilePathName_exp)
    imageSize = string.ljust(str(statinfo.st_size/1024)+" Kb",10," ")
    textureWidth = string.ljust(str(width),5," ")
    textureHeight = string.ljust(str(height),5," ")
    
    statinfo_lowRes = os.stat(outputFilePathName_exp)
    fastJpgImageSize = string.ljust(str(statinfo_lowRes.st_size/1024)+" Kb",10," ")
    textureWidthLowRes = string.ljust(str(width/2**lod),5," ")
    textureHeightLowRes = string.ljust(str(height/2**lod),5," ")

    sz=str(max(len(inputFilePathName),len(outputFilePathName)))
    print "#### {:>7}: resize (LOD {}) and convert to jpg (quality = {})".format("Info", str(lod), str(jpgQuality))
    print ("#### {:>7}: {:<"+sz+"}  -->  width: {}  height: {}  size: {}").format("Info", inputFilePathName, textureWidth, textureHeight, imageSize)
    print ("#### {:>7}: {:<"+sz+"}  -->  width: {}  height: {}  size: {}").format("Info", outputFilePathName, textureWidthLowRes, textureHeightLowRes, fastJpgImageSize)




def conformPreviewShadingTree ( shadEngineList = [], verbose = True, selectWrongShadEngine = True, preShadNodeType = "lambert", matShadNodeType= "dmnToon", matTextureInput = ".outColor", preTextureInput = ".color", gui = True):
    """
    from a ginven shading engine
    this script assumes the shading tree has 2 different parts:
        - a preview shading tree used for maya viewport, the preview shading node (preShadNode) is the node connected in the surfaceShader input of the shading engine
        - a material (or render) shading tree for the render engine, the material shading node (matShadNode) is the node connected in the aiSurfaceShader input shading engine
    the script
        - check the existence of the 'preShadNode', replace it, if it has a wrong type, create it doesn't exists
        - gets the 'matTextureInput' connection of the 'matShadNodeType' and duplicate it then connect the new texture node in the 'preShadNode.preTextureInput'
        - conform the shding tree nodes names using conformShaderName() function

    """
    if verbose == True: print ""
    if verbose == True: print "#### {:>7}: runing shading.conformTexturePath( shadEngineList = [...], verbose = {}, preShadNodeType = {}, matShadNodeType = {}, matTextureInput = {}, preTextureInput ={})".format("Info", preShadNodeType, verbose, matShadNodeType, matTextureInput, preTextureInput)


    if shadEngineList == "all":
        shadEngineList = mc.ls("*",type = "shadingEngine")
        shadEngineList.remove("initialParticleSE")
        shadEngineList.remove("initialShadingGroup")
        if not shadEngineList :
            print "#### {:>7}: no shading engine to conform".format("Warning")
            return
        if verbose == True:
            answer = mc.confirmDialog( title='Confirm', message='You are about to conform '+str(len(shadEngineList))+' shading engines, do you want to continue?', button=['Yes','Cancel'], defaultButton='Yes', cancelButton='Cancel', dismissString='Cancel' )
            if answer == "Cancel": return

    elif shadEngineList == "selection":
        shadEngineList = mc.ls(selection = True,type = "shadingEngine")
        if "initialParticleSE" in shadEngineList: shadEngineList.remove("initialParticleSE")
        if "initialShadingGroup" in shadEngineList: shadEngineList.remove("initialShadingGroup")
        shadEngineListTemp = shadEngineList
        for each in shadEngineListTemp:
            if ":" in each: shadEngineList.remove(each) 
        if not shadEngineList : 
            print "#### {:>7}: no shading engine selected".format("Warning")
            return
    elif isinstance(shadEngineList, (basestring)):
            shadEngineList = [shadEngineList]
    if not isinstance(shadEngineList, (list,tuple,set)):
        print "#### {:>7}: shadEngineList must be a list. shadEngineList: {}".format("Error", shadEngineList)
        return
    if shadEngineList == []: 
        print "#### {:>7}: No shading engine to process, shadEngineList is empty".format("Error")
        return

    try:
        mc.nodeType(preShadNodeType, isTypeName=True)
    except:
        print "#### {:>7}: the preview shading node type is unkowned: preShadNodeType = {}".format("Error", preShadNodeType)
        return

    try:
        mc.nodeType(matShadNodeType, isTypeName=True)
    except:
        print "#### {:>7}: the render shading node type is unkowned: matShadNodeType = {}".format("Error", matShadNodeType)
        return


    correctShadEngine =[]
    wrongShadEngine = []

    for shadingEngine in shadEngineList:

        if not re.match('^sgr_[a-zA-Z0-9]{1,24}$', shadingEngine):
            wrongShadEngine.append((shadingEngine,"does not match naming convention 'sgr_materialName' where is composed of 24 alphanumeric characters maximum"))
            continue

        preShadNode =  mc.listConnections(shadingEngine+'.surfaceShader',connections = False)
        matShadNode =  mc.listConnections(shadingEngine+'.aiSurfaceShader',connections = False)
        materialName = shadingEngine.split("sgr_")[-1]

        #check the existence of the 'preShadNode', replace it, if it has a wrong type, create it doesn't exists
        if not preShadNode:
            preShadNode = mc.shadingNode(preShadNodeType, asShader=True)
            mc.setAttr(preShadNode+preTextureInput, 1, 1,1, type = "double3")
            mc.setAttr(preShadNode+'.diffuse', 0.1)
            mc.setAttr(preShadNode+'.ambientColor', 0.9, 0.9, 0.9, type = "double3")
            mc.connectAttr(preShadNode+'.outColor', shadingEngine+'.surfaceShader', force =True)
            if verbose == True: print "#### {:>7}: {:^28} Preview shader created: '{}'".format("Info", shadingEngine, preShadNodeType)
        elif mc.nodeType(preShadNode[-1]) != preShadNodeType:
            if mc.nodeType(preShadNode[-1]) == "surfaceShader":
                surfShadColValue = mc.getAttr(preShadNode[-1]+'.outColor')
                surfShadTrsValue = mc.getAttr(preShadNode[-1]+'.outTransparency')
                try:
                    surfShadColConnect = mc.listConnections(preShadNode[-1]+'.outColor',connections = False, destination = False, source =True, plugs = True)[-1]
                except:
                    surfShadColConnect = None
                try:
                    surfShadTrsConnect = mc.listConnections(preShadNode[-1]+'.outTransparency',connections = False, destination = False, source =True, plugs = True)[-1]
                except:
                    surfShadTrsConnect = None
                mc.delete(preShadNode[-1])
                preShadNode = mc.shadingNode(preShadNodeType, asShader=True)
                mc.setAttr(preShadNode+'.diffuse', 0.1)
                mc.setAttr(preShadNode+'.ambientColor', 0.9, 0.9 ,0.9, type = "double3")
                print surfShadColValue[0][0] 
                print surfShadColValue[0][1]
                print surfShadColValue[0][2]
                print preShadNode+preTextureInput
                mc.setAttr(preShadNode+preTextureInput, surfShadColValue[0][0], surfShadColValue[0][1], surfShadColValue[0][2], type = "double3")
                mc.setAttr(preShadNode+'.transparency', surfShadTrsValue[0][0], surfShadTrsValue[0][1], surfShadTrsValue[0][2], type = "double3")
                mc.connectAttr(preShadNode+'.outColor', shadingEngine+'.surfaceShader', force =True)
                if surfShadColConnect: 
                    mc.connectAttr(surfShadColConnect, preShadNode+preTextureInput, force =True)
                if surfShadTrsConnect: 
                    mc.connectAttr(surfShadTrsConnect, preShadNode+'.transparency', force =True)
            else:
                mc.delete(preShadNode[-1])
                preShadNode = mc.shadingNode(preShadNodeType, asShader=True)
                mc.setAttr(preShadNode+'.diffuse', 0.1)
                mc.setAttr(preShadNode+'.ambientColor', 0.9, 0.9, 0.9, type = "double3")
                mc.setAttr(preShadNode+preTextureInput, 1, 1,1, type = "double3")
                mc.connectAttr(preShadNode+'.outColor', shadingEngine+'.surfaceShader', force =True)
            if verbose == True: print "#### {:>7}: {:^28} Preview shader replaced: '{}'".format("Info", shadingEngine, preShadNodeType)
        else:
            preShadNode = preShadNode[-1]

        if not matShadNode or mc.nodeType(matShadNode[-1]) != matShadNodeType:
            if verbose == True: print "#### {:>7}: {:^28} The material shading node is missing or has a wrong type,  ".format("Info", shadingEngine)
            matShadNode = mc.shadingNode(matShadNodeType, asShader=True)
            mc.connectAttr(matShadNode+".outColor", shadingEngine+'.aiSurfaceShader', force =True)
            continue
        else:
            matShadNode = matShadNode[-1]

        #get the input texture connection of the rendering shading node 
        matShadTextInputConnection = mc.listConnections (matShadNode+matTextureInput, source=True, destination=False)
        if matShadTextInputConnection:
            matShadTextInputValue = []
            matShadTextInputConnection = matShadTextInputConnection[-1]
            if mc.nodeType(matShadTextInputConnection) != "file":
                wrongShadEngine.append((shadingEngine,"The preview texture file node could not be found automaticaly :"))
                continue        
        else:
            matShadTextInputValue = mc.getAttr(matShadNode+matTextureInput)[0]


        #get the input texture connection of the preview shading node 
        preShadTextInputConnection = mc.listConnections (preShadNode+preTextureInput, source=True, destination=False)
        if preShadTextInputConnection:
            preShadTextInputConnection = preShadTextInputConnection[-1]
            if mc.nodeType(preShadTextInputConnection) == "file":
                #test if the file node is also connected to the render node
                if mc.listConnections (preShadTextInputConnection+".outColor", source=False, destination=True, exactType= True, type=matShadNodeType):
                    result = mc.duplicate(preShadTextInputConnection, upstreamNodes = True)[0]
                    mc.connectAttr(result+".outColor", preShadNode+preTextureInput, force =True)
                    if verbose == True: print "#### {:>7}: {:^28} Preview shader processed: texture file node duplicated".format("Info", shadingEngine)
                    conformShaderName(shadingEngine, selectWrongShadEngine = False, verbose = False )
                    continue
                else:
                    if verbose == True: print "#### {:>7}: {:^28} Preview shader ok".format("Info", shadingEngine)
                    continue
        elif matShadTextInputConnection:
            result = mc.duplicate(matShadTextInputConnection, upstreamNodes = True)[0]
            mc.connectAttr(result+".outColor", preShadNode+preTextureInput, force =True)
            if verbose == True: print "#### {:>7}: {:^28} Preview shader processed: texture file node duplicated".format("Info", shadingEngine)
            conformShaderName(shadingEngine, selectWrongShadEngine = False, verbose = False )
            #if the color is black replace it with the color from the render shader
        elif  mc.getAttr(preShadNode+preTextureInput)[0][0]+mc.getAttr(preShadNode+preTextureInput)[0][1]+mc.getAttr(preShadNode+preTextureInput)[0][2] == 0:
            try: 
                mc.setAttr(preShadNode+preTextureInput, matShadTextInputValue[0], matShadTextInputValue[1],matShadTextInputValue[2], type = "double3")
                if verbose == True: print "#### {:>7}: {:^28} Preview shader processed: color value inherited".format("Info", shadingEngine)
            except: 
                if verbose == True: print "#### {:>7}: {:^28} Preview shader untouched: color value locked".format("Warning", shadingEngine)


    if  wrongShadEngine != [] and selectWrongShadEngine == True:
        mc.select(clear = True)
        for each in wrongShadEngine:
            print "#### {:>7}: {:^28} {}".format("Error", each[0], each[1])
            if selectWrongShadEngine == True: mc.select(each[0], ne = True, add = True)
        print "#### {:>7}: Problematics shading engines have been selected".format("Error")
        if gui == True:
            mc.confirmDialog( title='Shader structure Error', message='Some shaders are not conform, please read the log to get more information', button=['Ok'], defaultButton='Ok' )
    return wrongShadEngine if wrongShadEngine != [] else  None


def generateJpgForPreview( fileNodeList = "all", verbose = True, preShadNodeType = "lambert", updateOnly=False):  
    """
    This script get a list of pre_* file node from the selection (fileNodeList = "selection") or 
    from the entire scene (fileNodeList = "all") and generate a low resolution jpg file from the existing .tga file.
    if a sgr_* shadingEngine node is selected, the script will consider all the 'pre_*' downstream nodes.
    the file path is modified to point the .jpg once it has been created.
        updateOnly: when True and a jpg already exists, last modificaton date of tga an jpg are compared to evaluate if the jpg needs to be generated again
        preShadNodeType: the type of node the file node must be plugged in
        verbose: allow the problematic file node to be selected at the end of the proccess
    """ 
    print ""
    print "#### {:>7}: runing shading.lowResJpgForPreview( fileNodeList = {}, verbose = {}, preShadNodeType = {}, updateOnly={} )".format("Info", fileNodeList, verbose, preShadNodeType, updateOnly)
    if mc.ls("|asset"):        
        mainFilePath = mc.file(q=True, list = True)[0]
        mainFilePathElem = mainFilePath.split("/")
        if  mainFilePathElem[-4] == "asset":
            privateMapdir = miscUtils.pathJoin("$PRIV_ZOMB_TEXTURE_PATH",mainFilePathElem[-3],mainFilePathElem[-2],"texture")
            privateMapdirExpand = os.path.expandvars(os.path.expandvars(privateMapdir))
        else:
            raise ValueError("#### Error: you are not working in an 'asset' structure directory")
    else :
        raise ValueError("#### Error: no '|asset' could be found in this scene")

    conformShaderName("all", selectWrongShadEngine = False, verbose = False )

    if fileNodeList == "all":
        fileNodeList = mc.ls("pre_*",type ="file")
        if updateOnly == False:
            answer = mc.confirmDialog( title='Confirm', message='You are about to generate jpg for '+str(len(fileNodeList))+' file nodes, do you want to continue?', button=['Yes','Cancel'], defaultButton='Yes', cancelButton='Cancel', dismissString='Cancel' )
            if answer == "Cancel": return
    elif fileNodeList == "selection":
        selectedFileList = mc.ls(selection = True, type ="file")
        selectedShaEngList = mc.ls(selection = True, type ="shadingEngine")
        fileNodeList=set()
        for each in selectedShaEngList:
            if re.match('^sgr_[a-zA-Z0-9]{1,24}$', each):
                nodes = mc.ls(mc.listHistory (each), type = "file")
                for eachNode in nodes:
                    if re.match('^pre_[a-zA-Z0-9]{1,24}_[a-zA-Z0-9]{1,24}$', eachNode):
                        fileNodeList.add(eachNode)
        for each in selectedFileList:
            if re.match('^pre_[a-zA-Z0-9]{1,24}_[a-zA-Z0-9]{1,24}$', each):
                fileNodeList.add(each)


    if len(fileNodeList) == 0:
        print "#### {:>7}: nothing to process, please select  'pre_*' file nodes or 'sgr_*' shading engine nodes first".format("Warning")

    wrongFileNodeList = []    
    for eachFileNode in fileNodeList:
        print "#### {:>7}: Processing: '{}' ".format("Info", eachFileNode)
        wrongFileNode = False
        mapFilePath = miscUtils.normPath(mc.getAttr(eachFileNode+".fileTextureName"))
        mapFilePathExpand = miscUtils.normPath(os.path.expandvars(os.path.expandvars(mapFilePath)))
        tgaFilePath = mapFilePath.replace(mapFilePath.split(".")[-1],"tga") 
        tgaFilePathExpand = mapFilePathExpand.replace(mapFilePathExpand.split(".")[-1],"tga")
        jpgFilePath = mapFilePath.replace(mapFilePath.split(".")[-1],"jpg") 
        jpgFilePathExpand = mapFilePathExpand.replace(mapFilePathExpand.split(".")[-1],"jpg")

        mapPath = os.path.split(mapFilePath)[0]
        fileName = os.path.split(mapFilePath)[1]       
        privateMapFilePathExpanded = miscUtils.pathJoin(privateMapdirExpand,fileName)
        privateMapFilePath = miscUtils.pathJoin(privateMapdir,fileName)


        if not os.path.isfile(tgaFilePathExpand) and os.path.isfile(jpgFilePathExpand):
            print "#### {:>7}: '{}' No '.tga' file could be found, '.jpg' is done already".format("Info", eachFileNode)
        elif not os.path.isfile(mapFilePathExpand) and not os.path.isfile(tgaFilePathExpand):
            print "#### {:>7}: '{}' Missing File  -->  {}".format("Error", eachFileNode, mapFilePathExpand)
            wrongFileNodeList.append(eachFileNode)
            continue
        elif not(mapFilePath == tgaFilePath or mapFilePath == jpgFilePath): 
            print "#### {:>7}: '{}' FileNode, wrong file format: '{}',  should be a jpg or tga".format("Error",eachFileNode,mapFilePath.split(".")[-1])
            wrongFileNodeList.append(eachFileNode)
            continue

        if mainFilePathElem[-3] == "chr": 
            LOD = 3
        else:
            LOD = 4

        if mainFilePathElem[-3] == "chr" and os.path.isfile(jpgFilePathExpand):
            print "#### {:>7}: '{}' FileNode, jpg file: '{}',  already exists, can't replace it automaticaly on characters,please delete it manually first".format("Warning",eachFileNode,os.path.split(mapFilePath)[-1])
        else:
            imageResize(inputFilePathName = tgaFilePath, outputFilePathName = "", lod = LOD, jpgQuality = 90, updateOnly = updateOnly, openImageMentalRay = True)

        if mapFilePath != jpgFilePath: 
            mc.setAttr(eachFileNode+".fileTextureName", jpgFilePath, type="string")


    if wrongFileNodeList: 
        print ""
        print "#### {:>7}: {} file node(s) cannot be processed".format("Warning",len(wrongFileNodeList))
        if verbose == True: 
            mc.select(wrongFileNodeList)
            print "#### {:>7}: The wrong file nodes have been selected".format("Info")
    return wrongFileNodeList if wrongFileNodeList != [] else  None



def makeTxForArnold(inputFilePathName = "", outputFilePathName = "", updateOnly = False):
    """
    from a given image, this script generates an mipmap arnold tx file
        inputFilePathName: the image path name to convert
        outputFilePathName: the .tx image path name, if = "" the script will just replace the inputFilePathName extention to ".tx"
        updateOnly: when True and a .tx already exists, last modificaton date of inputFilePathName and outputFilePathName are compared to evaluate if the .tx needs to be generated again
    """

    if not isinstance(inputFilePathName,basestring):
        print "#### {:>7}: 'inputFilePathName' is not a string".format("Error")
        return

    if not isinstance(outputFilePathName,basestring):
        print "#### {:>7}: 'outputFilePathName' is not a string".format("Error")
        return

    inputFilePathName_exp = miscUtils.normPath(os.path.expandvars(os.path.expandvars(inputFilePathName)))
    outputFilePathName_exp = miscUtils.normPath(os.path.expandvars(os.path.expandvars(outputFilePathName)))

    
    if inputFilePathName == "" :
        print "#### {:>7}: no 'inputFilePathName' given".format("Error")
        return
    elif not os.path.isfile(inputFilePathName_exp):
        print "#### {:>7}: Missing file : {} given".format("Error", inputFilePathName_exp)
        return

    if outputFilePathName == "" :
        outputFilePathName = inputFilePathName.replace(inputFilePathName.split(".")[-1],"tx")
        outputFilePathName_exp = miscUtils.normPath(os.path.expandvars(os.path.expandvars(outputFilePathName)))
    elif not os.path.isdir(os.path.split(outputFilePathName)[0]):
        print "#### {:>7}: Missing directory : {} given".format("Error", os.path.split(outputFilePathName))
        return
    elif not outputFilePathName.split(".")[-1] == "tx":
        print "#### {:>7}: 'outputFilePathName'must be a '.tx' file: {}".format("Error", outputFilePathName)
        return

    if os.path.isfile(outputFilePathName_exp) and updateOnly == True:
        inStatInfo = os.stat(inputFilePathName_exp)
        outStatInfo = os.stat(outputFilePathName_exp)
        if inStatInfo.st_mtime <= outStatInfo.st_ctime:
            print "#### {:>7}: {}  -->  is up to date".format("Info", outputFilePathName)
            return
        else:
            try :
                os.remove(outputFilePathName_exp)
            except:
                raise ValueError("#### Error: file is locked by your os, someone is accessing it: "+outputFilePathName_exp)
    elif os.path.isfile(outputFilePathName_exp):
        try :
            os.remove(outputFilePathName_exp)
        except:
            raise ValueError("#### Error: file is locked by your os, someone is accessing it: "+outputFilePathName_exp)

    renderDesc = os.environ["MAYA_RENDER_DESC_PATH"].split(":")
    mtoaPath = ""
    for each in renderDesc:
        normedEach = os.path.normpath(each).replace("\\", "/")
        if "/solidangle/mtoa" in normedEach:
            mtoaPath = normedEach
            continue
    if mtoaPath == "":
        print "#### {:>7}: 'could not find a valid solidangle path in 'MAYA_RENDER_DESC_PATH'".format("Error")
        return
    maketxCommand = mtoaPath+"/bin/maketx"
    subprocess.call([maketxCommand, "-u","--oiio", inputFilePathName_exp])   

    image = om.MImage()
    image.readFromFile(inputFilePathName_exp)
    util = om.MScriptUtil()
    widthUtil = om.MScriptUtil()
    heightUtil = om.MScriptUtil()
    widthPtr = widthUtil.asUintPtr()
    heightPtr = heightUtil.asUintPtr()
    image.getSize(widthPtr, heightPtr)
    width = util.getUint(widthPtr)
    height = util.getUint(heightPtr)

    statinfo = os.stat(inputFilePathName_exp)
    imageSize = string.ljust(str(statinfo.st_size/1024)+" Kb",10," ")
    textureWidth = string.ljust(str(width),5," ")
    textureHeight = string.ljust(str(height),5," ")
    
    statinfo_lowRes = os.stat(outputFilePathName_exp)
    fastJpgImageSize = string.ljust(str(statinfo_lowRes.st_size/1024)+" Kb",10," ")
    textureWidthTx = string.ljust(str(width),5," ")
    textureHeightTx = string.ljust(str(height),5," ")

    sz=str(max(len(inputFilePathName),len(outputFilePathName)))
    print "#### {:>7}: generate arnold '.tx' mipmap texture file".format("Info")
    print ("#### {:>7}: {:<"+sz+"}  -->  width: {}  height: {}  size: {}").format("Info", inputFilePathName, textureWidth, textureHeight, imageSize)
    print ("#### {:>7}: {:<"+sz+"}  -->  width: {}  height: {}  size: {}").format("Info", outputFilePathName, textureWidthTx, textureHeightTx, fastJpgImageSize)


def generateTxForRender(fileNodeList = "selection", verbose = True, updateOnly=False):    
    """
    This script get a list of mat_* file node from the selection (fileNodeList = "selection") or 
    from the entire scene (fileNodeList = "all") and generate a low resolution jpg file from the existing .tga file.
    if a sgr_* shadingEngine node is selected, the script will consider all the 'mat_*' downstream nodes.
        updateOnly: when True and a .tx already exists, last modificaton date of inputFilePathName and outputFilePathName are compared to evaluate if the .tx needs to be generated again
        verbose: allow the problematic file node to be selected at the end of the proccess
    """
    print ""
    print "#### {:>7}: runing shading.mipMapForRender( fileNodeList = {}, verbose = {}, updateOnly={})".format("Info", fileNodeList, verbose, updateOnly)
    if mc.ls("|asset"):        
        mainFilePath = mc.file(q=True, list = True)[0]
        mainFilePathElem = mainFilePath.split("/")
        if  mainFilePathElem[-4] == "asset":
            privateMapdir = miscUtils.pathJoin("$PRIV_ZOMB_TEXTURE_PATH",mainFilePathElem[-3],mainFilePathElem[-2],"texture")
            privateMapdirExpand = os.path.expandvars(os.path.expandvars(privateMapdir))
        else:
            raise ValueError("#### Error: you are not working in an 'asset' structure directory")
    else :
        raise ValueError("#### Error: no '|asset' could be found in this scene")  

    if not isinstance(fileNodeList,basestring):
        print "#### {:>7}: 'fileNodeList' is not a string".format("Error")
        return

    conformShaderName("all", selectWrongShadEngine = False, verbose = False )

    if fileNodeList == "all":
        fileNodeList = mc.ls("mat_*",type ="file")
        if updateOnly == False:
            answer = mc.confirmDialog( title='Confirm', message='You are about to generate .tx for '+str(len(fileNodeList))+' file nodes, do you want to continue?', button=['Yes','Cancel'], defaultButton='Yes', cancelButton='Cancel', dismissString='Cancel' )
            if answer == "Cancel": return
    elif fileNodeList == "selection":
        selectedFileList = mc.ls(selection = True, type ="file")
        selectedShaEngList = mc.ls(selection = True, type ="shadingEngine")
        fileNodeList=set()
        for each in selectedShaEngList:
            if re.match('^sgr_[a-zA-Z0-9]{1,24}$', each):
                nodes = mc.ls(mc.listHistory (each), type = "file") + mc.ls(mc.listHistory (mc.listConnections (each+".aiSurfaceShader", source=True, destination=False, connections = False)), type = "file")
                for eachNode in nodes:
                    if re.match('^mat_[a-zA-Z0-9]{1,24}_[a-zA-Z0-9]{1,24}$', eachNode):
                        fileNodeList.add(eachNode)
        for each in selectedFileList:
            if re.match('^mat_[a-zA-Z0-9]{1,24}_[a-zA-Z0-9]{1,24}$', each):
                fileNodeList.add(each)
       
    if len(fileNodeList) == 0:
        print "#### {:>7}: nothing to process, please select  'mat_*' file nodes or 'sgr_*' shading engine nodes first".format("Warning")

    wrongFileNodeList = []
    
    for eachFileNode in fileNodeList:
        print "#### {:>7}: Processing: '{}' ".format("Info", eachFileNode)
        wrongFileNode = False
        mapFilePath = miscUtils.normPath(mc.getAttr(eachFileNode+".fileTextureName"))
        mapFilePathExpand = miscUtils.normPath(os.path.expandvars(os.path.expandvars(mapFilePath)))
        tgaFilePath = mapFilePath.replace(mapFilePath.split(".")[-1],"tga") 
        tgaFilePathExpand = mapFilePathExpand.replace(mapFilePathExpand.split(".")[-1],"tga")
        mipMapFilePath = mapFilePath.replace(mapFilePath.split(".")[-1],"tx") 
        mipMapFilePathExpand = mapFilePathExpand.replace(mapFilePathExpand.split(".")[-1],"tx")

        mapPath = os.path.split(mapFilePath)[0]
        fileName = os.path.split(mapFilePath)[1]       
        privateMapFilePathExpanded = miscUtils.pathJoin(privateMapdirExpand,fileName)
        privateMapFilePath = miscUtils.pathJoin(privateMapdir,fileName)

        if mapFilePathExpand != tgaFilePathExpand: 
            print "#### {:>7}: '{}' FileNode, wrong file format: '{}',  should be a tga".format("Error",eachFileNode,tgaFilePathExpand.split(".")[-1])
            wrongFileNodeList.append(eachFileNode)
            continue
        elif not os.path.isfile(tgaFilePathExpand) and os.path.isfile(mipMapFilePathExpand):
            print "#### {:>7}: '{}' No '.tga' file could be found, '.tx' is done already".format("Info", eachFileNode)
        elif not os.path.isfile(mapFilePathExpand) and not os.path.isfile(tgaFilePathExpand):
            print "#### {:>7}: '{}' Missing File  -->  {}".format("Error", eachFileNode, mapFilePathExpand)
            wrongFileNodeList.append(eachFileNode)
            continue

        makeTxForArnold(inputFilePathName = tgaFilePathExpand, outputFilePathName = "", updateOnly = updateOnly)

        if ".1001." in os.path.split(tgaFilePathExpand)[-1]:
            udimNb = 1002
            while udimNb < 1100:
                udimMapFilePath = tgaFilePathExpand.replace(".1001.","."+str(udimNb)+".")
                udimMapFilePath_exp = miscUtils.normPath(os.path.expandvars(os.path.expandvars(udimMapFilePath)))
                if os.path.isfile(udimMapFilePath_exp) == True:
                    makeTxForArnold(inputFilePathName = udimMapFilePath, outputFilePathName = "", updateOnly = updateOnly)
                udimNb=udimNb+1

    if wrongFileNodeList: 
        print ""
        print "#### {:>7}: {} file node(s) cannot be processed".format("Warning",len(wrongFileNodeList))
        if verbose == True: 
            mc.select(wrongFileNodeList)
            print "#### {:>7}: The wrong file nodes have been selected".format("Info")
    return wrongFileNodeList if wrongFileNodeList != [] else  None



def getTexturesToPublish (verbose = True):
    mapFilePathList = conformTexturePath(inVerbose = False, inConform = False, returnMapPath = True)
    print "mapFilePathList "+str(mapFilePathList)
    print "#### {:>7}: runing shading.getTexturesToPublish(verbose = {})".format("Info", verbose)
    if not mapFilePathList:
        print "#### {:>7}: One (or several) the texture path is not conform, please run the conformTexturePath() procedure first".format("Error")
        return

    privateMapdirExpand = miscUtils.normPath(os.path.expandvars(os.path.expandvars(os.path.split(mapFilePathList[0])[0])))
    print "#### {:>7}: Expanded working directory: '{}'".format("Info",os.path.normpath(privateMapdirExpand))

    missingFiles = 0
    filesToPublish = []

    for mapFilePath in mapFilePathList:
        fileExtention = mapFilePath.split(".")[-1]
        filePath = mapFilePath.rstrip("."+fileExtention)
        filePathTga_exp = miscUtils.normPath(os.path.expandvars(os.path.expandvars(filePath+".tga")))
        filePathPsd_exp = miscUtils.normPath(os.path.expandvars(os.path.expandvars(filePath+".psd")))
        filePathTx_exp = miscUtils.normPath(os.path.expandvars(os.path.expandvars(filePath+".tx")))
        filePathJpg_exp = miscUtils.normPath(os.path.expandvars(os.path.expandvars(filePath+".jpg")))
        if fileExtention == "tga":
            if os.path.isfile(filePathTga_exp):
                filesToPublish.append(filePathTga_exp)
            else:
                print "#### {:>7}: Missing file: {}".format("Error", filePathTga_exp)
                missingFiles = missingFiles + 1
                
            if os.path.isfile(filePathPsd_exp):
                filesToPublish.append(filePathPsd_exp)
            # esle if the texture file is not a _col file, continue (not reported as missing)
            elif os.path.split(mapFilePath)[-1].split(".")[0].split("_")[-1] != "col":
                continue
            # else if the texture file has udim number, continue (not reported as missing)
            elif len(os.path.split(mapFilePath)[-1].split("."))==3:
                try:
                    udimNb = int(fileName.split(".")[-2])
                except:
                    udimNb = 0
                    pass        
                if 1001 < udimNb < 1011:
                    continue
            else:
                print "#### {:>7}: Missing file: {}".format("Error", filePathPsd_exp)
                missingFiles = missingFiles + 1
                
            if os.path.isfile(filePathTx_exp):
                filesToPublish.append(filePathTx_exp)
            else:
                print "#### {:>7}: Missing file: {}".format("Error", filePathTx_exp)
                missingFiles = missingFiles + 1
                
            if os.path.isfile(filePathJpg_exp):
                filesToPublish.append(filePathJpg_exp)

        if fileExtention == "jpg":
            if os.path.isfile(filePathJpg_exp):
                filesToPublish.append(filePathTga_exp)
            else:
                print "#### {:>7}: Missing file: {}".format("Error", filePathTga_exp)
                missingFiles = missingFiles + 1

            if os.path.isfile(filePathPsd_exp):
                filesToPublish.append(filePathPsd_exp)
            # esle if the texture file is not a _col file, continue (not reported as missing)
            elif os.path.split(mapFilePath)[-1].split(".")[0].split("_")[-1] != "col":
                continue
            else:
                print "#### {:>7}: Missing file: {}".format("Error", filePathPsd_exp)
                missingFiles = missingFiles + 1

    filesToPublishSet = set(filesToPublish)
    filesToPublish = list(filesToPublishSet)
    filesToPublish.sort()

    if verbose == True:
        print "#### {:>7}: {} files to publish:".format("Info", len(filesToPublish))
        for each in filesToPublish:
            print each

    unreferencedFileList = []
    texturePath_exp = os.path.split(filePathTga_exp)[0]
    dirContent = os.listdir(texturePath_exp)

    for each in dirContent:
        toIgnore =  ["Thumbs.db",".DS_Store"]
        eachFileName = miscUtils.normPath(os.path.join(texturePath_exp,each))
        if eachFileName not in filesToPublish and os.path.isfile(eachFileName) and each not in toIgnore :
            unreferencedFileList.append(each)

    if unreferencedFileList :
        print "#### {:>7}: {} file(s) of your working dir: '{}' is(are) not referenced in this scene:".format("Warning",len(unreferencedFileList), os.path.split(mapFilePath)[0])
        print "#### {:>7}: {}".format("Warning",unreferencedFileList)

    if missingFiles != 0:
        print "#### {:>7}: Missing file(s): {}".format("Error",missingFiles)
        return 


def createShadingGroup():
    """
    This script creates a shading engine for all the selected geometrie objects, and conform it
    """
    print ""
    print "#### {:>7}: runing shading.createShadingGroup()".format("Info")
    transformMeshList = []
    selection = mc.ls( selection=True, l=True)
    for each in selection:
        meshList = miscUtils.getAllTransfomMeshes(inParent = each)
        for eachMesh in meshList:
            transformMeshList.append(eachMesh)
    if not transformMeshList:
        print "#### {:>7}: nothing selected, please select at leas a geometrie and run again the script".format("Info")
        return

    answer =  mc.confirmDialog( title='Confirm', message="You are about to create a new shading group for all the selected 'geo_' objects (and children), all the existing shaers will be disconnected. Do you want to continue?", button=['Proceed','Cancel'], defaultButton='Proceed', cancelButton='Cancel', dismissString='Cancel' )
    if answer == "Cancel": 
        return
    wrongGeoList = modeling.checkMeshNamingConvention()
    if wrongGeoList:
        #raise ValueError("#### Error: 'geo_' wrong naming convention")
        mc.confirmDialog( title='Confirm', message="#### Error: 'geo_' wrong naming convention, please check the script editor log for details", button=['Ok'], defaultButton='Ok')
        return

    for each in transformMeshList:
        myName = each.split("|")[-1].lstrip("geo_")
        mynameSplit = myName.split("_")
        if len(mynameSplit)==2:
            myName = mynameSplit[0]+mynameSplit[1].capitalize()
        myName = "sgr_"+myName
        my_sgr = mc.sets(renderable=True,noSurfaceShader=True,empty=True, name=myName)
        mc.sets(each, forceElement=my_sgr)
    print "#### {:>7}:  {} shading groups created, assigned and conformed".format("Info",len(transformMeshList))
    conformPreviewShadingTree( shadEngineList = "all", verbose = False, selectWrongShadEngine = False)
    conformShaderName(shadEngineList = "all", selectWrongShadEngine = False, verbose = False )




def printTextureFileName (fileNodeList = "all"):
    if fileNodeList == "all":
        fileNodeList = mc.ls(type ="file")
    else:
        fileNodeList = mc.ls(selection = True, type ="file")

    for each in fileNodeList:
       mapFilePath = os.path.normpath(miscUtils.normPath(mc.getAttr(each+".fileTextureName")))
       mapFilePathExpand = miscUtils.normPath(os.path.expandvars(os.path.expandvars(mapFilePath))) 
       print "#### Info: '{0:^30}' Image Name: '{1}'".format(each,mapFilePath) 














