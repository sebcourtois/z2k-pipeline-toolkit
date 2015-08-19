import os
import pymel.core as pc

from pytd.util.fsutils import pathJoin

from dminutes import sceneManager
reload(sceneManager)

from davos.core import damproject
reload(damproject)

from davos_maya.core import mrclibrary  
#reload(mrclibrary)
MrcLibrary = mrclibrary.MrcLibrary

import dminutes.maya_scene_operations as mop
reload(mop)

SCENE_MANAGER = None

SG = None

CATEG_ITEMS = {}
TASKS = {}
VERSIONS = {}

ACTION_BUTTONS = []

def refreshOptionMenu(s_inName, a_Items):
    items = pc.optionMenu(s_inName, query=True, itemListShort=True)
    for item in items:
        pc.deleteUI(item)

    for item in a_Items:
        pc.menuItem(s_inName + "_" + item, label= item, parent=s_inName)

def sceneManagerUI():
    global SCENE_MANAGER
    global SG

    SCENE_MANAGER = sceneManager.SceneManager()
    SG = SCENE_MANAGER.context['damProject']._shotgundb

    if (pc.window('sceneManagerUI', q=True, exists=True)):
        pc.deleteUI('sceneManagerUI')

    dirname, filename = os.path.split(os.path.abspath(__file__))
    ui = pc.loadUI(uiFile=dirname + "/UI/sceneManagerUI.ui")
    connectCallbacks()

    initialize()
    pc.showWindow(ui)
    updateButtons()

def initialize(d_inContext=None):
    #User info
    pc.textField('sm_user_bt', edit=True, text=SG.currentUser['name'])
    pc.textField('sm_project_bt', edit=True, text=SCENE_MANAGER.projectname)

    steps = [astep['name'] for astep in SG.currentUser['sg_allowedsteps']]
    refreshOptionMenu('sm_step_dd', steps)

    if SG.currentUser['sg_currentstep'] != None and SG.currentUser['sg_currentstep']['name'] in steps:
        pc.optionMenu("sm_step_dd", edit=True, value=SG.currentUser['sg_currentstep']['name'])

    if d_inContext != None:
        SCENE_MANAGER.init(d_inContext)

    doStepChanged()

def updateButtons():
    for buttonName in ACTION_BUTTONS:
        prefix, action, suffix = buttonName.split('_')
        enable = False if not 'task' in SCENE_MANAGER.context else mop.canDo(action, SCENE_MANAGER.context['task']['content']) == True
        pc.control(buttonName, edit=True, enable=enable)

#Callbacks management

def connectCallbacks():
    pc.button('sm_disconnect_bt', edit=True, c=doDisconnect)
    pc.optionMenu("sm_step_dd", edit=True, cc=doStepChanged)
    pc.optionMenu('sm_categ_dd', edit=True, cc=doCategChanged)
    pc.optionMenu('sm_seq_dd', edit=True, cc=doCategChanged)
    pc.optionMenu('sm_shot_dd', edit=True, cc=doEntityChanged)
    pc.optionMenu('sm_asset_dd', edit=True, cc=doEntityChanged)
    pc.optionMenu('sm_task_dd', edit=True, cc=doTaskChanged)
    pc.textScrollList('sm_versions_lb', edit=True, sc=doVersionChanged)

    #buttons
    pc.button('sm_refreshScene_bt', edit=True, c=doRefreshSceneInfo)
    pc.button('sm_upscene_bt', edit=True, c=doUpdateScene)
    pc.button('sm_updb_bt', edit=True, c=doUpdateShotgun)

    #action buttons
    buttonName = 'sm_init_bt'
    pc.button(buttonName, edit=True, c=doInit)
    ACTION_BUTTONS.append(buttonName)

    buttonName = 'sm_create_bt'
    pc.button(buttonName, edit=True, c=doCreate)
    ACTION_BUTTONS.append(buttonName)

def doDisconnect(*args):
    SG.logoutUser()
    sceneManagerUI()

def doStepChanged(*args):
    step = pc.optionMenu("sm_step_dd", query=True, value=True)
    SCENE_MANAGER.context['step'] = None

    for allowedStep in SG.currentUser['sg_allowedsteps']:
        if allowedStep['name'] == step:
            SCENE_MANAGER.context['step'] = allowedStep
            SG.updateStep(allowedStep)
            break
    
    if SCENE_MANAGER.context['step'] == None:

        pc.error('Cannot get entity type from step {0} !'.format(step))

    refreshStep()

