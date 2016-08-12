#------------------------------------------------------------------
# UI handling for /UI/sceneManagerUIB.ui QT designer file (z2k-pipeline-toolkit\maya_mods\zombie\python\dminutes\UI\sceneManagerUIB.ui)
#------------------------------------------------------------------

#import os
import os.path as osp
import subprocess
from functools import partial
from collections import OrderedDict
from pprint import pprint

from PySide.QtCore import Qt

import maya.cmds as mc
import pymel.core

from pytd.gui.itemviews.utils import toDisplayText
from pytd.util.fsutils import pathResolve, pathJoin
from pytd.util.sysutils import inDevMode, toStr, fromUtf8
from pytd.util.logutils import logMsg
from pytd.util.qtutils import setWaitCursor
from pytd.gui.dialogs import QuickTreeDialog

from pytaya.util.sysutils import withSelectionRestored
from pytaya.util.qtutils import mayaMainWindow

from davos_maya.tool.general import okValue
from davos_maya.tool.general import getSgRelatedVersionsHistory, listRelatedAssets
from davos_maya.tool import reference as myaref

from zomblib import rvutils

from dminutes import maya_scene_operations as mop
from dminutes import sceneManager
from dminutes.sceneManager import scnFromTask
from dminutes import smoothOnCapture as soc

reload(myaref)
pc = pymel.core


"""Global instance of sceneManager Class"""
SCENE_MANAGER = None
SCENE_MANAGER_DOCK = 'sceneManagerDock'
SCENE_MANAGER_UI = 'sceneManagerUI'

"""Global instance of shotgunengine Class"""
SG_ENGINE = None

"""Various caches for UI lists"""
ENTITIES_PER_CATEG = {}
CURRENT_ENTITY_TASKS = {}
VERSIONS = {}

QWIDGETS = {}
#------------------------------------------------------------------
#               Main UI Creation/Initialization
#------------------------------------------------------------------

def kill():

    global SCENE_MANAGER_DOCK, SCENE_MANAGER_UI

    if mc.dockControl(SCENE_MANAGER_DOCK, q=True, exists=True):
        print "deleteUI", SCENE_MANAGER_UI, SCENE_MANAGER_DOCK
        pc.deleteUI(SCENE_MANAGER_UI)
        pc.deleteUI(SCENE_MANAGER_DOCK)
        return True

    if mc.control(SCENE_MANAGER_UI, q=True, exists=True):
        print "deleteUI", SCENE_MANAGER_UI
        pc.deleteUI(SCENE_MANAGER_UI)

    pc.refresh()

    return False

def saveDockState():
    pc.optionVar["Z2K_SM_dockState"] = mc.dockControl(SCENE_MANAGER_DOCK, q=True, state=True)
    pc.optionVar["Z2K_SM_dockFloating"] = mc.dockControl(SCENE_MANAGER_DOCK, q=True, floating=True)

def isLaunched():
    return mc.dockControl(SCENE_MANAGER_DOCK, q=True, exists=True) and SCENE_MANAGER

def isVisible():
    return mc.dockControl(SCENE_MANAGER_DOCK, q=True, visible=True)

@withSelectionRestored
def launch():
    """Main UI Creator"""
    global QWIDGETS

    states = dict()

    if isLaunched():
        mc.dockControl(SCENE_MANAGER_DOCK, e=True, visible=True)
    else:

        if mc.evaluationManager(q=True, enabled=True):
            mc.evaluationManager(mode="off")

        kill()

        if not mc.ls(sl=True):
            mc.select("|persp")

        dirname, _ = osp.split(osp.abspath(__file__))
        sLoadedUi = mc.loadUI(uiFile=dirname + "/UI/sceneManagerUIC.ui", v=False)
        if sLoadedUi != SCENE_MANAGER_UI:
            mc.deleteUI(sLoadedUi)
            mc.deleteUI(SCENE_MANAGER_UI)
            #sLoadedUi = mc.loadUI(uiFile=dirname + "/UI/sceneManagerUIC.ui", v=False)
            raise ValueError("Bad loaded UI Name: '{}'. Expected: '{}'"
                             .format(sLoadedUi, SCENE_MANAGER_UI))

        sWdgName = mc.textScrollList("sm_sceneInfo_lb", e=True,
                                           removeAll=True,
                                           font="fixedWidthFont",
                                           allowMultiSelection=True)
        QWIDGETS["sm_sceneInfo_lb"] = pc.ui.toPySideObject(sWdgName)

        sWdgName = mc.control("relatedAssetsGroup", q=True, fullPathName=True)
        QWIDGETS["relatedAssetsGroup"] = pc.ui.toPySideObject(sWdgName)

        sWdgName = mc.control("smoothGroup", q=True, fullPathName=True)
        QWIDGETS["smoothGroup"] = pc.ui.toPySideObject(sWdgName)

        sWdgName = mc.control("sm_setupAnimatic_bt", q=True, fullPathName=True)
        QWIDGETS["sm_setupAnimatic_bt"] = pc.ui.toPySideObject(sWdgName)

        sState = pc.optionVar.get("Z2K_SM_dockState")
        if sState:
            states.update(state=sState)
        states.update(floating=pc.optionVar.get("Z2K_SM_dockFloating", False))

