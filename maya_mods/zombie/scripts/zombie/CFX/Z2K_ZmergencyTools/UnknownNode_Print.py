import maya.cmds as cmds
# print unknown nodeL
unknownL=[]
unknownL = cmds.ls(type="unknown")
if len(unknownL):
	for node in unknownL:
		print node

	print "unknownL    :",len(unknownL),unknownL
else:
    unknownL = ["No unKnown Nodes in the scene!"]
cmds.confirmDialog(title="Unknown PRINT",message= str("\n-".join(unknownL)) ,button="Ok")
