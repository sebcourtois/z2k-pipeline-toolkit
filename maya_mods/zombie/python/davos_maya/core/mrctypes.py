
import os.path as osp

import pymel.core as pm
import pymel.versions as pmv

from davos.core.drctypes import DrcDir, DrcFile
from pytaya.core import system as myasys
from pytd.util.strutils import padded, underJoin
from pytd.util.fsutils import normCase
#from pytd.util.fsutils import pathSuffixed


class MrcDir(DrcDir):

    def __init__(self, drcLib, absPathOrInfo=None, **kwargs):
        super(MrcDir, self).__init__(drcLib, absPathOrInfo, **kwargs)


class MrcFile(DrcFile):

    def __init__(self, drcLib, absPathOrInfo=None, **kwargs):
        super(MrcFile, self).__init__(drcLib, absPathOrInfo, **kwargs)

    def edit(self, openFile=False, existing=""):

        self.library.project.assertMayaVersion(pmv.current())
        self.assertIsMayaScene()

        privFile = DrcFile.edit(self, openFile=False, existing=existing)

        if openFile and privFile:
            privFile.mayaOpen(checkFile=False)

        return privFile

    def assertIsMayaScene(self):

        p = self.absPath()
        _, sExt = osp.splitext(p)
        if sExt not in (".ma", ".mb"):
            raise AssertionError("Not a Maya Scene:\n'{}'".format(p))

        return p

    def mayaOpen(self, checkFile=True, **kwargs):

        if checkFile:
            assert self.isFile(), "File does NOT exists !"
            self.assertIsMayaScene()

        if self.isPublic():
            sWordList = (self.versionSuffix(self.currentVersion), '-', 'readonly')
            sOpenSuffix = "".join(sWordList)
            privFile, _ = self.copyToPrivateSpace(suffix=sOpenSuffix, **kwargs)
        else:
            privFile = self

        result = myasys.saveScene(discard=True)
        if not result:
            return

        return myasys.openScene(privFile.absPath(), force=True)

    def mayaImportScene(self, *args, **kwargs):

        sNamespace = ""
        p = self.absPath()

        if self.isPublic():

            p = self.envPath()

            damEntity = self.getEntity(fail=True)
            refDir = damEntity.getResource("public", "ref_dir", None)
            if refDir and (normCase(self.parentDir().absPath()) == normCase(refDir.absPath())):
                sNamespace = underJoin((damEntity.name, padded(1, 2)))

        if not sNamespace:
            sNamespace = underJoin((self.name.split(".", 1)[0], padded(1, 2)))

        return myasys.importFile(p, reference=True, ns=sNamespace, **kwargs)

    def mayaImportImage(self):

        if self.isPublic():
            p = self.envPath("ZOMB_TEXTURE_PATH")
        else:
            p = self.absPath()

        return pm.mel.importImageFile(p, False, False, True)
