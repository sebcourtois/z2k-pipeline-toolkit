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

## Scripts
nuke.menu( 'Nuke' ).addCommand( 'Zombi/init nuke shot', lambda: nkU.initNukeShot() )
nuke.menu( 'Nuke' ).addCommand( 'Zombi/conform file nodes', lambda: nkU.conformFileNode(readNodeL=nuke.allNodes('Read')+nuke.allNodes('Write'), gui=True, conformPathB = True) )
nuke.menu( 'Nuke' ).addCommand( 'Zombi/publish/publish compositing', lambda: nkU.publishCompo(dryRun=False, gui = True) )
nuke.menu( 'Nuke' ).addCommand( 'Zombi/publish/publish all inputs', lambda: nkU.publishNode(readNodeL=nuke.allNodes('Read'),guiPopUp = True) )
nuke.menu( 'Nuke' ).addCommand( 'Zombi/publish/publish selected inputs', lambda: nkU.publishNode(readNodeL=nuke.selectedNodes('Read'),guiPopUp = True) )
# myMenu = myToolbar.addMenu( 'zomb Tools' )
# myToolbar.addCommand( 'init nuke shot', lambda: nkU.initNukeShot() )