#        if not mc.window(SCENE_MANAGER_UI, q=True, exists=True):
#            mc.showWindow(SCENE_MANAGER_UI)

        sLabel = mc.window(sLoadedUi, q=True, title=True)
        mc.dockControl(SCENE_MANAGER_DOCK, area='left', content=sLoadedUi,
                       allowedArea=['left'], retain=True, label=sLabel,
                       closeCommand=saveDockState, **states)

        connectCallbacks()

    initialize()
    refreshContextUI()

    if states:
        mc.dockControl(SCENE_MANAGER_DOCK, e=True, **states)

    if not mc.dockControl(SCENE_MANAGER_DOCK, q=True, floating=True):
        mc.dockControl(SCENE_MANAGER_DOCK, e=True, r=True)

def initialize():
    """Initialize default values (Operator AllowedSteps and CurrentStep...), hide forbidden buttons"""

    global SCENE_MANAGER, SG_ENGINE

    if SCENE_MANAGER:
        del SCENE_MANAGER
    if SG_ENGINE:
        del SG_ENGINE

    SCENE_MANAGER = sceneManager.SceneManager()
    SG_ENGINE = SCENE_MANAGER.context['damProject']._shotgundb

    curSgUser = SG_ENGINE.currentUser
    userSgStep = curSgUser['sg_currentstep']

    #User info
    pc.textField('sm_user_bt', edit=True, text=curSgUser['name'])
    pc.textField('sm_project_bt', edit=True, text=SCENE_MANAGER.projectname)

    sAllowedSteps = list(step['code'] for step in curSgUser['sg_allowedsteps']
                                        if step['entity_type'] == 'Shot')
    refreshOptionMenu('sm_step_dd', sAllowedSteps)

    #print userSgStep
    sUserStep = userSgStep['code']
    if (userSgStep is not None) and (sUserStep in sAllowedSteps):
        pc.optionMenu("sm_step_dd", edit=True, value=sUserStep)

    #Hide some controls
    pc.control("fileStatusGroup", edit=True, visible=False)
    pc.control("versionsGroup", edit=True, visible=False)
    pc.control("sm_createFolder_bt", edit=True, visible=False)
    pc.control("sm_edit_bt", edit=True, visible=False)
    pc.control("sm_addOnly_bt", edit=True, visible=False)
    pc.control("sm_project_bt", edit=True, visible=False)
    #pc.control('sm_updateThumb_bt', edit=True, visible=False)
    #pc.control("sm_disconnect_bt", edit=True, visible=False)
    if not inDevMode():
        pc.control("sm_pouet_bt", edit=True, visible=False)

    doStepChanged(updateStep=False)

    damShot = SCENE_MANAGER.getDamShot()
    sAnn = "Create a capture into local project: '{}'".format(mop.getWipCaptureDir(damShot))
    pc.control("sm_wipCapture_bt", edit=True, annotation=sAnn)
    sAnn = ("Create a PUBLISHABLE capture into private area: '{}'"
            .format(damShot.getPath("private", "entity_dir")))
    pc.control("sm_capture_bt", edit=True, annotation=sAnn)

    pc.control("sm_increment_chk", edit=True, visible=False)

    loadContextFromScene()

test_toggle = False

