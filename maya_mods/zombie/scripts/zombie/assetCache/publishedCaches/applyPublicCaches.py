
from dminutes import geocaching
reload(geocaching)

geocaching.importCaches("public", dryRun=False, removeRefs=True, processLabel="Apply caches")
