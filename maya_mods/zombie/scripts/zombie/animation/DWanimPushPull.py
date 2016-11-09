# DWanimPushPull.py

## GPU caches: 1 file per asset
## ATOM files: all assets in 1 file

import maya.cmds as cmds
import pymel.core as pm
import maya.OpenMayaUI as omui
import sys
import os
import fnmatch
import glob
import subprocess

import shiboken
from PySide import QtCore 
from PySide import QtGui 
from shiboken import wrapInstance 

from pytd.util.fsutils import pathJoin
from davos_maya.tool.general import infosFromScene, iterGeoGroups
from dminutes import gpucaching
from pytaya.core import system as myasys
from dminutes import miscUtils

## TODO
# GPU export import doesnt work
# toggle display GPU caches / Ref Anim with ATOM or not
# add a button to refresh with the new scene (listAsset, attrAnimSplit, ..)


DIALOG_ERROR_COLOR = [0.8,0.2,0.2]
DIALOG_WARNING_COLOR = [0.8,0.5,0.2]
DIALOG_INFO_COLOR = [0.2,0.3,0.8]
DIALOG_ASKING_COLOR = [0.3,0.3,0.3]
DIALOG_SUCCESS_COLOR = [0.2,0.9,0.2]

## Atributes in 'shot'
ATTR_ANIM_SPLIT="animSplit"  # attribute boolean "animSplit" = True if maya scene has already be splitted.
ATTR_ANIM_SPLIT_A="animSplitA" # attribute string "animSplitA", contains list of assets needed in this split.
ATTR_ANIM_SPLIT_B="animSplitB" # attribute string "animSplitB", contains list of assets needed in this split.
ATTR_ANIM_SPLIT_C="animSplitC" # attribute string "animSplitC", contains list of assets needed in this split.
ATTR_START_TIME="startTime"
ATTR_END_TIME="endTime"

# Path caches for shot outside prod. (tests)
# TESTS STEPH
#PATH_CACHES="P:/ZOMB/SPLIT_ANIM/TESTS"
# PROD
#PATH_CACHES="P:/AnimSplit"
PATH_CACHES=os.path.expandvars(miscUtils.normPath("$ZOMB_PRIVATE_LOC\private\AnimSplit"))


