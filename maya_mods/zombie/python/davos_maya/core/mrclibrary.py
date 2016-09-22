
from davos.core.drclibrary import DrcLibrary

from .mrctypes import MrcFile, MrcDir, MrcPack

class MrcLibrary(DrcLibrary):

    classFile = MrcFile
    classDir = MrcDir
    classPack = MrcPack

    def __init__(self, sLibSection, sLibPath, sSpace="", project=None, **kwargs):
        super(MrcLibrary, self).__init__(sLibSection, sLibPath, sSpace, project, **kwargs)


