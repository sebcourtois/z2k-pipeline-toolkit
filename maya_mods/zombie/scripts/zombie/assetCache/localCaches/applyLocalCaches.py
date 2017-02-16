
from dminutes import geocaching
reload(geocaching)

sSpace = "local"
geocaching.importCaches(sSpace, dryRun=False, removeRefs=True, layout=True,
                        processLabel="Apply {} caches".format(sSpace.upper()))
