#------------------------------------------------------------------
# UI handling for /UI/sceneManagerUIB.ui QT designer file (z2k-pipeline-toolkit\maya_mods\zombie\python\dminutes\UI\sceneManagerUIB.ui)
#------------------------------------------------------------------

import os
import subprocess

import maya.cmds as cmds
import pymel.core
pc = pymel.core

from pytd.util.fsutils import pathResolve
from pytd.util.sysutils import inDevMode, timer
from pytd.util.logutils import logMsg
#from pytd.util.sysutils import getCaller
from pytd.util.qtutils import setWaitCursor

import dminutes.maya_scene_operations as mop
from dminutes import sceneManager

osp = os.path

"""Global instance of sceneManager Class"""
SCENE_MANAGER = None
SCENE_MANAGER_UI = 'sceneManagerDock'

"""Global instance of shotgunengine Class"""
SG = None

"""Various caches for UI lists"""
CATEG_ITEMS = {}
CURRENT_ENTITY_TASKS = {}
VERSIONS = {}

ACTION_BUTTONS = []
LIST_WIDGET = None
#------------------------------------------------------------------
#               Main UI Creation/Initialization
#------------------------------------------------------------------

def kill():

    global SCENE_MANAGER_UI

    if cmds.dockControl(SCENE_MANAGER_UI, q=True, exists=True):
        pc.deleteUI(SCENE_MANAGER_UI)
        return True

    return False

def saveDockState():
    pc.optionVar["Z2K_SM_dockState"] = cmds.dockControl(SCENE_MANAGER_UI, q=True, state=True)
    pc.optionVar["Z2K_SM_dockFloating"] = cmds.dockControl(SCENE_MANAGER_UI, q=True, floating=True)

def sceneManagerUI():
    """Main UI Creator"""
    global LIST_WIDGET

    states = dict()

    if cmds.dockControl(SCENE_MANAGER_UI, q=True, exists=True) and SCENE_MANAGER:
        cmds.dockControl(SCENE_MANAGER_UI, e=True, visible=True)
    else:
        kill()

        dirname, _ = osp.split(osp.abspath(__file__))
        ui = cmds.loadUI(uiFile=dirname + "/UI/sceneManagerUIC.ui")

        sListWdgName = cmds.textScrollList("sm_sceneInfo_lb", e=True,
                                           removeAll=True,
                                           font="fixedWidthFont",
                                           allowMultiSelection=True)
        LIST_WIDGET = pc.ui.toPySideObject(sListWdgName)

        sState = pc.optionVar.get("Z2K_SM_dockState")
        if sState:
            states.update(state=sState)
        states.update(floating=pc.optionVar.get("Z2K_SM_dockFloating", False))

        cmds.dockControl(SCENE_MANAGER_UI, area='left', content=ui,
                         allowedArea=['left'], retain=True,
                         label=cmds.window(ui, q=True, title=True),
                         closeCommand=saveDockState,
                         **states)

        connectCallbacks()

    initialize()
    refreshContextUI()

    if states:
        cmds.dockControl(SCENE_MANAGER_UI, e=True, **states)

    if not cmds.dockControl(SCENE_MANAGER_UI, q=True, floating=True):
        cmds.dockControl(SCENE_MANAGER_UI, e=True, r=True)

