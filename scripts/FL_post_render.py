
# -*- coding: cp1252 -*-

import os.path as osp
import argparse

from davos.core.damproject import DamProject
from pprint import pprint
from pytd.util.fsutils import pathJoin


#def run(sShotName, sRenderDirPath):
parser = argparse.ArgumentParser(description='Parse the shot name and directory of the private movies to publish',
                                 usage='pyrhon FL_post_render.py dirname')

#parser.add_argument('aShotName', help='Shot name should be in form of "sqxxxx_shxxxxa"')
parser.add_argument('aRenderDirPath', help='Directory that point to the private root of the shot"')
args = parser.parse_args()

# Get shot and output path from argv
sTempRenderDirPath = '//ZOMBIWALK/Projects/private/dominiquec/zomb/shot/sq6660/sq6660_sh0050a/06_finalLayout/render-v021'
sShotName = args.aRenderDirPath.split('/')[9]
sRenderDirPath = args.aRenderDirPath

proj = DamProject("zombillenium", user="rrender", password="arn0ld&r0yal")
shotgundb = proj._shotgundb
damShot = proj.getShot(sShotName)

flartMovie = damShot.getRcFile("public", "finalLayout_movie")
#print flartMovie.absPath()
arleqMovie = damShot.getRcFile("public", "arlequin_movie")
#print arleqMovie.absPath()
if arleqMovie:
    sSrcMovPath = pathJoin(sRenderDirPath, sShotName + '_arlequin.mov')
    print sSrcMovPath

    sgVersData = {"sg_status_list":"rev"}
    newVersFile, sgVersion = arleqMovie.publishVersion(sSrcMovPath, autoLock=True, autoUnlock=True,
                                                       sgVersionData=sgVersData,
                                                       comment="from " + osp.basename(sRenderDirPath))
    #print "*****", newVersFile.absPath()
    sgTask = sgVersion["sg_task"]
    #pprint(sgTask)
    sCurStatus = sgVersion["sg_task.Task.sg_status_list"]
    sNewStatus = ""
    if sCurStatus == "clc":
        sNewStatus = "rev"

    if sNewStatus:
        proj.updateSgEntity(sgTask, sg_status_list=sNewStatus)

if flartMovie:
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
    if sCurStatus == "clc":
        sNewStatus = "rev"

    if sNewStatus:
        proj.updateSgEntity(sgTask, sg_status_list=sNewStatus)





#damShot.showShotgunPage()
#proj._authobj.logOut()
#proj.reset()
#proj.authenticate(renew=True)

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
