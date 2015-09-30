#------------------------------------------------------------------
# UI handling for /UI/sceneManagerUIB.ui QT designer file (z2k-pipeline-toolkit\maya_mods\zombie\python\dminutes\UI\sceneManagerUIB.ui)
#------------------------------------------------------------------

import os
import pymel.core as pc

from pytd.util.fsutils import pathJoin

from dminutes import sceneManager
reload(sceneManager)

from davos.core import damproject
reload(damproject)

from davos_maya.core import mrclibrary  
MrcLibrary = mrclibrary.MrcLibrary

import dminutes.maya_scene_operations as mop
reload(mop)

"""Global instance of sceneManager Class""" 
SCENE_MANAGER = None

"""Global instance of shotgunengine Class""" 
SG = None

"""Various caches for UI lists""" 
CATEG_ITEMS = {}
TASKS = {}
VERSIONS = {}

ACTION_BUTTONS = []

#------------------------------------------------------------------
#               Main UI Creation/Initialization
#------------------------------------------------------------------

def sceneManagerUI():
    """Main UI Creator"""
    global SCENE_MANAGER
    global SG

    SCENE_MANAGER = sceneManager.SceneManager()
    SG = SCENE_MANAGER.context['damProject']._shotgundb

    if (pc.window('sceneManagerUI', q=True, exists=True)):
        pc.deleteUI('sceneManagerUI')

    dirname, filename = os.path.split(os.path.abspath(__file__))
    ui = pc.loadUI(uiFile=dirname + "/UI/sceneManagerUIB.ui")
    connectCallbacks()

    initialize()
    pc.showWindow(ui)
    updateButtons()

def initialize(d_inContext=None):
    """Initialize default values (Operator AllowedSteps and CurrentStep...), hide forbidden buttons"""
    #User info
    pc.textField('sm_user_bt', edit=True, text=SG.currentUser['name'])
    pc.textField('sm_project_bt', edit=True, text=SCENE_MANAGER.projectname)

    steps = [astep['name'] for astep in SG.currentUser['sg_allowedsteps']]
    refreshOptionMenu('sm_step_dd', steps)

    if SG.currentUser['sg_currentstep'] != None and SG.currentUser['sg_currentstep']['name'] in steps:
        pc.optionMenu("sm_step_dd", edit=True, value=SG.currentUser['sg_currentstep']['name'])

    if d_inContext != None:
        SCENE_MANAGER.init(d_inContext)

    #Hide some controls
    pc.control("fileStatusGroup", edit=True, visible=False)
    pc.control("sm_createFolder_bt", edit=True, visible=False)
    pc.control("sm_edit_bt", edit=True, visible=False)

    doStepChanged()

    setContextUI()

def updateButtons():
    """Update buttons availability from maya_scene_operations commands dictionary"""
    for buttonName in ACTION_BUTTONS:
        prefix, action, suffix = buttonName.split('_')
        enable = False if not 'task' in SCENE_MANAGER.context else mop.canDo(action, SCENE_MANAGER.context['task']['content']) == True
        pc.control(buttonName, edit=True, enable=enable)

    refreshContextUI()

def refreshContextUI():
    """Update buttons availability from contexts (scene Context / UI Context)"""
    contextMatches = SCENE_MANAGER.refreshSceneContext()

    pc.control('sm_switchContext_bt', edit=True, enable= not contextMatches)

    pc.control('sm_capture_bt', edit=True, enable=contextMatches)
    pc.control('sm_saveWip_bt', edit=True, enable=contextMatches)
    pc.control('sm_publish_bt', edit=True, enable=contextMatches)

def setContextUI():
    """Initialize UI from scene"""
    SCENE_MANAGER.refreshSceneContext()
    context = SCENE_MANAGER.getContextFromDavosData()

    if context != None:
        #print context
        somethingChanged = False

        somethingChanged |= setOption("sm_step_dd", context["step"])

        if "shot" in context:
            somethingChanged |= setOption("sm_seq_dd", context["seq"])
            somethingChanged |= setOption("sm_shot_dd", context["shot"])

        if not somethingChanged:
            refreshContextUI()

        return True

    return False

