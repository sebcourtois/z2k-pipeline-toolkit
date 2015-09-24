
import pymel.core as pm

from pytaya.util.toolsetup import ToolSetup
#from pytd.gui.dialogs import confirmDialog
#from pytd.util.sysutils import toStr

from davos_maya.tool import file_browser
from davos_maya.tool import publishing

class DavosSetup(ToolSetup):

    classMenuName = "davosMenu"
    classMenuLabel = "Davos"

    def __init__(self):
        super(DavosSetup, self).__init__()

    def populateMenu(self):

        with self.menu:
            pm.menuItem(label="Asset Browser", c=file_browser.launch)
            pm.menuItem(label="Publish...", c=publishing.publishCurrentScene)

        ToolSetup.populateMenu(self)