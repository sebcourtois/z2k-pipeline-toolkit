import os
import nuke
import nukescripts

ROOT_PATH = os.path.join(os.path.expanduser("~"), "zombillenium\\z2k-pipeline-toolkit\\nuke")
FAST_RELIGHT = ROOT_PATH + "\\" + "python" + "\\" + "fast_relight.nk"

def importFastRelight():
    nuke.nodePaste(FAST_RELIGHT)
    