#------------------------------------------------------------------
#               UI Refresh helpers
#------------------------------------------------------------------

def setOption(s_inName, s_inValue):
    """Change a value in an option menu as if option was selected manually"""
    changed = False
    items = pc.optionMenu(s_inName, query=True, itemListShort=True)
    #print items
    if not s_inName + "_" + s_inValue.replace(" ", "_") in items:
        pc.error("Value does not exists or is not available for this user {0} ({1}) !!".format(s_inValue, s_inName))

    if pc.optionMenu(s_inName, query=True, value=True) != s_inValue:
        pc.optionMenu(s_inName, edit=True, value=s_inValue)
        changed = True
        if s_inName == 'sm_step_dd':
            doStepChanged()
        elif s_inName == 'sm_categ_dd' or s_inName == 'sm_seq_dd':
            doCategChanged()
        elif s_inName == 'sm_asset_dd' or s_inName == 'sm_shot_dd':
            doEntityChanged()
        elif s_inName == 'sm_task_dd':
            doTaskChanged()

    return changed

def refreshOptionMenu(s_inName, a_Items):
    """Change the items in an option menu (In Maya we have to delete old uiItems then create and associate new ones...)"""
    items = pc.optionMenu(s_inName, query=True, itemListShort=True)
    for item in items:
        pc.deleteUI(item)

    for item in a_Items:
        pc.menuItem(s_inName + "_" + item, label= item, parent=s_inName)

def refreshStep(*args):
    """Call when the step is changed (this could be included in 'doStepChanged')"""
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
        doCategChanged(*args)

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
        doCategChanged(*args)

    else:
        pc.error('Unknown entity type {0} from step {1} !'.format(SCENE_MANAGER.context['entity_type'], step))

#------------------------------------------------------------------
#               Button functions
#------------------------------------------------------------------

def connectCallbacks():
    """Connect all ui items events to functions declared in this file"""
    pc.button('sm_disconnect_bt', edit=True, c=doDisconnect)
    pc.optionMenu("sm_step_dd", edit=True, cc=doStepChanged)
    pc.optionMenu('sm_categ_dd', edit=True, cc=doCategChanged)
    pc.optionMenu('sm_seq_dd', edit=True, cc=doCategChanged)
    pc.optionMenu('sm_shot_dd', edit=True, cc=doEntityChanged)
    pc.optionMenu('sm_asset_dd', edit=True, cc=doEntityChanged)
    pc.optionMenu('sm_task_dd', edit=True, cc=doTaskChanged)
    pc.textScrollList('sm_versions_lb', edit=True, sc=doVersionChanged)

    #buttons
    pc.button('sm_detect_bt', edit=True, c=doDetect)

    pc.button('sm_refreshScene_bt', edit=True, c=doRefreshSceneInfo)
    pc.button('sm_upscene_bt', edit=True, c=doUpdateScene)
    pc.button('sm_updb_bt', edit=True, c=doUpdateShotgun)
    pc.button('sm_capture_bt', edit=True, c=doCapture)
    pc.button('sm_saveWip_bt', edit=True, c=doSaveWip)

    pc.button('sm_switchContext_bt', edit=True, c=doSwitchContext)

    #davos
    pc.button('sm_unlock_bt', edit=True, c=doUnlock)
    pc.button('sm_edit_bt', edit=True, c=doEdit)
    pc.button('sm_publish_bt', edit=True, c=doPublish)
    pc.button('sm_createFolder_bt', edit=True, c=doCreateFolder)

    #action buttons
    buttonName = 'sm_init_bt'
    pc.button(buttonName, edit=True, c=doInit)
    ACTION_BUTTONS.append(buttonName)

    pc.button('sm_pouet_bt', edit=True, c=doPouet)
    #buttonName = 'sm_create_bt'
    #pc.button(buttonName, edit=True, c=doCreate)
    #ACTION_BUTTONS.append(buttonName)

