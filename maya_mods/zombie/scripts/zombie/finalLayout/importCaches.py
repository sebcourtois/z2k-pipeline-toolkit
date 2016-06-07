

from dminutes import maya_scene_operations as mop
from dminutes import geocaching
reload(geocaching)
reload(mop)

mop.importLayoutVisibilities()
geocaching.importCaches(dryRun=False, removeRefs=True)