class DWanimPushPull(QtGui.QWidget):

	def __init__(self, *args, **kwargs):
		super(DWanimPushPull, self).__init__(*args, **kwargs)
		mayaMainWindowPtr = omui.MQtUtil.mainWindow()
		mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QtGui.QWidget)
		self.setParent(mayaMainWindow)        
		self.setWindowFlags(QtCore.Qt.Window) # Make this widget a standalone window even though it is parented 

		#QtGui.QWidget.__init__(self, shiboken.wrapInstance(long(mui.MQtUtil.mainWindow()), QtGui.QWidget))

		self.resize(300,200)
		#self.setFont(QtGui.QFont("Verdana"))
		try:
			self.setWindowIcon(QtGui.Icon("icon.jpg"))
		except:pass

		self.palette = QtGui.QPalette()
		self.setWindowTitle("Anim Exchange Manager")
		self.palette.setColor(QtGui.QPalette.Background, QtGui.QColor(75, 116, 75)) # green
		self.setPalette(self.palette)

		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

		# Read maya filename and check if it is a split anim.
		self.curMayaFullPathScene = cmds.file(q = True, sceneName = True) # get full path scene name loaded.
		self.curSceneName = os.path.basename(self.curMayaFullPathScene) # current Maya scene name.
		print("self.curSceneName = " + str(self.curSceneName))
		# sq6660_sh0080a_animSplitA.mb
		if not "animSplit" in self.curSceneName:
			self.isMasterShot = True
			print("It's the master shot")
		else:
			self.isMasterShot = False

		# list assets
		self.listAssetA = []
		self.listAssetB = []
		self.listAssetC = []
		self.curListAsset = None

		# get list of assets for each split anim.
		if  cmds.attributeQuery(ATTR_ANIM_SPLIT_A, node="shot", exists=True): # if list asset split anim A doesnt exist ?
			self.readListAssetsSplitAnimA() # update list assets from split anim A attribute.
		print("self.listAssetA = " + str(self.listAssetA))

		if cmds.attributeQuery(ATTR_ANIM_SPLIT_B, node="shot", exists=True):
			self.readListAssetsSplitAnimB() # update list assets from split anim B attribute.
		print("self.listAssetB = " + str(self.listAssetB))

		if cmds.attributeQuery(ATTR_ANIM_SPLIT_C, node="shot", exists=True):
			self.readListAssetsSplitAnimC()
		print("self.listAssetC = " + str(self.listAssetC))

		# Get which splitAnim it is, A, B or C ?
		self.attrAnimSplit = "" # contains ATTR_ANIM_SPLIT_A or ATTR_ANIM_SPLIT_B or ATTR_ANIM_SPLIT_C
		if not self.isMasterShot:
			if "animSplitA" in self.curSceneName:
				self.attrAnimSplit = ATTR_ANIM_SPLIT_A
				self.curListAsset = self.listAssetA
			elif "animSplitB" in self.curSceneName:
				self.attrAnimSplit = ATTR_ANIM_SPLIT_B
				self.curListAsset = self.listAssetB
			elif "animSplitC" in self.curSceneName:
				self.attrAnimSplit = ATTR_ANIM_SPLIT_C
				self.curListAsset = self.listAssetC
			else:
				print("ERROR: this is not a splitAnim shot !")
				self.attrAnimSplit = ATTR_ANIM_SPLIT_A # for testing only
				self.curListAsset = self.listAssetA

		print("self.curListAsset = " + str(self.curListAsset))

		# Check Maya scene (shot group, ...)
		if not cmds.objExists("shot"):
			cmds.error("ERROR: missing group 'shot'")
			return

		# Get start startTime and endTime
		if not self.isMasterShot:
			self.startTime = 101
			if not cmds.attributeQuery(ATTR_START_TIME, node="shot", exists=True):
				cmds.error("ERROR: missing shot attribute: " + ATTR_START_TIME)
			else:
				self.startTime = cmds.getAttr("shot."+ ATTR_START_TIME)

			self.endTime = 102
			if not cmds.attributeQuery(ATTR_END_TIME, node="shot", exists=True):
				cmds.error("ERROR: missing shot attribute: " + ATTR_END_TIME)
			else:
				self.endTime = cmds.getAttr("shot."+ ATTR_END_TIME)

			cmds.playbackOptions(animationStartTime=self.startTime, animationEndTime=self.endTime) # set start end timeline

		# Audio (Sebastien s'occupe de l'audio !)
		##if not self.isMasterShot:
		##	if cmds.objExists("audio"):
		##		cmds.setAttr("audio.sourceStart", self.startTime)

		# Get list asset splitted and not empty
		self.listAsset = None
		if not self.isMasterShot:
			isAttrAnimSplit = True
			if not cmds.attributeQuery(self.attrAnimSplit, node="shot", exists=True):
				isAttrAnimSplit = False
				cmds.error("Missing shot attribute: " + self.attrAnimSplit)
				##return

			# Get list asset splitted and not empty
			if isAttrAnimSplit:
				strList = cmds.getAttr("shot."+self.attrAnimSplit)
				self.listAsset = str(strList).split(" ")
				if not self.listAsset:
					cmds.error("Unknown 'splitAnim'")
					##return


		self.createLayout() # create GUI


	def createLayout(self):
		mainLayout = QtGui.QVBoxLayout()

		if self.isMasterShot: # if scene is a master shot
			self.getMasterAnimGpuButton = self.addButtonWidget("Get anim GPU", mainLayout, self.doMasterGetAnimGPU)
			self.getMasterAnimAtomButton = self.addButtonWidget("Get anim ATOM", mainLayout, self.doMasterGetAnimATOM)
			self.getMasterAnimAtomButton = self.addButtonWidget("Delete GPU caches", mainLayout, self.doMasterCleanGpuCaches)
			#button to hide GPU or ATOM anim
		else: # its a split anim shot
			self.pushSplitAnimGpuButton = self.addButtonWidget("Push anim GPU", mainLayout, self.doPushAnimSplitGPU)
			self.pushSplitAtomButton = self.addButtonWidget("Publish To Master", mainLayout, self.doPushAnimSplitATOM)
			self.getSplitGpuButton = self.addButtonWidget("Get anim GPU", mainLayout, self.doGetAnimSplitGPU)

		self.setLayout(mainLayout)


	def addButtonWidget(self, label, parentLayout, callFunc):
		buttonWidget = QtGui.QPushButton(label)
		parentLayout.addWidget(buttonWidget)
		buttonWidget.clicked.connect(callFunc)
		return buttonWidget

	def readListAssetsSplitAnimA(self):
		strList = cmds.getAttr("shot."+ATTR_ANIM_SPLIT_A)
		if strList:
			self.listAssetA = str(strList).split(" ")

	def readListAssetsSplitAnimB(self):
		strList = cmds.getAttr("shot."+ATTR_ANIM_SPLIT_B)
		if strList:
			self.listAssetB = str(strList).split(" ")

	def readListAssetsSplitAnimC(self):
		strList = cmds.getAttr("shot."+ATTR_ANIM_SPLIT_C)
		if strList:
			self.listAssetC = str(strList).split(" ")

	def getGpuCachePath(self): # Get path where the GPU caches of the current scene are saved
		print("getAssetGpuCachePath")
		seqShot = (self.curSceneName.split("_anim")[0]) # isolate 'sq6660_sh0080a'
		path = PATH_CACHES + "/" + seqShot
		if not os.path.exists(path): # if path is not existing yet
			os.makedirs(path) # create it
		return path

	# fix getGpuPath for each splitAnim A,B, and C ??
	def doMasterGetAnimGPU(self): # Get all GPU caches from 'anim split' scenes into the 'Master"
		print("doMasterGetAnimGPU")
		cmds.waitCursor(state=True)
		gpuCachePath = self.getGpuCachePath()
		isGpuCache = False
		if self.listAssetA:  
			self.importGpuCachesFromListAssets(gpuCachePath, self.listAssetA) # import GPU caches for each asset in animSplitA
			isGpuCache = True
		if self.listAssetB: 
			self.importGpuCachesFromListAssets(gpuCachePath, self.listAssetB) # import GPU caches for each asset in animSplitB
			isGpuCache = True
		if self.listAssetC:  
			self.importGpuCachesFromListAssets(gpuCachePath, self.listAssetC) # import GPU caches for each asset in animSplitC
			isGpuCache = True
		resetCursor()
		if isGpuCache:
			viewMessage("All GPU's animation loaded")
		else:
			viewMessage("No asset in split anim lists")


	# Build full path 'PATH_CACHES/sq6660_sh0080a/sq6660_sh0080a_animSplitA.atom' of Atom file
	def getAtomPath(self, animSplit=None): # get full path for the ATOM file containing the animation of this splitAnim.
		print("getAtomPath")
		# curSceneName has sq6660_sh0080a_anim.ma for the master or sq6660_sh0080a_animSplitA.ma for the animSplit shots.
		seqShot = (self.curSceneName.split("_anim")[0]) # isolate 'sq6660_sh0080a'
		path = PATH_CACHES + "/" + seqShot
		if not os.path.exists(path): # if path is not existing yet
			os.makedirs(path) # create it
		fullPathAtom = ""
		if not animSplit: # if no animSplit argument, take the current scene
			fullPathAtom = path + "/" + self.curSceneName.split(".")[0] # remove extension to build 'sq6660_sh0080a_animSplitA(.atom)'
		else:
			fullPathAtom = path + "/" + seqShot + "_" + animSplit
		return fullPathAtom

	def doMasterGetAnimATOM(self): # Import all ATOM animation from animSplit A, B and C
		print("doMasterGetAnimATOM")
		cmds.waitCursor(state=True)
		if self.listAssetA:
			animSplitAatomPath = self.getAtomPath(animSplit="animSplitA") 
			self.importAtomFile(animSplitAatomPath, self.listAssetA) # read anim ATOM file for this asset
		if self.listAssetB:
			animSplitBatomPath = self.getAtomPath(animSplit="animSplitB") 
			self.importAtomFile(animSplitBatomPath, self.listAssetB) # read anim ATOM file for this asset
		if self.listAssetC:
			animSplitCatomPath = self.getAtomPath(animSplit="animSplitC") 
			self.importAtomFile(animSplitCatomPath, self.listAssetC) # read anim ATOM file for this asset
		resetCursor()
		#viewMessage("All ATOM's animation loaded")
		displayInfoAndStop("All ATOM's animation loaded")

	def filterListAssetCharAndProps(self, listAssets): # filter list asset by keeping only characters and props.
		#print("filterListAssetCharAndProps")
		filterListAssets = []
		if listAssets:
			for asset in listAssets:
				if asset[0:4] == "chr_" or asset[0:4] == "prp_":
					filterListAssets.append(asset)
		return filterListAssets

	def doPushAnimSplitGPU(self): # Export GPU caches files from the current animSplit scene.
		print("doPushAnimSplitGPU")
		cmds.waitCursor(state=True)
		print("\texport GPU caches for assets: " + str(self.curListAsset))
		if self.curListAsset:
			filterListAssets = self.filterListAssetCharAndProps(self.curListAsset) # filter assets to keep only characters and props
			assetsGpuPath = self.getGpuCachePath() # get path to export
			self.exportGpuCache(filterListAssets, assetsGpuPath) # export all assets as GPU caches in subprocess
		resetCursor()
		viewMessage("GPU caches are being exported from another maya process...")

	def doPushAnimSplitATOM(self): # Export ATOM animation files from the current animSplit scene.
		print("doPushAnimSplitATOM")
		cmds.waitCursor(state=True)
		if self.curListAsset:
			filterListAssets = self.filterListAssetCharAndProps(self.curListAsset) # filter assets to keep only characters and props
			atomPath = self.getAtomPath(animSplit=self.attrAnimSplit) # get path where to export ATOM file
			print("\tatomPath = " + str(atomPath))
			print("\tfilterListAssets = " + str(filterListAssets))
			if filterListAssets:
				self.exportAtomFile(filterListAssets, atomPath) # export all assets in one ATOM file.
				cmds.waitCursor(state=False)
				viewMessage("All ATOM's animation files exported")
			else:
				resetCursor()
				viewMessage("No asset to export")

	def doGetAnimSplitGPU(self): # Get GPU caches in the current animSplit scene.
		print("doGetAnimSplitGPU")
		cmds.waitCursor(state=True)
		gpuCachesPath = self.getGpuCachePath()

		if self.attrAnimSplit == ATTR_ANIM_SPLIT_A:
			if self.listAssetB:
				self.importGpuCachesFromListAssets(gpuCachesPath, self.listAssetB)
			if self.listAssetC:
				self.importGpuCachesFromListAssets(gpuCachesPath, self.listAssetC)
		elif self.attrAnimSplit == ATTR_ANIM_SPLIT_B:
			if self.listAssetA:
				self.importGpuCachesFromListAssets(gpuCachesPath, self.listAssetA)
			if self.listAssetC:
				self.importGpuCachesFromListAssets(gpuCachesPath, self.listAssetC)
		elif self.attrAnimSplit == ATTR_ANIM_SPLIT_C:
			if self.listAssetA:
				self.importGpuCachesFromListAssets(gpuCachesPath, self.listAssetA)
			if self.listAssetB:
				self.importGpuCachesFromListAssets(gpuCachesPath, self.listAssetB)

		resetCursor()

		if self.curListAsset:
			cmds.waitCursor(state=True)
			gpuCachesPath = self.getGpuCachePath()
			self.importGpuCachesFromListAssets(gpuCachesPath, self.curListAsset)
			cmds.waitCursor(state=False)
		viewMessage("All GPU's animation caches imported")

