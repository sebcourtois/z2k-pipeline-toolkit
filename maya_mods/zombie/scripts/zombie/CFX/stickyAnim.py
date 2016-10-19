# StickyAnim.py

import maya.cmds as cmds
import pymel.core as pm
import maya.OpenMayaUI as omui

import shiboken
from PySide import QtCore 
from PySide import QtGui 
from shiboken import wrapInstance
import sys, os
import math

DIALOG_ERROR_COLOR = [0.8,0.2,0.2]
DIALOG_WARNING_COLOR = [0.8,0.5,0.2]
DIALOG_INFO_COLOR = [0.2,0.3,0.8]
DIALOG_ASKING_COLOR = [0.3,0.3,0.3]
DIALOG_SUCCESS_COLOR = [0.2,0.9,0.2]

GRP_STICKY="__STICKY__"
STICKY_SHADER="stickyShader"

ATTR_PARENT_CONSTRAIN = "parent_constrain"
ATTR_SCULPT_NODE = "sculpt_node"
ATTR_MAX_DISPLACEMENT = "max_displacement"
ATTR_DROPOFF_DISTANCE = "dropoff_distance"
ATTR_STICKY_CTL = "controller"

FILTER_CONTROLLERS = "*:*_ctr_*"

SLIDER_RES_MIN = -1000. # for a good resolution on the slider.
SLIDER_RES_MAX = 1000.

SCRIPT_NODE_TIME_CHANGED = "SNscriptNode"

DISPLAY_LAYER_NAME="stickyCtls"
DISPLAY_LAYER_COLOR=9 # Pink-Violet

## TODO
## if no ref selected (no ":" so no namespace)
## work directly on a selected cluster of vertex ?

## Tool Sphere Deformer ??


class StickyAnim(QtGui.QWidget):
	def __init__(self, *args, **kwargs):
		super(StickyAnim, self).__init__(*args, **kwargs)
		mayaMainWindowPtr = omui.MQtUtil.mainWindow()
		mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QtGui.QWidget)
		self.setParent(mayaMainWindow)        
		self.setWindowFlags(QtCore.Qt.Window) # Make this widget a standalone window even though it is parented 
		self.resize(300,400)

		self.palette = QtGui.QPalette()
		self.setWindowTitle("Sticky Anim")
		self.palette.setColor(QtGui.QPalette.Background, QtGui.QColor(70,70,70))
		self.setPalette(self.palette)

		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		
