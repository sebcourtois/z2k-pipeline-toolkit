import maya.cmds as cmds
import maya.mel as mel

#taking an sourceItem.attr, create a timeOffset of this attr on targetItem.targetAttr ( offset controlled by an attribute "offset" created on targetItem )
def offsetAttr(sourceItem,sourceAttr,targetItem,targetAttr):
    
    if not cmds.attributeQuery(targetAttr+'Offset',n=item,exists=True):
        cmds.addAttr(targetItem,ln=targetAttr+'Offset',k=True,at='double')
    
    frameCache = cmds.createNode('frameCache')
    plusMinusAverage = cmds.createNode('plusMinusAverage')

    cmds.connectAttr('time1.outTime',plusMinusAverage+'.input1D[0]')
    cmds.connectAttr(targetItem+'.'+targetAttr+'Offset',plusMinusAverage+'.input1D[1]',f=True)
    cmds.connectAttr(plusMinusAverage+'.output1D',frameCache+'.varyTime')    
    cmds.connectAttr(sourceItem+'.'+sourceAttr,frameCache+'.stream')
    
    cmds.connectAttr(frameCache+'.varying',targetItem+'.'+targetAttr)