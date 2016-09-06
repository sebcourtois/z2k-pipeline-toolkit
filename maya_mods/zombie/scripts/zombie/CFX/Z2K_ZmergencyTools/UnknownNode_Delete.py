import maya.cmds as cmds
# print unknown nodeL
unknownL=[]
unknownL = cmds.ls(type="unknown")
deletedL = []
notDeletedL = []
for node in unknownL:
    print node
    try:
        cmds.delete(node)
        deletedL.append(node)
    except Exception,err :
        print Exception,err
        notDeletedL.append(node)
a= "Unknown Total   : {0} ".ljust(20).format(len(unknownL), )
b= "           -deleted    : {0} ".ljust(20).format(len(deletedL),)
c= "        -notDeleted : {0} ".ljust(20).format(len(notDeletedL),)
uu= cmds.confirmDialog(title="Unknown DELETE",message= str("\n".join([a,b,c])) ,
    button='OK')