##	def doExportAtom(self, **kwargs):
##		cmds.loadPlugin('atomImportExport.mll', quiet=True) # load plugins
##		
##		# file -force -options "precision=8;exportEdits=C:/Users/STEPH/Documents/ZOMBILLENIUM/TEST_SPLIT_ANIM/animSplitA.editMA;statics=1;baked=1;sdk=0;constraint=1;animLayers=1;selected=selectedOnly;

	def importGpuCachesFromListAssets(self, gpuCachesPath, listAsset): # Get GPU caches for a list of assets.
		print("importGpuCachesFromListAssets")
		filterListAsset = self.filterListAssetCharAndProps(listAsset)
		if len(filterListAsset) > 0:
			for asset in filterListAsset:
				namespace = asset.split(":")[0]
				filename = "gpu_" + namespace + "_grp_geo.abc"
				fullPathName = gpuCachesPath + "/" + filename
				if os.path.isfile(fullPathName):
					print("\timport GPU cache: " + fullPathName)
					self.importGpuCache(fullPathName) # corrected function from gpucaching.py
					# gpucaching.importGpuCache(fullPathName)
				else:
					print("\tWARNING: gpu cache " + str(fullPathName) + " does not exist")

	def exportGpuCache(self, listAssets, gpuPath): # export assets as GPU caches in a subprocess
		print("exportGpuCache: listAssets = " + str(listAssets) + " gpuPath = " + str(gpuPath))
		##cmds.select(listAssets, replace=True)
		##gpucaching.exportFromAssets(selected=True, namespaces=None, outputDir=gpuPath) # make a subprocess to export the gpu caches of assets
		# Get Camera
		cameras = cmds.ls("*:cam_shot_default*", cameras=1)
		if len(cameras) == 1:
			self.exportFromAssets(listAssets = listAssets, outputDir=gpuPath, shotCamera = cameras[0]) # make a subprocess to export the gpu caches of assets
		else:
			print("ERROR: exportGpuCache: cameras = " + str(cameras))

	# vient de "gpuCache" de 2minutes.
	def importGpuCache(self, sAbcPath): 

		statinfo = os.stat(sAbcPath)
		sBaseName, _ = os.path.splitext(os.path.basename(sAbcPath))

		sGpuGrp = "|shot|grp_gpuCache"
		if not cmds.objExists(sGpuGrp):
			cmds.createNode("transform", n="grp_gpuCache", parent="|shot", skipSelect=True)

		# Test if node 'gpuCache' already exists
		if cmds.objExists(sBaseName):
			cmds.delete(sBaseName)

		sGpuShape = cmds.createNode("gpuCache", n=sBaseName + "Shape", skipSelect=True)
		cmds.addAttr(sGpuShape, ln="cacheFileMtime", at="long", dv=0)
		cmds.addAttr(sGpuShape, ln="cacheFileSize", at="long", dv=0)

		sGpuXfm = cmds.listRelatives(sGpuShape, parent=True, path=True)[0]
		sGpuXfm = cmds.rename(sGpuXfm, sBaseName)
		cmds.parent(sGpuXfm, sGpuGrp)

		cmds.setAttr(sGpuShape + ".cacheFileName", sAbcPath, type="string")
		cmds.setAttr(sGpuShape + ".cacheGeomPath", "|", type="string")
		cmds.setAttr(sGpuShape + ".cacheFileMtime", long(statinfo.st_mtime)) # modification time
		cmds.setAttr(sGpuShape + ".cacheFileSize", statinfo.st_size)

		#return sGpuXfm, sGpuShape

	# Export Atom file for list of assets (one ATOM file for all the assets).
	def exportAtomFile(self, listAssets, assetsAtomPath):
		print("exportAtomFile: assetsAtomPath = " + str(assetsAtomPath))
		# Select first the asset(s) root before (like "chr_francis_default_01:asset")
		cmds.select(listAssets, replace=True)
		# work with multiple assets. Use "time_slider" (ComboBox ??) to lit export time when cycles !
		myasys.exportAtomFile(assetsAtomPath,
							  SDK=False,
							  constraints=False, # do we need True ?
							  animLayers=True,
							  statics=True,
							  baked=True,
							  points=False,
							  hierarchy="below", # "selected":1, "below":2
							  channels="all_keyable", # "all_keyable":1, "from_channel_box":2
							  timeRange="time_slider" # "all":1, "time_slider":2, "single_frame":3, "start_end":4
							 )

	# Import Atom file (one ATOM file may contain multiple assets)
	def importAtomFile(self, path, listAsset):
		print("importAtomfile: path = " + str(path))
		filterListAsset = self.filterListAssetCharAndProps(listAsset) # filter assets to keep only characters and props
		cmds.select(filterListAsset, replace=True)
		#if not os.path.exists(path): # check if path exists
		#	cmds.error("path = " + str(path) + " does not exist")
		#	return
		# find the last file in the 'path'
		files = filter(os.path.isfile, glob.glob(path + "*.atom"))
		files.sort(key=lambda x: os.path.getmtime(x)) # sort by time
		if files:
			lastFile = files[-1]
			print("\tlastFile = " + str(lastFile))
			# Select first the asset(s) root before (like "chr_francis_default_01:asset")            
			myasys.importAtomFile(lastFile,
								 targetTime="from_file",
								 option="replace", # replace existing animation
								 match="string",
								 selected="childrenToo")

	## From gpucaching
	# export GPU caches for list of assets
	def exportFromAssets(self, listAssets=None, outputDir="", shotCamera=None):
		print("listAssets= " + str(listAssets) + " outputDir= " + str(outputDir) + " shotCamera= " + str(shotCamera))

		if not listAssets:
			print("ERROR: No asset to export")
			return

		sGeoGrpList = () # tuple initialization.
		geoList = []

		for asset in listAssets:
			ns = asset.split(":")[0] # isolate namespace.
			geoName = ns + ":grp_geo"
			if cmds.objExists(geoName):
				geoList.append(geoName)
		if geoList:
			sGeoGrpList = tuple(geoList) # Convert list to tuple
		else:
			sMsg = "No geo groups found{}".format(" from selection.")
			raise RuntimeError(sMsg)

		print("sGeoGrpList = " + str(sGeoGrpList))

		##sShotCam = mop.getShotCamera(damShot.name, fail=True).name()
		sShotCam = shotCamera

		sOutDirPath = outputDir

		sSelList = list(s.replace(":grp_geo", ":asset") for s in sGeoGrpList)
		cmds.select(sSelList + [sShotCam], r=True)
		curTime = cmds.currentTime(q=True)
		cmds.currentTime(101)
		cmds.refresh()
		try:
			sFilePath = pm.exportSelected(pathJoin(sOutDirPath, "export_gpuCache_" + str(self.attrAnimSplit) + "_tmp.mb"),
										  type="mayaBinary",
										  preserveReferences=False,
										  shader=True,
										  channels=True,
										  constraints=True,
										  expressions=True,
										  constructionHistory=True,
										  force=True)
		finally:
			cmds.currentTime(curTime)

		sPython27Path = r"C:\Python27\python.exe"
		sZ2kEnvScript = os.environ["Z2K_LAUNCH_SCRIPT"]
		sAppPath = os.path.join(os.environ["MAYA_LOCATION"], "bin", "mayabatch.exe")

		timeRange = (pm.playbackOptions(q=True, animationStartTime=True),
					pm.playbackOptions(q=True, animationEndTime=True))

