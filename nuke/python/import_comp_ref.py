import nuke
import nukescripts
import sys
import os

COMP_REF = os.environ['USERPROFILE'] + '\\zombillenium\\z2k-pipeline-toolkit\\nuke\\template\\'
lastTemplate = []
for file in os.listdir(COMP_REF):
    if file.endswith(".nk"):
        lastTemplate.append(file)
newTemplatePath = COMP_REF + lastTemplate[0]
print newTemplatePath

def importCompRef():
    #nuke.selectAll()
    #nukescripts.node_delete(popupOnError=True)
    nuke.nodePaste(newTemplatePath)