def refreshContextUI():
    """Update buttons availability from contexts (scene Context / UI Context)"""

    global test_toggle

    if not mc.control(SCENE_MANAGER_DOCK, q=True, visible=True):
        return

    #print getCaller()

    sceneInfos = SCENE_MANAGER.infosFromCurrentScene()
    bRcsMatchUp = SCENE_MANAGER.resourcesMatchUp(sceneInfos)
    bPublishable = bRcsMatchUp and SCENE_MANAGER.scenePublishable(sceneInfos)
    sCtxStep = SCENE_MANAGER.context["step"]["code"].lower()

    bEnabled = (('task' in SCENE_MANAGER.context)
                and scnFromTask(SCENE_MANAGER.context['task'])
                and bRcsMatchUp)
    pc.control("sm_init_bt", edit=True, enable=bEnabled)

    pc.control('sm_switchContext_bt', edit=True, enable=(not bPublishable))

    pc.control('sm_capture_bt', edit=True, enable=bPublishable)
    pc.control('sm_wipCapture_bt', edit=True, enable=bRcsMatchUp)
    pc.control('sm_incrementSave_bt', edit=True, enable=bPublishable)
    pc.control('sm_publish_bt', edit=True, enable=bPublishable)

    pc.control('sm_updateThumb_bt', edit=True, enable=bRcsMatchUp)

    bEnabled = (sCtxStep not in ("previz 3d", "stereo")) and bPublishable
    pc.control('sm_editCam_bt', edit=True, enable=bEnabled)

    _, oImgPlaneCam = mop.getImagePlaneItems(create=False)
    bEnabled = True if (bRcsMatchUp and oImgPlaneCam) else False
    pc.button('sm_setupAnimatic_bt', edit=True, enable=bEnabled)
    sInfo = " - NEEDED !"
    sLabel = pc.button('sm_setupAnimatic_bt', q=True, label=True).rsplit(sInfo, 1)[0]
    sStyle = "background-color: none;"
    if bEnabled:
        infos = mop.getAnimaticInfos(SCENE_MANAGER.getDamShot(), sCtxStep)
        pc.button('sm_setupAnimatic_bt', q=True, label=True)
        if infos["newer_movie"]:
            if (sInfo not in sLabel):
                sLabel += sInfo
                sStyle = "background-color:rgba(200, 0, 0, 90);"
    QWIDGETS["sm_setupAnimatic_bt"].setStyleSheet(sStyle)
    pc.button('sm_setupAnimatic_bt', edit=True, label=sLabel)

    test_toggle = not test_toggle

    pc.checkBox('sm_imgPlane_chk', edit=True, value=mop.isImgPlaneHidden())
    pc.checkBox('sm_increment_chk', edit=True, value=pc.optionVar.get("Z2K_SM_increment", False))
    pc.checkBox('sm_sendToRv_chk', edit=True, value=pc.optionVar.get("Z2K_SM_sendToRv", False))

    pc.checkBox('sm_blocking_chk', edit=True, value=pc.playbackOptions(q=True, blockingAnim=True))
    pc.checkBox('sm_updAllViews_chk', edit=True, value=(pc.playbackOptions(q=True, view=True) == "all"))

    bListAssets = pc.optionVar.get("Z2K_SM_listAssets",
                                   False if sCtxStep in ("animation", "charfx") else True)
    QWIDGETS["relatedAssetsGroup"].setChecked(bListAssets)
    if bListAssets:
        pc.control('sm_updScene_bt', edit=True, enable=bPublishable)
        pc.control('sm_updShotgun_bt', edit=True, enable=bPublishable and
                   (sCtxStep in ("previz 3d", "layout", "final layout")))
        pc.control('sm_selectRefs_bt', edit=True, enable=bRcsMatchUp)

    bEnable = pc.optionVar.get("Z2K_SM_smoothOnCapture", False)
    QWIDGETS["smoothGroup"].setChecked(bEnable)
    updSmoothOnCaptureState(bEnable, warn=False)

