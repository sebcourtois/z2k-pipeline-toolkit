
from dminutes import geocaching
reload(geocaching)

geocaching.importCaches("local", dryRun=True, removeRefs=False, processLabel="Reference caches")

