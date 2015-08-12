import maya.cmds as mc
import re
import os




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
    permitted_render_shader_type = ["aiStandard"]

    if shadEngineList == "all":
        shadEngineList = mc.ls(type = "shadingEngine")
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
                
                
           

