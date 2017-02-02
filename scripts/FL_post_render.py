
import os.path as osp
import argparse
from pprint import pprint

from davos.core.damproject import DamProject
from pytd.util.fsutils import pathJoin, pathNorm
from pytd.util.logutils import setLogLevel
from collections import OrderedDict
import traceback
from pytd.util.sysutils import toStr


#setLogLevel(0)
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

sImgDirPath = pathNorm(args.aRenderDirPath)
sImgDirList = sImgDirPath.split('/')
sUserName = sImgDirList[5]
sShotName = sImgDirList[9]

proj = DamProject("zombillenium", user="rrender", password="arn0ld&r0yal", standalone=True)
shotgundb = proj._shotgundb
damShot = proj.getShot(sShotName)

movieDct = OrderedDict({"arlequin.mov":"arlequin_movie",
                        "beauty.mov":"finalLayout_movie"})
missingList = []
for sMovSuffix, sRcName in movieDct.iteritems():

    sMovPath = pathJoin(sImgDirPath, sShotName + "_" + sMovSuffix)

    if not osp.isfile(sMovPath):
        missingList.append(sMovPath)
        continue

    pubMovie = damShot.getRcFile("public", sRcName)
    movieDct[sMovSuffix] = (sMovPath, pubMovie)

sSep = "\n  - "
if missingList:
    c = len(missingList)
    sMsg = "{} movie{} to publish NOT found:".format(c, "s" if c > 1 else "")
    raise EnvironmentError(sMsg + sSep + sSep.join(missingList))
else:
    print "Found all movies to publish:" + sSep + sSep.join(p for p, _ in movieDct.itervalues())

# publish movies
sgOpe = shotgundb.sg.find_one("CustomNonProjectEntity01", [["sg_login", "is", sUserName]])

for sSuffix, (sSrcMovPath, pubFile) in movieDct.items():
    sgVersData = {"sg_status_list":"rev", "sg_operator":sgOpe}
    newVersFile, sgVersion = pubFile.publishVersion(sSrcMovPath, autoLock=True, autoUnlock=True,
                                                    sgVersionData=sgVersData, sgUpload=False,
                                                    comment="from " + osp.basename(sImgDirPath))
    movieDct[sSuffix] = (newVersFile, sgVersion)

errorList = []
# update task statuses
for sSuffix, (newVersFile, sgVersion) in movieDct.iteritems():
    try:
        #print "*****", newVersFile.absPath()
        sgTask = sgVersion["sg_task"]
        #pprint(sgTask)
        sCurStatus = sgVersion["sg_task.Task.sg_status_list"]
        sNewStatus = ""
        if sCurStatus == "clc":
            sNewStatus = "rev"
    
        if sNewStatus:
            sTask = sgTask.get("code", sgTask.get("name", sgTask.get("id", "undefined")))
            print "\n", "Updating status of '{}' task to '{}'.".format(sTask, sNewStatus)
            proj.updateSgEntity(sgTask, sg_status_list=sNewStatus)
    except Exception as e:
        errorList.append(e)
        traceback.print_exc()

# upload movies
for sSuffix, (newVersFile, sgVersion) in movieDct.iteritems():
    try:
        proj.uploadSgVersion(sgVersion, newVersFile.absPath(), apart=False)
    except Exception as e:
        errorList.append(e)
        traceback.print_exc()

if errorList:
    numErrors =len(errorList)
    if numErrors == 1:
        raise errorList[0]
    else:
        sMsg = "\n{} errors while publishing movies:".format(numErrors)
        sErrList = "{}: {}".format(type(e).__name__, toStr(e))
        sMsg += (sSep + sSep.join(sErrList))
        raise RuntimeError(sMsg)

#damShot.showShotgunPage()
#proj._authobj.logOut()
#proj.reset()
#proj.authenticate(renew=True)

