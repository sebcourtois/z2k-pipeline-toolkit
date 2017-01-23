
import os.path as osp
from pprint import pprint

import maya.cmds as mc
import pymel.core as pm

from pytd.util.fsutils import pathJoin
from davos.core.damproject import DamProject

from davos_maya.tool import reference as myaref
from davos_maya.tool.general import infosFromScene

from dminutes import geocaching
from dminutes import finalLayout
import traceback

reload(myaref)
reload(geocaching)
reload(finalLayout)

def quitWithStatus(func):
    def doIt(*args, **kwargs):
        bSave = kwargs.pop("save", False)
        bQuit = kwargs.pop("quit", mc.about(batch=True))
        try:
            res = func(*args, **kwargs)
        except:
            if bQuit:
                sTrace = traceback.format_exc()
#                lines = [""] + sTrace.splitlines(True)
#                print "!ERROR!".join(lines)
                pm.displayError(sTrace)
                mc.quit(f=True, exitCode=1)
            else:
                raise
        else:
            if bSave:
                pm.saveFile(force=True)
            if bQuit:
                mc.quit(force=True, exitCode=0)
        return res
    return doIt

@quitWithStatus
def setupLayoutScene(**kwargs):

    proj = DamProject("zombillenium", user="rrender", password="arn0ld&r0yal", standalone=False)

    scnInfos = infosFromScene(project=proj)
    if scnInfos["resource"] != "layout_scene":
        pm.displayWarning("Not a layout scene: batchrender.setupLayoutScene() not applied.")
        return

    def excludeRef(oFileRef):
        return(not oFileRef.namespace.lower().startswith("set_"))

    myaref.loadAssetsAsResource("anim_ref", checkSyncState=True, selected=False,
                                exclude=excludeRef, fail=True)

    sOutDirPath = pm.sceneName().dirname() + "/geoCache"
    mc.select("set_*:grp_geo")
    exportData = geocaching.exportCaches(selected=True, confirm=False,
                                         sceneInfos=scnInfos, outputDir=sOutDirPath)

    jobList = exportData["jobs"]
    for jobInfos in jobList:
        sFilePath = jobInfos["file"]
        if not osp.isabs(sFilePath):
            jobInfos["file"] = pathJoin(sOutDirPath, sFilePath)

    #pprint(exportData)

    myaref.loadAssetsAsResource("render_ref", checkSyncState=True, selected=False,
                                exclude=excludeRef, fail=True)

    geocaching.importCaches(jobs=jobList, layoutViz=False, useCacheSet=True,
                            dryRun=False, beforeHistory=False, removeRefs=True,
                            showScriptEditor=False, sceneInfos=scnInfos)

    finalLayout.renderSetup()