def initialize():
    """Initialize default values (Operator AllowedSteps and CurrentStep...), hide forbidden buttons"""

    global SCENE_MANAGER, SG

    if SCENE_MANAGER:
        del SCENE_MANAGER
    if SG:
        del SG

    SCENE_MANAGER = sceneManager.SceneManager()
    SG = SCENE_MANAGER.context['damProject']._shotgundb

    curSgUser = SG.currentUser
    userSgStep = curSgUser['sg_currentstep']

    #User info
    pc.textField('sm_user_bt', edit=True, text=curSgUser['name'])
    pc.textField('sm_project_bt', edit=True, text=SCENE_MANAGER.projectname)

    sStepCodes = list(step['code'] for step in curSgUser['sg_allowedsteps']
                                        if step['entity_type'] == 'Shot')
    refreshOptionMenu('sm_step_dd', sStepCodes)

    #print userSgStep
    if (userSgStep is not None) and (userSgStep['code'] in sStepCodes):
        pc.optionMenu("sm_step_dd", edit=True, value=userSgStep['code'])

    #Hide some controls
    pc.control("fileStatusGroup", edit=True, visible=False)
    pc.control("versionsGroup", edit=True, visible=False)
    pc.control("sm_createFolder_bt", edit=True, visible=False)
    pc.control("sm_edit_bt", edit=True, visible=False)
    pc.control("sm_addOnly_bt", edit=True, visible=False)
    pc.control("sm_project_bt", edit=True, visible=False)
    #pc.control("sm_disconnect_bt", edit=True, visible=False)
    if not inDevMode():
        pc.control("sm_pouet_bt", edit=True, visible=False)

    doStepChanged(updateStep=False)
    setContextUI()

def updateButtons():
    """Update buttons availability from maya_scene_operations commands dictionary"""
    for buttonName in ACTION_BUTTONS:
        _, action, _ = buttonName.split('_')
        enable = (False if not 'task' in SCENE_MANAGER.context
                  else mop.canDo(action, SCENE_MANAGER.context['task']['content']) == True)
        pc.control(buttonName, edit=True, enable=enable)

    refreshContextUI()

def refreshContextUI():
    """Update buttons availability from contexts (scene Context / UI Context)"""
    contextMatches = SCENE_MANAGER.refreshSceneContext()

    pc.control('sm_switchContext_bt', edit=True, enable=not contextMatches)

    pc.control('sm_capture_bt', edit=True, enable=contextMatches)
    pc.control('sm_saveWip_bt', edit=True, enable=contextMatches)
    pc.control('sm_publish_bt', edit=True, enable=contextMatches)
    pc.control('sm_upscene_bt', edit=True, enable=contextMatches)
    pc.control('sm_updb_bt', edit=True, enable=contextMatches)

    sStepName = SCENE_MANAGER.context["step"]["code"].lower()
    bEnabled = (sStepName != "previz 3d") and contextMatches
    pc.control('sm_editCam_bt', edit=True, enable=bEnabled)

    pc.checkBox('sm_imgPlane_chk', edit=True, value=mop.isImgPlaneVisible())
    pc.checkBox('sm_increment_chk', edit=True, value=pc.optionVar.get("Z2K_SM_increment", False))
    pc.checkBox('sm_sendToRv_chk', edit=True, value=pc.optionVar.get("Z2K_SM_sendToRv", False))

def setContextUI():
    """Initialize UI from scene"""
    SCENE_MANAGER.refreshSceneContext()
    context = SCENE_MANAGER.getContextFromDavosData()

    if context != None:
        #print context
        somethingChanged = False

        #print context["step"]
        somethingChanged |= setOption("sm_step_dd", context["step"], runEntityChanged=False)

        if "shot" in context:
            #print context["seq"], context["shot"]
            somethingChanged |= setOption("sm_seq_dd", context["seq"], runEntityChanged=False)
            somethingChanged |= setOption("sm_shot_dd", context["shot"], runEntityChanged=False)

        doEntityChanged()

        if not somethingChanged:
            refreshContextUI()

        return True

    doEntityChanged()

    return False


#------------------------------------------------------------------
#               UI Refresh helpers
#------------------------------------------------------------------

def setOption(s_inName, s_inValue, runEntityChanged=True):
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
            doStepChanged(updateStep=False, runEntityChanged=runEntityChanged)
        elif s_inName == 'sm_categ_dd' or s_inName == 'sm_seq_dd':
            doCategChanged(runEntityChanged=runEntityChanged)
        elif s_inName == 'sm_asset_dd' or s_inName == 'sm_shot_dd':
            if runEntityChanged:
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
        pc.menuItem(s_inName + "_" + item, label=item, parent=s_inName)