def doDisconnect(*args):
    SG.logoutUser()
    sceneManagerUI()

def doStepChanged(*args):
    #print args
    step = pc.optionMenu("sm_step_dd", query=True, value=True)
    SCENE_MANAGER.context['step'] = None

    for allowedStep in SG.currentUser['sg_allowedsteps']:
        if allowedStep['name'] == step:
            SCENE_MANAGER.context['step'] = allowedStep
            SG.updateStep(allowedStep)
            break
    
    if SCENE_MANAGER.context['step'] == None:
        pc.error('Cannot get entity type from step {0} !'.format(step))

    refreshStep(*args)

def doCategChanged(*args):
    categCtrlName = 'sm_seq_dd' if SCENE_MANAGER.context['step']['entity_type'] == 'Shot' else 'sm_categ_dd'
    entityCtrlName = 'sm_shot_dd' if SCENE_MANAGER.context['step']['entity_type'] == 'Shot' else 'sm_asset_dd'

    categ = pc.optionMenu(categCtrlName, query=True, value=True)
    SCENE_MANAGER.context['categ'] = categ

    refreshOptionMenu(entityCtrlName, sorted(CATEG_ITEMS[categ].keys()))

    doEntityChanged(*args)

#Entity is a Shot or an Asset
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

    doTaskChanged(*args)

def doTaskChanged(*args):
    global VERSIONS
    taskName = pc.optionMenu('sm_task_dd', query=True, value=True)
    SCENE_MANAGER.context['task'] = TASKS[taskName]

    #get Versions on task
    VERSIONS = {}
    versions = SCENE_MANAGER.getVersions()
    
    for version in versions:
        VERSIONS[version['code']] = version
        SCENE_MANAGER.context['version'] = version

    pc.textScrollList("sm_versions_lb", edit=True, removeAll=True)
    if len(versions) > 0:
        pc.textScrollList("sm_versions_lb", edit=True, append=sorted(VERSIONS.keys()))

    doRefreshSceneInfo(*args)

    doRefreshFileStatus()

    doVersionChanged(*args)

def doVersionChanged(*args):
    """I don't use versions at all in the end..."""
    updateButtons()
    #print pc.textScrollList("sm_versions_lb", query=True, selectItem=True)

def doRefreshFileStatus(*args):
    """File status is still tracked but the control that displays it is hidden (forbidden ^^)"""
    SCENE_MANAGER.refreshStatus()

    pc.button('sm_unlock_bt', edit=True, enable=False)
    statusText = "Unlocked"

    if SCENE_MANAGER.context['lock'] != "":
        if SCENE_MANAGER.context['lock'] == SG.currentUser['login']:
            statusText = "Locked by Me"
            pc.button('sm_unlock_bt', edit=True, enable=True)
        else:
            statusText = "Locked by {0}".format(SCENE_MANAGER.context['lock'])

    pc.textField("sm_lock_tb", edit=True, text=statusText)

    editable = SCENE_MANAGER.isEditable()

    pc.button('sm_edit_bt', edit=True, enable=editable)
    pc.button('sm_publish_bt', edit=True, enable=editable)
    pc.button('sm_capture_bt', edit=True, enable=editable)
    pc.button('sm_saveWip_bt', edit=True, enable=editable)

#buttons
def doDetect(*args):
    setContextUI()

def doRefreshSceneInfo(*args):
    """Displays the comparison of shotgun and active scene Assets"""
    assetsInfo = SCENE_MANAGER.getAssetsInfo()

    gridContent = ["Scene", "Shotgun"]

    lengths = [20,20]
    for assetInfo in assetsInfo:
        if len(assetInfo['localinfo']) > lengths[0]:
            lengths[0] = len(assetInfo['localinfo'])

        if len(assetInfo['dbinfo']) > lengths[1]:
            lengths[1] = len(assetInfo['dbinfo'])    

    formatting = " {0:<"+str(lengths[0])+"}| {1:<"+str(lengths[1])+"}"

    pc.textScrollList("sm_sceneInfo_lb", edit=True, removeAll=True)
    pc.textScrollList("sm_sceneInfo_lb", edit=True, append=formatting.format("SCENE", "DATABASE"))

    for assetInfo in assetsInfo:
        pc.textScrollList("sm_sceneInfo_lb", edit=True, append=formatting.format(assetInfo['localinfo'], assetInfo['dbinfo']))