def loadContextFromScene(**kwargs):
    """Initialize UI Context from scene"""

    sceneInfos = SCENE_MANAGER.infosFromCurrentScene()
    uiContext = SCENE_MANAGER.contextFromSceneInfos(sceneInfos)

    if uiContext:
        #print context
        somethingChanged = False

        if "shot" in uiContext:
            #print context["seq"], context["shot"]
            somethingChanged |= setOption("sm_seq_dd", uiContext["seq"], runEntityChanged=False)
            somethingChanged |= setOption("sm_shot_dd", uiContext["shot"], runEntityChanged=False)

        sCtxStep = uiContext["step"]
        curSgUser = SG_ENGINE.currentUser
        sAllowedSteps = list(step['code'] for step in curSgUser['sg_allowedsteps']
                                                if step['entity_type'] == 'Shot')
        if sCtxStep not in sAllowedSteps:
            pc.displayError("{} NOT assigned to '{}' step yet."
                            .format(SG_ENGINE.currentUser["name"], sCtxStep))
        else:
            somethingChanged |= setOption("sm_step_dd", sCtxStep, runEntityChanged=False)

        doEntityChanged(**kwargs)

        if not somethingChanged:
            refreshContextUI()

        return True

    doEntityChanged(**kwargs)

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
    global ENTITIES_PER_CATEG

    sgStep = SCENE_MANAGER.context['step']
    if sgStep['entity_type'] == 'Shot':
        pc.control('sm_asset_chooser_grp', edit=True, visible=False)
        pc.control('sm_shot_chooser_grp', edit=True, visible=True)

        sequences = SG_ENGINE.getSequencesInfo()

        categ_names = list(seq["code"] for seq in sequences)

        refreshOptionMenu('sm_seq_dd', categ_names)
        doCategChanged(*args, **kwargs)

    elif sgStep['entity_type'] == 'Asset':
        pc.control('sm_asset_chooser_grp', edit=True, visible=True)
        pc.control('sm_shot_chooser_grp', edit=True, visible=False)

        assets = SG_ENGINE.getAssetsInfo()

        categ_names = []
        ENTITIES_PER_CATEG = OrderedDict()
        for asset in assets:
            if asset['sg_asset_type'] == None:
                pc.warning('entity {0} with category "None" will be ignored'
                           .format(asset['code']))
                continue

            if not asset['sg_asset_type'] in ENTITIES_PER_CATEG:
                categ_names.append(asset['sg_asset_type'])
                ENTITIES_PER_CATEG[asset['sg_asset_type']] = OrderedDict()

            ENTITIES_PER_CATEG[asset['sg_asset_type']][asset['code']] = asset

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
    pc.button('sm_switchContext_bt', edit=True, c=doSwitchContext)

    #misc. operations
    pc.button('sm_shotgunPage_bt', edit=True, c=doShowInShotgun)
    pc.button('sm_wipCaptureDir_bt', edit=True, c=doShowWipCapturesDir)
    pc.button('sm_rvScreeningRoom_bt', edit=True, c=doShowSequenceInRv)
    pc.button('sm_viewLatest_bt', edit=True, c=doPlayLatestCapture)

    #shot operations
    pc.button('sm_init_bt', edit=True, c=doShotSetup)
    pc.button('sm_setupAnimatic_bt', edit=True, c=doSetupAnimatic)
    pc.button('sm_editCam_bt', edit=True, c=doEditCam)

    #Smooth on capture
    QWIDGETS["smoothGroup"].clicked[bool].connect(updSmoothOnCaptureState)
    pc.button('sm_smoothAdd_bt', edit=True, c=doAddToSmooth)
    pc.button('sm_smoothRem_bt', edit=True, c=doDelFromSmooth)
    pc.button('sm_smoothSelect_bt', edit=True, c=doSelectSmoothed)
    pc.button('sm_clearIncluded_bt', edit=True, c=partial(doClearObjectSet,
                                                          "set_applySmoothOnCapture"))
    pc.button('sm_clearExcluded_bt', edit=True, c=partial(doClearObjectSet,
                                                          "set_ignoreSmoothOnCapture"))
    pc.button('sm_selectIncluded_bt', edit=True, c=partial(doSelectSetMembers,
                                                          "set_applySmoothOnCapture"))
    pc.button('sm_selectExcluded_bt', edit=True, c=partial(doSelectSetMembers,
                                                          "set_ignoreSmoothOnCapture"))

    #Playback options
    pc.checkBox('sm_imgPlane_chk', edit=True, cc=doShowImagePlane)
    pc.checkBox('sm_blocking_chk', edit=True, cc=updBlockingAnimState)
    pc.checkBox('sm_updAllViews_chk', edit=True, cc=setAllViewsUpdated)


    #Capture operations
    pc.checkBox('sm_sendToRv_chk', edit=True, cc=updAddCaptureToRvState)
    pc.checkBox('sm_increment_chk', edit=True, cc=updIncrementalSaveState)
    pc.button('sm_capture_bt', edit=True, c=doCapture)
    pc.button('sm_wipCapture_bt', edit=True, c=doWipCapture)

    #File operations
    pc.button('sm_incrementSave_bt', edit=True, c=doIncrementSave)
    pc.button('sm_publish_bt', edit=True, c=doPublish)

    #Related assets
    QWIDGETS["relatedAssetsGroup"].clicked[bool].connect(updRelatedAssetsShown)
    pc.button('sm_refreshScene_bt', edit=True, c=doRefreshSceneInfo)
    pc.button('sm_selectRefs_bt', edit=True, c=doSelectRefs)
    pc.button('sm_updScene_bt', edit=True, c=doUpdateSceneAssets)
    pc.button('sm_updShotgun_bt', edit=True, c=doUpdateShotgunAssets)
    sMsg = "Which assets do you want to lock to a version ?"
    pc.button('sm_lockVersions_bt', edit=True, c=partial(setAssetVersionsLocked, True, sMsg))
    sMsg = "Which assets do you want to switch to latest file ?"
    pc.button('sm_unlockVersions_bt', edit=True, c=partial(setAssetVersionsLocked, False, sMsg))

    pc.button('sm_pouet_bt', edit=True, c=doPouet)


def iterSelectedAssets():
    sceneInfoWdg = QWIDGETS["sm_sceneInfo_lb"]
    for item in sceneInfoWdg.selectedItems():
        yield item.data(32)

def setAssetVersionsLocked(bLock, sConfirmMsg, *args):

    damShot = SCENE_MANAGER.getDamShot()
