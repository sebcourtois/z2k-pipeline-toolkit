
import os.path as osp

import pymel.core as pm
import pymel.versions as pmv

from davos.core.drctypes import DrcDir, DrcFile
from pytaya.core import system as myasys
from pytd.util.strutils import padded, underJoin
from pytd.util.fsutils import normCase
from davos.core.utils import mkVersionSuffix
#from pytd.util.fsutils import pathSuffixed


class MrcDir(DrcDir):

    def __init__(self, drcLib, absPathOrInfo=None, **kwargs):
        super(MrcDir, self).__init__(drcLib, absPathOrInfo, **kwargs)


class MrcFile(DrcFile):

    def __init__(self, drcLib, absPathOrInfo=None, **kwargs):
        super(MrcFile, self).__init__(drcLib, absPathOrInfo, **kwargs)

    def edit(self, openFile=False, existing="", **kwargs):

        self.library.project.assertMayaVersion(pmv.current())
        self.assertIsMayaScene()

        privFile = DrcFile.edit(self, openFile=False, existing=existing)

        if openFile and privFile:
            kwargs['loadReferenceDepth'] = "default"
            privFile.mayaOpen(checkFile=False, **kwargs)

        return privFile

    def assertIsMayaScene(self):

        p = self.absPath()
        _, sExt = osp.splitext(p)
        if sExt not in (".ma", ".mb"):
            raise AssertionError("Not a Maya Scene:\n'{}'".format(p))

        return p

    def mayaOpen(self, checkFile=True, existing="", **kwargs):

        if checkFile:
            assert self.isFile(), "File does NOT exists !"
            self.assertIsMayaScene()

        if self.isPublic():
            sVersSuffix = ""
            if self.versionFromName() is None:
                sVersSuffix = mkVersionSuffix(self.currentVersion)

            sWordList = (sVersSuffix, '-', 'readonly')
            sSuffix = "".join(sWordList)
            privFile, _ = self.copyToPrivateSpace(suffix=sSuffix, existing=existing)
        else:
            privFile = self

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
                    refDir = damEntity.getResource("public", "ref_dir", None)
                    if refDir and (normCase(self.parentDir().absPath()) == normCase(refDir.absPath())):
                        sNamespace = underJoin((damEntity.name, padded(1, 2)))
        else:
            p = self.absPath()

        if not sNamespace:
            sNamespace = underJoin((self.name.split(".", 1)[0], padded(1, 2)))

        return myasys.importFile(p, reference=True, namespace=sNamespace, **kwargs)

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
