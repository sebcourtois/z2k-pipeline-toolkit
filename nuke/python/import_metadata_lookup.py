import os
import nuke
import nukescripts

ROOT_PATH = os.path.join(os.path.expanduser("~"), "zombillenium\\z2k-pipeline-toolkit\\nuke")
METADATA_LOOK = ROOT_PATH + "\\" + "python" + "\\" + "metadata_lookup.nk"

def importMetaLookUp():
    nuke.nodePaste(METADATA_LOOK)
    
