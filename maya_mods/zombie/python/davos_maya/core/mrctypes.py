

#import pymel.core as pm
import pymel.versions as pmv

from davos.core.drctypes import DrcDir, DrcFile
from pytaya.core.system import saveFile, openFile


class MrcDir(DrcDir):

    def __init__(self, drcLib, absPathOrInfo=None, **kwargs):
        super(MrcDir, self).__init__(drcLib, absPathOrInfo, **kwargs)


class MrcFile(DrcFile):

    def __init__(self, drcLib, absPathOrInfo=None, **kwargs):
        super(MrcFile, self).__init__(drcLib, absPathOrInfo, **kwargs)

    def edit(self, **kwargs):

        self.assertMayaVersion()

        privFile = DrcFile.edit(self)
        if not privFile:
            self.restoreLockState()
            return None

        result = saveFile(discard=True)
        if result == '_cancelled_':
            self.restoreLockState()
            return None

        sFilePath = privFile.absPath()
        openFile(sFilePath, force=True)

        return privFile

    def assertMayaVersion(self):

        proj = self.library.project

        sMayaProjVersion = str(proj.getVar("project", "maya_version"))
        sMayaVersion = pmv.flavor()

        if sMayaVersion != sMayaProjVersion:
            sMsg = ("{0} requires Maya {1}, but you're running Maya {2} !"
                    .format(proj, sMayaProjVersion, sMayaVersion))
            raise EnvironmentError, sMsg
