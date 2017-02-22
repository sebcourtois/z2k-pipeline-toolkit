import os
import nuke
import nukescripts

ROOT_PATH = os.path.join(os.path.expanduser("~"), "zombillenium\\z2k-pipeline-toolkit\\nuke")
COMBINE_D = ROOT_PATH + "\\" + "python" + "\\" + "combine_depth.nk"

def importCombineDepth():
    nuke.nodePaste(COMBINE_D)
    
