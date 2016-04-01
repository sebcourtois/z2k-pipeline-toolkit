# Load all cameras from all shots cantaining this asset.
import maya.OpenMayaUI as omui
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya

import os
from shotgun_api3 import shotgun
import fnmatch

from PySide import QtCore
from PySide import QtGui

from shiboken import wrapInstance

from dminutes import miscUtils
reload (miscUtils)

SERVER_PATH = "https://zombillenium.shotgunstudio.com"
SCRIPT_NAME = 'dreamwall'
SCRIPT_KEY = 'cadd9ab033a932d7cdaea404c9c6e7e653367c0041ef6d49fcb7c070450f3c4e'

GRP_MOD_CAMS = "GRP_MOD_CAMS"
GRP_TMP_MAT_SET = "GRP_TMP_MAT_SET"

assetEdit = QtGui.QComboBox() # global var

def shotgunConnect(): # connect to shotgun
    sg = shotgun.Shotgun(SERVER_PATH, SCRIPT_NAME, SCRIPT_KEY)
    return sg
    
sg=shotgunConnect()
projectId = 67 # Zombillenium
    
def sgProject (sg, input): # find a project given the name
    return sg.find_one("Project", [["name", "is", input]])
    

def sgShot (sg, projectId, episodeName, shotName): # finding a shot given the name, return  shotObject = {'type': 'Shot', 'id': 15793}
    #return sg.find_one('Shot',[['code','is',shot],['project','is',project]],['sg_cut_in','sg_cut_out','sg_client_version', 'code'])
    episodeObject = sg.find_one('CustomEntity01',[['project', 'is', {'type': 'Project','id': projectId}],['code','is',episodeName]])
    return sg.find_one('Shot', [['project', 'is', {'type': 'Project', 'id': projectId}],['sg_episode', 'is', episodeObject],['sg_shortname', 'is', shotName]])
    
def sgAssetShotsRelated(sg, projectId, assetName):
    filters = [["project", "is", {"type":"Project", "id":projectId}],["code", "contains", assetName]]
    return sg.find("Asset", filters, ["code", "shots"])
    
def sgGetShotsFromAsset(assetName):
    datas = sgAssetShotsRelated(sg, projectId, assetName)
    return datas[0]['shots']
    
def setGroupTRS(grpName, t, r, s):
    cmds.xform(grpName, r=True, t=(t[0], t[1], t[2]))
    cmds.xform(grpName, r=True, ro=(r[0], r[1], r[2]))
    cmds.xform(grpName, r=True, s=(s[0], s[1], s[2]))

def mayaMainWindow():
    mainWindowPtr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(mainWindowPtr), QtGui.QWidget)
    
def matrixInverse(matSet):
    mUtil = OpenMaya.MScriptUtil()
    m0 = OpenMaya.MMatrix()
    mUtil.createMatrixFromList(matSet, m0) # transform list to matrix pointer.
    m3 = m0.inverse()
    mList = [
    m3(0,0), m3(0,1), m3(0,2), m3(0,3),
    m3(1,0), m3(1,1), m3(1,2), m3(1,3),
    m3(2,0), m3(2,1), m3(2,2), m3(2,3),
    m3(3,0), m3(3,1), m3(3,2), m3(3,3)
    ]
    return mList 

def doLoadAllCameras():

