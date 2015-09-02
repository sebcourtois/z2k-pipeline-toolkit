
import os.path as osp

#import pymel.core as pm
import pymel.versions as pmv

from davos.core.drctypes import DrcDir, DrcFile
from pytaya.core import system as myasys
#from pytd.util.fsutils import pathSuffixed


class MrcDir(DrcDir):

    def __init__(self, drcLib, absPathOrInfo=None, **kwargs):
        super(MrcDir, self).__init__(drcLib, absPathOrInfo, **kwargs)


class MrcFile(DrcFile):

    def __init__(self, drcLib, absPathOrInfo=None, **kwargs):
        super(MrcFile, self).__init__(drcLib, absPathOrInfo, **kwargs)

    def edit(self, openFile=False, existing=""):

        self.assertMayaVersion()
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

    def assertMayaVersion(self):

        proj = self.library.project

        sMayaProjVersion = str(proj.getVar("project", "maya_version"))
        sMayaVersion = pmv.flavor()

        if sMayaVersion != sMayaProjVersion:
            sMsg = ("{0} requires Maya {1}, but you're running Maya {2} !"
                    .format(proj, sMayaProjVersion, sMayaVersion))
            raise EnvironmentError(sMsg)

    def mayaOpen(self, checkFile=True):

        if checkFile:
            assert self.isFile(), "File does NOT exists !"
            self.assertIsMayaScene()

        if self.isPublic():
            sOpenSuffix = "".join((self.versionSuffix(), '-', 'temp'))
            privFile, _ = self.copyToPrivateSpace(suffix=sOpenSuffix)
        else:
            privFile = self

        result = myasys.saveScene(discard=True)
        if result == '_cancelled_':
            return

        return myasys.openScene(privFile.absPath(), force=True)
