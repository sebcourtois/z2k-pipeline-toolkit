import os
import nuke
import nukescripts

ROOT_PATH = os.path.join(os.path.expanduser("~"), "zombillenium\\z2k-pipeline-toolkit\\nuke")
ptoZ = ROOT_PATH + "\\" + "python" + "\\" + "convert_p_to_z.nk"

def importConvertPtoZ():
    nuke.nodePaste(ptoZ)
    
