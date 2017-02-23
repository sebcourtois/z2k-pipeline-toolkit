import os
import nuke
import nukescripts

ROOT_PATH = os.path.join(os.path.expanduser("~"), "zombillenium\\z2k-pipeline-toolkit\\nuke")
CAM_METADATA = ROOT_PATH + "\\" + "python" + "\\" + "camera_metadata.nk"

def importBakedCam():
    nuke.nodePaste(CAM_METADATA)
    
