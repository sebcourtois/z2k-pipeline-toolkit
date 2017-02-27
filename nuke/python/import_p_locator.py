import os
import nuke
import nukescripts

ROOT_PATH = os.path.join(os.path.expanduser("~"), "zombillenium\\z2k-pipeline-toolkit\\nuke")
COMP_LOCATOR = ROOT_PATH + "\\" + "python" + "\\" + "p_locator.nk"

def importCompLoc():
    #nuke.selectAll()
    #nukescripts.node_delete(popupOnError=True)
    nuke.nodePaste(COMP_LOCATOR)
    
