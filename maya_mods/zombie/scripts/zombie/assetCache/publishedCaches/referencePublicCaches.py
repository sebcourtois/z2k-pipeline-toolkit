
from dminutes import geocaching
reload(geocaching)

sSpace = "public"
geocaching.importCaches(sSpace, dryRun=True, removeRefs=False, layout=True,
                        processLabel="Reference {} caches".format(sSpace.upper()))
