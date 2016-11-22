
from dminutes import gpucaching
reload(gpucaching)

sMsg = """GPU CACHES EXPORTED !

You can now display GPU CACHED VERSIONS of exported assets
using "Show All" or "Toggle Selected".
"""
gpucaching.exportFromAssets(selected=True, message=sMsg)