#    proj = damShot.project
#    astLib = proj.getLibrary("public", "asset_lib")

    sAstList = tuple(d["name"] for d in iterSelectedAssets())

    sButtonList = ['All', 'Cancel']
    if sAstList:
        sButtonList.insert(0, '{} Selected'.format(len(sAstList)))

    sRes = pc.confirmDialog(title='QUESTION ?',
                            message=sConfirmMsg,
                            button=sButtonList,
                            icon="question")
    if sRes == "Cancel":
        pc.displayInfo("Canceled !")
        return
    elif sRes == 'All':
        sAstList = None

    relAstList = listRelatedAssets(damShot, assetNames=sAstList)

    if bLock:
        sgShotVersList = getSgRelatedVersionsHistory(logInfo=False, limit=10,
                                                     relatedAssets=relAstList)
        sgShotVers = chooseSgShotVersion(sgShotVersList)
        if not sgShotVers:
            return

        sVersPathDct = dict((d["entity"]["name"].lower(), pathResolve(d["sg_source_file"]))
                            for d in sgShotVers["sg_related_asset_versions"])
        #pprint(sVersPathDct)

        count = 0
        for relAst in relAstList:
            damAst = relAst.get("dam_entity")
            if not damAst:
                continue
            p = sVersPathDct.get(damAst.name.lower())
            relAst["version_file"] = relAst["library"].getEntry(p, dbNode=False)
            count += 1

        print (" Switching {} asset refs to versions from {} "
               .format(count, sgShotVers["code"]).center(120, "-"))

        myaref.lockAssetRefsToRelatedVersion(relAstList, dryRun=False)
    else:
        myaref.switchAssetRefsToHeadFile(relAstList, dryRun=False)

    doRefreshSceneInfo()

def chooseSgShotVersion(sgShotVersList):

    treeDataList = []
    for sgShotVers in sgShotVersList:
        sShotVersPath = pathJoin(sgShotVers["code"])
        roleData = {Qt.UserRole:(0, sgShotVers)}
        sComment = fromUtf8(sgShotVers["description"])
        sTextList = [sgShotVers["code"], sComment,
                     sgShotVers["sg_task.Task.sg_status_list"],
                     toDisplayText(sgShotVers["created_at"])]
        treeDataList.append({"path":sShotVersPath,
                             "texts":sTextList,
                             "flags":None, "roles":roleData})

        sgRelVersList = sgShotVers["sg_related_asset_versions"]
        for sgRelVers in sorted(sgRelVersList, key=lambda d:d["code"]):
            sAstVersPath = pathJoin(sShotVersPath, sgRelVers["code"])
            roleData = {Qt.UserRole:(0, sgRelVers)}
            #sSplitList = sgRelVers["code"].split("_")
            sComment = fromUtf8(sgRelVers["description"])
            sTextList = [sgRelVers["code"], sComment, "", toDisplayText(sgRelVers["created_at"])]
            treeDataList.append({"path":sAstVersPath,
                                 "texts":sTextList,
                                 "flags":Qt.NoItemFlags, "roles":roleData})

    dlg = QuickTreeDialog(mayaMainWindow())
    dlg.resize(600, 500)
    treeWdg = dlg.treeWidget
    treeWdg.itemDelegate().setItemMarginSize(2, 2)
    treeWdg.setHeaderLabels(("Versions From", "Comment", "Status", "Date"))
    treeWdg.createTree(treeDataList)

    bOk = dlg.exec_()
    if bOk:
        selItems = treeWdg.selectedItems()
        if selItems:
            return selItems[0].data(0, Qt.UserRole)

    return None

def doPlayLatestCapture(*args):
    bSend = pc.checkBox('sm_sendToRv_chk', query=True, value=True)
    SCENE_MANAGER.playLatestCapture(bSend)

@mop.undoAtOnce
@withSelectionRestored
def doSetupAnimatic(*args):

    damShot = SCENE_MANAGER.getDamShot()
    sSgStep = SCENE_MANAGER.context["step"]["code"]

    mop.setupAnimatic(mop.getAnimaticInfos(damShot, sSgStep), create=False)

    pc.refresh()
    refreshContextUI()

def setAllViewsUpdated(bEnable):
    mc.playbackOptions(e=True, view="all" if bEnable else "active")

def doClearObjectSet(sSetName, bChecked):
    soc.clearObjectSet(sSetName)
    updSmoothOnCaptureState()

def doSelectSetMembers(sSetName, bChecked):
    members = soc.objectSetMembers(sSetName, recursive=False)
    if members:
        mc.select(list(members))
    else:
        pc.displayWarning("Nothing to select.")

def doSelectSmoothed(*args):
    smoothData = updSmoothOnCaptureState()
    if not smoothData:
        pc.displayWarning("Nothing to select.")
        return

    mc.select(smoothData.keys())

def doDelFromSmooth(*args):
    soc.delFromSmooth()
    updSmoothOnCaptureState()

def doAddToSmooth(*args):
    soc.addToSmooth()
    updSmoothOnCaptureState()

