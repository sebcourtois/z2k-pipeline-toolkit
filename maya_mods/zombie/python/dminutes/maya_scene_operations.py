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
    return []

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
    strucure_path = os.environ['ZOMBI_TOOL_PATH'] + "\\template\\{0}_layout_tree.ma".format(o_inSceneManager.context['entity']['type'].lower())

    if os.path.isfile(strucure_path):
        mc.file(strucure_path, i=True, rpr='')
    else:
        pc.warning("Base file structure not found for entity type : {0}".format(entity['type']))

    print 'base creation done ! ({0})'.format(o_inSceneManager.context)

def create_previz_scene(o_inSceneManager):
    sceneInfo = o_inSceneManager.getAssetsInfo()

    init_scene_base(o_inSceneManager)
    init_previz_scene(o_inSceneManager)
    print 'previz creation done ! ({0})'.format(o_inSceneManager)

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

    #entity specific initialisation
    if o_inSceneManager.context['entity']['type'] == 'Shot':
        init_shot_constants(o_inSceneManager)

    print 'base initialization done ! ({0})'.format(o_inSceneManager.context)

def init_previz_scene(o_inSceneManager):
    # - Remove previous Animatic Camera
    cam_animatic = pc.ls("cam_animatic*")
    if len(cam_animatic) > 0:
        pc.delete(cam_animatic)

    # - Create new Animatic Camera
    cam_animatic = pc.camera( name= 'cam_animatic', aspectRatio=1.77, displayFilmGate=True )
    cam_animatic[0].rename('cam_animatic')
    pc.setAttr( cam_animatic[1].name() +'.visibility', 0 )
    #mc.parent( CAM_Animatic[0], grpDict['GD_ROOT'] )

    # - Create imagePlane
    IMGP = pc.imagePlane(camera = cam_animatic[1], showInAllViews=False )

    #SET DE L'IMAGE PLANE
    pc.setAttr(IMGP[1].name()+".type",2)
    #IMGP[1].fileName( Video_Path )
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
    pc.modelPanel( sidePanel, edit= True, camera= 'side' )
    #Camera
    perspPanel = mc.getPanel( withLabel= 'Persp View' )
    pc.modelPanel( perspPanel, edit= True, camera= 'top' )
    #Work view
    workPanel = mc.getPanel( withLabel= 'Top View' )
    pc.modelPanel( workPanel, edit= True, camera= 'persp' )

    pc.modelEditor( sidePanel, edit= True, allObjects= 0, imagePlane= True, grid= False )

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