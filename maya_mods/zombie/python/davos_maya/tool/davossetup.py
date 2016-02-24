

import pymel.core as pm
import pymel.util as pmu

import pymel.versions
pmv = pymel.versions

from functools import partial

from pytaya.util.toolsetup import ToolSetup
from pytaya.util import qtutils as myaqt
#from pytd.util.sysutils import toStr

from davos.tools import create_dirs_n_files

from davos_maya.tool import file_browser
from davos_maya.tool import publishing
from pytd.util.sysutils import inDevMode

from pytd.util.sysutils import toStr

if inDevMode():
    try:
        from pytaya.util import refparser
        from davos_maya.tool import reference
    except ImportError:
        pass

def doCreateFolders(sEntiType, *args):
    create_dirs_n_files.launch(sEntiType, dryRun=False,
                               dialogParent=myaqt.mayaMainWindow())

def doDependencyScan(*args):
    from davos_maya.tool import dependency_scan
    dependency_scan.launch()

def doEditTextures(*args):
    from davos_maya.tool import dependency_edit
    dependency_edit.editTextureFiles()

def doSwitchReferences(*args):
    from davos_maya.tool.reference import switchSelectedReferences
    switchSelectedReferences(filter="*_ref")

class DavosSetup(ToolSetup):

    classMenuName = "davosMenu"
    classMenuLabel = "Davos"

    def __init__(self):
        super(DavosSetup, self).__init__()

    def populateMenu(self):

        with self.menu:

            pm.menuItem(label="File Browser", c=file_browser.launch)
            pm.menuItem(divider=True)

            with pm.subMenuItem(label="Create Folders", to=False):
                pm.menuItem(label="Assets...", c=partial(doCreateFolders, "asset"))
                pm.menuItem(label="Shots...", c=partial(doCreateFolders, "shot"))

            pm.menuItem(label="Switch References", c=doSwitchReferences)
            pm.menuItem(divider=True)
            pm.menuItem(label="Edit Textures...", c=doEditTextures)
            pm.menuItem(label="Check Dependencies...", c=doDependencyScan)
            pm.menuItem(label="Publish...", c=publishing.publishCurrentScene)

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

        if not pm.about(batch=True):
            if not pm.stackTrace(q=True, state=True):
                pm.mel.ScriptEditor()
                pm.mel.handleScriptEditorAction("showStackTrace")

        import logging

        sMuteModList = ["requests.packages.urllib3.connectionpool",
                        "pytd.util.external.parse",
                        "PIL.Image", ]

#        if inDevMode():
#            sMuteModList[0] = ""

        for sModule in sMuteModList:

            if not sModule:
                continue

            try:
                logger = logging.getLogger(sModule)
                if logger:
                    logger.disabled = True
            except Exception as e:
                pm.displayWarning(toStr(e))

    def beforeReloading(self, *args):
        file_browser.kill()

        try:
            from dminutes import sceneManagerUI
            sceneManagerUI.kill()
        except Exception as e:
            pm.displayInfo("Could not kill 'sceneManagerUI': {}".format(toStr(e)))

        ToolSetup.beforeReloading(self, *args)

    def onPreFileNewOrOpened(self, *args):
        ToolSetup.onPreFileNewOrOpened(self, *args)
        pm.colorManagementPrefs(e=True, cmEnabled=False)

#    def onSceneOpened(self, *args):
#        ToolSetup.onSceneOpened(self, *args)
#
#        if pmu.getEnv("DAVOS_FILE_CHECK", "1"):
#            fncAst.checkCgsFileState(warnNotLocked=False)
#        else:
#            pmu.putEnv("DAVOS_FILE_CHECK", "1")
#
#    def onSceneSaved(self):
#        ToolSetup.onSceneSaved(self)
#
#        if pmu.getEnv("DAVOS_FILE_CHECK", "1"):
#            fncAst.checkCgsFileState(mandatory=False)
#        else:
#            pmu.putEnv("DAVOS_FILE_CHECK", "1")
