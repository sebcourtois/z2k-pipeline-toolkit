
from dminutes import geocaching
reload(geocaching)

sSpace = "local"
geocaching.importCaches(sSpace, dryRun=True, removeRefs=False, layout=True,
                        processLabel="Reference {} caches".format(sSpace.upper()))