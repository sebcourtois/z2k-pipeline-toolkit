import site
import os

sSitePath = os.path.dirname(__file__)
print "adding python site: '{}'".format(sSitePath)
site.addsitedir(sSitePath)

for p in os.environ.get("Z2K_PYTHON_SITES", "").split(os.pathsep):
    if not p:
        continue
    print "adding python site: '{}'".format(p)
    site.addsitedir(p)
