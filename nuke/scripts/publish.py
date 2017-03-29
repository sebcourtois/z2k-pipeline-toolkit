import nuke
import sys
nukeScriptS = nuke.rawArgs[-1]




print "opening ", nukeScriptS

nuke.scriptOpen( nukeScriptS )

if "_precomp" in nukeScriptS:
	nkU.publishNode(readNodeL=nuke.allNodes('Read'),guiPopUp = True)
	nuke.scriptSave( nukeScriptS )
	statusD = {"sg_status_list":"rev"} #ip, rev, omt, wfa ou final
	commentS = "auto comment" 
else:
	commentS = raw_input("Please enter a publish comment:")
	statusD = None
	if not commentS:
	    raise RuntimeError("comment needed, Publish canceled")




nkU.publishCompo(dryRun=False, gui = False, commentS=commentS, sgVersionData=statusD) 
