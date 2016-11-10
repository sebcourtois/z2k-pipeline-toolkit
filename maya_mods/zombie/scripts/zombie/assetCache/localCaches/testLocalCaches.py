
from dminutes import geocaching
reload(geocaching)

geocaching.importCaches("local", dryRun=True, removeRefs=True, processLabel="Test caches")
