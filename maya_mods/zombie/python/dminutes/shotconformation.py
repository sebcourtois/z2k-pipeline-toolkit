import maya.cmds as mc

def removeRefEditByAttr(refNodeL=[], attr= "smoothDrawType"):

	if not refNodeL:
	    refNodeL= mc.ls(type = "reference")

	for eachRefNode in refNodeL:
		myAttrRefEditL = []
		allRefEditL = mc.referenceQuery( eachRefNode, editStrings=True)

		for eachRefEdit in allRefEditL:
		    if "."+attr in eachRefEdit:
		        myAttrRefEditL.append(eachRefEdit.split(" ")[1])

		for each in myAttrRefEditL:
		    mc.referenceEdit( each, failedEdits = True, successfulEdits = True, editCommand = 'setAttr', removeEdits = True )

		print "#### {:>7}: 'removeRefEditByAttr': '{:>40}', {} '{}' reference edit deleted".format("Info",eachRefNode,len(myAttrRefEditL),attr )
	    
	    




