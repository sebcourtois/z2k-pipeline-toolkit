
from davos.core.drclibrary import DrcLibrary

from .mrctypes import MrcFile, MrcDir

class MrcLibrary(DrcLibrary):

    classFile = MrcFile
    classDir = MrcDir

    def __init__(self, sLibName, sLibPath, sSpace="", project=None):
        super(MrcLibrary, self).__init__(sLibName, sLibPath, sSpace, project)


