
import sys
import argparse

from davos.tools import asset_browser
from pytd.util.sysutils import inDevMode

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--project", type=str)
    argspace = parser.parse_args()

    sProject = argspace.project
    if not sProject:
        sProject = "zombtest" if inDevMode() else "zombillenium"

    print ""
    print (" Project: '{}' ".format(sProject)).center(80, "-")

    asset_browser.launch(sProject, sys.argv)
