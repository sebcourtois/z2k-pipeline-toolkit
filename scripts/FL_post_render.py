
# -*- coding: cp1252 -*-

import os.path as osp
import argparse

from davos.core.damproject import DamProject
from pprint import pprint
from pytd.util.fsutils import pathJoin


#def run(sShotName, sRenderDirPath):
#parser = argparse.ArgumentParser()
#parser.add_argument("%sShotName%")
#ns = parser.parse_args()

# Get shot and output path from argv
sShotName = "sq6660_sh0050a"
sRenderDirPath = "//ZOMBIWALK/Projects/private/dominiquec/zomb/shot/sq6660/sq6660_sh0050a/06_finalLayout/render-v021"

proj = DamProject("zombillenium", user="rrender", password="arn0ld&r0yal")
shotgundb = proj._shotgundb
damShot = proj.getShot(sShotName)

flartMovie = damShot.getRcFile("public", "finalLayout_movie")
#print flartMovie.absPath()
arleqMovie = damShot.getRcFile("public", "arlequin_movie")
#print arleqMovie.absPath()
if flartMovie:
    print "OK!"
    try:
        sSrcMovPath = pathJoin(sRenderDirPath, sShotName + '_beauty.mov')
        print sSrcMovPath

        sgVersData = {"sg_status_list":"rev"}
        newVersFile, sgVersion = flartMovie.publishVersion(sSrcMovPath, autoLock=True, autoUnlock=True,
                                                           sgVersionData=sgVersData,
                                                           comment="from " + osp.basename(sRenderDirPath))
        #print "*****", newVersFile.absPath()
        sgTask = sgVersion["sg_task"]
        #pprint(sgTask)
        sCurStatus = sgVersion["sg_task.Task.sg_status_list"]
        sNewStatus = ""
        if sCurStatus == "ip":
            sNewStatus = "rev"

        if sNewStatus:
            proj.updateSgEntity(sgTask, sg_statut_list=sNewStatus)
    except:
        print u"there are an error in da paté"





damShot.showShotgunPage()
proj._authobj.logOut()
proj.reset()
proj.authenticate(renew=True)

#if __name__ == "__main__":
#
#    parser = argparse.ArgumentParser()
#    parser.add_argument("--dry", action="store_true")
#
#    ns = parser.parse_args()
#
#    run(dryRun=ns.dry)
#else:
#    run()
