
from dminutes import geocaching
reload(geocaching)

geocaching.importCaches("local", dryRun=False, removeRefs=True, processLabel="Apply")
