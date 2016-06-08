
from dminutes import geocaching
reload(geocaching)

geocaching.importCaches(dryRun=True, removeRefs=True, processLabel="Check import of")