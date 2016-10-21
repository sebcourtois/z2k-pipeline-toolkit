## DWsplitAnim.py

import maya.cmds as cmds
import pymel.core as pm
import maya.OpenMayaUI as omui
import sys

import shiboken
from PySide import QtCore 
from PySide import QtGui 
from shiboken import wrapInstance 

from dminutes import gpucaching
from davos_maya.tool.general import infosFromScene
from davos.core.damproject import DamProject

## TODO

# add context menu to choice all asset, only char, only prop, ....

DIALOG_ERROR_COLOR = [0.8,0.2,0.2]
DIALOG_WARNING_COLOR = [0.8,0.5,0.2]
DIALOG_INFO_COLOR = [0.2,0.3,0.8]
DIALOG_ASKING_COLOR = [0.3,0.3,0.3]
DIALOG_SUCCESS_COLOR = [0.2,0.9,0.2]

ATTR_ANIM_SPLIT="animSplit"  # attribute boolean "animSplit" = True if maya scene has already be splitted.
ATTR_ANIM_SPLIT_A="animSplitA" # attribute string "animSplitA", contains list of assets needed in this split.
ATTR_ANIM_SPLIT_B="animSplitB" # attribute string "animSplitB", contains list of assets needed in this split.
ATTR_ANIM_SPLIT_C="animSplitC" # attribute string "animSplitC", contains list of assets needed in this split.
ATTR_START_TIME="startTime"
ATTR_END_TIME="endTime"

TEST_EXPORT_PATH=r"C:\Users\STEPH\Documents\ZOMBILLENIUM\TEST_SPLIT_ANIM"


