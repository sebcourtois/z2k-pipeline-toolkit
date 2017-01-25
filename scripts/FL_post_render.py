# coding: cp1252

from os import listdir as lsd
import os.path as osp
import argparse

from davos.core.damproject import DamProject
from pprint import pprint
from pytd.util.fsutils import pathJoin


#def run(sShotName, sRenderDirPath):
parser = argparse.ArgumentParser(description='Parse the shot name and directory of the private movies to publish',
                                 usage='python FL_post_render.py absolute_dir_path')

#parser.add_argument('aShotName', help='Shot name should be in form of "sqxxxx_shxxxxa"')
parser.add_argument('aRenderDirPath', help='Directory that point to the private root of the shot"')
args = parser.parse_args()

# Get shot and output path from argv
## DEBUG PATH ##
#sTempRenderDirPath = '//ZOMBIWALK/Projects/private/dominiquec/zomb/shot/sq6660/sq6660_sh0050a/06_finalLayout/render-v021'
#sUserName = sTempRenderDirPath.split('/')[5]
#sShotName = sTempRenderDirPath.split('/')[9]
#sRenderDirPath = sTempRenderDirPath

sUserName = args.aRenderDirPath.split('/')[5]
sShotName = args.aRenderDirPath.split('/')[9]

sRenderDirPath = args.aRenderDirPath

proj = DamProject("zombillenium", user="rrender", password="arn0ld&r0yal")
shotgundb = proj._shotgundb
damShot = proj.getShot(sShotName)

sgOpe = shotgundb.sg.find_one("CustomNonProjectEntity01", [["sg_login", "is", sUserName]])

flartMovie = damShot.getRcFile("public", "finalLayout_movie")
arleqMovie = damShot.getRcFile("public", "arlequin_movie")

filesL = lsd(sRenderDirPath)
batchRenderMoviesL = []

for each in filesL:
    if filesL and each.endswith('arlequin.mov') or each.endswith('beauty.mov'):
        batchRenderMoviesL.append(each)

if len(batchRenderMoviesL) == 2:
    print "Found: 2 movies :: %s and %s :::: Publishing Movies!!" % (batchRenderMoviesL[0], batchRenderMoviesL[1])
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
            proj.updateSgEntity(sgTask, sg_status_list=sNewStatus, sg_operators=[sgOpe])

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
            proj.updateSgEntity(sgTask, sg_status_list=sNewStatus, sg_operators=[sgOpe])

else:
    print 'Nothing to do, no renderBatchMovies found!'
    pass


#damShot.showShotgunPage()
#proj._authobj.logOut()
#proj.reset()
#proj.authenticate(renew=True)

