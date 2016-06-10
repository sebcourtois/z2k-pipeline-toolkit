

import os
sPort = os.getenv("DAMAS_DEV_PORT", "8443")

if sPort == "8443":
    from damas_stable import *
elif sPort == "8444":
    from damas_testing import *