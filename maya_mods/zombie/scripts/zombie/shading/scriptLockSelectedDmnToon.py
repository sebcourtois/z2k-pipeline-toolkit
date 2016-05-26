import maya.cmds as mc
from dminutes import shading
reload (shading)
        
    
myNode = mc.ls(selection = True)
if not myNode:
    myNode=[]
    

shading.scriptLockShadingNode(nodeList=myNode,lock=True, type="dmnToon")