def doShowInShotgun(*args):
    SCENE_MANAGER.showInShotgun()

def doShowWipCapturesDir(*args):
    p = mop.getWipCaptureDir(SCENE_MANAGER.getDamShot()).replace("/", "\\")
    if osp.isdir(p):
        subprocess.call("explorer {}".format(p))
    else:
        pc.displayError("No such directory: '{}'".format(p))

def doShowSequenceInRv(*args):
    seqId = SCENE_MANAGER.context["entity"]["sg_sequence"]["id"]
    rvutils.openToSgSequence(seqId)

def doShowImagePlane(bShow):
    mop.setImgPlaneHidden(bShow)

def updBlockingAnimState(bEnable):
    pc.playbackOptions(e=True, blockingAnim=bEnable)

def updIncrementalSaveState(bEnable):
    pc.optionVar["Z2K_SM_increment"] = bEnable

def updAddCaptureToRvState(bEnable):
    pc.optionVar["Z2K_SM_sendToRv"] = bEnable

def updSmoothOnCaptureState(bEnable=None, warn=True):

    if bEnable is not None:
        pc.optionVar["Z2K_SM_smoothOnCapture"] = bEnable
    else:
        bEnable = pc.optionVar.get("Z2K_SM_smoothOnCapture", False)

    if bEnable:
        smoothData, numFaces = soc.listSmoothableMeshes(project=SCENE_MANAGER.context["damProject"],
                                                        warn=warn)
        QWIDGETS["smoothGroup"].setTitle("Smooth On Capture ({} meshes - {:,} faces)"
                                         .format(len(smoothData), numFaces))
        return smoothData

def updRelatedAssetsShown(bEnable):
    pc.optionVar["Z2K_SM_listAssets"] = bEnable
    doRefreshSceneInfo()

def doDisconnect(*args):
    SG_ENGINE.logoutUser()
    launch()

def doStepChanged(*args, **kwargs):

    bUpdSg = kwargs.get("updateStep", True)

    prevStep = SCENE_MANAGER.context.get('step')
    stepName = pc.optionMenu("sm_step_dd", query=True, value=True)
    newStep = None

    for allowedStep in SG_ENGINE.currentUser['sg_allowedsteps']:
        if allowedStep['code'] == stepName:
            newStep = allowedStep
            if bUpdSg:
                print "updating {}'s step to {}".format(SG_ENGINE.currentUser["name"], allowedStep)
                SG_ENGINE.updateStep(allowedStep)
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

    global ENTITIES_PER_CATEG

    sEntiType = SCENE_MANAGER.context['step']['entity_type']
    if sEntiType == 'Shot':
        sCateg = pc.optionMenu("sm_seq_dd", query=True, value=True)
        entityCtrlName = 'sm_shot_dd'
        infos = SG_ENGINE.getShotsInfo("", sCateg)
    elif sEntiType == 'Asset':
        sCateg = pc.optionMenu("sm_categ_dd", query=True, value=True)
        entityCtrlName = 'sm_asset_dd'
        infos = SG_ENGINE.getAssetsInfo("", sCateg)
    else:
        raise TypeError("Unknown Shotgun Entity type: '{}'".format(sEntiType))

    SCENE_MANAGER.context['categ'] = sCateg

    sEntityList = []
    ENTITIES_PER_CATEG[sCateg] = OrderedDict()

    if infos:
        ENTITIES_PER_CATEG[sCateg] = OrderedDict((i["code"], i) for i in infos)
        sEntityList = list(i["code"] for i in infos)

    refreshOptionMenu(entityCtrlName, sEntityList)

    if kwargs.get("runEntityChanged", True):
        doEntityChanged(*args)

#Entity is a Shot or an Asset
def doEntityChanged(*args, **kwargs):

    #print "doEntityChanged", getCaller(fo=0)

    global CURRENT_ENTITY_TASKS

    sEntiType = SCENE_MANAGER.context['step']['entity_type']

    if sEntiType == 'Shot':
        sEntityName = pc.optionMenu('sm_shot_dd', query=True, value=True)
        #sgEntity = SG_ENGINE.getShotInfo(sEntityName)
    elif sEntiType == 'Asset':
        sEntityName = pc.optionMenu('sm_asset_dd', query=True, value=True)
        #sgEntity = SG_ENGINE.getAssetInfo(sEntityName)
    else:
        raise TypeError("Unknown Shotgun Entity type: '{}'".format(sEntiType))

    sCurCateg = SCENE_MANAGER.context['categ']
    SCENE_MANAGER.context['entity'] = ENTITIES_PER_CATEG[sCurCateg][sEntityName]

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
    refreshContextUI()
    #print pc.textScrollList("sm_versions_lb", query=True, selectItem=True)

