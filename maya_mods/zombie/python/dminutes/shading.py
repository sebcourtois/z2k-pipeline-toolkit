import maya.cmds as mc
import re
import os
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
        print "####    error: 'conformShaderNames': '"+myNode+"' is connected to several shading groups  -->   "+str(upStreamShadingGroupList)
        return True
    else:
        return False



def conformShaderName(shadEngineList = "selection"):
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
    correctShadEngine =[]
    wrongShadEngine = []

    permitted_preview_shader_type = ["lambert","surfaceShader"]
    permitted_render_shader_type = ["aiStandard", "dmnToon"]

    if shadEngineList == "all":
        shadEngineList = mc.ls(":*",type = "shadingEngine")
        shadEngineList.remove("initialParticleSE")
        shadEngineList.remove("initialShadingGroup")
        if not shadEngineList :
            print "#### info: 'conformShaderNames': no shading engine to conform"
            return

    elif shadEngineList == "selection":
        shadEngineList = mc.ls(selection = True,type = "shadingEngine")
        if "initialParticleSE" in shadEngineList: shadEngineList.remove("initialParticleSE")
        if "initialParticleSE" in shadEngineList: shadEngineList.remove("initialParticleSE")
        if not shadEngineList : 
            print "#### info: 'conformShaderNames': no shading engine selected"
            return

    for each in shadEngineList:
        #check shading group name convention
        if not re.match('^sgr_[a-zA-Z0-9]{1,24}$', each):
            wrongShadEngine.append((each,"does not match naming convention 'sgr_materialName' where is composed of 24 alphanumeric characters maximum"))
        else:
            #check that 2 different2 shading nodes are plugged into the surfaceShader and aiSurfaceShader input of the SG node
            correctShadEngine.append(each)
            materialName = each.lstrip("sgr_")
            print materialName
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

        print "####    info: 'conformShaderNames': -- "+each+" --  tree has been conformed properly" 

    for each in wrongShadEngine:
        print "#### warning: 'conformShaderNames': "+each[0]+"   -->   "+each[1]


def referenceShadingCamera(cameraName = "cam_shading_default", fileType=".ma"):
    """
    reference a camera for shading purpose. This tools is not to use for shot bulding.
        cameraName (string): the camera name you want to reference
        fileType(string): specify if the '.ma' or '.mb' file is to reference
    """
    zombie_asset_dir =  os.environ["ZOMBI_ASSET_DIR"]
    shading_cam_filename =  os.path.join("$ZOMBI_ASSET_DIR", "cam",cameraName,cameraName+fileType)
    
    
    if cameraName in  str(mc.file(query=True, list=True, reference = True)):
        print "#### info 'referenceShadingCamera': a camera '"+cameraName+"' is already referenced in this scene, operation canceled"
    else:
        mc.file(shading_cam_filename, reference = True, namespace = cameraName+"00", ignoreVersion  = True,  groupLocator = True, mergeNamespacesOnClash = False)
              



def conformMapPath(inVerbose = True, inConform = False, inCopy =False, inAuthorizedFormat=["jpg","tga"]):
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
            finalMapdir = miscUtils.pathJoin("$PRIVATE_MAP_DIR","asset",mainFilePathElem[-3],mainFilePathElem[-2],"texture")
            finalMapdirExpand = miscUtils.pathJoin(os.environ["PRIVATE_MAP_DIR"],"asset",mainFilePathElem[-3],mainFilePathElem[-2],"texture")
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


            