def doUnlock(*args):
    """Simply unlocks current entry, but button is hidden (forbidden)"""
    entry = SCENE_MANAGER.getEntry()

    if entry == None:
        pc.error("Cannot get entry form context {0}".format(SCENE_MANAGER.context))

    entry.setLocked(False)
    doRefreshFileStatus()

def doUpdateScene(*args):
    """Matches scene Assets with Shotgun Assets"""
    addOnly = pc.checkBox("sm_addOnly_bt", query=True, value=True)
    SCENE_MANAGER.updateScene(addOnly)
    doRefreshSceneInfo(args)

def doUpdateShotgun(*args):
    """Matches Shotgun Assets with scene Assets (NOT IMPLEMENTED)"""
    addOnly = pc.checkBox("sm_addOnly_bt", query=True, value=True)
    SCENE_MANAGER.updateShotgun(addOnly)
    doRefreshSceneInfo(args)

def doCapture(*args):
    if SCENE_MANAGER.assert_isEditable():
        b_increment = pc.checkBox('sm_increment_bt', query=True, value=True)
        SCENE_MANAGER.capture(b_increment)
        doRefreshSceneInfo(args)
    else:
        doDetect(args)

def doSaveWip(*args):
    if SCENE_MANAGER.assert_isEditable():
        SCENE_MANAGER.saveIncrement()
    else:
        doDetect(args)

def doSwitchContext(*args):
    """Use the current scene for an edition on the entry currently showing in the UI (basically an edit, creating folders if needed)"""
    if SCENE_MANAGER.refreshSceneContext():
        pc.warning("Your context is already matching !!")
        return

    if not SCENE_MANAGER.isEditable() and SCENE_MANAGER.context["lock"] == "Error":
        #Maybe this is because folders does not exists ?
        SCENE_MANAGER.createFolder()
        doRefreshFileStatus()

    if not SCENE_MANAGER.isEditable():
        pc.warning("Your entity is locked by {0}".format(SCENE_MANAGER.context["lock"]))
        return

    if len(SCENE_MANAGER.getVersions()) == 0 or pc.confirmDialog(title="Entity override", message="Your entity already have published versions, are you sure you want to use current scene ?") == "Confirm":
        SCENE_MANAGER.edit(True)
        doTaskChanged()
    else:
        pc.warning("Switch context aborted !")

#davos
def doEdit(*args):
    """Associated button is hidden (forbidden)"""
    if SCENE_MANAGER.assert_isEditable():
        SCENE_MANAGER.edit(False)
        doTaskChanged()
    else:
        doDetect(args)

def doPublish(*args):
    if SCENE_MANAGER.assert_isEditable():
        SCENE_MANAGER.publish()
        doTaskChanged()
        #doRefreshFileStatus()
    else:
        doDetect(args)

def doCreateFolder(*args):
    """Associated button is hidden (forbidden)"""
    #For debug purposes (Cheers !!!)
    #print str(SCENE_MANAGER.context)
    SCENE_MANAGER.createFolder() 

#action buttons
def doInit(*args):
    """Button is named 'Shot Setup'"""
    SCENE_MANAGER.do('init')
    doRefreshSceneInfo()

def doCreate(*args):
    """Associated button is hidden (forbidden)"""
    SCENE_MANAGER.do('create')
    doRefreshSceneInfo()
    doRefreshFileStatus()

def doPouet(*args,**kwargs):
    """Best function ever"""
    print "pouet"
    for i,j in  SCENE_MANAGER.context.iteritems():
        print "    ",i,j