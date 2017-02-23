import os
import nuke
import nukescripts

ROOT_PATH = os.path.join(os.path.expanduser("~"), "zombillenium\\z2k-pipeline-toolkit\\nuke")
MOTION_PASS = ROOT_PATH + "\\" + "python" + "\\" + "fake_motion_pass.nk"

def importMotionPass():
    nuke.nodePaste(MOTION_PASS)