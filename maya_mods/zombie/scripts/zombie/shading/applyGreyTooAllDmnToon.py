import maya.cmds as mc
from dminutes import miscUtils

allDmnToonL = mc.ls("mat_*",type="dmnToon")

for each in allDmnToonL:
    miscUtils.setAttrC(each+'.ambientColor', 0.733, 0.733, 0.733, type = "double3")
    miscUtils.setAttrC(each+'.diffuseColor', 0.733, 0.733, 0.733, type = "double3")
    
allLambertL = allLambertL = mc.ls("pre_*",type="lambert")

for each in allDmnToonL:
    miscUtils.setAttrC(each+'.color', 0.733, 0.733, 0.733, type = "double3")