def refreshStep(*args, **kwargs):
    """Call when the step is changed (this could be included in 'doStepChanged')"""
    global CATEG_ITEMS

    sgStep = SCENE_MANAGER.context['step']
    if sgStep['entity_type'] == 'Shot':
        pc.control('sm_asset_chooser_grp', edit=True, visible=False)
        pc.control('sm_shot_chooser_grp', edit=True, visible=True)

        shots = SG.getShotsInfo()

        categ_names = []
        CATEG_ITEMS = {}
        for shot in shots:
            if shot['sg_sequence'] == None:
                pc.warning('entity {0} with category "None" will be ignored'
                           .format(shot['code']))
                continue

            seqName = shot['sg_sequence']['name']
            if seqName not in CATEG_ITEMS:
                categ_names.append(seqName)
                CATEG_ITEMS[seqName] = {}

            CATEG_ITEMS[seqName][shot['code']] = shot

        refreshOptionMenu('sm_seq_dd', categ_names)
        doCategChanged(*args, **kwargs)

    elif sgStep['entity_type'] == 'Asset':
        pc.control('sm_asset_chooser_grp', edit=True, visible=True)
        pc.control('sm_shot_chooser_grp', edit=True, visible=False)

        assets = SG.getAssetsInfo()

        categ_names = []
        CATEG_ITEMS = {}
        for asset in assets:
            if asset['sg_asset_type'] == None:
                pc.warning('entity {0} with category "None" will be ignored'
                           .format(asset['code']))
                continue

            if not asset['sg_asset_type'] in CATEG_ITEMS:
                categ_names.append(asset['sg_asset_type'])
                CATEG_ITEMS[asset['sg_asset_type']] = {}

            CATEG_ITEMS[asset['sg_asset_type']][asset['code']] = asset

        refreshOptionMenu('sm_categ_dd', categ_names)
        doCategChanged(*args, **kwargs)

    else:
        pc.error('Unknown entity type {0} from step {1} !'
                 .format(SCENE_MANAGER.context['entity_type'], sgStep))

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
    pc.button('sm_selectRefs_bt', edit=True, c=doSelectRefs)

    pc.button('sm_upscene_bt', edit=True, c=doUpdateScene)
    pc.button('sm_updb_bt', edit=True, c=doUpdateShotgun)
    pc.button('sm_capture_bt', edit=True, c=doCapture)
    pc.button('sm_wipCapture_bt', edit=True, c=doWipCapture)

    pc.button('sm_saveWip_bt', edit=True, c=doSaveWip)

    pc.button('sm_switchContext_bt', edit=True, c=doSwitchContext)

    pc.button('sm_shotgunPage_bt', edit=True, c=doShowInShotgun)
    pc.button('sm_wipCaptureDir_bt', edit=True, c=doShowWipCapturesDir)
    pc.button('sm_rvScreeningRoom_bt', edit=True, c=doShowSequenceInRv)

    #davos
    pc.button('sm_unlock_bt', edit=True, c=doUnlock)
    pc.button('sm_edit_bt', edit=True, c=doEdit)
    pc.button('sm_publish_bt', edit=True, c=doPublish)
    pc.button('sm_createFolder_bt', edit=True, c=doCreateFolder)

    #action buttons
    buttonName = 'sm_init_bt'
    pc.button(buttonName, edit=True, c=doInit)
    ACTION_BUTTONS.append(buttonName)

    pc.button('sm_editCam_bt', edit=True, c=doEditCam)
    pc.checkBox('sm_imgPlane_chk', edit=True, cc=doShowImagePlane)
    pc.checkBox('sm_increment_chk', edit=True, cc=doSetIncremental)
    pc.checkBox('sm_sendToRv_chk', edit=True, cc=doSetCaptureSentToRv)


    pc.button('sm_pouet_bt', edit=True, c=doPouet)
    #buttonName = 'sm_create_bt'
    #pc.button(buttonName, edit=True, c=doCreate)
    #ACTION_BUTTONS.append(buttonName)


def doShowInShotgun(*args):
    SCENE_MANAGER.showInShotgun()