class SplitAnimMgr(QtGui.QWidget):
#	def __init__(self, parent=None):
#		QtGui.QWidget.__init__(self, shiboken.wrapInstance(long(mui.MQtUtil.mainWindow()), QtGui.QWidget))
		
	def __init__(self, *args, **kwargs):
		super(SplitAnimMgr, self).__init__(*args, **kwargs)
		mayaMainWindowPtr = omui.MQtUtil.mainWindow()
		mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QtGui.QWidget)
		self.setParent(mayaMainWindow)        
		self.setWindowFlags(QtCore.Qt.Window) # Make this widget a standalone window even though it is parented 
		
		#QtGui.QWidget.__init__(self, shiboken.wrapInstance(long(mui.MQtUtil.mainWindow()), QtGui.QWidget))
		
		self.resize(600,500)
		#self.setFont(QtGui.QFont("Verdana"))
		try:
			self.setWindowIcon(QtGui.Icon("icon.jpg"))
		except:pass
		
		self.palette = QtGui.QPalette()
		self.setWindowTitle("Split Anim Manager")
		self.palette.setColor(QtGui.QPalette.Background, QtGui.QColor(75, 95, 116)) # blue
		self.setPalette(self.palette)

		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		
		# list of different assets in Maya scene.
		self.listChr = []
		self.listC2d = []
		self.listCrw = []
		self.listPrp = []
		self.listVhl = []
		self.listCam = []
		self.listSet = []
		self.listEnv = []
		
		# list assets
		self.listAssetM = []
		self.listAssetA = []
		self.listAssetB = []
		self.listAssetC = []
		
		# display asset filter
		self.assetFilterM = "ALL"
		self.assetFilterA = "ALL"
		self.assetFilterB = "ALL"
		self.assetFilterC = "ALL"
		
		# UI
		self.assetListWidgetM = None
		self.assetListWidgetA = None
		self.assetListWidgetB = None
		self.assetListWidgetC = None
		
		# Check Maya scene (shot group, list assets not empty, ...)
		if not cmds.objExists("shot"):
			print("ERROR: missing group 'shot'")
			return -1

		self.exportPath = TEST_EXPORT_PATH

		# update from Maya scene
		if not cmds.attributeQuery(ATTR_ANIM_SPLIT, node="shot", exists=True): # if attribute SPLIT_ANIM doesnt exists
			cmds.addAttr("shot", longName=ATTR_ANIM_SPLIT, at='bool') # create one

			# and reset all attribute list plit anim A,B,C
			if not cmds.attributeQuery(ATTR_ANIM_SPLIT_A, node="shot", exists=True): # if list asset split anim A doesnt exist ?
				cmds.addAttr("shot", longName=ATTR_ANIM_SPLIT_A, dt='string') # create this list
			cmds.setAttr("shot."+ATTR_ANIM_SPLIT_A, "", type='string') # reset list 'animSplitA'

			if not cmds.attributeQuery(ATTR_ANIM_SPLIT_B, node="shot", exists=True):
				cmds.addAttr("shot", longName=ATTR_ANIM_SPLIT_B, dt='string')
			cmds.setAttr("shot."+ATTR_ANIM_SPLIT_B, "", type='string') # reset list 'animSplitB'

			if not cmds.attributeQuery(ATTR_ANIM_SPLIT_C, node="shot", exists=True):
				cmds.addAttr("shot", longName=ATTR_ANIM_SPLIT_C, dt='string')
			cmds.setAttr("shot."+ATTR_ANIM_SPLIT_C, "", type='string') # reset list 'animSplitC'

		else: # split anim already existing in maya scene, so read saved assets list and update gui.
			print("attribute SPLIT_ANIM exists")
			if not cmds.attributeQuery(ATTR_ANIM_SPLIT_A, node="shot", exists=True): # if list asset split anim A doesnt exist ?
				cmds.addAttr("shot", longName=ATTR_ANIM_SPLIT_A, dt='string')
				cmds.setAttr("shot."+ATTR_ANIM_SPLIT_A, "", type='string') # reset list 'animSplitA'
			else:
				print("list asset split anim A exists")
				self.readListAssetsSplitAnimA() # update list assets from split anim A attribute.

			if not cmds.attributeQuery(ATTR_ANIM_SPLIT_B, node="shot", exists=True):
				cmds.addAttr("shot", longName=ATTR_ANIM_SPLIT_B, dt='string')
				cmds.setAttr("shot."+ATTR_ANIM_SPLIT_B, "", type='string') # reset list 'animSplitB'
			else:
				self.readListAssetsSplitAnimB() # update list assets from split anim B attribute.

			if not cmds.attributeQuery(ATTR_ANIM_SPLIT_C, node="shot", exists=True):
				cmds.addAttr("shot", longName=ATTR_ANIM_SPLIT_C, dt='string')
				cmds.setAttr("shot."+ATTR_ANIM_SPLIT_C, "", type='string') # reset list 'animSplitC'
			else:
				self.readListAssetsSplitAnimC()

		# Get shot time range and save it in 'shot" attributes.
		timeRange = (pm.playbackOptions(q=True, animationStartTime=True),pm.playbackOptions(q=True, animationEndTime=True))
		if not cmds.attributeQuery(ATTR_START_TIME, node="shot", exists=True):
			cmds.addAttr("shot", longName=ATTR_START_TIME, at='float')
		cmds.setAttr("shot."+ATTR_START_TIME, timeRange[0])
		if not cmds.attributeQuery(ATTR_END_TIME, node="shot", exists=True):
			cmds.addAttr("shot", longName=ATTR_END_TIME, at='float')
		cmds.setAttr("shot."+ATTR_END_TIME, timeRange[1])
		
		self.createLayout() # create GUI
		
		self.refreshAssetListWidgetA() # refresh UI widget list asset animator A
		self.refreshAssetListWidgetB() # refresh UI widget list asset animator B
		self.refreshAssetListWidgetC() # refresh UI widget list asset animator C


