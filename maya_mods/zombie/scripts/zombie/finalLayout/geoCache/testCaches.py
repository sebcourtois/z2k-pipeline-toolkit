
from dminutes import geocaching
reload(geocaching)

geocaching.importCaches(dryRun=True, removeRefs=True, processLabel="Test")