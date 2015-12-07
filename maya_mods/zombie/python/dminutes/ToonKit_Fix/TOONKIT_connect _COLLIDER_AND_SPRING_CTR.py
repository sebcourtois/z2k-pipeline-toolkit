# connect TOONKIT COLLIDER AND SPRING CTR
# v001
# tmp, use in case of hair and body dynamics not working at all
# this doesn't adjust the collider position itself.


import maya.cmds as cmds

cmds.select("hair**_Collider")
for j in cmds.ls(sl=1):
    print j
    try:
        cmds.parentConstraint("Head_FK",j,mo=1,)
    except Exception,err:
        print "    error:",err
        
        
cmds.select("*SpringRef_Control")
for j in cmds.ls(sl=1):
    print j
    try:
        cmds.parentConstraint("Local_SRT",j,mo=1,)
    except Exception,err:
        print "    error:",err