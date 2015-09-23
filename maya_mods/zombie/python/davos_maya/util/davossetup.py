

from pytaya.util.toolsetup import ToolSetup
from davos_maya.tool import file_browser

import pymel.core as pm

class DavosSetup(ToolSetup):

    classMenuName = "davosMenu"
    classMenuLabel = "Davos Tools"

    def __init__(self):
        super(DavosSetup, self).__init__()

    def populateMenu(self):

        with self.menu:
            pm.menuItem(label="File Browser", c=file_browser.launch)

        ToolSetup.populateMenu(self)