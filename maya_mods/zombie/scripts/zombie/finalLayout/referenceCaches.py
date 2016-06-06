

from dminutes import geocaching
reload(geocaching)

geocaching.importCaches(dryRun=True, removeRefs=False, processLabel="Reference")

