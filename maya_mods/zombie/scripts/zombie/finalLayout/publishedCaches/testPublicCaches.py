
from dminutes import geocaching
reload(geocaching)

geocaching.importCaches("public", dryRun=True, removeRefs=True, processLabel="Test")