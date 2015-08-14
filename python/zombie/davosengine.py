
import argparse

from davos.core.damproject import DamProject
from pytd.util.sysutils import inDevMode

"""
from davos.tools import create_directories_from_csv
create_directories_from_csv.launch(proj,dry_run=True)
"""

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--project", type=str)
    argspace = parser.parse_args()

    sProject = argspace.project
    if not sProject:
        sProject = "zombtest" if inDevMode() else "zombillenium"

    print ""
    print (" Project: '{}' ".format(sProject)).center(80, "-")
    proj = DamProject(sProject)
