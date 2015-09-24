
import hashlib
from getpass import getpass

import os
os.environ["PYTHONINSPECT"] = "1"

def getPass():
    sPwd1 = getpass()
    sPwd2 = getpass("Confirm:")
    if sPwd1 != sPwd2:
        return
    return sPwd1

sPwd = ""
while not sPwd:
    sPwd = getPass()

h = hashlib.md5()
h.update(sPwd)
print h.hexdigest()
