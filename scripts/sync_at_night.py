
import sys
import os
import os.path as osp
import argparse
import time
import codecs
from itertools import groupby
from datetime import datetime
import shutil

from tabulate import tabulate


from pytd.util.fsutils import pathJoin, pathSuffixed
from pytd.util.systypes import MemSize
from davos.core.damproject import DamProject
from pytd.util.logutils import confirmMessage
#from pytd.gui.itemviews.utils import toDisplayText


def makeOutputPath(sFileName, timestamp=None, save=True):

    #for sFileName in ("maya_jobs.json", "maya_batch.bat", "maya_batch.log"):
    sOutDirPath = pathJoin(osp.dirname(os.environ["Z2K_TOOLKIT_PATH"]),
                           osp.splitext(osp.basename(__file__))[0])

    sFilePath = pathJoin(sOutDirPath, sFileName)
    if timestamp:
        sDate = datetime.fromtimestamp(timestamp).strftime("_%Y%m%d-%H%M%S")
        sFilePath = pathSuffixed(sFilePath, sDate)
        save = False

    if not osp.isdir(sOutDirPath):
        os.makedirs(sOutDirPath)
    elif save and osp.isfile(sFilePath):
        st = os.stat(sFilePath)
        if st.st_size:
            sTimestamp = datetime.fromtimestamp(st.st_mtime).strftime("_%Y%m%d-%H%M%S")
            shutil.copy2(sFilePath, pathSuffixed(sFilePath, sTimestamp))

    return sFilePath

def findResources(proj):

    p = "/zomb"
    query = {
    "file":r"REGEX_^{}/.+".format(p),

    #"sync_at_night":{"$exists":False},
    "sync_at_night":1,

    #"sync_disabled":{"$exists":False},
    "sync_disabled":1,
    }
    allNodeList = proj._db.findNodes(query)

    print query

    bLatest = True
    bHeads = True
    if not bLatest:
        updNodeList = allNodeList
        updNodeList.sort(key=lambda n:n.time)
        #updNodeList.sort(key=lambda n:n.synced_online)
    else:
        updNodeList = list(n for n in allNodeList if ("#parent" not in n._data))
        sHeadIdList = tuple(n.id_ for n in updNodeList)
        # for each head file, its latest version needs to be updated too
        sortKey = lambda n: n._data["#parent"] + "_" + n.name
        dbVersIter = (n for n in allNodeList if ("#parent" in n._data) and (n._data["#parent"] in sHeadIdList))
        dbVersList = sorted(dbVersIter, key=sortKey, reverse=True)
        grpIter = groupby(dbVersList, key=lambda n: n._data["#parent"])

        if not bHeads:
            updNodeList = []

        updNodeList.extend((next(g) for _, g in grpIter))
        #updNodeList.sort(key=lambda n:n.file.strip("/").split("/")[4])
        updNodeList.sort(key=lambda n:n.time)

    return updNodeList

def logResources(dbNodeList, htmlPath=""):

    table = []
    totalSize = 0
    for i, n in enumerate(dbNodeList):
        #print n.dataRepr("file", "time", "sync_disabled", "source_size")
        sSize = ""
        if n.source_size:
            totalSize += n.source_size
            sSize = "{:.2cM}".format(MemSize(n.source_size))

        sTime = datetime.fromtimestamp(n.time / 1000).strftime("%Y-%m-%d %H:%M:%S")
        table.append((i, n.file, sSize, sTime, n.origin,
                      n.getField("sync_at_night"),
                      n.getField("sync_disabled"),
                      n.getField("sync_priority"),))
        #print n.dataRepr()

    headers = ["n", "file", "size", "time", "origin", "SN", "SD", "SP"]

    if htmlPath:
        sCharset = '<head>\n<meta charset="UTF-8">\n</head>\n'
        with codecs.open(htmlPath, "w", "utf_8") as fo:
            fo.writelines(sCharset + tabulate(table, headers, tablefmt="html"))
    else:
        print tabulate(table, headers, tablefmt="simple")
        print "{} resources - {:.2cM}".format(len(dbNodeList), (MemSize(totalSize)))

def launch(proj, batch=False, dryRun=True):

    dbNodeList = findResources(proj)
    logResources(dbNodeList)

    numNodes = len(dbNodeList) 
    if not batch:
        sChoiceList = ["Quit", "Refresh"]
        if numNodes:
            sChoiceList.insert(0, "Enable")

        sMsg = "Found {} resource(s) to sync".format(numNodes)
        res = confirmMessage("DO YOU WANT TO...", sMsg, sChoiceList)
        if res == "Quit":
            sys.exit(0)
        elif res == "Refresh":
            return launch(proj, batch=batch, dryRun=dryRun)

    sFilename = "enabled_log.html"
    if not dryRun:
        proj._db.updateNodes(dbNodeList, {"sync_disabled":None})
    else:
        sFilename = "dry_" + sFilename

    p = makeOutputPath(sFilename, timestamp=time.time())
    logResources(dbNodeList, htmlPath=p)
    print "\n", "log file: {}".format(osp.normpath(p))

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--dry", action="store_true")
    parser.add_argument("--batch", action="store_true")
    ns = parser.parse_args()

    try:
        proj = DamProject("zombillenium", shotgun=False, checkTemplates=False)
        launch(proj, batch=ns.batch, dryRun=ns.dry)
    except Exception as e:
        os.environ["PYTHONINSPECT"] = "1"
        if isinstance(e, Warning):
            print e.message
        else:
            raise

#data = dict(("synced_" + sSite, None) for sSite in proj.listAllSites())
#data.update({"sync_at_night":1})
#proj._db.updateNodes(updNodeList, data)

#proj._db.updateNodes(updNodeList, {"sync_disabled":None})

#proj._db.updateNodes(updNodeList, {"sync_disabled":1, "sync_at_night":1})

#{"file":"REGEX_^/zomb/","sync_disabled":1,"sync_at_night":1,"origin":"dmn_paris","synced_dmn_angouleme":{"$exists":false}}


