import os
import nuke
import nukescripts

ROOT_PATH = os.path.join(os.path.expanduser("~"), "zombillenium\\z2k-pipeline-toolkit\\nuke")
READER_FAST = ROOT_PATH + "\\" + "python" + "\\" + "fast_finder.nk"

def importFastFinder():
    nuke.nodePaste(READER_FAST)
    