def doShowWipCapturesDir(*args):
    p = SCENE_MANAGER.getWipCaptureDir().replace("/", "\\")
    if osp.isdir(p):
        subprocess.call("explorer {}".format(p))
    else:
        pc.displayWarning("No such directory: '{}'".format(p))

def doShowSequenceInRv(*args):

    seqId = SCENE_MANAGER.context["entity"]["sg_sequence"]["id"]

    sMuCmd = ('shotgun_review_app.theMode().setServer("https://zombillenium.shotgunstudio.com");\
    shotgun_review_app.theMode().launchTimeline([(string, string)] {{("entity_type", "Sequence"), ("entity_id", "{}")}});'
    .format(seqId))

    sLauncherLoc = osp.dirname(os.environ["Z2K_LAUNCH_SCRIPT"])
    p = osp.join(sLauncherLoc, "rvpush.bat")
    print p
    sCmdAgrs = [p, "-tag", "playblast", "mu-eval", sMuCmd]

    subprocess.call(sCmdAgrs)

def doShowImagePlane(bShow):
    mop.setImgPlaneVisible(bShow)

def doSetIncremental(bEnable):
    pc.optionVar["Z2K_SM_increment"] = bEnable

def doSetCaptureSentToRv(bEnable):
    pc.optionVar["Z2K_SM_sendToRv"] = bEnable

def doDisconnect(*args):
    SG.logoutUser()
    sceneManagerUI()

def doStepChanged(*args, **kwargs):
    #print args
    bUpdSg = kwargs.get("updateStep", True)

    prevStep = SCENE_MANAGER.context.get('step')
    stepName = pc.optionMenu("sm_step_dd", query=True, value=True)
    newStep = None

    for allowedStep in SG.currentUser['sg_allowedsteps']:
        if allowedStep['code'] == stepName:
            newStep = allowedStep
            if bUpdSg:
                print "updating {}'s step to {}".format(SG.currentUser["name"], allowedStep)
                SG.updateStep(allowedStep)
            break

    if newStep == None:
        pc.error('Cannot get entity type from step {0} !'.format(stepName))
    else:
        SCENE_MANAGER.context['step'] = newStep

    if (not prevStep) or (prevStep['entity_type'] != newStep['entity_type']):
        refreshStep(*args, runEntityChanged=False)

    if kwargs.pop("runEntityChanged", True):
        doEntityChanged(refreshSceneInfo=False)

def doCategChanged(*args, **kwargs):
    categCtrlName = 'sm_seq_dd' if SCENE_MANAGER.context['step']['entity_type'] == 'Shot' else 'sm_categ_dd'
    entityCtrlName = 'sm_shot_dd' if SCENE_MANAGER.context['step']['entity_type'] == 'Shot' else 'sm_asset_dd'

    categ = pc.optionMenu(categCtrlName, query=True, value=True)
    SCENE_MANAGER.context['categ'] = categ

    refreshOptionMenu(entityCtrlName, sorted(CATEG_ITEMS[categ].keys()))

    if kwargs.get("runEntityChanged", True):
        doEntityChanged(*args)

#Entity is a Shot or an Asset
def doEntityChanged(*args, **kwargs):

    #print "doEntityChanged", getCaller(fo=0)

    global CURRENT_ENTITY_TASKS
    entityCtrlName = 'sm_shot_dd' if SCENE_MANAGER.context['step']['entity_type'] == 'Shot' else 'sm_asset_dd'

    entityName = pc.optionMenu(entityCtrlName, query=True, value=True)
    SCENE_MANAGER.context['entity'] = CATEG_ITEMS[SCENE_MANAGER.context['categ']][entityName]

    #get tasks on entity
    CURRENT_ENTITY_TASKS = {}
    sgTasks = SCENE_MANAGER.getTasks()

    sTaskList = []
    for sgTask in sgTasks:
        sTask = sgTask['content']
        CURRENT_ENTITY_TASKS[sTask] = sgTask
        sTaskList.append(sTask)

    refreshOptionMenu('sm_task_dd', sTaskList)

    if kwargs.get("runTaskChanged", True):
        doTaskChanged(*args)

    if kwargs.get("refreshSceneInfo", True):
        doRefreshSceneInfo()

