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
toolbar = nuke.menu('Nodes')
z2ktools_menu = toolbar.addMenu('Z2K', icon='Z2KTools.png')

z2ktools_menu.addCommand('LdvDmToon', lambda: nuke.createNode('LdvDmToon'))
z2ktools_menu.addCommand('LyrCheck', lambda: nuke.createNode('LyrCheck'))
z2ktools_menu.addCommand('MaskAovs', lambda: nuke.createNode('MaskAovs'))

## P Matte Gizmos
z2ktools_menu.addCommand('P_Matte', lambda: nuke.createNode('P_Matte'))

## P Map Gizmos
z2ktools_menu.addCommand('P_Map', lambda: nuke.createNode('P_Map'))

## P Noise Gizmos
z2ktools_menu.addCommand('P_Noise', lambda: nuke.createNode('P_Noise'))

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

nuke.menu( 'Nuke' ).addCommand( 'Zombi/lighting/toPrivate/all read nodes', lambda: nkU.pointToPrivate(readNodeL=nuke.allNodes('Read'), gui=True) )
nuke.menu( 'Nuke' ).addCommand( 'Zombi/lighting/toPrivate/selected read nodes', lambda: nkU.pointToPrivate(readNodeL=nuke.selectedNodes('Read'), gui=True) )

nuke.menu( 'Nuke' ).addCommand( 'Zombi/import template/ compositing', lambda: nkU.inportOutTemplate(template = "compo") )
nuke.menu( 'Nuke' ).addCommand( 'Zombi/import template/ stereo', lambda: nkU.inportOutTemplate(template = "stereo") )
nuke.menu( 'Nuke' ).addCommand( 'Zombi/import template/ render precomp', lambda: nkU.inportOutTemplate(template = "renderprecomp") )
nuke.menu( 'Nuke' ).addCommand( 'Zombi/publish/publish compositing', lambda: nkU.publishCompo(dryRun=False, gui = True) )
nuke.menu( 'Nuke' ).addCommand( 'Zombi/publish/publish all inputs', lambda: nkU.publishNode(readNodeL=nuke.allNodes('Read'),guiPopUp = True) )
nuke.menu( 'Nuke' ).addCommand( 'Zombi/publish/publish selected inputs', lambda: nkU.publishNode(readNodeL=nuke.selectedNodes('Read'),guiPopUp = True) )

nuke.menu( 'Nuke' ).addCommand( 'Zombi/stereo/create layer breakdown files', lambda: nkU.createLayerBreakdown(gui = False))
nuke.menu( 'Nuke' ).addCommand( 'Zombi/stereo/import stereo Info', lambda: nkU.getStereoInfo() )
# myMenu = myToolbar.addMenu( 'zomb Tools' )
# myToolbar.addCommand( 'init nuke shot', lambda: nkU.initNukeShot() )

m=menubar.addMenu("RRender");
m.addCommand("Submit Comp", "nuke.load('rrSubmit_Nuke_5'), rrSubmit_Nuke()")
m.addCommand("Submit Shotgun Nodes", "nuke.load('rrSubmit_Nuke_5'), rrSubmit_Nuke_Shotgun()")


#---------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------ToolBox from Compositing Angouleme----------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------#

#import nuke
import nukescripts

#import Tooling
import localizeOff_all
import localizeOff_selected
import localizeOn_all
import localizeOn_selected

import render_all
import import_comp_ref
import import_camera_metadata

import import_reader_ref
import import_p_locator
import import_combine_depth
import import_convert_p_to_uv
import import_convert_p_to_z
import import_fake_motion_pass
import import_metadata_lookup
import import_fast_relight

import toggle_FS

#Register Tooling to toolbar
toolbar = nuke.menu('Nodes')
zombToolBox = toolbar.addMenu('Toolbox', icon='zombi_logo.png')

zombToolBox.addCommand( 'Reader/Localize Off/All', 'localizeOff_all.locOffAllStart()')
zombToolBox.addCommand( 'Reader/Localize Off/Selected', 'localizeOff_selected.locOffSelectedStart()')
zombToolBox.addCommand( 'Reader/Localize On/All', 'localizeOn_all.locOnAllStart()')
zombToolBox.addCommand( 'Reader/Localize On/Selected', 'localizeOn_selected.locOnSelectedStart()')

zombToolBox.addCommand( 'Render/Render All (exr, Qt) ', 'render_all.rndStart()')

zombToolBox.addCommand( 'Tools/Metadata Lookup', 'import_metadata_lookup.importMetaLookUp()')
zombToolBox.addCommand( 'Tools/Baked Camera', 'import_camera_metadata.importBakedCam()')
zombToolBox.addCommand( 'Tools/ReProject3D', 'nuke.createNode(\"ReProject3D\")')
zombToolBox.addCommand( 'Tools/P_Locator', 'import_p_locator.importCompLoc()')
zombToolBox.addCommand( 'Tools/Combine_Depth', 'import_combine_depth.importCombineDepth()')
zombToolBox.addCommand( 'Tools/Convert P to Z', 'import_convert_p_to_z.importConvertPtoZ()')
zombToolBox.addCommand( 'Tools/Convert P to UV', 'import_convert_p_to_uv.importConvertPtoUV()')
zombToolBox.addCommand( 'Tools/Fake Motion Pass', 'import_fake_motion_pass.importMotionPass()')
zombToolBox.addCommand( 'Tools/Fast Relighting', 'import_fast_relight.importFastRelight()')
zombToolBox.addCommand( 'Tools/Edge Extend', 'nuke.createNode(\"edge_extend\")')
zombToolBox.addCommand( 'Tools/Antialiasing', 'nuke.createNode(\"antialiasing\")')

zombToolBox.addCommand( 'Ref/Match Shot', 'import_reader_ref.importFastFinder()')
zombToolBox.addCommand( 'Ref/Template', 'import_comp_ref.importCompRef()')
zombToolBox.addCommand( 'Ref/Match Shot Dpt', 'nuke.createNode(\"dpt_viewer\")')

zombToolBox.addCommand( 'Other/Viewer/Toogle FullScreen', 'toggle_FS.FullscreenViewer()', shortcut='alt+shift+e', tooltip='alt+shift+e')

