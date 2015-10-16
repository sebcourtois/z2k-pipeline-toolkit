
import os
import pymel.core as pm
import pymel.util as pmu

from davos.core.damproject import DamProject
from pytaya.util.toolsetup import ToolSetup
#from pytd.util.sysutils import toStr

from davos_maya.tool import file_browser
from davos_maya.tool import publishing


def loadProject():

    bBatchMode = pm.about(batch=True)
    proj = DamProject(os.environ["DAVOS_INIT_PROJECT"], empty=bBatchMode)
    proj.loadEnviron()

class DavosSetup(ToolSetup):

    classMenuName = "davosMenu"
    classMenuLabel = "Davos"

    def __init__(self):
        super(DavosSetup, self).__init__()

    def populateMenu(self):

        with self.menu:
            pm.menuItem(label="Asset Browser", c=file_browser.launch)
            pm.menuItem(label="Publish...", c=publishing.publishCurrentScene)

        ToolSetup.populateMenu(self)

    def afterBuildingMenu(self):
        ToolSetup.afterBuildingMenu(self)
        pmu.putEnv("DAVOS_FILE_CHECK", "1")
        pm.colorManagementPrefs(e=True, cmEnabled=False)

    def beforeReloading(self, *args):
        file_browser.kill()
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
