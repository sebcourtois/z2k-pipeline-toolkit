
import os
import os.path as osp
import re
import traceback
#from functools import partial

import pymel.core as pm
import pymel.util as pmu
import pymel.versions as pmv

from pytd.util.sysutils import inDevMode
from pytd.util.sysutils import toStr

from pytaya.util.toolsetup import ToolSetup

from davos.core.damproject import DamProject
from davos.core.damtypes import DamShot

from davos_maya.tool import file_browser
from davos_maya.tool import publishing
from davos_maya.tool.general import infosFromScene, setMayaProject

try:
    from dminutes import sceneManagerUI
except ImportError as e:
    pm.warning(e.message)
    smui = None
else:
    smui = sceneManagerUI

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
    damEntity = scnInfos.get("dam_entity")
    if isinstance(damEntity, DamShot):
        raise TypeError("Shots can ONLY be published from Scene Manager.")

    return publishing.publishCurrentScene(sceneInfos=scnInfos)

class DavosSetup(ToolSetup):

    classMenuName = "davosMenu"
    classMenuLabel = "Davos"

    def __init__(self):
        super(DavosSetup, self).__init__()

        self.publicLibrariesItems = []
        self.privateLibraryPaths = []

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
                       "mtoa.mll",
                       )

        for sPlugin in sPluginList:

            if not pm.pluginInfo(sPlugin, q=True, loaded=True):

                try:
                    pm.loadPlugin(sPlugin)
                except Exception, e:
                    pm.displayWarning(e.message)
                    continue

                pm.pluginInfo(sPlugin, e=True, autoload=True)

        return True

    def afterBuildingMenu(self):
        ToolSetup.afterBuildingMenu(self)

        bBatchMode = pm.about(batch=True)

        if not bBatchMode:
            pubLibsItems = sPrivLibPathList = []
            try:
                proj = DamProject(os.environ["DAVOS_INIT_PROJECT"])
                if proj:
                    #proj.loadEnviron()
                    allLibList = tuple(proj.iterLibraries(dbNode=False, weak=True, remember=False))

                    pubLibsItems = tuple((lib.fullName, lib.dbPath(), lib.envPath())
                                         for lib in allLibList if lib.space == "public")
                    sPrivLibPathList = tuple(lib.dbPath() for lib in allLibList
                                                            if lib.space == "private")
            except:
                traceback.print_exc()
            else:
                self.publicLibrariesItems = pubLibsItems
                self.privateLibraryPaths = sPrivLibPathList

        pmu.putEnv("DAVOS_FILE_CHECK", "1")

        pm.colorManagementPrefs(e=True, cmEnabled=False)
        pm.polyOptions(newPolymesh=True, smoothDrawType=0)

        try:
            setMayaProject(pmu.getEnv("DAVOS_INIT_PROJECT"), "ZOMB_MAYA_PROJECT_PATH")
        except Exception as e:
            pm.displayError(e.message)

        if not bBatchMode:
            if not pm.stackTrace(q=True, state=True):
                pm.mel.ScriptEditor()
                pm.mel.handleScriptEditorAction("showStackTrace")

    def beforeReloading(self, *args):

        file_browser.kill()

        if smui:
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
        if smui:
            if smui.isLaunched() and smui.isVisible():
                smui.doDetect()

    def onPreCreateReferenceCheck(self, mFileObj, clientData=None):
        """updates reference path to comply with the davos library's env. variable from where the reference belongs."""

        flags = 0
        if os.name == "nt":
            flags |= re.IGNORECASE

        try:
            sRefRawPath = osp.normpath(mFileObj.rawFullName()).replace("\\", "/")

            for sPrivLibPath in self.privateLibraryPaths:
                if osp.normcase(sPrivLibPath) in osp.normcase(sRefRawPath):
                    return True

            for _, sPubLibPath, sLibEnv in self.publicLibrariesItems:
                if osp.normcase(sPubLibPath) in osp.normcase(sRefRawPath):
                    #print re.split(sPubLibPath, sRefRawPath, 1, flags=flags)
                    sRefEnvPath = re.split(re.escape(sPubLibPath), sRefRawPath, 1, flags=flags)[-1]
                    sRefEnvPath = osp.join(sLibEnv, sRefEnvPath).replace("\\", "/")
                    if osp.isfile(osp.expanduser(osp.expandvars(sRefEnvPath))):
                        #print "\n","ref from '{}': {} ...\n    ...conformed to {}".format(sLibName,sRefRawPath, sRefEnvPath)
                        print "reference conformed to {}".format(sRefEnvPath)
                        mFileObj.setRawFullName(sRefEnvPath)
                        break
        except Exception as e:
            pm.displayError(e.message)
            traceback.print_exc()

        return True

#    def onSceneSaved(self):
#        ToolSetup.onSceneSaved(self)
#
#        if pmu.getEnv("DAVOS_FILE_CHECK", "1"):
#            fncAst.checkCgsFileState(mandatory=False)
#        else:
#            pmu.putEnv("DAVOS_FILE_CHECK", "1")