def doTaskChanged(*args, **kwargs):
    logMsg(log="all")

    global VERSIONS
    sTaskName = pc.optionMenu('sm_task_dd', query=True, value=True)
    SCENE_MANAGER.context['task'] = CURRENT_ENTITY_TASKS[sTaskName]

    #get Versions on task
    VERSIONS = {}
    versions = SCENE_MANAGER.getVersions()

    for version in versions:
        VERSIONS[version['code']] = version
        SCENE_MANAGER.context['version'] = version

    pc.textScrollList("sm_versions_lb", edit=True, removeAll=True)
    if len(versions) > 0:
        pc.textScrollList("sm_versions_lb", edit=True, append=sorted(VERSIONS.keys()))

#    doRefreshSceneInfo(*args)
    doRefreshFileStatus()
    doVersionChanged()

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

FILEREFS_FOR_LINE = {}

def doSelectRefs(*args):

    global LIST_WIDGET

    sSelList = []
    count = 0
    for item in LIST_WIDGET.selectedItems():

        for oFileRef in item.data(32):

            if not oFileRef.isLoaded():
                continue

            sRefNode = oFileRef.refNode.name()
            sNodeList = cmds.referenceQuery(sRefNode, nodes=True, dagPath=True)
            if sNodeList:
                sDagNodeList = cmds.ls(sNodeList, type="dagNode")
                if sDagNodeList:
                    sNodeList = sDagNodeList
                sNodeList = [sNodeList[0], sRefNode]
            else:
                sNodeList = [sRefNode]

            sSelList.extend(sNodeList)
            count += 1

    if sSelList:
        cmds.select(sSelList, replace=True, noExpand=True)
        pc.displayInfo("{} references selected.".format(count))
    else:
        pc.displayWarning("No references to select !")

    return sSelList

@setWaitCursor
def doRefreshSceneInfo(*args):
    """Displays the comparison of shotgun and active scene Assets"""
    logMsg(log='all')

    global FILEREFS_FOR_LINE, LIST_WIDGET

    LIST_WIDGET.clear()
    pc.refresh()

    assetDataList = SCENE_MANAGER.listRelatedAssets()

    headerData = ["NB", "ASSET NAME", "ASSET FILE", "SHOTGUN LINK"]

    sRcNameList = set()
    for astData in assetDataList:
        sAstRcDct = astData["maya_refs"]
        if sAstRcDct:
            sRcNameList.update(sAstRcDct.iterkeys())
    sRcNameList = sorted(sRcNameList)

    headerData.extend((s.upper() for s in sRcNameList))
    headerData.append([])

    numColumns = len(headerData) - 1

    sUnknownList = []
    rowDataList = [headerData]
    for astData in assetDataList:

        oFileRefList = astData["file_refs"]

        sAstName = astData["name"]
        rowData = [ str(astData["occurences"]),
                    sAstName,
                    astData["resource"],
                    astData["sg_info"],
                    ]

        sAstRcDct = astData["maya_refs"]
        if sAstRcDct:
            for sRcName in sRcNameList:
                rcDct = sAstRcDct.get(sRcName)
                sRcInfo = ""
                if rcDct:
                    sRcInfo = rcDct["status"]
                rowData.append(sRcInfo)
        else:
            rowData.extend(len(sRcNameList) * ("",))

        rowData = rowData[:numColumns] + [oFileRefList]
        if sAstName:
            rowDataList.append(rowData)
        else:
            sUnknownList.append(rowData)

    rowDataList.extend(sUnknownList)

    rowFmts = numColumns * [""]
    for i in xrange(numColumns):
        w = max((len(r[i]) for r in rowDataList)) + 1
        rowFmts[i] = " {{{0}:<{1}}}".format(i, w)

    itemList = []
    for rowData in rowDataList:

        oFileRefList = rowData[-1]
        sAstName = rowData[1]
        c = numColumns
        if not sAstName:
            p = pathResolve(oFileRefList[0].path).replace("/", "\\")
            sInfo = "UNKNOWN ASSET: " + p
            rowData = [rowData[0], sInfo, oFileRefList]
            c = len(rowData) - 1

        sRowFmt = "|".join(rowFmts[:c])
        sLine = sRowFmt.format(*rowData[:c])

        LIST_WIDGET.addItem(sLine)
        item = LIST_WIDGET.item(LIST_WIDGET.count() - 1)
        item.setData(32, oFileRefList)

        itemList.append(item)

    return itemList

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
    if SCENE_MANAGER.updateScene(addOnly):
        doRefreshSceneInfo(args)

    pc.displayWarning("Done !")

