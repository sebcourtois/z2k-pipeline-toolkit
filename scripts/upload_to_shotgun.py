

import os
import sys
import argparse

if __name__ == "__main__":
    os.environ["PYTHONINSPECT"] = "1"

from zomblib.shotgunengine import ShotgunEngine


def run():

    parser = argparse.ArgumentParser()
    parser.add_argument("entityType")
    parser.add_argument("entityId")
    parser.add_argument("filePath")
    parser.add_argument("fieldName")

    ns = parser.parse_args()

    sgEngine = ShotgunEngine("zombillenium")

    print ("Uploading '{}'...\n          ...onto '{}' field of {}(id={})."
           .format(ns.filePath, ns.fieldName , ns.entityType, ns.entityId))

    print "\nDO NOT CLOSE THIS WINDOW ! It will close by itself once the upload succeeded.."

    sgEngine.sg.upload(ns.entityType, int(ns.entityId), ns.filePath, ns.fieldName)
    sys.exit()

if __name__ == "__main__":
    run()
