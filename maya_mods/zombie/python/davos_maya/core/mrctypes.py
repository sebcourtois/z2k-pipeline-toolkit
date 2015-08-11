
from davos.core.drctypes import DrcDir, DrcFile


class MrcDir(DrcDir):

    def __init__(self, drcLib, absPathOrInfo=None, **kwargs):
        super(MrcDir, self).__init__(drcLib, absPathOrInfo, **kwargs)


class MrcFile(DrcFile):

    def __init__(self, drcLib, absPathOrInfo=None, **kwargs):
        super(MrcFile, self).__init__(drcLib, absPathOrInfo, **kwargs)