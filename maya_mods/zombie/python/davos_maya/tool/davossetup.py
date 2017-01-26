
import os
import os.path as osp
import re
import traceback
#from functools import partial
import glob

import maya.cmds as mc

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
from pytd.util.fsutils import copyFile, pathJoin

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
    reload(dependency_scan)
    dependency_scan.launch()

def doEditTextures(*args):
    from davos_maya.tool import dependency_edit
    dependency_edit.editTextureFiles()

def doPublish(*args):

    scnInfos = infosFromScene(fail=False)
    damEntity = scnInfos.get("dam_entity")
    if isinstance(damEntity, DamShot):
        raise TypeError("Shots can ONLY be published from Scene Manager.")

    return publishing.publishCurrentScene(sceneInfos=scnInfos)

def loadPlugins():

    sPluginList = ("AbcExport.mll",
                   "AbcImport.mll",
                   "atomImportExport.mll",
                   "matrixNodes.mll" if (pmv.current() > pmv.v2013) else "decomposeMatrix.mll",
                   "nearestPointOnMesh.mll",# for stickyDeformer
                   "pointOnMeshInfo.mll",# bonus tools for stickyDeformer
                   "closestPointOnCurve.mll", # bonus tools for stickyDeformer
                   "mtoa.mll", # arnold
                   "gpuCache.mll",
                   )

    for sPlugin in sPluginList:

        if not pm.pluginInfo(sPlugin, q=True, loaded=True):

            try:
                pm.loadPlugin(sPlugin)
            except Exception as e:
                pm.displayWarning(toStr(e))
            else:
                pm.pluginInfo(sPlugin, e=True, autoload=True)

    if os.environ.get("DAVOS_SITE", "") == "dmn_paris":
        sPlugin = "rrSubmit_Maya_Z2K.py"
        if not pm.pluginInfo(sPlugin, q=True, loaded=True):
            try:
                pm.loadPlugin(sPlugin)
            except Exception as e:
                pm.displayWarning(toStr(e))
            else:
                pm.pluginInfo(sPlugin, e=True, autoload=True)

                sOldPlugin = "rrSubmit_Maya_2016+Z2K.py"
                if pm.pluginInfo(sOldPlugin, q=True, loaded=True):
                    pm.loadPlugin(sOldPlugin)

class DavosSetup(ToolSetup):

    classMenuName = "davosMenu"
    classMenuLabel = "Davos"

    def __init__(self):
        super(DavosSetup, self).__init__()

        self.project = None
        self.publicLibrariesItems = []
        self.privateLibraryPaths = []
        self.copiedXgnFileNames = []

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

        #bBatchMode = pm.about(batch=True)
        loadPlugins()

        try:
            setMayaProject(pmu.getEnv("DAVOS_INIT_PROJECT"), "ZOMB_MAYA_PROJECT_PATH")
        except Exception as e:
            pm.displayError(toStr(e))

        pubLibsItems = []
        #sPrivLibPathList = []
        try:
            proj = DamProject(os.environ["DAVOS_INIT_PROJECT"], empty=True, standalone=True)
            if proj:
                allLibList = tuple(proj.iterLibraries(dbNode=False, weak=True, remember=False))

                pubLibsItems = tuple((lib.fullName, lib.dbPath(), lib.envPath())
                                     for lib in allLibList if lib.space == "public")
