

#from functools import partial

import pymel.core as pm
import pymel.util as pmu
import pymel.versions as pmv

from pytd.util.sysutils import inDevMode
from pytd.util.sysutils import toStr

from pytaya.util.toolsetup import ToolSetup
#from pytaya.util import qtutils as myaqt
#from pytd.util.sysutils import toStr

#from davos.tools import create_dirs_n_files
from davos_maya.tool import file_browser
from davos_maya.tool import publishing

from dminutes import sceneManagerUI as smui
from davos_maya.tool.general import infosFromScene, setMayaProject
from davos.core.damtypes import DamShot

if inDevMode():
    try:
        from pytaya.util import refparser
        from davos_maya.tool import reference
    except ImportError:
        pass

def doDependencyScan(*args):
    from davos_maya.tool import dependency_scan
    dependency_scan.launch()

def doEditTextures(*args):
    from davos_maya.tool import dependency_edit
    dependency_edit.editTextureFiles()

def doSwitchReferences(*args):
    from davos_maya.tool.reference import switchSelectedReferences
    switchSelectedReferences(filter="*_ref")

def doPublish(*args):

    scnInfos = infosFromScene(fail=False)
    if isinstance(scnInfos["dam_entity"], DamShot):
        raise TypeError("Shots can only be published from Scene Manager.")

    publishing.publishCurrentScene(sceneInfos=scnInfos)

class DavosSetup(ToolSetup):

    classMenuName = "davosMenu"
    classMenuLabel = "Davos"

    def __init__(self):
        super(DavosSetup, self).__init__()

    def populateMenu(self):

        with self.menu:

            pm.menuItem(label="File Browser", c=file_browser.launch)
            pm.menuItem(divider=True)

            pm.menuItem(label="Edit Textures...", c=doEditTextures)
            pm.menuItem(label="Check Dependencies...", c=doDependencyScan)
            pm.menuItem(label="Publish...", c=doPublish)

        ToolSetup.populateMenu(self)

    def beforeBuildingMenu(self):

        if not ToolSetup.beforeBuildingMenu(self):
            return False

        sPluginList = ("AbcExport.mll",
                       "AbcImport.mll",
                       "atomImportExport.mll",
                       "matrixNodes.mll" if (pmv.current() > pmv.v2013) else "decomposeMatrix.mll",
                       )

        for sPlugin in sPluginList:

            if not pm.pluginInfo(sPlugin, q=True, loaded=True):

                try:
                    pm.loadPlugin(sPlugin)
                except Exception, msg:
                    pm.displayWarning(msg)
                    continue

                pm.pluginInfo(sPlugin, e=True, autoload=True)

        return True

    def afterBuildingMenu(self):
        ToolSetup.afterBuildingMenu(self)

        pmu.putEnv("DAVOS_FILE_CHECK", "1")

        pm.colorManagementPrefs(e=True, cmEnabled=False)
        pm.polyOptions(newPolymesh=True, smoothDrawType=0)

        try:
            setMayaProject(pmu.getEnv("DAVOS_INIT_PROJECT"), "ZOMB_MAYA_PROJECT_PATH")
        except ValueError as e:
            pm.displayError(e.message)

        if not pm.about(batch=True):
            if not pm.stackTrace(q=True, state=True):
                pm.mel.ScriptEditor()
                pm.mel.handleScriptEditorAction("showStackTrace")

    def beforeReloading(self, *args):
        file_browser.kill()

        try:
            smui.kill()
        except Exception as e:
            pm.displayInfo("Could not kill 'sceneManagerUI': {}".format(toStr(e)))

        ToolSetup.beforeReloading(self, *args)

    def onPreFileNewOrOpened(self, *args):
        ToolSetup.onPreFileNewOrOpened(self, *args)
        pm.colorManagementPrefs(e=True, cmEnabled=False)

    def onSceneOpened(self, *args):
        ToolSetup.onSceneOpened(self, *args)

        if smui.isLaunched() and smui.isVisible():
            smui.doDetect()

#    def onSceneSaved(self):
#        ToolSetup.onSceneSaved(self)
#
#        if pmu.getEnv("DAVOS_FILE_CHECK", "1"):
#            fncAst.checkCgsFileState(mandatory=False)
#        else:
#            pmu.putEnv("DAVOS_FILE_CHECK", "1")
