import nuke
import nukescripts
import threading
import time

#TODO : Disable Postage Stamp to speedUp load/forward.

# Check if nodes inside output backdrop is disable
# By default should be disable
def checkNodesState():
    for qtnodes in nuke.toNode('output').getNodes():
        if qtnodes['disable'].value() == True:
			qtnodes['disable'].setValue(False)

def exrRenderStep():
	# Execute Write_exr WRITER node
	writerExr = nuke.toNode("Write_exr")
	nuke.executeInMainThread(nuke.execute, args=writerExr)

def qtRenderStep():	
	# Execute out_movie WRITER node
	writerQt = nuke.toNode("out_movie")
	nuke.executeInMainThread(nuke.execute, args=writerQt)
	
def disableNodes():
	for qtnodes in nuke.toNode('output').getNodes():
		qtnodes['disable'].setValue(True)
		
def rndStart():
	checkNodesState()
	exrRenderStep()		
	# Have a break
	time.sleep(2)
	# Reload read_exr READER	
	nuke.toNode("read_exr")['reload'].execute()
	qtRenderStep()
	disableNodes()
	# User Return
	nuke.message('Render Done.')