#                sPrivLibPathList = tuple(lib.dbPath() for lib in allLibList
#                                                        if lib.space == "private")
            self.project = proj
        except:
            traceback.print_exc()
        else:
            self.publicLibrariesItems = pubLibsItems
            #self.privateLibraryPaths = sPrivLibPathList

        pmu.putEnv("DAVOS_FILE_CHECK", "1")

        return True

    def afterBuildingMenu(self):
        ToolSetup.afterBuildingMenu(self)

        bBatchMode = pm.about(batch=True)

        pm.colorManagementPrefs(e=True, cmEnabled=False)
        pm.polyOptions(newPolymesh=True, smoothDrawType=0)

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

        sPanelList = mc.getPanel(type="modelPanel")
        if sPanelList:
            for sPanel in sPanelList:
                try:
                    mc.modelEditor(sPanel, e=True,
                                   particleInstancers=False,
                                   pluginShapes=False)
                except RuntimeError as e:
                    pm.displayWarning(toStr(e))

        if smui:
            if smui.isLaunched():
                smui.doDetect()

    def onPreCreateReferenceCheck(self, mFileObj, clientData=None):
        """updates reference path to comply with the davos library's env. variable from where the reference belongs."""
        ToolSetup.onPreCreateReferenceCheck(self, mFileObj, clientData)

        flags = 0
        if os.name == "nt":
            flags |= re.IGNORECASE

        sRefRawPath = osp.normpath(mFileObj.rawFullName()).replace("\\", "/")

        if "/private/" not in osp.normcase(sRefRawPath):
            for _, sPubLibPath, sLibEnv in self.publicLibrariesItems:
                if osp.normcase(sPubLibPath) in osp.normcase(sRefRawPath):
                    #print re.split(sPubLibPath, sRefRawPath, 1, flags=flags)
                    sRefEnvPath = re.split(re.escape(sPubLibPath),
                                           sRefRawPath, 1, flags=flags)[-1]
                    sRefEnvPath = osp.join(sLibEnv, sRefEnvPath).replace("\\", "/")
                    if osp.isfile(osp.expanduser(osp.expandvars(sRefEnvPath))):
                        #print "\n","ref from '{}': {} ...\n    ...conformed to {}".format(sLibSection,sRefRawPath, sRefEnvPath)
                        print "reference conformed to {}".format(sRefEnvPath)
                        mFileObj.setRawFullName(sRefEnvPath)
                        break

        sCurScnPath = self.currentSceneName
        if sCurScnPath and ("/private/" in sCurScnPath.lower()):
            sRefResPath = osp.normpath(mFileObj.resolvedFullName()).replace("\\", "/")
            if ("/set/" in sRefResPath) and ("/ref/" in sRefResPath):
                sCopiedXgnFileList = self.copiedXgnFileNames
                sCurScnDir = osp.dirname(sCurScnPath)
                sAstDirPath = osp.normpath(sRefResPath.rsplit("/ref/", 1)[0])
                for sXgnFilePath in glob.iglob(sAstDirPath + "\\*.xgen"):
                    
                    sFilename = osp.basename(sXgnFilePath)
                    if sFilename in sCopiedXgnFileList:
                        pm.displayInfo("Xgen file already copied from current shot's data directory: '{}'"
                                       .format(sFilename))
                        continue

#                    sDstPath = pathJoin(sCurScnDir, sFilename)
#                    if os.environ.get("OVERWRITE_XGEN_FILES") or (not osp.exists(sDstPath)):
                    bUpdate = False if os.environ.get("FORCE_XGEN_FILES_COPY") else True
                    try:
                        copyFile(sXgnFilePath, sCurScnDir, update=bUpdate)
                    except EnvironmentError as e:
                        pm.displayError(toStr(e))
        return True

    def onBeforeOpenCheck(self, mFileObj, clientData=None):
        ToolSetup.onBeforeOpenCheck(self, mFileObj, clientData=clientData)
        
        self.copiedXgnFileNames = []

        sCurScnPath = self.currentSceneName
        sDataDirPath = ""
        proj = self.project
        sLowerScnPath = sCurScnPath.lower()
        if ("/private/" in sLowerScnPath):
            if ("/zomb/shot/" in sLowerScnPath):
                sShotCode = "_".join(osp.basename(sCurScnPath).split("_")[:2])
                damShot = proj.getShot(sShotCode)
                sDataDirPath = damShot.getPath("public", "data_dir")
            elif ("/zomb/asset/" in sLowerScnPath):
                sAstName = "_".join(osp.basename(sCurScnPath).split("_")[:3])
                damAst = proj.getAsset(sAstName)
                sDataDirPath = damAst.getPath("public", "entity_dir")

        if sDataDirPath:
            sCurScnDir = osp.dirname(sCurScnPath)
            for sXgnFilePath in glob.iglob(osp.normpath(sDataDirPath + "/*.xgen")):
                sFilename = osp.basename(sXgnFilePath)
#                sDstPath = pathJoin(sCurScnDir, sFilename)
#                if os.environ.get("OVERWRITE_XGEN_FILES") or (not osp.exists(sDstPath)):
                bUpdate = False if os.environ.get("FORCE_XGEN_FILES_COPY") else True
                try:
                    copyFile(sXgnFilePath, sCurScnDir, update=bUpdate)
                except EnvironmentError as e:
                    pm.displayError(toStr(e))
                else:
                    self.copiedXgnFileNames.append(sFilename)

        return True

#    def onSceneSaved(self):
#        ToolSetup.onSceneSaved(self)
#
#        if pmu.getEnv("DAVOS_FILE_CHECK", "1"):
#            fncAst.checkCgsFileState(mandatory=False)
#        else:
#            pmu.putEnv("DAVOS_FILE_CHECK", "1")
