import os
import nuke
import nukescripts

ROOT_PATH = os.path.join(os.path.expanduser("~"), "zombillenium\\z2k-pipeline-toolkit\\nuke")
ptoUV = ROOT_PATH + "\\" + "python" + "\\" + "convert_p_to_uv.nk"

def importConvertPtoUV():
    nuke.nodePaste(ptoUV)
    
