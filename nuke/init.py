#
#
#  Copyright (c) 2014, 2015, 2016 Psyop Media Company, LLC
#  See license.txt
#
#

import os
import cryptomatte_utilities
cryptomatte_utilities.setup_cryptomatte()

userName = os.environ["USERNAME"]
userPath = 'C:/Users/' + userName + '/zombillenium/z2k-pipeline-toolkit/nuke/gizmos'
if os.path.isdir( userPath ):
    nuke.pluginAddPath( userPath )