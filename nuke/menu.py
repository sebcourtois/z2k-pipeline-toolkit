#
#
#  Copyright (c) 2014, 2015, 2016 Psyop Media Company, LLC
#  See license.txt
#
#

import cryptomatte_utilities
cryptomatte_utilities.setup_cryptomatte_ui()

## DmnToon
nuke.menu('Nodes').addCommand('Z2K/LdvDmToon', lambda: nuke.createNode('LdvDmToon'))
nuke.menu('Nodes').addCommand('Z2K/LyrCheck', lambda: nuke.createNode('LyrCheck'))
nuke.menu('Nodes').addCommand('Z2K/MaskAovs', lambda: nuke.createNode('MaskAovs'))

## Other Gizmos
nuke.menu('Nodes').addCommand('Z2K/P_Matte', lambda: nuke.createNode('P_Matte'))
