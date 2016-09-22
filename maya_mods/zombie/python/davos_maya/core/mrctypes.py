
import os.path as osp

import pymel.core as pm
import pymel.versions as pmv

from davos.core.drctypes import DrcDir, DrcFile, DrcPack
from pytaya.core import system as myasys
from pytd.util.strutils import padded, underJoin
from pytd.util.fsutils import pathEqual
from davos.core.utils import mkVersionSuffix
#from pytd.util.fsutils import pathSuffixed


class MrcDir(DrcDir):

    def __init__(self, drcLib, absPathOrInfo=None, **kwargs):
        super(MrcDir, self).__init__(drcLib, absPathOrInfo, **kwargs)

    def _publishFiles(self, sSrcPathList, **kwargs):

        global SCRIPT_EDITOR_SHOWN

        showScriptEditor()
        try:
            res = DrcDir._publishFiles(self, sSrcPathList, **kwargs)
        finally:
            SCRIPT_EDITOR_SHOWN = False

        return res

class MrcFile(DrcFile):

    def __init__(self, drcLib, absPathOrInfo=None, **kwargs):
        super(MrcFile, self).__init__(drcLib, absPathOrInfo, **kwargs)

    def edit(self, openFile=False, existing="", prompt=False, **kwargs):

        self.library.project.assertMayaVersion(pmv.current())
        self.assertIsMayaScene()

        privFile = DrcFile.edit(self, openFile=openFile, existing=existing, prompt=prompt)

        if openFile and privFile:
            if not privFile.mayaOpen(checkFile=False, **kwargs):
                self.restoreLockState()

        return privFile

    def assertIsMayaScene(self):

        p = self.absPath()
        _, sExt = osp.splitext(p)
        if sExt not in (".ma", ".mb"):
            raise AssertionError("Not a Maya Scene:\n'{}'".format(p))

        return p

    def mayaOpen(self, **kwargs):

        bCheckFile = kwargs.pop("checkFile", True)
        sExisting = kwargs.pop("existing", "")
        bPrompt = kwargs.pop("prompt", False)

        if bCheckFile:
            assert self.isFile(), "File does NOT exists !"
            self.assertIsMayaScene()

        if self.isPublic():
            sVersSuffix = ""
            if self.versionFromName() is None:
                sVersSuffix = mkVersionSuffix(self.currentVersion)

            srcFile = None

            if not self.isVersionFile():
                srcFile = self.assertLatestFile(refresh=True, newerFix=False,
                                                prompt=bPrompt, strict=bPrompt)
                if srcFile == self:
                    srcFile = None

            sSuffix = "".join((sVersSuffix, '-', 'readonly'))
            privFile, _ = self.copyToPrivateSpace(suffix=sSuffix, existing=sExisting,
                                                  sourceFile=srcFile)
        else:
            privFile = self

        if not privFile:
            return

        result = myasys.saveScene(discard=True)
        if not result:
            return

        sRefDepth = kwargs.pop("loadReferenceDepth", kwargs.pop("lrd", None))
        if sRefDepth is None:
            if not self.library.project.mayaLoadReferences:
                kwargs["loadReferenceDepth"] = "none"
        elif sRefDepth != "default":
            kwargs["loadReferenceDepth"] = sRefDepth

        return myasys.openScene(privFile.absPath(), force=True, fail=False, **kwargs)

    def mayaImportScene(self, **kwargs):

        sNamespace = kwargs.pop("namespace", kwargs.pop("ns", ""))
        bAsRef = kwargs.pop("reference", kwargs.pop("r", True))

        sRefDepth = kwargs.pop("loadReferenceDepth", kwargs.pop("lrd", None))
        if sRefDepth is None:
            if not self.library.project.mayaLoadReferences:
                kwargs["loadReferenceDepth"] = "none"
        elif sRefDepth != "default":
            kwargs["loadReferenceDepth"] = sRefDepth

        if self.isPublic():

            p = self.envPath()

            if not sNamespace:
                damEntity = self.getEntity()
                if damEntity:
                    refDir = damEntity.getResource("public", "ref_dir", fail=False)
                    if refDir and pathEqual(self.parentDir().absPath(), refDir.absPath()):
                        sNamespace = underJoin((damEntity.name, padded(1, 2)))
        else:
            p = self.absPath()

        if not sNamespace:
            sNamespace = underJoin((self.name.split(".", 1)[0], padded(1, 2)))

        return myasys.importFile(p, reference=bAsRef, namespace=sNamespace, **kwargs)

    def mayaImportImage(self):

        if self.isPublic():
            sEnvVarList = self.library.getVar("public_path_envars")
            if "ZOMB_TEXTURE_PATH" in sEnvVarList:
                p = self.envPath("ZOMB_TEXTURE_PATH")
            else:
                p = self.envPath()
        else:
            p = self.absPath()

        return pm.mel.importImageFile(p, False, False, True)


class MrcPack(DrcPack):

    def __init__(self, drcLib, absPathOrInfo=None, **kwargs):
        super(MrcPack, self).__init__(drcLib, absPathOrInfo, **kwargs)

    def _makeCopyOf(self, sSrcPackPath, **kwargs):

        if kwargs.pop("showScriptEditor", True):
            kwargs["beforeCopyCall"] = showScriptEditor

        return DrcPack._makeCopyOf(self, sSrcPackPath, **kwargs)

SCRIPT_EDITOR_SHOWN = False
def showScriptEditor():
    global SCRIPT_EDITOR_SHOWN
    if not SCRIPT_EDITOR_SHOWN:
        pm.mel.ScriptEditor()
        pm.mel.handleScriptEditorAction("maximizeHistory")
        SCRIPT_EDITOR_SHOWN = True