##    assetName = "set_salleReunion_default"
##    assetName = "set_parcStreets_default"
##    assetName = "set_mainStreet_default"
    assetName = assetEdit.currentText()
    print("**** Start loading all cameras for set: " + assetName)

    # GRP_MOD_CAMS
    print("\tDeleting " + GRP_MOD_CAMS + " ...")
    if cmds.objExists(GRP_MOD_CAMS):
	    cmds.delete(GRP_MOD_CAMS)
    cmds.group(em=True, name=GRP_MOD_CAMS)

    print("\tGetting shots from shotgun ...")
    shots = sgGetShotsFromAsset(assetName) # get shots containing the asset.
    print("\t" + str(len(shots)) + " shots found from shotgun")
    #print shots
    for shot in shots: # for each shot
        shotName = shot['name']
        seqName = shotName.split("_")[0]
        #print ("\tseqName: " + str(seqName) + " shotName: " + str(shotName))
        
        pathText = miscUtils.pathJoin(os.environ["ZOMB_SHOT_PATH"],seqName,shotName,"00_data",shotName+"_infoSet.txt")
        #pathText = "Z:/shot/"+seqName+"/"+shotName+"/00_data/"+shotName+"_infoSet.txt" # build path of metadata file
        if not os.path.exists(pathText): # metadata file exists ?
            print ("\tERROR: Datas and camera missing for " + str(pathText))
            continue
        else:
            print("\tOK: Datas and camera readed for " + str(pathText))

        # import metadata file
        ##print("INFO: Importing metadata file ...")
        tmp_handle = open(pathText, 'r')
        tmp_content = tmp_handle.readlines()
        tmp_handle.close()
        tmp_content = ''.join(tmp_content)
        # We eval the content of the file to recreate the dict
        META = eval(tmp_content) 

        grpName = shotName+"_"+GRP_TMP_MAT_SET
        if cmds.objExists(grpName):
            cmds.delete(grpName) 
        grpTmpMat = cmds.group(n=grpName, em=True)
        ##print("grpTmpMat: " + str(grpTmpMat))
        grpBigDaddy = cmds.group(n="BigDaddy", em=True, p=grpTmpMat)
        grpGlobal = cmds.group(n="Global_SRT", em=True, p=grpBigDaddy)
        grpLocal = cmds.group(n="Local_SRT", em=True, p=grpGlobal)
    
        for itm in META:
            if assetName in itm:
                if "BigDaddy" in itm:
                    #print("\t\tBigDaddy: " + " META["+itm+"]:" + str(META[itm]))
                    setGroupTRS(grpBigDaddy, META[itm]["translate"], META[itm]["rotate"], META[itm]["scale"])
                elif "Global_SRT" in itm:
                    #print("\t\tGlobal_SRT: " + " META["+itm+"]:" + str(META[itm]))
                    setGroupTRS(grpGlobal, META[itm]["translate"], META[itm]["rotate"], META[itm]["scale"])
                elif "Local_SRT" in itm:
                    #print("\t\tLocal_SRT: " + " META["+itm+"]:" + str(META[itm]))
                    setGroupTRS(grpLocal, META[itm]["translate"], META[itm]["rotate"], META[itm]["scale"])

        # get matrix of Asset transform
        matSet = cmds.xform(grpLocal, q=True, ws=True, m=True)
        matSetInv = matrixInverse(matSet)
        
        # delete group TMP_MAT_SET
        cmds.delete(grpTmpMat)

        # import camera
        #pathCam = "Z:/shot/"+seqName+"/"+shotName+"/00_data/"+shotName+"_camera.ma" # build path of metadata file
        pathCam = miscUtils.pathJoin(os.environ["ZOMB_SHOT_PATH"],seqName,shotName,"00_data",shotName+"_camera.ma")
        cmds.file(pathCam, i=True, type="mayaAscii", renameAll=True, mergeNamespacesOnClash=False, namespace=shotName, options="v=0;") # import camera
        grpCamMatInv = cmds.group(n=shotName+"_camMatInv", em=True, p=GRP_MOD_CAMS) # create group CamMatInv parented to GRP_MOD_CAMS
        cmds.select(shotName+"*:grp_camera*")
        shotCams = cmds.ls(selection=True, l=True)
        cmds.parent(shotCams[0], grpCamMatInv)
        cmds.xform(grpCamMatInv, ws=True, matrix=matSetInv) # set matrix set inverse to camera          

    print("***** Loading camera for asset: " + assetName + " done !") 
            
def camAssetMgr():
    mainWindow = QtGui.QDialog(parent=mayaMainWindow())
    palette = QtGui.QPalette()
    mainWindow.setWindowTitle("Loading cameras tool")
    palette.setColor(QtGui.QPalette.Background, QtGui.QColor(75, 95, 116)) # blue
    mainWindow.setPalette(palette)
    mainWindow.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    createLayout(mainWindow)
    mainWindow.show()
    
def createLayout(parentWindow):
    mainLayout = QtGui.QVBoxLayout()
    
    selectionGroupBox = QtGui.QGroupBox("Select")
    selectionLayout = QtGui.QVBoxLayout()
    
    # Asset selector
    assetLayout = QtGui.QHBoxLayout()
    assetLabel = QtGui.QLabel("Set : ")
##    assetEdit = QtGui.QComboBox()
    assetEdit.setMinimumWidth(80)
    assetLayout.addWidget(assetLabel)
    assetLayout.addStretch()
    assetLayout.addWidget(assetEdit)
    selectionLayout.addLayout(assetLayout)      
        
    selectionGroupBox.setLayout(selectionLayout)
    mainLayout.addWidget(selectionGroupBox)
        
    # Button load all cameras
    loadButton = QtGui.QPushButton("Load all cameras")
    loadButton.clicked.connect(doLoadAllCameras)
    mainLayout.addWidget(loadButton)
    
    # fillSetSelector
    assetEdit.blockSignals(True)
    assetEdit.clear()
        
    #setsPath = "Z:/asset/set"
    setsPath = miscUtils.pathJoin(os.environ["ZOMB_ASSET_PATH"],"set")
    if (os.path.exists(setsPath)):
        files = os.listdir(setsPath)
        files.sort()
        count = 0
        for file in files:
            if fnmatch.fnmatch(file, "set_*"):
                assetEdit.addItem(file)
                count+=1
                
    assetEdit.setCurrentIndex(count-1)
    assetEdit.blockSignals(False)
    
    parentWindow.setLayout(mainLayout)


if __name__ == "__main__":
    camAssetMgr()