#    timeRange = (pm.playbackOptions(q=True, minTime=True),
#                 pm.playbackOptions(q=True, maxTime=True))

		sPyCmd = "from dminutes import gpucaching;reload(gpucaching);"
		sPyCmd += "gpucaching._doExportGpuCaches('{}',{},{},'{}');".format(sOutDirPath,
																		   timeRange[0],
																		   timeRange[1],
																		   sShotCam)
		sMelCmd = "python(\"{}\"); quit -f;".format(sPyCmd)

		sCmdArgs = [sPython27Path,
					os.path.normpath(sZ2kEnvScript),
					"launch", "--update", "0", "--renew", "1",
					os.path.normpath(sAppPath),
					"-file", os.path.normpath(sFilePath),
					"-command", sMelCmd, "-prompt"
					]

		print("sMelCmd: " + str(sMelCmd))
		print("sCmdArgs: " + str(sCmdArgs))

		SW_MINIMIZE = 6
		info = subprocess.STARTUPINFO()
		info.dwFlags = subprocess.STARTF_USESHOWWINDOW
		info.wShowWindow = SW_MINIMIZE

		subprocess.Popen(sCmdArgs, startupinfo=info)

		pm.displayInfo("GPU caches are being exported from another maya process...")


	def doMasterCleanGpuCaches(self):
		#print("doMasterCleanGpuCaches")
		if cmds.objExists("grp_gpuCache"):
			cmds.delete("grp_gpuCache")
			viewMessage("All GPU caches deleted")
		else:
			viewMessage("No more GPU caches")


def resetCursor(): # to avoid cursor in wait state (the waitCursor has a pile of state and when it crash the cursor can stay in the wrong state)
	while cmds.waitCursor(q=1, state=0):
		cmds.waitCursor(state=0)


def viewMessage(text):
	print(text) # to hav ethe text in script editor
	cmds.inViewMessage( amg='<hl>' + text + '</hl>.', pos='midCenter', fade=True )
	
def displayInfoAndStop(message):
	result = cmds.confirmDialog( title='Info', backgroundColor=DIALOG_INFO_COLOR, message=message, button=['Ok'], defaultButton='Ok' )
	return result


# Launch DWanimPushPull
try :
    uiDWanimPushPull.close()
except :
    pass
uiDWanimPushPull = DWanimPushPull()
uiDWanimPushPull.show()