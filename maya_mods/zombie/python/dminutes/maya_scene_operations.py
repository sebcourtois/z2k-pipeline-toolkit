import pymel.core as pc
import maya.cmds as mc
import os

#0 as Maya CC, and 1 as OSD Uniform, 2 OSD adaptive
def setSubdivPref(i_inSubDiv=0):
    attrValue = i_inSubDiv
    if attrValue == 2:
        attrValue = 3
    elif attrValue == 1:
        attrValue = 2

    meshes = pc.ls(type='mesh', noIntermediate=True)
    for mesh in meshes:
        useGlobal = pc.getAttr('{0}.useGlobalSmoothDrawType'.format(mesh.name()))
        if useGlobal:
            pc.setAttr('{0}.smoothDrawType'.format(mesh.name()), attrValue)

    pc.polyOptions(newPolymesh=True, smoothDrawType=i_inSubDiv)

def getSceneContent(o_inSceneManager):
    sceneContent = []

    #Collect references
    refs = pc.listReferences(namespaces=True)
    for ref in refs:
        ns = ref[0]
        sceneContent.append({'name':'_'.join(ns.split("_")[:-1]), 'path':ref[1]})

    return sceneContent

def createImgPlane():
    IMGP = None

    IMGPs = pc.ls("cam_animatic:assetShape->imgPlane_animatic*")
    if len(IMGPs) > 0:
        IMGP = IMGPs[0]

    if IMGP != None:
        cam_animatic = pc.ls("cam_animatic:*")
        if len(cam_animatic) > 0:
            return (IMGP, cam_animatic[0])
        else:
            pc.delete(IMGP)

    # - Remove previous Animatic Camera
    cam_animatic = pc.ls("cam_animatic:*")
    if len(cam_animatic) > 0:
        pc.delete(cam_animatic)

    # - Create new Animatic Camera
    if not pc.namespace(exists='cam_animatic'):
        pc.namespace(addNamespace='cam_animatic')

    cam_animatic = pc.camera( name= 'cam_animatic:asset', aspectRatio=1.77, displayFilmGate=True )
    cam_animatic[0].rename('cam_animatic:asset')
    pc.setAttr( cam_animatic[1].name() +'.visibility', 0 )
    #mc.parent( CAM_Animatic[0], grpDict['GD_ROOT'] )

    IMGP = pc.imagePlane(camera = cam_animatic[1], showInAllViews=False, name="imgPlane_animatic")
    IMGP[1].rename("imgPlane_animatic")

    #SET DE L'IMAGE PLANE
    pc.setAttr(IMGP[1].name()+".type",2)
    pc.setAttr(IMGP[1].name()+".fit",1)
    pc.setAttr(IMGP[1].name()+".useFrameExtension",1)
    pc.setAttr(IMGP[1].name()+".frameOffset",-100)
    pc.setAttr(IMGP[1].name()+".frameIn",101)
    pc.setAttr(IMGP[1].name()+".frameOut",1000)
    pc.setAttr(cam_animatic[1] +".displayFilmGate", 1)
    pc.setAttr(cam_animatic[1] +".displayGateMask", 1)
    pc.setAttr(cam_animatic[1] +".overscan", 1.4)
    pc.setAttr(cam_animatic[1] +".displaySafeTitle", 1)
    pc.setAttr(cam_animatic[1] +".displaySafeAction", 1)
    pc.setAttr(cam_animatic[1] +".displayGateMaskColor", [0,0,0])

    return (IMGP[1], cam_animatic[0])

def importAsset(s_inPath, s_inNS='', b_inRef=True):
    importedAsset = None
    if b_inRef:
        importedAsset = pc.system.createReference(s_inPath, namespace=s_inNS)
    else:
        importedAsset = pc.system.importFile(s_inPath, namespace=s_inNS)

def removeAsset(s_inPath):
    mc.file(s_inPath, removeReference=True )

def getAssetRoot(s_inNS):
    assetRoot = None
    deprecatedMessage = 'Asset root name is obsolete ({0})'

    #try with "asset", this should be the right way
    roots = pc.ls('{0}:asset'.format(s_inNS))
    if len(roots) > 0:
        assetRoot = roots[0]
    else:
        #try with NS:NS, for 'old' assets
        roots = pc.ls('{0}:{0}'.format(s_inNS))
        if len(roots) > 0:
            assetRoot = roots[0]
            pc.warning(deprecatedMessage.format(assetRoot.name()))
        else:
            #try with NS:NS except '_default' if found, for 'older' assets
            oldRootName = '{0}:{1}'.format(s_inNS, s_inNS.replace('_default', ''))
            roots = pc.ls(oldRootName)
            if len(roots) > 0:
                assetRoot = roots[0]
                pc.warning(deprecatedMessage.format(assetRoot.name()))
            else:
                roots = pc.ls('{0}:{1}'.format(s_inNS, s_inNS.replace('Ref', '')))
                if len(roots) > 0:
                    assetRoot = roots[0]
                    pc.warning(deprecatedMessage.format(assetRoot.name()))
                else:
                    #try with NS:NS except '_default' if found, for 'older' assets
                    oldRootName = '{0}:{1}'.format(s_inNS, s_inNS.replace('_default', '').replace('Ref', ''))
                    roots = pc.ls(oldRootName)
                    if len(roots) > 0:
                        assetRoot = roots[0]
                        pc.warning(deprecatedMessage.format(assetRoot.name()))

    return assetRoot