def doRefreshFileStatus(*args):
    """File status is still tracked but the control that displays it is hidden (forbidden ^^)"""
    SCENE_MANAGER.refreshStatus()

    pc.button('sm_unlock_bt', edit=True, enable=False)
    statusText = "Unlocked"

    if SCENE_MANAGER.context['lock'] != "":
        if SCENE_MANAGER.context['lock'] == SG_ENGINE.currentUser['login']:
            statusText = "Locked by Me"
            pc.button('sm_unlock_bt', edit=True, enable=True)
        else:
            statusText = "Locked by {0}".format(SCENE_MANAGER.context['lock'])

    pc.textField("sm_lock_tb", edit=True, text=statusText)

#    bPublishable = SCENE_MANAGER.scenePublishable()
#
#    pc.button('sm_edit_bt', edit=True, enable=bPublishable)
#    pc.button('sm_publish_bt', edit=True, enable=bPublishable)
#    pc.button('sm_capture_bt', edit=True, enable=bPublishable)
#    pc.button('sm_incrementSave_bt', edit=True, enable=bPublishable)

#buttons
def doDetect(*args, **kwargs):
    """load context from scene"""
    loadContextFromScene(**kwargs)

FILEREFS_FOR_LINE = {}

def doSelectRefs(*args):

    sceneInfoWdg = QWIDGETS["sm_sceneInfo_lb"]
    sSelList = []
    count = 0
    for item in sceneInfoWdg.selectedItems():

        oFileRefList = item.data(32)["file_refs"]
        for oFileRef in oFileRefList:

#            if not oFileRef.isLoaded():
#                continue

            sRefNode = oFileRef.refNode.name()
            sNodeList = mc.referenceQuery(sRefNode, nodes=True, dagPath=True)
            if sNodeList:
                sDagNodeList = mc.ls(sNodeList, type="dagNode")
                if sDagNodeList:
                    sNodeList = sDagNodeList
                sNodeList = [sNodeList[0], sRefNode]
            else:
                sNodeList = [sRefNode]

            sSelList.extend(sNodeList)
            count += 1

    if sSelList:
        mc.select(sSelList, replace=True, noExpand=True)
        pc.displayInfo("{} references selected.".format(count))
    else:
        pc.displayWarning("No references to select !")

    return sSelList

@setWaitCursor
def doRefreshSceneInfo(*args):
    """Displays the comparison of shotgun and active scene Assets"""
    logMsg(log='all')

    global FILEREFS_FOR_LINE

    sceneInfoWdg = QWIDGETS["sm_sceneInfo_lb"]

    sceneInfoWdg.clear()
    pc.refresh()

    sCtxStep = ""
    try:
        sCtxStep = SCENE_MANAGER.context["step"]["code"].lower()
    except KeyError:
        pass

    if not pc.optionVar.get("Z2K_SM_listAssets", False if sCtxStep == "animation" else True):
        return []

    assetDataList = SCENE_MANAGER.listRelatedAssets()

    headerData = ["NB", "ASSET NAME", "ASSET FILE", "SHOTGUN"]

    sRcNameList = set()
    for astData in assetDataList:
        sAstRcDct = astData["maya_rcs"]
        if sAstRcDct:
            sRcNameList.update(sAstRcDct.iterkeys())
    sRcNameList = sorted(sRcNameList)

    headerData.extend((s.upper() for s in sRcNameList))
    headerData.append({})

    numColumns = len(headerData) - 1

    sUnknownList = []
    rowDataList = [headerData]
    for astData in assetDataList:

        sAstName = astData["name"]
        v = astData.get("version", -1)

        rowData = [str(astData["occurences"]),
                   sAstName,
                   astData["resource"] + (" v{:03d}".format(v) if v > -1 else ""),
                   astData["sg_link"],
                   ]

        sCurRcName = astData["resource"]
        sAstRcDct = astData["maya_rcs"]
        if sAstRcDct:
            for sRcName in sRcNameList:
                rcDct = sAstRcDct.get(sRcName)
                sRcInfo = ""
                if rcDct:
                    sRcInfo = rcDct["status"]

                if (sRcName == sCurRcName and v > -1 and
                    sRcInfo == okValue and "version" in rcDct):
                    sRcInfo += " v{:03d}".format(rcDct["version"])

                rowData.append(sRcInfo)
        else:
            rowData.extend(len(sRcNameList) * ("",))

        rowData = rowData[:numColumns] + [astData]
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

        astData = rowData[-1]
        oFileRefList = astData.get("file_refs", [])
        sAstName = rowData[1]
        c = numColumns
        if not sAstName:
            p = pathResolve(oFileRefList[0].path).replace("/", "\\")
            sInfo = "NOT AN ASSET: " + p
            rowData = [rowData[0], sInfo, oFileRefList]
            c = len(rowData) - 1

        sRowFmt = "|".join(rowFmts[:c])
        sLine = sRowFmt.format(*rowData[:c])

        sceneInfoWdg.addItem(sLine)
        item = sceneInfoWdg.item(sceneInfoWdg.count() - 1)
        item.setData(32, astData)

        itemList.append(item)

    return itemList