def doUpdateShotgun(*args):
    """Matches Shotgun Assets with scene Assets (NOT IMPLEMENTED)"""
    addOnly = pc.checkBox("sm_addOnly_bt", query=True, value=True)
    SCENE_MANAGER.updateShotgun(addOnly)
    doRefreshSceneInfo(args)

    pc.displayWarning("Done !")

#@timer
def doCapture(*args , **kwargs):

    bQuick = kwargs.get("quick", False)
    if bQuick or SCENE_MANAGER.assert_isEditable():
        bIncrement = pc.checkBox('sm_increment_chk', query=True, value=True)
        bSend = pc.checkBox('sm_sendToRv_chk', query=True, value=True)
        SCENE_MANAGER.capture(bIncrement, quick=bQuick, sendToRv=bSend)
        if not bQuick:
            doRefreshSceneInfo(args)
    else:
        doDetect(args)

def doWipCapture(*args):
    doCapture(*args, quick=True)

def doSaveWip(*args):
    if SCENE_MANAGER.assert_isEditable():
        SCENE_MANAGER.saveIncrement()
    else:
        doDetect(args)

def doSwitchContext(*args):
    """Use the current scene for an edition on the entry currently showing in the UI 
    (basically an edit, creating folders if needed)"""

    if SCENE_MANAGER.refreshSceneContext():
        pc.warning("Your context is already matching !!")
        return

#    if not SCENE_MANAGER.isEditable() and SCENE_MANAGER.context["lock"] == "Error":
#        #Maybe this is because folders does not exists ?
#        SCENE_MANAGER.createFolder()
#        doRefreshFileStatus()
#
#    if not SCENE_MANAGER.isEditable():
#        pc.warning("Your entity is locked by {0}".format(SCENE_MANAGER.context["lock"]))
#        return

    sMsg = "Your entity already have published versions, are you sure you want to use current scene ?"
    if (len(SCENE_MANAGER.getVersions()) == 0
        or pc.confirmDialog(title="Entity override", message=sMsg) == "Confirm"):
        SCENE_MANAGER.edit(True)
        doTaskChanged()
        #print "after", SCENE_MANAGER.context['task']['content']
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

#    if not SCENE_MANAGER.contextIsMatching():
#        raise RuntimeError("Sorry, context does not match current scene")

    SCENE_MANAGER.do('init')
    doRefreshSceneInfo()

def doCreate(*args):
    """Associated button is hidden (forbidden)"""
    SCENE_MANAGER.do('create')
    doRefreshSceneInfo()
    doRefreshFileStatus()

def doEditCam(*args):

    sMsg = "Edit the shot camera ??"
    sRes = pc.confirmDialog(title='ARE YOU SURE ?',
                            message=sMsg,
                            button=['OK', 'Cancel'],
                            defaultButton='Cancel',
                            cancelButton='Cancel',
                            dismissString='Cancel',
                            icon="warning")
    if sRes == "Cancel":
        pc.displayInfo("Canceled !")
        return

    SCENE_MANAGER.editShotCam()

def doPouet(*args, **kwargs):
    """Best function ever"""
    print "pouet"
    for i, j in  SCENE_MANAGER.context.iteritems():
        print "    ", i, j
