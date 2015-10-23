
import os.path as osp

import pymel.core as pm

from davos.core.damproject import DamProject
from pytd.gui.dialogs import SimpleTreeDialog
#from pytd.util.logutils import logMsg
from pytaya.core.general import lsNodes
from pytd.util.fsutils import pathResolve, normCase
from pytd.util.utiltypes import MemSize

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

mainWin = None

class MayaSimpleTreeDialog(MayaQWidgetDockableMixin, SimpleTreeDialog):

    def __init__(self, parent=None):
        super(MayaSimpleTreeDialog, self).__init__(parent=parent)

def scanTextureDependency(damAst):

    proj = damAst.project
    sAstName = damAst.name
    #privTexDir = damAst.getResource("private", "texture_dir")
    sPrivTexDirPath = damAst.getPath("private", "texture_dir")
    sAllowTexTypes = proj.getVar("project", "allowed_texture_formats")

    fileNodeList = lsNodes("*", type='file', not_rn=True)
    scanResults = []

    for fileNode in fileNodeList:

        sErrorList = []

        p = fileNode.getAttr("fileTextureName")
        if not p:
            continue

        sAbsTexPath = pathResolve(p)

        bExists = True
        if not osp.isfile(sAbsTexPath):
            sErrorList.append(('FileNotFound', ""))
            bExists = False

        sDirPath, sFilename = osp.split(sAbsTexPath)
        sBasePath, sExt = osp.splitext(sAbsTexPath)
        if sExt.lower() not in sAllowTexTypes:
            sMsg = ("Only accepts: '{}'".format("' '".join(sAllowTexTypes)))
            sErrorList.append(('BadTextureFormat', sMsg))

        if normCase(sDirPath) != normCase(sPrivTexDirPath):
            sMsg = ("Not in '{}'".format(osp.normpath(sPrivTexDirPath)))
            sErrorList.append(('BadLocation', sMsg))

        if normCase(sFilename).startswith(normCase(sAstName)):
            sMsg = ("Must NOT start with the asset name.")
            sErrorList.append(('BadFilename', sMsg))

        if sExt == ".tga":
            sBuddyPath = sBasePath + ".psd"
            if not osp.isfile(sBuddyPath):
                sErrorList.append(('PsdFileNotFound', ""))

            sBuddyPath = sBasePath + ".tx"
            if not osp.isfile(sBuddyPath):
                sErrorList.append(('TxFileNotFound', ""))

            if bExists:
                fileSize = MemSize(osp.getsize(sAbsTexPath))
                limitSize = MemSize(5e7)
                if fileSize > limitSize:
                    sMsg = "{:.0cM} > {:.0cM}".format(fileSize, limitSize)
                    sErrorList.append(('OversizedFile', sMsg))

        resultDct = {
                     "path":sAbsTexPath,
                     "errors":sErrorList,
                     "fileNode":fileNode
                     }

        scanResults.append(resultDct)

    return scanResults

def launch():

    sCurScnPath = pm.sceneName()
    if not sCurScnPath:
        raise ValueError("Invalid scene name: '{}'".format(sCurScnPath))

    proj = DamProject.fromPath(sCurScnPath, fail=True)
    damAst = proj.entityFromPath(sCurScnPath, fail=True)

    scanResults = scanTextureDependency(damAst)

    for result in scanResults:

        print result["fileNode"], ":", result["path"]
        for sErrorCode, sMsg in  result["errors"]:
            print "    ", sErrorCode, ':', sMsg