def doUpdateSceneAssets(*args):
    """Matches scene Assets with Shotgun Assets"""
    #addOnly = pc.checkBox("sm_addOnly_bt", query=True, value=True)
    if SCENE_MANAGER.updateSceneAssets():
        doRefreshSceneInfo(args)

    pc.displayWarning("Done !")

def doUpdateShotgunAssets(*args):
    """Matches Shotgun Assets with scene Assets (NOT IMPLEMENTED)"""
    #addOnly = pc.checkBox("sm_addOnly_bt", query=True, value=True)
    if SCENE_MANAGER.updateShotgunAssets():
        doRefreshSceneInfo(args)
        pc.displayWarning("Done !")

@mop.withErrorDialog
def doCapture(*args , **kwargs):

    bQuick = kwargs.get("quick", False)
    if bQuick or SCENE_MANAGER.assertScenePublishable():

        bIncrement = False
        if pc.checkBox('sm_increment_chk', query=True, visible=True):
            bIncrement = pc.checkBox('sm_increment_chk', query=True, value=True)

        bSend = pc.checkBox('sm_sendToRv_chk', query=True, value=True)
        smoothData = updSmoothOnCaptureState()
        SCENE_MANAGER.capture(saveScene=(not bQuick), increment=bIncrement, quick=bQuick,
                              sendToRv=bSend, smoothData=smoothData)
#        if not bQuick:
#            doRefreshSceneInfo(args)
    else:
        doDetect(args)

def doWipCapture(*args):
    doCapture(*args, quick=True)

def doIncrementSave(*args):
    if SCENE_MANAGER.assertScenePublishable():
        SCENE_MANAGER.saveIncrement()
    else:
        doDetect(args)

def doSwitchContext(*args, **kwargs):
    """Use the current scene for an edition on the entry currently showing in the UI 
    (basically an edit, creating folders if needed)"""

    sceneInfos = SCENE_MANAGER.infosFromCurrentScene()
    bRcsMatchUp = SCENE_MANAGER.resourcesMatchUp(sceneInfos, warn=True)
    bPublishable = bRcsMatchUp and SCENE_MANAGER.scenePublishable(sceneInfos, warn=True)
    if bPublishable:
        pc.warning("Your context is already matching !!")
        return

    if kwargs.get("prompt", True):

        pubFile = SCENE_MANAGER.rcFileFromContext(fail=True)
        sMsg = "Use the current scene to work on '{}' ?".format(pubFile.nextVersionName())

        sRes = pc.confirmDialog(title='DO YOU WANT TO...',
                                message=sMsg,
                                button=['OK', 'Cancel'],
                                defaultButton='Cancel',
                                cancelButton='Cancel',
                                dismissString='Cancel',
                                icon="question")
        if sRes == "Cancel":
            pc.displayWarning("Canceled !")
            return

    SCENE_MANAGER.edit(True)
    doTaskChanged()

def doPublish(*args):

    if SCENE_MANAGER.assertScenePublishable():

        res = SCENE_MANAGER.publish()
        doTaskChanged()
        #doRefreshFileStatus()

        if not res:
            return

        sYes = "Yes, keep it locked."
        sNo = "No, unlock it."
        sMsg = '"{}" published successfully !\n\n'.format(res["private_file"].name)
        sRes = pc.confirmDialog(title='DO YOU WANT TO...',
                                message=sMsg + "Continue working on this scene ?",
                                button=[sYes, sNo],
                                defaultButton=sNo,
                                cancelButton=sNo,
                                dismissString=sNo,
                                icon="question")
        if sRes == sNo:
            return

        doSwitchContext(prompt=False)
    else:
        doDetect(args)

#action buttons
def doShotSetup(*args):
    """Button is named 'Shot Setup'"""

    sceneInfos = SCENE_MANAGER.infosFromCurrentScene()
    SCENE_MANAGER.assertEntitiesMatchUp(sceneInfos)

    SCENE_MANAGER.setupScene()

    doRefreshSceneInfo()
    refreshContextUI()

def doEditCam(*args):

    sMsg = "Edit the shot camera ??"
    sRes = pc.confirmDialog(title='ARE YOU SURE ?',
                            message=sMsg,
                            button=['OK', 'Cancel'],
                            defaultButton='Cancel',
                            cancelButton='Cancel',
                            dismissString='Cancel',
                            icon="question")
    if sRes == "Cancel":
        pc.displayInfo("Canceled !")
        return

    SCENE_MANAGER.editShotCam()

def doPouet(*args, **kwargs):
    """Best function ever"""

    SCENE_MANAGER.logContext()