def getRoot(o_inObj):
    ns = o_inObj.namespace()
    obj = o_inObj
    objParent = obj.getParent()
    while(objParent != None and objParent.namespace() == ns):
        obj = objParent
        objParent = obj.getParent()

    return obj

def reArrangeAssets():
    #this is the template, it lacks grp_prop, grp_crowd, grp_vehicle, grp_fx, grp_light (and eventually grp_extra_rig, grp_trash)
    structure = {
        'cam':'grp_camera',
        'chr':'grp_character',
        'set':'grp_set'
    }

    #Collect references
    refs = pc.listReferences(namespaces=True)

    for ref in refs:
        ns = ref[0]
        nsPrefix = ns.split('_')[0]
        for structKey in structure:
            structParent = structure[structKey]
            if structKey == nsPrefix:
                #Ok, we can rearrange this !
                root = getAssetRoot(ns)
                if root == None:
                    pc.warning('Can"t find root of asset with namespace {0}'.format(ns))
                    continue
                rootParent = root.getParent()
                if rootParent == None or rootParent.name() != structParent:
                    pc.parent(root, structParent)

    #We could also have local cameras (cam_animatic and/or cam_sq####_sh####)
    cams = pc.ls('cam_*:*', type='camera')
    for cam in cams:
        #print "cam " + str(cam)
        camRoot = getRoot(cam)
        #print "camRoot " + str(camRoot)
        camParent = camRoot.getParent()
        if camParent == None or camParent.name() != structure['cam']:
            #print camRoot, structure['cam']
            pc.parent(camRoot, structure['cam'])

#GLOBALS METHODS
def canDo(s_inCommand, s_inTask):
    cmd = COMMANDS.get(s_inCommand)
    if cmd != None:
        return s_inTask in cmd

    return None

def do(s_inCommand, s_inTask, o_inSceneManager):
    cmd = COMMANDS.get(s_inCommand)
    if cmd == None:
        pc.error('Command "{0}" does not exists !'.format(s_inCommand))

    cmdCallable = cmd.get(s_inTask)
    if cmdCallable == None:
        pc.error('Process "{0}" does not exists for command "{1}" !'.format(s_inTask, s_inCommand))

    cmdBaseCallable = cmd.get('BASE')
    if cmdBaseCallable != None:
        cmdBaseCallable(o_inSceneManager)

    cmdCallable(o_inSceneManager)

#Creates
def create_scene_base(o_inSceneManager):
    mc.file(force=True, new=True)

    #Import scene structure
    template_path = o_inSceneManager.context['damProject'].getPath('template', 'project')
    strucure_path = os.path.join(template_path, "{0}_layout_tree.ma".format(o_inSceneManager.context['entity']['type'].lower()))
    #strucure_path = os.environ['ZOMBI_TOOL_PATH'] + "\\template\\{0}_layout_tree.ma".format(o_inSceneManager.context['entity']['type'].lower())

    if os.path.isfile(strucure_path):
        mc.file(strucure_path, i=True, rpr='')
    else:
        pc.warning("Base file structure not found for entity type : {0}".format(entity['type']))

    print 'base creation done ! ({0})'.format(o_inSceneManager.context)

def create_previz_scene(o_inSceneManager):
    o_inSceneManager.updateScene()

    init_scene_base(o_inSceneManager)
    init_previz_scene(o_inSceneManager)

    reArrangeAssets()

    #lock previz, save v001 in private, here ?
    privFile = o_inSceneManager.edit(onBase=True)

    if privFile != None:
        #save the created file on the private
        pc.saveAs(privFile.absPath())

        print 'previz creation done ! ({0})'.format(o_inSceneManager)
    else:
        print 'previz creation failed to Edit and save !'

#Inits
def init_shot_constants(o_inSceneManager):
    start = 101
    duration = o_inSceneManager.context['entity']['sg_cut_out'] - o_inSceneManager.context['entity']['sg_cut_in']

    pc.playbackOptions(edit=True, minTime=start)
    pc.playbackOptions(edit=True, animationStartTime=start)
    pc.playbackOptions(edit=True, maxTime=start + duration)
    pc.playbackOptions(edit=True, animationEndTime=start + duration)

