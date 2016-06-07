

from dminutes import geocaching
reload(geocaching)

geocaching.importLayoutVisibilities()
geocaching.importCaches(dryRun=False, removeRefs=True)