#	def readListAssetsSplitAnim(self, attrName, listAsset):
#		print("readListAssetsSplitAnim")
#		strList = cmds.getAttr("shot."+attrName)
#		print("\tstrList = " + str(strList))
#		listAsset = str(strList).split(" ")
#		print("\tlistAsset = " + str(listAsset))

	def readListAssetsSplitAnimA(self):
		print("readListAssetsSplitAnimA: self.listAssetA = " + str(self.listAssetA))
		strList = cmds.getAttr("shot."+ATTR_ANIM_SPLIT_A)
		self.listAssetA = str(strList).split(" ")
		print("self.listAssetA = " + str(self.listAssetA))

	def readListAssetsSplitAnimB(self):
		strList = cmds.getAttr("shot."+ATTR_ANIM_SPLIT_B)
		self.listAssetB = str(strList).split(" ")

	def readListAssetsSplitAnimC(self):
		strList = cmds.getAttr("shot."+ATTR_ANIM_SPLIT_C)
		if strList:
			self.listAssetC = str(strList).split(" ")

	def writeListAssetsSplitAnim(self, attrName, listAsset):
		strList = ""
		if listAsset:
			strList = " ".join(listAsset)
		cmds.setAttr("shot."+attrName, strList, type='string')

	def writeListAssetSplitAnimA(self):
		print("writeListAssetSplitAnimA")
		self.writeListAssetsSplitAnim(ATTR_ANIM_SPLIT_A, self.listAssetA)

	def writeListAssetSplitAnimB(self):
		self.writeListAssetsSplitAnim(ATTR_ANIM_SPLIT_B, self.listAssetB)

	def writeListAssetSplitAnimC(self):
		self.writeListAssetsSplitAnim(ATTR_ANIM_SPLIT_C, self.listAssetC)


	def createLayout(self):
		mainLayout = QtGui.QHBoxLayout()

		## MASTER
		animMasterGroupBox = QtGui.QGroupBox("Anim Master")
		animMasterGroupBox.setAutoFillBackground(True) # to have the possibility to change the color background.
		#self.paletteM = animMasterGroupBox.palette()
		#self.paletteM = QtGui.QPalette()
		#self.paletteM.setColor(QtGui.QPalette.Background, QtGui.QColor(112, 142, 174)) # red
		##animMasterGroupBox.setStyleSheet("border:2px solid rgb(112, 142, 174);  border-radius: 5px; margin-top: 0px; margin-bottom: 0px")
		#animMasterGroupBox.setStyleSheet("QtGui.QGroupBox.title {background-color: transparent; padding-top: -24px; padding-left: 8px"})
		#animMasterGroupBox.setPalette(self.paletteM)
		animMasterLayout = QtGui.QVBoxLayout()

		topListButtonsLayout = QtGui.QHBoxLayout() # layout list buttons horizontal

		self.assetSelectorM = self.addFilterAssetWidgetABC(topListButtonsLayout, self.selectorActivatedM) # Display Asset Selection Filter

		self.refreshAssetButton = self.addButtonABC("Refresh", topListButtonsLayout, self.doRefreshAssetsM) # Add button 'Refresh'

		self.getSelectionButton = self.addButtonABC("Get Selection", topListButtonsLayout, self.getSelectedItemsM) # Add button 'Refresh'

		animMasterLayout.addLayout(topListButtonsLayout)

		#animMasterLayout.addStretch()
		self.assetListWidgetM = QtGui.QListWidget()
		animMasterLayout.addWidget(self.assetListWidgetM)
		self.assetListWidgetM.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection) # Allow multiples selections.
		self.assetListWidgetM.setAlternatingRowColors(True)
		self.assetListWidgetM.setStyleSheet("alternate-background-color:#333333; background-color: #222222")
		self.addContextMenuABCM(self.assetListWidgetM, self.openMenuM) # add context menu to list assets.

		animMasterGroupBox.setLayout(animMasterLayout)
		mainLayout.addWidget(animMasterGroupBox)


		## ANIMATOR A
		animGroupBoxA = QtGui.QGroupBox("Animator A")
		animLayoutA = QtGui.QVBoxLayout()

		topButtonsLayoutA = QtGui.QHBoxLayout() # layout list buttons "filter, add, remove"
		self.assetSelectorA = self.addFilterAssetWidgetABC(topButtonsLayoutA, self.selectorActivatedA) # add filter asset widget.
		self.addButtonABC("Add", topButtonsLayoutA, self.addAssetA) # Add button 'Add asset'
		self.addButtonABC("Remove", topButtonsLayoutA, self.removeAssetA) # Add button 'Remove asset'
		animLayoutA.addLayout(topButtonsLayoutA)

		self.assetListWidgetA = self.addListAssetsWidgetABC(animLayoutA) # Add list assets
		##self.addContextMenuABCM(self.assetListWidgetA, self.openMenuABC) # add context menu to list assets.

		animGroupBoxA.setLayout(animLayoutA)
		mainLayout.addWidget(animGroupBoxA)

		## ANIMATOR B
		animGroupBoxB = QtGui.QGroupBox("Animator B")
		animLayoutB = QtGui.QVBoxLayout()

		topButtonsLayoutB = QtGui.QHBoxLayout() # layout list buttons "filter, add, remove"
		self.assetSelectorB = self.addFilterAssetWidgetABC(topButtonsLayoutB, self.selectorActivatedB) # add filter asset widget.
		self.addButtonABC("Add", topButtonsLayoutB, self.addAssetB) # Add button 'Add asset'
		self.addButtonABC("Remove", topButtonsLayoutB, self.removeAssetB) # Add button 'Remove asset'
		animLayoutB.addLayout(topButtonsLayoutB)

		self.assetListWidgetB = self.addListAssetsWidgetABC(animLayoutB) # Add list assets
		##self.addContextMenuABCM(self.assetListWidgetB, self.openMenuABC) # add context menu to list assets.

		animGroupBoxB.setLayout(animLayoutB)
		mainLayout.addWidget(animGroupBoxB)

		## ANIMATOR C
		animGroupBoxC = QtGui.QGroupBox("Animator C")
		animLayoutC = QtGui.QVBoxLayout()

		topButtonsLayoutC = QtGui.QHBoxLayout() # layout list buttons "filter, add, remove"
		self.assetSelectorC = self.addFilterAssetWidgetABC(topButtonsLayoutC, self.selectorActivatedC) # add filter asset widget.
		self.addButtonABC("Add", topButtonsLayoutC, self.addAssetC) # Add button 'Add asset'
		self.addButtonABC("Remove", topButtonsLayoutC, self.removeAssetC) # Add button 'Remove asset'
		animLayoutC.addLayout(topButtonsLayoutC)

		self.assetListWidgetC = self.addListAssetsWidgetABC(animLayoutC) # Add list assets
		##self.addContextMenuABCM(self.assetListWidgetC, self.openMenuABC) # add context menu to list assets.

		animGroupBoxC.setLayout(animLayoutC)
		mainLayout.addWidget(animGroupBoxC)

		self.setLayout(mainLayout)

		# refresh assets master
		self.doRefreshAssetsM()