def init_scene_base(o_inSceneManager):
    #Set units
    angle = 'degree'
    linear = 'centimeter'
    time='film'
    pc.currentUnit(angle=angle, linear=linear, time=time)

    #color management
    pc.colorManagementPrefs(edit=True, cmEnabled=False)

    #Subdiv
    setSubdivPref(0)

    #Swatches size
    mc.optionVar(iv=('maxImageSizeForSwatchGen', 1000))

    #Legacy Viewport textures
    mc.displayPref(maxTextureResolution=1024)

    #Viewport 2.0 textures
    mc.setAttr("hardwareRenderingGlobals.enableTextureMaxRes", 1)
    mc.setAttr("hardwareRenderingGlobals.textureMaxResolution", 1024)

    #entity specific initialisation
    if o_inSceneManager.context['entity']['type'] == 'Shot':
        init_shot_constants(o_inSceneManager)

    print 'base initialization done ! ({0})'.format(o_inSceneManager.context)

def init_previz_scene(o_inSceneManager):
    # - Create imagePlane
    IMGP = createImgPlane()

    # --- Set Viewport 2.0 AO default Value
    pc.setAttr( 'hardwareRenderingGlobals.ssaoAmount', 0.3)
    pc.setAttr( 'hardwareRenderingGlobals.ssaoRadius', 8 )
    pc.setAttr( 'hardwareRenderingGlobals.ssaoFilterRadius', 8 )
    pc.setAttr( 'hardwareRenderingGlobals.ssaoSamples', 16 )

    # Set Viewport
    pc.mel.eval( 'setNamedPanelLayout("Four View")' )
    pc.mel.eval( 'ThreeRightSplitViewArrangement' )

    #Image plane
    sidePanel = mc.getPanel( withLabel= 'Side View' )
    pc.modelPanel( sidePanel, edit= True, camera= IMGP[1])
    #Camera
    perspPanel = mc.getPanel( withLabel= 'Persp View' )
    pc.modelPanel( perspPanel, edit= True, camera= 'persp' )
    #Work view
    workPanel = mc.getPanel( withLabel= 'Top View' )
    pc.modelPanel( workPanel, edit= True, camera= 'persp' )

    pc.modelEditor( sidePanel, edit= True, allObjects= 0, imagePlane= True, grid= False )

    #Import camera  "X:\asset\cam\cam_shot_default\cam_shot_default.ma"
    
    camDefaultPath = o_inSceneManager.context['damProject'].getPath('public', 'camera', 'scene', tokens={'name':'cam_shot_default'})

    camName = 'cam_{0}'.format(o_inSceneManager.context['entity']['code'])

    #remove any other shot camera
    otherCams = pc.ls('cam_sq*sh*:*', type='camera')
    for otherCam in otherCams:
        if not camName in otherCam.namespace():
            otherRoot = getRoot(otherCam)
            pc.delete(otherRoot)

    camObjs = pc.ls('{0}:*'.format(camName), type='camera')
    if len(camObjs) == 0:
        if os.path.isfile(camDefaultPath):
            importAsset(camDefaultPath, camName, False)
            camObjs = pc.ls('{0}:*'.format(camName), type='camera')
        else:
            pc.warning('Default camera file cannot be found ({0})'.format(camDefaultPath))

    if len(camObjs) > 0:
        perspPanel = mc.getPanel( withLabel= 'Persp View' )
        pc.modelPanel( perspPanel, edit= True, camera=camObjs[0])
    else:
        pc.warning("Cannot find the shot camera {0} !!".format(camName))

    #image plane "Y:\shot\...\00_data\sqXXXX_shXXXXa_animatic.mov"
    imgPlanePath = o_inSceneManager.getPath(o_inSceneManager.context['entity'], 'animatic_capture')
    if os.path.isfile(imgPlanePath):
        IMGP = createImgPlane()
        pc.imagePlane(IMGP[0], edit=True, fileName=imgPlanePath)
        #IMGP[0].fileName(imgPlanePath)
    else:
        pc.warning('Image plane file cannot be found ({0})'.format(imgPlanePath))

    #son "Y:\shot\...\00_data\sqXXXX_shXXXXa_sound.wav"
    soundPath = o_inSceneManager.getPath(o_inSceneManager.context['entity'], 'animatic_sound')
    if os.path.isfile(soundPath):
        # --- Import Sound
        # - Remove previous
        pc.runtime.DeleteAllSounds()

        # - Import current shot Sound
        audio_shot = pc.sound( offset=101, file= soundPath, name = 'audio')

        # - Show Sound in Timeline
        aPlayBackSliderPython = pc.mel.eval('$tmpVar=$gPlayBackSlider')
        pc.timeControl( aPlayBackSliderPython, e=True, sound=audio_shot, displaySound=True )

    else:
        pc.warning('Sound file cannot be found ({0})'.format(soundPath))

    reArrangeAssets()
    print 'previz initialization done ! ({0})'.format(o_inSceneManager.context)

COMMANDS = {
    'create':{
        'BASE':create_scene_base,
        'previz 3D':create_previz_scene
    },
    'init':{
        'BASE':init_scene_base,
        'previz 3D':init_previz_scene
    }
}