
import os
import sys
import argparse
import time
import ctypes
from urllib2 import URLError
import traceback

if __name__ == "__main__":
    os.environ["PYTHONINSPECT"] = "1"

from zomblib.shotgunengine import ShotgunEngine


def reportErrorOrExit(func):

    def doIt(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except:
            ctypes.windll.user32.MessageBoxA(0, traceback.format_exc(),
                                             'SHOTGUN UPLOAD FAILED',
                                             (0x10 | 0x0 | 0x1000))
            raise
        sys.exit(0)
    return doIt

@reportErrorOrExit
def run():

    parser = argparse.ArgumentParser()
    parser.add_argument("entityType")
    parser.add_argument("entityId")
    parser.add_argument("filePath")
    parser.add_argument("fieldName")

    ns = parser.parse_args()

    sgEngine = ShotgunEngine("zombillenium")

    print ("\n\nUploading '{}'...\n          ...onto '{}' field of {}(id={})."
           .format(ns.filePath, ns.fieldName , ns.entityType, ns.entityId))

    print "\nDO NOT CLOSE THIS WINDOW ! It will be closed once the upload succeeded..."

    attempt = -1
    maxAttempts = 5
    delay = 3
    while (attempt < maxAttempts):
        attempt += 1
        try:
            sgEngine.sg.upload(ns.entityType, int(ns.entityId), ns.filePath, ns.fieldName)
        except URLError as e:
            print e

            if attempt == maxAttempts:
                raise

            print ("{}/{} retry in {} seconds...\n"
                    .format(attempt + 1, maxAttempts, delay))
            time.sleep(delay)
        else:
            print "Upload succeeded !"
            break

if __name__ == "__main__":
    run()