# SIGNALS - SLOTS
		# different in pySide !!!!
		#self.epiEdit.connect(self.seasonEdit, QtCore.SIGNAL("currentIndexChanged (int)"), self.fillEpiCombo) # update Episode combo from Season.
		self.assetListWidgetM.itemClicked.connect(self.Clicked)

	def addFilterAssetWidgetABC(self, parentLayout, callFunc):
		comboBoxFilterAsset = QtGui.QComboBox()
		comboBoxFilterAsset.setMinimumWidth(50)
		comboBoxFilterAsset.addItem("All")
		comboBoxFilterAsset.addItem("Character")
		comboBoxFilterAsset.addItem("Prop")
		comboBoxFilterAsset.addItem("Set")
		comboBoxFilterAsset.addItem("Vehicle")
		comboBoxFilterAsset.addItem("Env")
		comboBoxFilterAsset.addItem("Char2d")
		comboBoxFilterAsset.addItem("Crowd")
		parentLayout.addWidget(comboBoxFilterAsset)
		comboBoxFilterAsset.activated[str].connect(callFunc)
		return comboBoxFilterAsset

	def addButtonABC(self, label, parentLayout, callFunc):
		buttonWidget = QtGui.QPushButton(label)
		parentLayout.addWidget(buttonWidget)
		buttonWidget.clicked.connect(callFunc)
		return buttonWidget
		
	def addListAssetsWidgetABC(self, parentLayout):
		assetListWidget = QtGui.QListWidget()
		parentLayout.addWidget(assetListWidget)
		assetListWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection) # Allow multiples selections.
		assetListWidget.setAlternatingRowColors(True)
		assetListWidget.setStyleSheet("alternate-background-color:#333333; background-color: #222222")
		return assetListWidget
		
	def addContextMenuABCM(self, myWidget, callFunc):
		myWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		myWidget.customContextMenuRequested.connect(callFunc)

	def fillAssetListWidgetM(self):
		#print("fillAssetListWidgetM\n")
		self.assetListWidgetM.blockSignals(True)
		self.assetListWidgetM.clear()

		#self.buildListAssetsM() # read all asset in current scene.
		print("self.assetFilterM = " + str(self.assetFilterM))
		if (self.assetFilterM == "ALL" or self.assetFilterM == "CHARACTER") and self.listChr:
			for char in self.listChr:
				self.assetListWidgetM.addItem(char)
		if (self.assetFilterM == "ALL" or self.assetFilterM == "PROP") and self.listPrp:
			for prop in self.listPrp:
				self.assetListWidgetM.addItem(prop)
		if (self.assetFilterM == "ALL" or self.assetFilterM == "SET") and self.listSet:
			for set in self.listSet:
				self.assetListWidgetM.addItem(set)
		if (self.assetFilterM == "ALL" or self.assetFilterM == "VEHICLE") and self.listVhl:
			for vhl in self.listVhl:
				self.assetListWidgetM.addItem(vhl)
		if (self.assetFilterM == "ALL" or self.assetFilterM == "ENV") and self.listEnv:
			for env in self.listEnv:
				self.assetListWidgetM.addItem(env)
		if (self.assetFilterM == "ALL" or self.assetFilterM == "CHAR2D") and self.listC2d:
			for c2d in self.listC2d:
				self.assetListWidgetM.addItem(env)
		if (self.assetFilterM == "ALL" or self.assetFilterM == "CROWD") and self.listCrw:
			for crw in self.listCrw:
				self.assetListWidgetM.addItem(crw)
		# add c2d, crw, cam, env ?

		#self.assetListWidgetM.repaint()
		self.assetListWidgetM.blockSignals(False)


	def fillAssetListWidgetABC(self, assetList, assetListWidget, assetFilter):
		assetListWidget.blockSignals(True)
		assetListWidget.clear()
		print("fillAssetListWidget")
		print("\tassetList = " + str(assetList))
		if "ALL" in assetFilter:
			for item in assetList:
				assetListWidget.addItem(item)
		else:
			prefix = None
			if "CHARACTER" in assetFilter:
				prefix = "chr_"
			elif "PROP" in assetFilter:
				prefix = "prp_"
			elif "SET" in assetFilter:
				prefix = "set_"
			elif "VEHICLE" in assetFilter:
				prefix = "vhl_"
			elif "ENV" in assetFilter:
				prefix = "env_"
			elif "CHAR2D" in assetFilter:
				prefix = "c2d_"
			elif "CROWD" in assetFilter:
				prefix = "crw_"

			for item in assetList:
				if prefix in item:
					assetListWidget.addItem(item)

		assetListWidget.blockSignals(False)


	def Clicked(self,item):
		print("ListWidget", "You clicked: "+item.text())

	def refreshAssetListWidgetA(self):
		self.fillAssetListWidgetABC(self.listAssetA, self.assetListWidgetA, self.assetFilterA)
		#self.writeListAssetSpliAnimA()

	def refreshAssetListWidgetB(self):
		self.fillAssetListWidgetABC(self.listAssetB, self.assetListWidgetB, self.assetFilterB)
		#self.writeListAssetSpliAnimB()

	def refreshAssetListWidgetC(self):
		self.fillAssetListWidgetABC(self.listAssetC, self.assetListWidgetC, self.assetFilterC)
		#self.writeListAssetSpliAnimC()

	def addAssetABC(self, listAsset):
		#print("addAssetABC: " + str(self.sender().text()))
		items = self.getSelectedItemsM() # get selected items from Master
		#print("Master selection = " + str(assets))
		# for each item, test if already used in A,B, or C
		for item in items:
			# TODO: get prefix of asset and for (chr_, prp_), test if already 
			if not item.text() in listAsset:
				listAsset.append(item.text())

	def addAssetA(self): # Add selected asset from Master to animatorABC.
		#print("addAssetA " + str(self.sender().text()))
		self.addAssetABC(self.listAssetA)
		self.refreshAssetListWidgetA() # refresh list asset widget
		self.writeListAssetSplitAnimA() # write list in attribute

	def addAssetB(self): # Add selected asset from Master to animatorABC.
		self.addAssetABC(self.listAssetB)
		self.refreshAssetListWidgetB() # refresh list asset widget
		self.writeListAssetSplitAnimB()

	def addAssetC(self): # Add selected asset from Master to animatorABC.
		self.addAssetABC(self.listAssetC)
		self.refreshAssetListWidgetC() # refresh list asset widget
		self.writeListAssetSplitAnimC()

	def removeAssetA(self): # Remove selected asset(s) from Master from animatorABC.
		self.removeSelectedAssetFromAssetList(self.listAssetA, self.assetListWidgetA)
		self.refreshAssetListWidgetA()
		self.writeListAssetSplitAnimA()

	def removeAssetB(self): # Remove selected asset(s) from Master from animatorABC.
		self.removeSelectedAssetFromAssetList(self.listAssetB, self.assetListWidgetB)
		self.refreshAssetListWidgetB()
		self.writeListAssetSplitAnimB()

	def removeAssetC(self): # Remove selected asset(s) from Master from animatorABC.
		self.removeSelectedAssetFromAssetList(self.listAssetC, self.assetListWidgetC)
		self.refreshAssetListWidgetC()
		self.writeListAssetSplitAnimC()

	def getSelectedItemsM(self):
		#print "Current Items are : ", self.assetListWidgetM.selectedItems()
		return self.getSelectedItemsFromAssetListWidget(self.assetListWidgetM)

	def getSelectedItemsFromAssetListWidget(self, assetListWidget):
		#print "Current Items are : ", assetListWidget.selectedItems()
		sel = []
		if not assetListWidget.selectedItems(): return sel
		for item in assetListWidget.selectedItems():  
			sel.append(item) # item and not item.text()

		return sel

	def addSelectedAssetFromMasterToAssetList(self, dstAssetList):
		sel = self.getSelectedItemsM()
		if not sel: return
		for item in sel:
			self.dstAssetList.addItem(item.text())

