

import os

s = os.getenv("DEV_MODE_ENV", "0")
DEV_MODE = eval(s) if s else False

sPort = os.getenv("DAMAS_DEV_PORT", "8443") if DEV_MODE else "8443"

if sPort == "8443":
    from damas_stable import *
elif sPort == "8444":
    from damas_testing import *