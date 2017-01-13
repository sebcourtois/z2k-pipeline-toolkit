
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

reload(myaref)
reload(geocaching)
reload(finalLayout)


def setupLayoutScene(save=False):

    proj = DamProject("zombillenium", user="rrender", password="arn0ld&r0yal", standalone=True)

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
    exportData = geocaching.exportCaches(selected=True, confirm=False, outputDir=sOutDirPath)

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
                            showScriptEditor=False)

    finalLayout.renderSetup()

    if save:
        pm.saveFile(force=True)