##	def removeSelectedAssetFromAssetListWidget(self, assetList):
##		listItems = self.getSelectedItemsFromAssetListWidget(assetList)
##		if not listItems: return
##		for item in listItems:
##			assetList.takeItem(item)
			
	def removeSelectedAssetFromAssetList(self, assetList, assetListWidget):
		listItems = self.getSelectedItemsFromAssetListWidget(assetListWidget)
		if not listItems: return
		for item in listItems:
			try:
				assetList.remove(item.text())
			except ValueError:
				print("ERROR: Can't remove " + str(item.text()))


	def buildListAssetsM(self):
		# Get list of assets from Master. Sometimes asset can be out of groups in Maya scene ...
		assets = cmds.ls("*:asset")
		self.listChr = []
		self.listPrp = []
		self.listSet = []
		self.listVhl = []
		self.listCam = []
		self.listC2d = []
		self.listCrw = []
		self.listEnv = []
		if not assets:
			print("ERROR: no more assets in maya scene !")
			return -1
		for asset in assets:
			prefix = asset.split("_")[0]
			if prefix == "chr": # character 3d
				self.listChr.append(asset)
			elif prefix == "prp": # prop, accessoires(rigges/animes)
				self.listPrp.append(asset)
			elif prefix == "set": # element de décor (statiques mais pouvant etre positionnes de façon differentes dans chaque plan)
				self.listSet.append(asset)
			elif prefix == "vhl": # vehicule
				self.listVhl.append(asset)
			elif prefix == "cam": # camera
				self.listCam.append(asset)
			elif prefix == "c2d": # character 2d
				self.listC2d.append(asset)
			elif prefix == "crw": # crowd personnages simplifies destines aux foules
				self.listCrw.append(asset)
			elif prefix == "env": # environment (ciel et/ou matte painting...)
				self.listEnv.append(asset)
			else:
				print("WARNING: asset prefix unknown: " + str(asset))

	def doRefreshAssetsM(self): # Refresh master list from scene
		self.buildListAssetsM() # read asset from Maya scene
		self.fillAssetListWidgetM() # re-build the list widget.
		# TODO update Animator A,B,C.

	def selectorActivatedM(self, text):
		#print("selectorActivatedM: text = " + str(text))
		self.assetFilterM = text.upper()
		#print("self.assetFilterM = " + str(self.assetFilterM))
		self.fillAssetListWidgetM()

	def selectorActivatedA(self, text):

		# refresh list assets
		self.assetFilterA = text.upper()
		self.refreshAssetListWidgetA()

	def selectorActivatedB(self, text):
		# refresh list assets
		self.assetFilterB = text.upper()
		self.refreshAssetListWidgetB()
		
	def selectorActivatedC(self, text):
		# refresh list assets
		self.assetFilterC = text.upper()
		self.refreshAssetListWidgetC()

	def openMenuM(self): # context menu Master
		mainMenu = QtGui.QMenu()

		selectMenu = mainMenu.addMenu("&Select")
		selectMenu.addAction(self.tr("AnimatorA"), self.selectAssetsAnimA)
		selectMenu.addAction(self.tr("AnimatorB"), self.selectAssetsAnimB)
		selectMenu.addAction(self.tr("AnimatorC"), self.selectAssetsAnimC)
		selectAllAnimator = selectMenu.addAction(self.tr("All animators"), self.selectAssetsAllAnim)

		generateMenu = mainMenu.addMenu("&Generate Scene")
		generateAnimatorA = generateMenu.addAction(self.tr("AnimatorA"), self.generateSceneAnimA)
		generateAnimatorA = generateMenu.addAction(self.tr("AnimatorB"), self.generateSceneAnimB)
		generateAnimatorA = generateMenu.addAction(self.tr("AnimatorC"), self.generateSceneAnimC)
		generateAllAnimator = generateMenu.addAction(self.tr("All animators"), self.generateAllSceneAnim)

		mainMenu.exec_(QtGui.QCursor.pos())


	## Not yet ready.
	def openMenuABC(self): # context menu
		mainMenu = QtGui.QMenu()
		actionSelect = mainMenu.addAction(self.tr("Select"), self.doSelect)
		mainMenu.addAction(self.tr("Do action2"))
		mainMenu.addSeparator()
		helpMenu = mainMenu.addMenu("&Help")
		helpMenu.addAction(self.tr("About"), self.about)

		#self.assetListWidgetA.connect(action1, QtCore.SIGNAL("triggered"), self.doAction1)

		mainMenu.exec_(QtGui.QCursor.pos())

	def doSelectA(self):
		print("doSelect")
		cmds.select(listAsset, add=True) # Select objects in list
		cmds.select(cl=True) # clear selection.

	def about(self):
		print("About")
		
	def selectAssetsAnimABC(self, listAsset):
		cmds.select(cl=True) # clear selection.
		cmds.select(listAsset, add=True) # Select objects in list

	def selectAssetsAnimA(self):
		self.selectAssetsAnimABC(self.listAssetA)

	def selectAssetsAnimB(self):
		self.selectAssetsAnimABC(self.listAssetB)

	def selectAssetsAnimC(self):
		self.selectAssetsAnimABC(self.listAssetC)

	def selectAssetsAllAnim(self):
		self.selectAssetsAnimA()
		self.selectAssetsAnimB()
		self.selectAssetsAnimC()
		
	def createDavosPublicSplitAnim(self, type="animSplitA_scene"): # create the shot animSplit(A,B,C)_scene as 'public' thru Davos
		scnInfos = infosFromScene()
		#print("scnInfos = " + str(scnInfos))
		# {'abs_path': u'//lv7000_fileserver/Zombidamas/private/stephanes/zomb/shot/sq0050/sq0050_sh0010a/04_anim/sq0050_sh0010a_anim-v017-readonly.ma', 'resource': 'anim_scene', 'name': u'sq0050_sh0010a', 'space': 'private', 'section': 'shot_lib', 'sequence': u'sq0050', 'library': Library('private|shot_lib'), 'project': DamProject('zombillenium'), 'step': u'04_anim', 'rc_entry': File('sq0050_sh0010a_anim-v017-readonly.ma'), 'sg_step': 'Animation', 'dam_entity': Shot('sq0050_sh0010a')}
		damShot = scnInfos["dam_entity"]
		#print("proj: " + str(proj))
		shotName = scnInfos['name']
		#print("shotName: " + shotName)
		# gets the shot entity giving a shot name
		proj = DamProject("zombillenium")
		damShot = proj.getShot(shotName)
		#print vars(damShot) # >> {'project': DamProject('zombillenium'), 'confSection': 'shot_lib', 'baseName': 'sh0050a', 'name': 'sq6660_sh0050a', 'sequence': 'sq6660'}

		pubScn = damShot.getRcFile("public", type, create=True) # public scene created if missing
		sPubScnPath = pubScn.absPath()
		print("\tsPubScnPath = " + str(sPubScnPath))

		if pubScn.currentVersion == 0: 
			# no version published yet
			print("\tNo version published yet, we can overwrite the public scene")
		else:
			print("\tAlready published, create a private scene")
			# ERROR si on veut re-publier une scene split anim existante comment on fait ?
			
		return sPubScnPath # return absolute path of the split scene created

	def generateSceneAnimABC(self, type, listAsset, listAssetWidget):
		#print("generateSceneAnimABC: type = " + str(type) + " listAsset = " + str(listAsset) + " listAssetWidget = " + str(listAssetWidget))
		cmds.select(cl=True) # clear selection.
		cmds.select("grp_camera", add=True) # add always camera
		cmds.select(listAsset, add=True) # Select objects in list

		filename = self.createDavosPublicSplitAnim(type=type) # create the splitAnim scene thru Davos. Return full path filename
		
		if filename:
			##cmds.file(filename, pr=True, exportSelected=True, type='mayaAscii')
			try:
				sFilePath = pm.exportSelected(filename,type="mayaAscii",preserveReferences=True,shader=True,channels=True,constraints=True,expressions=True,constructionHistory=True,force=True)
				#print("\tanim split " + sFilePath + " generated")
			except:
				dialogError("Can't export " + filename)
				#print(\t"ERROR: export " + filename)

		cmds.select(cl=True) # clear selection.

	def generateSceneAnimA(self):
		if len(self.listAssetA) != 0:
			cmds.waitCursor(state=True)
			#filenameA = self.exportPath + "/splitAnimA.ma"
			self.generateSceneAnimABC("animSplitA_scene", self.listAssetA, self.assetListWidgetA)
			viewMessage("Split anim A generated")
			cmds.waitCursor(state=False)

	def generateSceneAnimB(self):
		if len(self.listAssetB) != 0:
			cmds.waitCursor(state=True)
			#filenameB = self.exportPath + "/splitAnimB.ma"
			self.generateSceneAnimABC("animSplitB_scene", self.listAssetB, self.assetListWidgetB)
			viewMessage("Split anim B generated")
			cmds.waitCursor(state=False)

	def generateSceneAnimC(self):
		if len(self.listAssetC) != 0:
			cmds.waitCursor(state=True)
			#filenameC = self.exportPath + "/splitAnimC.ma"
			self.generateSceneAnimABC("animSplitC_scene", self.listAssetC, self.assetListWidgetC)
			viewMessage("Split anim C generated")
			cmds.waitCursor(state=False)
		
	def generateAllSceneAnim(self):
		cmds.waitCursor(state=True)
		self.generateSceneAnimA()
		self.generateSceneAnimB()
		self.generateSceneAnimC()
		viewMessage("All split anim scenes generated")
		cmds.waitCursor(state=False)
		
	def getGpuAnimListAsset(self, listAsset):
		print("getGpuAnimListAsset")
		for asset in listAsset:
			print ("asset = " + asset)
			
	def getGpuAnimFromAllSplitAnims(self):
		if self.listAssetA:
			self.getGpuAnimListAsset(self.listAssetA)

	def mergeAllAnimatorScene(self):
		# TODO: for each list asset, get ATOM files
		pass