#		self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

		self.createLayout()

		self.fillListStickyWidget() # refresh list sticky from scene

		cmds.selectPref(useDepth=True) # Camera based Selection

		# scriptNode to update the sliders every time the current time changes
		
		if not cmds.objExists(SCRIPT_NODE_TIME_CHANGED):
			cmds.scriptNode(st=7, bs='uiStickyAnim.timeChanged()', n=SCRIPT_NODE_TIME_CHANGED, stp='python')

		if cmds.objExists(DISPLAY_LAYER_NAME):
			cmds.delete(DISPLAY_LAYER_NAME)
		cmds.createDisplayLayer(empty=1, name=DISPLAY_LAYER_NAME) # create display layer for sticky controllers
		cmds.setAttr (DISPLAY_LAYER_NAME+".color", DISPLAY_LAYER_COLOR) # set color of sticky ctls
		cmds.setAttr (DISPLAY_LAYER_NAME+".visibility", 1) # set sticky ctls visible or not


	class SliderWidget(): # class to create UI horizontal slider with label and textValue
		def __init__(self, label="", toolTipText="", min=0, max=5, defaultValue=1, callFunc=None, parentLayout=None):

			self.min = min
			self.max = max
			self.callFunc = callFunc

			self.groupSliderLayout = QtGui.QHBoxLayout()
			#self.groupSlider.setToolTip(toolTipText)
			#self.groupSlider.setLayout(groupSliderLayout)
			labelSlider = QtGui.QLabel(label)
			self.groupSliderLayout.addWidget(labelSlider)
			self.slider = QtGui.QSlider(QtCore.Qt.Horizontal) # slider only INT
			self.slider.setRange(SLIDER_RES_MIN,SLIDER_RES_MAX) # to have enough precision.
			self.slider.setValue(defaultValue)
			self.slider.valueChanged[int].connect(self.doSlider)
			self.groupSliderLayout.addWidget(self.slider)
			self.valueSlider = QtGui.QLineEdit()
			self.valueSlider.setFixedWidth(50)
			#valueSlider.setInputMask('000.00')
			self.valueSlider.setText(str(defaultValue))
			self.groupSliderLayout.addWidget(self.valueSlider)
			self.valueSlider.returnPressed.connect(self.doValueSliderChanged)
			self.doValueSliderChanged() # update slider from value
			parentLayout.addLayout(self.groupSliderLayout)

		def convertValueFromSlider(self, value): # compute real value from slider value.
			#print("value = " + str(value))
			return (value - SLIDER_RES_MIN) / (SLIDER_RES_MAX-SLIDER_RES_MIN) * (self.max - self.min) + self.min # all values are in float.
			
		def convertValueToSlider(self, value):
			return (value - self.min) / (self.max - self.min) * (SLIDER_RES_MAX-SLIDER_RES_MIN) + SLIDER_RES_MIN

		def doSlider(self, value): # when slider is moved
			#print("doSlider: value = " + str(value))
			realValue = self.convertValueFromSlider(value)
			#print("\trealValue = " + str(realValue))
			self.valueSlider.setText("%.3f" % realValue)
			self.callFunc(realValue)

		def doValueSliderChanged(self): # when value is entered
			#print("doValueSliderChanged")
			text = self.valueSlider.text()
			# update slider
			value = float(text)
			#print value
			clampValue = value
			if value < self.min:
				clampValue = self.min
			elif value > self.max:
				clampValue = self.max

			sliderValue = self.convertValueToSlider(clampValue)
			#print("\tsliderValue = " + str(sliderValue))
			self.slider.setValue(sliderValue) # set slider with clamped value
			self.callFunc(value) # but update sticky with the non-clamped value

		def updateWithValue(self, value): #update slider and sliderValue
			#print("updateWithValue: " + str(value))
			sliderValue = self.convertValueToSlider(float(value))
			#print("sliderValue = " + str(sliderValue))
			self.slider.setValue(sliderValue)
			self.valueSlider.setText("%.3f" % value)


	def createLayout(self):

		mainLayout = QtGui.QVBoxLayout()

		# TEST add buttons.
		refreshButton = self.addButtonWidget("Refresh from scene", mainLayout, self.refreshFromScene)
		refreshButton.setToolTip("Refresh the UI to stick to the scene")

		##parentWidget = QtGui.QWidget()
		##mainLayout.addWidget(parentWidget)

		self.tabWidget = QtGui.QTabWidget()
		self.tabWidget.resize(400,600)
		mainLayout.addWidget(self.tabWidget)
		##parentWidget.addWidget(self.tabWidget)

		# STICKY Tab
		self.groupSticky = QtGui.QGroupBox()
		groupStickyLayout = QtGui.QVBoxLayout()

		self.groupSticky.setLayout(groupStickyLayout)
		self.tabWidget.addTab(self.groupSticky,' Stickies ')

		self.listStickyWidget = QtGui.QListWidget()
		self.listStickyWidget.setSelectionMode(QtGui.QAbstractItemView.SingleSelection) # Allow single selection.
		self.listStickyWidget.setAlternatingRowColors(True)
		self.listStickyWidget.setStyleSheet("alternate-background-color:#333333; background-color: #222222")
		groupStickyLayout.addWidget(self.listStickyWidget)

		self.listStickyWidget.itemClicked.connect(self.stickyClicked)

		stickyButtonsLayout = QtGui.QHBoxLayout()
		self.addButtonWidget("New sticky", stickyButtonsLayout, self.doNewSticky)
		self.addButtonWidget("Remove sticky", stickyButtonsLayout, self.doDeleteCurrentSticky)
		groupStickyLayout.addLayout(stickyButtonsLayout)
  
		constrainButtonsLayout = QtGui.QHBoxLayout()
		self.addButtonWidget("Constraint CTLs", constrainButtonsLayout, self.doConstrainCtls)
		self.addButtonWidget("Show CTLs", constrainButtonsLayout, self.doShowConstrain)
		self.addButtonWidget("Remove CTLs", constrainButtonsLayout, self.doRemoveConstrain)
		groupStickyLayout.addLayout(constrainButtonsLayout)  


		# SHAPES Tab
		self.groupShapes = QtGui.QGroupBox()
		groupShapesLayout = QtGui.QVBoxLayout()

		self.groupShapes.setLayout(groupShapesLayout)
		self.tabWidget.addTab(self.groupShapes,' Shapes ')

		self.listShapesWidget = QtGui.QListWidget()
		self.listShapesWidget.setSelectionMode(QtGui.QAbstractItemView.MultiSelection) # Allow multiples selections. and toggle.
		self.listShapesWidget.setAlternatingRowColors(True)
		self.listShapesWidget.setStyleSheet("alternate-background-color:#333333; background-color: #222222")
		groupShapesLayout.addWidget(self.listShapesWidget)

		self.listShapesWidget.itemPressed.connect(self.shapeItemPressed)

		self.tabWidget.connect(self.tabWidget, QtCore.SIGNAL("currentChanged(int)"), self.tabSelected) 

		groupButtonsDisableEnableStickiesLayout = QtGui.QHBoxLayout()
		self.addButtonWidget("Disable Stickies", groupButtonsDisableEnableStickiesLayout, self.disableAllStickies)
		self.addButtonWidget("Enable Stickies", groupButtonsDisableEnableStickiesLayout, self.enableAllStickies)
		mainLayout.addLayout(groupButtonsDisableEnableStickiesLayout)
		
		## SLIDERS
		#self.sliderPushPull, self.valueSliderPushPull = self.addSliderWidget("push-pull", "push pull the deformer", -3, 3, 0, self.doPushPull, mainLayout)
		#self.sliderDropoff, self.valueSliderDropoff = self.addSliderWidget("dropoff", "zone influence deformer", 0, 10, 1, self.doDropoff, mainLayout)
		self.sliderPushPull = self.SliderWidget(label="push-pull", toolTipText="push pull the deformer", min=-3., max=3., defaultValue=0., callFunc=self.doPushPull, parentLayout=mainLayout)
		self.sliderDropoff = self.SliderWidget(label="dropoff", toolTipText="zone influence deformer", min=0., max=10., defaultValue=1., callFunc=self.doDropoff, parentLayout=mainLayout)

		# KEY button
		keyButton = self.addButtonWidget("Key", mainLayout, self.doKey)
		keyButton.setStyleSheet("background-color: red")
		#keyButton.setStyleSheet('QPushButton {background-color: #A3C1DA; color: red;}')

		self.setLayout(mainLayout)


	def addButtonWidget(self, label, parentLayout, callFunc):
		buttonWidget = QtGui.QPushButton(label)
		parentLayout.addWidget(buttonWidget)
		buttonWidget.clicked.connect(callFunc)
		return buttonWidget

	def refreshFromScene(self):
		# update GUI from group __STICKY__
		# TODO save current sticky
		self.fillListStickyWidget()
		self.fillListShapesWidget() # do we need this one ?
		# TODO set back current sticky saved

	def tabSelected(self, index): # tab cselected in UI
		#print("tabSelected")
		#print("currentIndex = " + str(index))
		if index==0:
		
			#print("Sticky")
			pass
		else:
			#print("Shapes")
			self.fillListShapesWidget()

	def timeChanged(time): # link to scriptNode. Called when current time changes.
		import maya.cmds as cmds # needs that because linked to a script node !!
		#print cmds.currentTime()
		uiStickyAnim.stickyClicked()

	def stickyClicked(self): # sticky clicked in UI
		#print("stickyClicked")
		stickyGrp = self.getCurrentStickyGrp()
		#self.selectSculptFromCurrentSticky() # select sculpt deformer
		#cmds.select(stickyGrp, replace=True) # select sticky group with all attributes to key
		cmds.select(self.getStickyController(stickyGrp), replace=True) # select controller of current sticky.
		self.sliderPushPull.updateWithValue(-(cmds.getAttr(stickyGrp+"."+ATTR_MAX_DISPLACEMENT))) # update slider Push Pull
		self.sliderDropoff.updateWithValue(cmds.getAttr(stickyGrp+"."+ATTR_DROPOFF_DISTANCE)) # update slider Drop Off

	def selectSculptFromCurrentSticky(self):
		curSticky = self.getCurrentSticky() # Get current sticky
		if curSticky:
			stickyFullName = self.getFullStickyNameFromShort(curSticky)
			if stickyFullName:
				cmds.select(self.getStickySculptNode(stickyFullName))

	def shapeItemPressed(self, item): # shape selected
		#print("shapeItemPressed item = " + item.text())
		shortStickyName = self.getCurrentSticky() # Get current sticky
		if shortStickyName:
			stickyGrp = self.getFullStickyNameFromShort(shortStickyName)
			self.stickyToggleShape(stickyGrp, item.text()) # toggle shape, link or unlink to sticky

	def fillListStickyWidget(self):
		self.listStickyWidget.blockSignals(True)
		self.listStickyWidget.clear() # empty list
		print("fillListStickyWidget")

		# Get all sticky in the group __STICKY__
		if cmds.objExists(GRP_STICKY):
			stickies = cmds.listRelatives(GRP_STICKY, children=True, type="transform")
			if stickies:
				for sticky in stickies:
					shortStickyName = sticky.split("__")[1]
					self.listStickyWidget.addItem(shortStickyName)
		else:
			print("No sticky in this scene")

		self.listStickyWidget.blockSignals(False)


	def fillListShapesWidget(self):
		self.listShapesWidget.blockSignals(True)
		self.listShapesWidget.clear() # empty list
		##print("fillListShapesWidget")

		curSticky = self.getCurrentSticky() # Get current sticky
		##print("\tcurSticky = " + str(curSticky))
		if curSticky: # if current sticky
			fullStickyName = self.getFullStickyNameFromShort(str(curSticky))
			##print("\tfullStickyName = " + str(fullStickyName))
			ns = fullStickyName.split('__')[0] # get namespace
			##grpGeos = ns +":grp_geo" # "chr_francis_default_01:grp_geo".
			##print("grpGeos = " + str(grpGeos))

			nodes = cmds.listConnections(ns+":set_meshCache"+'.dagSetMembers') # get nodes from 'set_meshCache'
			shapes = cmds.listRelatives(nodes, shapes=1) # Get all shapes from Nodes
			lastShapes = cmds.ls(shapes, ni=True) # get last shape or shapeDeformed, but not shapeOrig
			print lastShapes
			shortShapes = []
			for shape in lastShapes:
				shortShapeName = self.converLong2ShortShapeName(shape) # remove namespace and 'geo_' from shape name.
				if shortShapeName:
					shortShapes.append(shortShapeName)

			shortShapes.sort() # sort alphabetically, but uppercase come first.
			for shortShape in shortShapes:
					self.listShapesWidget.addItem(shortShape) 

			# Select shapes in list shapes linked with the current sticky.
			shapes = self.stickyGetShapesLinked(fullStickyName) # get shapes linked with current sticky.
			print shapes
			for shape in shapes:
				shortShapeName = self.converLong2ShortShapeName(shape) # remove namespace and 'geo_' from shape name.
				if shortShapeName:
					items = self.listShapesWidget.findItems(shortShapeName, QtCore.Qt.MatchExactly)
					#print("items = " + str(items))
					if items:
						items[0].setSelected(True) # select item-shape in list shapes.

		self.listShapesWidget.blockSignals(False)


	def converLong2ShortShapeName(self, longShapeName):
		#print("converLong2ShortShapeName: " + str(longShapeName))
		if ':' in longShapeName:
			return longShapeName.split(':')[1].replace("geo_", "")
		## If shape Deformed, no namespace  ':'
		else:
			return longShapeName.replace("geo_", "")

	# TODO: for shape deformed without namespace ':'
	def convertShort2LongShapeName(self, shortShapeName):
		curSticky = self.getCurrentSticky() # Get current sticky
		if curSticky:
			fullStickyName = self.getFullStickyNameFromShort(str(curSticky))
			ns = fullStickyName.split('__')[0] # get namespace
			if cmds.objExists(ns+":geo_"+shortShapeName):
				return ns+":geo_"+shortShapeName
			elif cmds.objExists("geo_"+shortShapeName):
				return "geo_"+shortShapeName
			else:
				return None
		else:
			return None

	def doNewSticky(self): # Create a new sticky.
		print("do new sticky")

		objs = cmds.ls(sl=1, fl=1) # Get selection

		# check if vertices selectionned
		vertices, shape, ns, indices = self.getVerticesPositionSelected()
		##print vertices
		##print shape
		##print ns
		##print indices
		if not vertices:
			self.dialogError("Please select vertice(s) first")
			return

		# ask name with dialog, and check if name is not already exists.
		isStickyNameGood = False
		while not isStickyNameGood:
			stickyName = self.dialogAsk("Sticky name ?", "")
			# check if sticky name is not already existing ?
			if not self.listStickyWidget.findItems(stickyName, QtCore.Qt.MatchExactly):
				isStickyNameGood = True
			else:
				self.viewMessage("This name already exist, please choice another")

		# Get midVertex, midNormal, name of shape, and his namespace from current vertex selection.
		centerVertex, centerNormal, shape, ns = self.getPositionCenterAndNormalOfVerticesSelected()

		#print centerVertex, centerNormal, shape, ns

		if not cmds.objExists(GRP_STICKY):
			cmds.group(em=True, name=GRP_STICKY) # be care, deselect the previous selection !

		# Add new sticky to list of sticky
		stickyFullName = ns+"__"+stickyName+"__sticky"
		stickyGrp = cmds.group(em=True, name=stickyFullName, parent=GRP_STICKY) # create group for new sticky.
		

		sphereRadius = 0.2
		sphereOffset = 0.5
		sphereX = centerVertex[0] + centerNormal[0] * sphereOffset + sphereRadius
		sphereY = centerVertex[1] + centerNormal[1] * sphereOffset + sphereRadius
		sphereZ = centerVertex[2] + centerNormal[2] * sphereOffset + sphereRadius

		sculptToolSphere = cmds.sphere(radius=sphereRadius, po=0, name=stickyName+"_sculptSphere") # create Nurbs sphere as sculpt tool (return: [u'nurbsSphere2', u'makeNurbSphere2'])
		cmds.setAttr(sculptToolSphere[0]+".translate",sphereX,sphereY,sphereZ, type="double3")
		#cmds.setAttr(sculptToolSphere[0]+".translate",centerVertex[0],centerVertex[1],centerVertex[2], type="double3")
		cmds.setAttr(sculptToolSphere[0]+".visibility", 0) # make sphere invisible
		cmds.parent(sculptToolSphere, stickyGrp)
		#TODO: constraint sphere orientation to centerNormal.
		
		# create controller
		stickyCtl = self.createStickyController(stickyName, stickyGrp, centerVertex, sphereRadius)
		cmds.setAttr(stickyCtl+".translate",sphereX,sphereY,sphereZ, type="double3")
		cmds.addAttr(stickyGrp, longName=ATTR_STICKY_CTL, dt='string') # save stickyCtrl in attribute on StickyGrp
		cmds.setAttr(stickyGrp+"."+ATTR_STICKY_CTL, stickyCtl, type="string") 

		# create sculpt node

		# sculpt all the vertex of the shape
		sculptNodes = cmds.sculpt(ns+":"+shape, sculptTool = str(sculptToolSphere[0]), mode='flip', objectCentered=True, groupWithLocator=True) # sculpt deformer from shape with nurbs sphere

		# sculpt only vertex selected
		##sculptNodes = cmds.sculpt(objs, sculptTool = str(sculptToolSphere[0]), mode='flip', objectCentered=True, groupWithLocator=True) # sculpt deformer from shape with nurbs sphere

		##sculptNodes = cmds.sculpt(objs, sculptTool = str(sculptToolSphere[0]), mode='flip', groupWithLocator=True) # sculpt deformer from vertices with nurbs sphere 
		##sculptNodes = cmds.sculpt(objs, mode='flip', groupWithLocator=True)
		#print("\tsculptNodes = " + str(sculptNodes)) # [u'sculpt1', u'manteau1_sculptSphere', u'sculpt1StretchOrigin']
		cmds.parent(sculptNodes[2], sculptToolSphere[0]) # parent sculpt1StretchOrigin to sculpt tool sphere.

		sculptGrp = cmds.listRelatives(sculptNodes[1], parent=1, type='transform') # get the group with the sculpt tool
		cmds.parent(sculptGrp, stickyGrp) # parent it to sticky group

		# create and group some attributes on StickyGrp
		cmds.addAttr(stickyGrp, longName=ATTR_SCULPT_NODE, dt='string') # save SculptNode in attribute on StickyGrp
		cmds.setAttr(stickyGrp+"."+ATTR_SCULPT_NODE, sculptNodes[0], type="string") 

		cmds.addAttr(stickyGrp, longName=ATTR_MAX_DISPLACEMENT, at='float', keyable=True)
		print cmds.connectAttr(stickyGrp+"."+ATTR_MAX_DISPLACEMENT, sculptNodes[0]+".maximumDisplacement", force=True)
		cmds.setAttr(stickyGrp+"."+ATTR_MAX_DISPLACEMENT, 0.0) # no displacement at start.

		cmds.addAttr(stickyGrp, longName=ATTR_DROPOFF_DISTANCE, at='float', keyable=True)
		print cmds.connectAttr(stickyGrp+"."+ATTR_DROPOFF_DISTANCE, sculptNodes[0]+".dropoffDistance", force=True)
		cmds.setAttr(stickyGrp+"."+ATTR_DROPOFF_DISTANCE, 0.8)

		cmds.setAttr(sculptNodes[0]+".envelope", 0.5) # At this time this parameter is not open for user.

		# refresh list sticky widget.
		self.fillListStickyWidget() # refresh list sticky
		self.listStickyWidget.setCurrentItem(self.listStickyWidget.findItems(stickyName, QtCore.Qt.MatchExactly)[0]) # select the sticky just added.
		#self.fillListShapesWidget() # Refresh list shapes

		self.fillListShapesWidget() # update list shapes widget because most of the shapes (but not all, thanks Maya) with a sculpt on it, create a shapeDeformed !

		self.selectSculptFromCurrentSticky() # active the sculpt of this new sticky.

	def createStickyController(self, stickyName, stickyGrp, center, scale): # sticky controller is a cube.
		# TODO constraint orientation cube to centerNormal !
		curveCtl = cmds.curve(p =[(-1., 1., -1.), (-1., 1., 1.), (1., 1., 1.), (1., 1., -1.), (-1., 1., -1.), (-1., -1., -1.), (1., -1., -1.), (1., 1., -1.), (1., 1., 1.), (1., -1., 1.), (1., -1., -1.), (-1., -1., -1.), (-1., -1., 1.), (1., -1., 1.), (1., 1., 1.), (-1., 1., 1.), (-1., -1., 1.)],per = False, d=1, k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16])
		curveCtl = cmds.rename(curveCtl, stickyName + "_CTL")
		cmds.xform(ws=True, translation=(center[0], center[1], center[2]))
		cmds.xform(ws=True, scale=(scale, scale, scale))
		cmds.parent(curveCtl, stickyGrp)
		cmds.editDisplayLayerMembers(DISPLAY_LAYER_NAME, curveCtl) # add curveCtl to display layer to have the correct color
		return curveCtl
		
	def getStickyController(self, stickyGrp): # get the controller of this sticky
		return cmds.getAttr(stickyGrp+"."+ATTR_STICKY_CTL)

	def getFullStickyNameFromShort(self, stickyName): # return sticky group name, child of __STICKY__
		#print("getFullStickyNameFromShort")
		if cmds.objExists(GRP_STICKY):
			fullStickies = cmds.listRelatives(GRP_STICKY, children=True, type="transform")
			#print("fullStickies = " + str(fullStickies))
			if fullStickies:
				for fullSticky in fullStickies:
					if stickyName in fullSticky:
						return fullSticky
			print("No sticky with name: " + stickyName + " in this scene")
		else:
			print("No '__STICKY__' in this scene")
		return None 

	# Get the sculpt node associated with this sticky
	def getStickySculptNode(self, stickyGrp): # the stickyGrp beside '__STICKY__'
		return cmds.getAttr(stickyGrp+"."+ATTR_SCULPT_NODE)

	def stickyGetStatus(self, stickyGrp): # Get status of sticky. True if enable, False if disable
		sculptNode = self.getStickySculptNode(stickyGrp) # get sculpt Node
		if sculptNode:
			state = cmds.getAttr(sculptNode+ ".nodeState")
			if state == 0:
				return True

		return False

	def stickySetStatus(self, stickyGrp, state): # Set status of sticky, True if emabled, False if disabled
		sculptNode = self.getStickySculptNode(stickyGrp) # get sculpt Node
		if state:
			cmds.setAttr(sculptNode+ ".nodeState", 0) # enable this sticky
		else:
			cmds.setAttr(sculptNode+ ".nodeState", 1) # disable this sticky
			
	def disableAllStickies(self):
		# Get all sticky in the group __STICKY__
		if cmds.objExists(GRP_STICKY):
			stickies = cmds.listRelatives(GRP_STICKY, children=True, type="transform")
			for sticky in stickies:
				self.stickySetStatus(sticky, False)
				
	def enableAllStickies(self):
		# Get all sticky in the group __STICKY__
		if cmds.objExists(GRP_STICKY):
			stickies = cmds.listRelatives(GRP_STICKY, children=True, type="transform")
			for sticky in stickies:
				self.stickySetStatus(sticky, True)

	def stickyGetShapesLinked(self, stickyGrp):
		sculptNode = self.getStickySculptNode(stickyGrp) # get the sculptId
		return cmds.sculpt(sculptNode, q=1, g=1) # get the shapes linked to this sculpt

	def stickyToggleShape(self, stickyGrp, shortShapeName):
		#print("stickyToggleShape")
		sculptNode = self.getStickySculptNode(stickyGrp) # get the sculpt deformer node
		shapesLinked = cmds.sculpt(sculptNode, q=1, g=1) # get shapes linked to sculpt deformer
		#print("\tshapesLinked = " + str(shapesLinked))
		longShapeName = self.convertShort2LongShapeName(shortShapeName)
		#print("\tlongShapeName = " + str(longShapeName))
		if shapesLinked:
			if longShapeName in shapesLinked:
				cmds.sculpt(sculptNode, edit=True, g=longShapeName, remove=True) # remove shape from sculpt deformer
				print("\tunlink: " + str(longShapeName))
				self.viewMessage("unlink: " + str(longShapeName))
			else:
				cmds.sculpt(sculptNode, edit=True, g=longShapeName) # add shape to sculpt deformer
				print("\tlink: " + str(longShapeName))
				self.viewMessage("link: " + str(longShapeName))
		else:
			cmds.sculpt(sculptNode, edit=True, g=longShapeName) # add shape to sculpt deformer
			print("\tlink: " + str(longShapeName))
			self.viewMessage("link: " + str(longShapeName))

	def getCurrentSticky(self): # return shortStickyName
		curItem = self.listStickyWidget.currentItem() # # get current selection in self.listStickyWidget
		if curItem:
			sel = curItem.text()
			#print("current sticky = " + str(sel))
			return sel
		else:
			return None

	def getCurrentStickyGrp(self):
		curSticky = self.getCurrentSticky()
		if curSticky: # if one sticky selected
			return self.getFullStickyNameFromShort(curSticky)
		else:
			return None

	def doDeleteCurrentSticky(self):
		#print("do delete current sticky")
		# get current sticky in list widget
		stickyGrp = self.getCurrentStickyGrp()
		if stickyGrp:
			#print("current stickyGrp = " + stickyGrp)
			result = self.dialogInfo("Do you want to delete the current sticky ?")
			if result == "Yes":
				cmds.delete(stickyGrp) # remove group sticky
				self.viewMessage("sticky " + str(converLong2ShortShapeName(stickyGrp)) + " deleted")
				self.fillListStickyWidget() # update tab list stickies
				self.fillListShapesWidget() # update tab list shapes
		else:
			self.viewMessage("No sticky selected to delete")

	def getSelectedItemsFromListShapesWidget(self):
		#print "Current Items are : ", self.ListShapesWidget.selectedItems()
		sel = []
		if not self.listShapesWidget.selectedItems(): return sel
		for item in self.ListShapesWidgett.selectedItems():  
			sel.append(item) # item and not item.text()

		return sel

	def removeSelectedItemFromListStickyWidget(self):
		listItems = self.getSelectedItemsFromListStickyWidget()
		if not listItems: return
		for item in listItems:
			try:
				self.listStickyWidget.remove(item.text())
			except ValueError:
				print("ERROR: Can't remove " + str(item.text()))

	def doConstrainCtls(self):
		#print("doConstrainCtls")
		listCtls = cmds.ls(FILTER_CONTROLLERS, sl=1, fl=1, typ='transform') # get selection transform and '_ctr_' (only controller)
		# if no sel, please select ctls only
		if not listCtls:
			self.dialogWarning("Please select only controller(s)")
		else:
			self.addStickyConstrain(listCtls)

	def doShowConstrain(self):
		#print("doConstrainCtls")
		listConstrain = self.getStickyConstrainsList()
		if listConstrain:
			cmds.select(listConstrain, replace=True)
		else:
			dialogWarning("No CTL constrain on this sticky")

	def doRemoveConstrain(self):
		#print("doRemoveConstrain")
		stickyGrp = self.getCurrentStickyGrp() # get current sticky grp
		#stickyName = self.getCurrentSticky()
		if not cmds.attributeQuery(ATTR_PARENT_CONSTRAIN, node=stickyGrp, exists=True): # check if attribute exists
			self.dialogWarning("No constrain on this sticky")
			return
		constrainName = self.getStickyParentConstrainName(stickyGrp) # get constrain name
		#print("\tconstrainName = " + str(constrainName))
		if not constrainName:
			dialogWarning("No CTL constrain on this sticky")
			return
		listCtrls = cmds.ls(FILTER_CONTROLLERS, sl=1, fl=1, typ='transform') # get selection. Only transform node with filter "*:*_ctr_*"
		if listCtrls: # if selection remove selected
			result = cmds.promptDialog(title='Remove constraint', backgroundColor=DIALOG_ASKING_COLOR, message="Are you sure to remove CTLs constraint selectionned ?", button=['Yes', 'No'], defaultButton='No')
			if result == 'Yes':
				cmds.parentConstraint(listCtrls, stickyGrp, e=1, rm=1) # remove constraint
		else: # if no selection: ask remove all constrains (yes,no)
			result = cmds.promptDialog(title='Remove all constraints', backgroundColor=DIALOG_ASKING_COLOR, message="Do you want to remove all CTLs constraint ?", button=['Yes', 'No'], defaultButton='No')
			if result == "Yes":
				cmds.delete(constrainName)
				setStickyParentConstrainName(stickyGrp, "")
			
	# Get the parentConstrain node associated with this sticky
	def getStickyParentConstrainName(self, stickyGrp): # stickyGrp beside '__STICKY__'
		return cmds.getAttr(stickyGrp+"."+ATTR_PARENT_CONSTRAIN)

	# Set the parentConstrain node associated with this sticky
	def setStickyParentConstrainName(self, stickyGrp, constrainName):
		cmds.setAttr(stickyGrp+"."+ATTR_PARENT_CONSTRAIN, constrainName, type="string")

	def addStickyConstrain(self, listCtrls):
		#print("addStickyConstrain: listCtrls = " + str(listCtrls))
		stickyGrp = self.getCurrentStickyGrp() # get current sticky grp
		#stickyName = self.getCurrentSticky()
		if not cmds.attributeQuery(ATTR_PARENT_CONSTRAIN, node=stickyGrp, exists=True): # check if attribute exists
			cmds.addAttr(stickyGrp, longName=ATTR_PARENT_CONSTRAIN, dt='string') # if not, create attribute
			print("\tCreate new one")
			constrainName = cmds.parentConstraint(listCtrls, stickyGrp, maintainOffset=True)[0] # create the parent constrain
			self.setStickyParentConstrainName(stickyGrp, constrainName)
		else:
			constrainName = self.getStickyParentConstrainName(stickyGrp) # get string from attribute
			print("\tconstrainName = " + str(constrainName))
			if constrainName and cmds.objExists(constrainName): # parent constrain exist ?
				# ask dialog add, replace or cancel
				result = cmds.confirmDialog(title='Add CTLs constraint', backgroundColor=DIALOG_ASKING_COLOR, message="Do you want to add to or replace the existing controllers constrain ?" , button=['Add', 'Replace', 'Cancel'], defaultButton='Add', cancelButton='Cancel', dismissString='Cancel')
				if result == 'Add':
					print("\tAdd")
					cmds.parentConstraint(listCtrls, constrainName, edit=True) # Add list controller to existing parent constrain.
				elif result == 'Replace':
					print("\tReplace")
					cmds.delete(constrainName) # delete the old parent constrain
					cmds.parentConstraint(listCtrls, n=constrainName, maintainOffset=True)  # create the new parent constrain with the list of controllers
			else: # create new one
				print("\tCreate new one")
				constrainName = cmds.parentConstraint(listCtrls, stickyGrp, maintainOffset=True)[0]
				self.setStickyParentConstrainName(stickyGrp, constrainName)


	def getStickyConstrainsList(self):
		#print("getStickyConstrainsList")
		stickyGrp = self.getCurrentStickyGrp() # get current sticky grp
		if not cmds.attributeQuery(ATTR_PARENT_CONSTRAIN, node=stickyGrp, exists=True): # check if attribute exists
			return []
		constrainName = self.getStickyParentConstrainName(stickyGrp) # get constrain name
		if constrainName:
			return cmds.parentConstraint(constrainName, q=1, targetList=1) # get list constrain
		else:
			return []
			
	def doPushPull(self, value):
		#print("doPushPull: value = " + str(value))
		stickyGrp = self.getCurrentStickyGrp()
		#print("stickyGrp = " + str(stickyGrp))
		if stickyGrp:
			cmds.setAttr(stickyGrp+"."+ATTR_MAX_DISPLACEMENT, -value)

	def doDropoff(self, value):
		#print("doDropoff: value = " + str(value))
		stickyGrp = self.getCurrentStickyGrp()
		#print("stickyGrp = " + str(stickyGrp))
		if stickyGrp:
			cmds.setAttr(stickyGrp+"."+ATTR_DROPOFF_DISTANCE, value)

	def doKey(self): # Key at current frame
		#print("doKey")
		stickyGrp = self.getCurrentStickyGrp()
		listAttr = []
		listAttr.append(stickyGrp+"."+ATTR_MAX_DISPLACEMENT)
		listAttr.append(stickyGrp+"."+ATTR_DROPOFF_DISTANCE)
		print cmds.setKeyframe(listAttr)

	def getVerticesPositionSelected(self):
		#print("getVerticesPositionSelected")
		vertices = []
		indices = []
		objs = cmds.ls(sl=1, fl=1) # return [u'chr_aurelien_manteau_01:geo_coatManteau.vtx[849]', u'chr_aurelien_manteau_01:geo_coatManteau.vtx[1111]', u'chr_aurelien_manteau_01:geo_coatManteau.vtx[1112]']
		#print objs
		if objs:
			for obj in objs:
				if ".vtx[" in obj: # is vertex ?
					#vertex = (obj, cmds.pointPosition(world=True)) # Get position, return [0.0, 0.0, -1.0000004768371582]
					vertex = cmds.xform(obj, t=True, ws=True, q=1)
					##print("vertex = " + str(vertex))
					vertices.append(vertex)
					indices.append(int((obj.split("[")[1]).split("]")[0]))
			obj = objs[0]
			#print("\tobj = " + str(obj))
			if ':' in obj:
				ns = obj.split(":")[0] # get namespace
				shape = obj.split(":")[1].split('.vtx')[0]+"Shape" # get shape
			else:
				ns = None
				shape = None
			##print "\tns = "+str(ns)
			##print "\tshape = "+str(shape)
			##print indices
			return vertices, shape, ns, indices
		else:
			return vertices, None, None, None

	def getPositionCenterAndNormalOfVerticesSelected(self):
		centerVertex = [0,0,0]
		centerNormal = [0,0,0]
		vertices, shape, ns, indices = self.getVerticesPositionSelected()
		if vertices:
			vx = 0
			vy = 0
			vz = 0
			for vertex in vertices:
				#print vertex
				vx = vx + vertex[0]
				vy = vy + vertex[1]
				vz = vz + vertex[2]
			count = len(vertices)
			#print("vertices count = " + str(count))
			centerVertex = [vx/count, vy/count, vz/count]
			#print("centerVertex = " + str(centerVertex))

			normals = cmds.polyNormalPerVertex(query=True, normalXYZ=True) # get normals of slected vertices
			#print("len(normals) = " + str(len(normals)))
			#print normals
			if normals:
				nnx = 0.
				nny = 0.
				nnz = 0.
				count = len(normals) / 3
				for i in range(count):
					nx = normals[i*3]
					ny = normals[i*3+1]
					nz = normals[i*3+2]
					#mag = math.sqrt(nx*nx+ny*ny+nz*nz) # compute magnitude.
					nnx = nnx+ nx
					nny = nny+ ny
					nnz = nnz+ nz

				mag = math.sqrt(nnx*nnx+nny*nny+nnz*nnz) # compute magnitude.
				#print("mag = " + str(mag))
				centerNormal = [nnx/mag, nny/mag, nnz/mag] # normalize normal.
				#print("centerNormal = " + str(centerNormal))

		return centerVertex, centerNormal, shape, ns

	def assignShape2StickyShader(self, shape):
		if not cmds.objExists(STICKY_SHADER):
			self.createStickyShader()

		sg = cmds.listConnections(STICKY_SHADER, d=True, et=True, t='shadingEngine') # get Shading Group
		cmds.sets(shape, e=1, forceElement=sg[0]) # attach item to SG

	def createStickyShader(self):
		if cmds.objExists(STICKY_SHADER):
			return 
		material = cmds.shadingNode("lambert", asShader=True, name=STICKY_SHADER)
		SG = cmds.sets(renderable=1, noSurfaceShader=1, empty=1, name='stickyShaderSG')
		cmds.connectAttr((material+'.outColor'),(SG+'.surfaceShader'),f=1)

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

	def viewMessage(self, text):
		cmds.inViewMessage( amg='<hl>' + text + '</hl>.', pos='midCenter', fade=True )


# Launch StickyAnim
try :
	uiStickyAnim.close()
except :
	pass
uiStickyAnim = StickyAnim()
uiStickyAnim.show()