def doCategChanged(*args):
    categCtrlName = 'sm_seq_dd' if SCENE_MANAGER.context['step']['entity_type'] == 'Shot' else 'sm_categ_dd'
    entityCtrlName = 'sm_shot_dd' if SCENE_MANAGER.context['step']['entity_type'] == 'Shot' else 'sm_asset_dd'

    categ = pc.optionMenu(categCtrlName, query=True, value=True)
    SCENE_MANAGER.context['categ'] = categ

    refreshOptionMenu(entityCtrlName, sorted(CATEG_ITEMS[categ].keys()))

    doEntityChanged()

def doEntityChanged(*args):
    global TASKS
    entityCtrlName = 'sm_shot_dd' if SCENE_MANAGER.context['step']['entity_type'] == 'Shot' else 'sm_asset_dd'

    entityName = pc.optionMenu(entityCtrlName, query=True, value=True)
    SCENE_MANAGER.context['entity'] = CATEG_ITEMS[SCENE_MANAGER.context['categ']][entityName]

    #get tasks on entity
    TASKS = {}
    tasks = SCENE_MANAGER.getTasks()

    for task in tasks:
        TASKS[task['content']] = task

    refreshOptionMenu('sm_task_dd', sorted(TASKS.keys()))

    doTaskChanged()

def doTaskChanged(*args):
    global VERSIONS
    taskName = pc.optionMenu('sm_task_dd', query=True, value=True)
    SCENE_MANAGER.context['task'] = TASKS[taskName]

    #get Versions on task
    VERSIONS = {}
    versions = SCENE_MANAGER.getVersions()
    
    for version in versions:
        VERSIONS[version['code']] = version

    pc.textScrollList("sm_versions_lb", edit=True, removeAll=True)
    if len(versions) > 0:
        pc.textScrollList("sm_versions_lb", edit=True, append=sorted(VERSIONS.keys()))

    doVersionChanged()

    doRefreshSceneInfo()

def doVersionChanged(*args):
    updateButtons()
    #print pc.textScrollList("sm_versions_lb", query=True, selectItem=True)

def refreshStep(*args):
    global CATEG_ITEMS

    if SCENE_MANAGER.context['step']['entity_type'] == 'Shot':
        pc.control('sm_asset_chooser_grp', edit=True, visible=False)
        pc.control('sm_shot_chooser_grp', edit=True, visible=True)

        shots = SG.getShotsInfo()

        categ_names = []
        CATEG_ITEMS = {}
        for shot in shots:
            if shot['sg_sequence'] == None:
                pc.warning('entity {0} with category "None" will be ignored'.format(shot['code']))
                continue

            seqName = shot['sg_sequence']['name']
            if not seqName in CATEG_ITEMS:
                categ_names.append(seqName)
                CATEG_ITEMS[seqName] = {}

            CATEG_ITEMS[seqName][shot['code']] = shot

        refreshOptionMenu('sm_seq_dd', categ_names)
        doCategChanged()

    elif SCENE_MANAGER.context['step']['entity_type'] == 'Asset':
        pc.control('sm_asset_chooser_grp', edit=True, visible=True)
        pc.control('sm_shot_chooser_grp', edit=True, visible=False)

        assets = SG.getAssetsInfo()

        categ_names = []
        CATEG_ITEMS = {}
        for asset in assets:
            if asset['sg_asset_type'] == None:
                pc.warning('entity {0} with category "None" will be ignored'.format(asset['code']))
                continue

            if not asset['sg_asset_type'] in CATEG_ITEMS:
                categ_names.append(asset['sg_asset_type'])
                CATEG_ITEMS[asset['sg_asset_type']] = {}

            CATEG_ITEMS[asset['sg_asset_type']][asset['code']] = asset

        refreshOptionMenu('sm_categ_dd', categ_names)
        doCategChanged()

    else:
        pc.error('Unknown entity type {0} from step {1} !'.format(SCENE_MANAGER.context['entity_type'], step))

#buttons
def doRefreshSceneInfo(*args):
    assetsInfo = SCENE_MANAGER.getAssetsInfo()

    gridContent = ["Scene", "Shotgun"]

    pc.textScrollList("sm_sceneInfo_lb", edit=True, removeAll=True)
    pc.textScrollList("sm_sceneInfo_lb", edit=True, append=" {0:<50}| {1:<50}".format("SCENE", "DATABASE"))

    for assetInfo in assetsInfo:
        pc.textScrollList("sm_sceneInfo_lb", edit=True, append=" {0:<50}| {1:<50}".format(assetInfo['localinfo'], assetInfo['dbinfo']))

def doUpdateScene(*args):
    pass

def doUpdateShotgun(*args):
    pass

#action buttons
def doInit(*args):
    SCENE_MANAGER.do('init')

def doCreate(*args):
    SCENE_MANAGER.do('create')