def dialogInfo(self, message):
	result = cmds.confirmDialog( title='Info', backgroundColor=DIALOG_INFO_COLOR, message=message, button=['Yes', 'No', 'Cancel'], defaultButton='Yes', cancelButton='No', dismissString='No' )
	return result

def dialogError(self, message):
	cmds.confirmDialog( title='Error', backgroundColor=DIALOG_ERROR_COLOR, message=message, button=['OK'], defaultButton='OK')

def dialogWarning(self, message):
	cmds.confirmDialog( title='Warning', backgroundColor=DIALOG_WARNING_COLOR, message=message, button=['OK'], defaultButton='OK')

def dialogAsk(self, message, text):
	result = cmds.promptDialog(title='Rename Object', backgroundColor=DIALOG_ASKING_COLOR, message=message, text=text, button=['OK', 'Cancel'], defaultButton='OK', cancelButton='Cancel', dismissString='Cancel')
	if result == 'OK':
		response = cmds.promptDialog(query=True, text=True)
		return response
	else:
		return ""

def viewMessage(text):
	cmds.inViewMessage( amg='<hl>' + text + '</hl>.', pos='midCenter', fade=True )


# Launch splitAnimManager
try :
    uiSplitAnim.close()
except :
    pass
uiSplitAnim = SplitAnimMgr()
uiSplitAnim.show()
