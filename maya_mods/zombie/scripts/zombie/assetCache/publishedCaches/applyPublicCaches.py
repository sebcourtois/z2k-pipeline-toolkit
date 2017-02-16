
from dminutes import geocaching
reload(geocaching)

sSpace = "public"
geocaching.importCaches(sSpace, dryRun=False, removeRefs=True, layout=True,
                        processLabel="Apply {} caches".format(sSpace.upper()))
