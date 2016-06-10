
from dminutes import geocaching
reload(geocaching)

geocaching.importCaches(dryRun=False, removeRefs=True, processLabel="Apply")