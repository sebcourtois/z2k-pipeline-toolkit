#
#
#  Copyright (c) 2014, 2015, 2016 Psyop Media Company, LLC
#  See license.txt
#
#
import cryptomatte_utilities
cryptomatte_utilities.setup_cryptomatte_ui()

#from davos.core.damproject import DamProject



import nkU as nkU
reload(nkU)

## DmnToon
nuke.menu('Nodes').addCommand('Z2K/LdvDmToon', lambda: nuke.createNode('LdvDmToon'))
nuke.menu('Nodes').addCommand('Z2K/LyrCheck', lambda: nuke.createNode('LyrCheck'))
nuke.menu('Nodes').addCommand('Z2K/MaskAovs', lambda: nuke.createNode('MaskAovs'))

## P Matte Gizmos
nuke.menu('Nodes').addCommand('Z2K/P_Matte', lambda: nuke.createNode('P_Matte'))

## P Map Gizmos
nuke.menu('Nodes').addCommand('Z2K/P_Map', lambda: nuke.createNode('P_Map'))

## P Noise Gizmos
nuke.menu('Nodes').addCommand('Z2K/P_Noise', lambda: nuke.createNode('P_Noise'))

## Stereo Gizmo
toolbar = nuke.menu("Nodes")
menu_3D = toolbar.addMenu('Tools_3D', 'menu_3d.png')
menu_3D.addCommand('StereoDisparityGenerator', 'nuke.createNode(\"StereoDisparityGenerator\")')
menu_3D.addCommand('StereoDisplaceTool', 'nuke.createNode(\"StereoDisplaceTool\")')

## Scripts
nuke.menu( 'Nuke' ).addCommand( 'Zombi/init nuke shot', lambda: nkU.initNukeShot() )
nuke.menu( 'Nuke' ).addCommand( 'Zombi/conform/all/read nodes', lambda: nkU.conformReadNode(readNodeL=nuke.allNodes('Read'), gui=True, conformPathB = True) )
nuke.menu( 'Nuke' ).addCommand( 'Zombi/conform/selected/read nodes', lambda: nkU.conformReadNode(readNodeL=nuke.selectedNodes('Read'), gui=True, conformPathB = True) )
nuke.menu( 'Nuke' ).addCommand( 'Zombi/conform/all/read nodes (error)', lambda: nkU.conformReadNode(readNodeL=nuke.allNodes('Read'), gui=True, conformPathB = True, changeOnErrorI = 0) )
nuke.menu( 'Nuke' ).addCommand( 'Zombi/conform/selected/read nodes (error)', lambda: nkU.conformReadNode(readNodeL=nuke.selectedNodes('Read'), gui=True, conformPathB = True, changeOnErrorI = 0) )
nuke.menu( 'Nuke' ).addCommand( 'Zombi/conform/all/read nodes (nearest frame)', lambda: nkU.conformReadNode(readNodeL=nuke.allNodes('Read'), gui=True, conformPathB = True, changeOnErrorI = 3) )
nuke.menu( 'Nuke' ).addCommand( 'Zombi/conform/selected/read nodes (nearest frame)', lambda: nkU.conformReadNode(readNodeL=nuke.selectedNodes('Read'), gui=True, conformPathB = True, changeOnErrorI = 3) )
nuke.menu( 'Nuke' ).addCommand( 'Zombi/conform/all/read nodes (update to last vers)', lambda: nkU.conformReadNode(readNodeL=nuke.allNodes('Read'), gui=True, conformPathB = True, switchToLastVer = True) )
nuke.menu( 'Nuke' ).addCommand( 'Zombi/conform/selected/read nodes (update to last vers)', lambda: nkU.conformReadNode(readNodeL=nuke.selectedNodes('Read'), gui=True, conformPathB = True, switchToLastVer = True) )


nuke.menu( 'Nuke' ).addCommand( 'Zombi/import template/ compositing', lambda: nkU.inportOutTemplate(template = "compo") )
nuke.menu( 'Nuke' ).addCommand( 'Zombi/import template/ stereo', lambda: nkU.inportOutTemplate(template = "stereo") )
nuke.menu( 'Nuke' ).addCommand( 'Zombi/import template/ render precomp', lambda: nkU.inportOutTemplate(template = "renderprecomp") )
nuke.menu( 'Nuke' ).addCommand( 'Zombi/publish/publish compositing', lambda: nkU.publishCompo(dryRun=False, gui = True) )
nuke.menu( 'Nuke' ).addCommand( 'Zombi/publish/publish all inputs', lambda: nkU.publishNode(readNodeL=nuke.allNodes('Read'),guiPopUp = True) )
nuke.menu( 'Nuke' ).addCommand( 'Zombi/publish/publish selected inputs', lambda: nkU.publishNode(readNodeL=nuke.selectedNodes('Read'),guiPopUp = True) )

nuke.menu( 'Nuke' ).addCommand( 'Zombi/import stereo Info', lambda: nkU.getStereoInfo() )
# myMenu = myToolbar.addMenu( 'zomb Tools' )
# myToolbar.addCommand( 'init nuke shot', lambda: nkU.initNukeShot() )

m=menubar.addMenu("RRender");
m.addCommand("Submit Comp", "nuke.load('rrSubmit_Nuke_5'), rrSubmit_Nuke()")
m.addCommand("Submit Shotgun Nodes", "nuke.load('rrSubmit_Nuke_5'), rrSubmit_Nuke_Shotgun()")
