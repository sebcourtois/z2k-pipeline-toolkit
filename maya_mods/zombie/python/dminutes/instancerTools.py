###############################################################################

# Name: 

#   instancerTools.py

#

# Description: 

#   toolbox to scatter instances on a mesh and append/extract instances 

#   to particle instancer in Maya 2015

#

#

# Author: 
#   Alexandre Bermond for zombie group studios
#

#
###############################################################################

from PySide import QtCore
from PySide import QtGui
from shiboken import wrapInstance


import maya.cmds
mc = maya.cmds
import maya.OpenMayaUI as omui


import re
import random
import traceback
import customUi as ui
import random

def maya_main_window():
    '''
    Return the Maya main window widget as a Python object
    '''
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtGui.QWidget)



class Ui_instancerTool_Dialog(QtGui.QMainWindow):
    #test_signal = QtCore.Signal()
    def __init__(self, parent=maya_main_window()):
        super(Ui_instancerTool_Dialog, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.master2Instances = ""
        self.maxParticleCount = 150
        self.perFrameEmissionRate = 50
        self.frameDuration = 100
        self.particleRadius = 0.2
        self.sclMaxVar = 1.2
        self.sclMinVar = 0.8
        self.elevMaxVar = 0
        self.elevMinVar = 0
        self.oriVar = 360
        self.incVar = 20
        self.subdivLevel = 2
        self.emisOverlapPruning = 1
      
        self.master2particles = ""
        self.particleInstancer = ""
        self.particleMaxRange = 250
        self.particleMinRange = 0

    def setupUi(self):
        self.intValidator = QtGui.QIntValidator(self)
        self.floatValidator = QtGui.QDoubleValidator(self)

        self.readOnly_palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(70, 70, 70))
        brush.setStyle(QtCore.Qt.SolidPattern)
        self.readOnly_palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Base, brush)
        self.readOnly_palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Base, brush)
        self.readOnly_palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)


####Window dialog creation
        self.setObjectName("instancerTool_Dialog")
        self.resize(380, 450)
        self.setMinimumSize(QtCore.QSize(380, 0))

        self.centralwidget = QtGui.QWidget(self)
        self.centralwidget.setObjectName("centralwidget")
        self.setCentralWidget(self.centralwidget)
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(2,2,2,2)
        self.setWindowTitle(QtGui.QApplication.translate("instancerTool_Dialog", "Instancer Tools", None, QtGui.QApplication.UnicodeUTF8))

        self.menubar = QtGui.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 18))
        self.menubar.setObjectName("menubar")
        self.menuHelp = QtGui.QMenu(self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        self.setMenuBar(self.menubar)
#        self.statusbar = QtGui.QStatusBar(self)
#        self.statusbar.setObjectName("statusbar")
#        self.setStatusBar(self.statusbar)
        self.actionHelp = QtGui.QAction(self)
        self.actionHelp.setObjectName("actionHelp")
#        self.menuHelp.addSeparator()
        self.menuHelp.addAction(self.actionHelp)
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menuHelp.setTitle(QtGui.QApplication.translate("MainWindow", "help", None, QtGui.QApplication.UnicodeUTF8))
        self.actionHelp.setText(QtGui.QApplication.translate("MainWindow", "help", None, QtGui.QApplication.UnicodeUTF8))


####Tab Widget creation 
        self.tabWidget = QtGui.QTabWidget(self)
        self.tabWidget.setAutoFillBackground(False)
        self.tabWidget.setElideMode(QtCore.Qt.ElideNone)
        self.tabWidget.setObjectName("tabWidget")

        self.tabWidgetPage1 = QtGui.QWidget()
        self.tabWidgetPage1.setObjectName("tabWidgetPage1")
        self.tabWidget.addTab(self.tabWidgetPage1, "Instance Scatterer")
        self.verticalLayout_tab1 = QtGui.QVBoxLayout(self.tabWidgetPage1)
        self.verticalLayout_tab1.setObjectName("verticalLayout_tab1")

        self.tabWidgetPage2 = QtGui.QWidget()
        self.tabWidgetPage2.setObjectName("tabWidgetPage2")
        self.verticalLayout_tab2 = QtGui.QVBoxLayout(self.tabWidgetPage2)
        self.verticalLayout_tab2.setObjectName("verticalLayout_tab2")
        self.tabWidget.addTab(self.tabWidgetPage2, "To Particle Instancer")
        
        self.verticalLayout.addWidget(self.tabWidget)
        self.tabWidget.setCurrentIndex(0)

################### tab1 : "Instance Scatter"
####Group "Master"
        self.master2Instances_groupBox = QtGui.QGroupBox(self.tabWidgetPage1)
        self.master2Instances_groupBox.setObjectName("master2Instances_groupBox")
        self.master2Instances_groupBox.setTitle(QtGui.QApplication.translate("instancerTool_Dialog", "Master", None, QtGui.QApplication.UnicodeUTF8))
        self.verticalLayout_tab1.addWidget(self.master2Instances_groupBox)
        self.master2Instances_formLayout = QtGui.QFormLayout(self.master2Instances_groupBox)
        self.master2Instances_formLayout.setObjectName("master2Instances_formLayout")
        #push button "master2Instances"
        self.master2Instances_pushButton = QtGui.QPushButton(self.master2Instances_groupBox)
        self.master2Instances_pushButton.setObjectName("master2Instances_pushButton")
        self.master2Instances_pushButton.setText(QtGui.QApplication.translate("instancerTool_Dialog", "Select", None, QtGui.QApplication.UnicodeUTF8))
        self.master2Instances_formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.master2Instances_pushButton)
        #lineEdit "master2Instances"
        self.master2Instances_lineEdit = QtGui.QLineEdit(self.master2Instances_groupBox)
        self.master2Instances_lineEdit.setReadOnly(True)
        self.master2Instances_lineEdit.setObjectName("master2Instances_lineEdit")
        self.master2Instances_lineEdit.setPalette(self.readOnly_palette)
        self.master2Instances_formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.master2Instances_lineEdit)

####Group "Simulation parameters"
        self.simulationParam_groupBox = QtGui.QGroupBox(self.tabWidgetPage1)
        self.simulationParam_groupBox.setObjectName("simulationParam_groupBox")
        self.simulationParam_groupBox.setTitle(QtGui.QApplication.translate("instancerTool_Dialog", "Simulation Parameters", None, QtGui.QApplication.UnicodeUTF8))
        self.verticalLayout_tab1.addWidget(self.simulationParam_groupBox)
        self.simulationParam_gridLayout = QtGui.QGridLayout(self.simulationParam_groupBox)
        self.simulationParam_gridLayout.setObjectName("simulationParam_gridLayout")
        ## label "frame emission rate"
        self.perFrameEmissionRate_label = QtGui.QLabel(self.simulationParam_groupBox)
        self.perFrameEmissionRate_label.setObjectName("perFrameEmissionRate_label")
        self.perFrameEmissionRate_label.setText(QtGui.QApplication.translate("instancerTool_Dialog", "Per Frame Emission Rate", None, QtGui.QApplication.UnicodeUTF8))
        self.simulationParam_gridLayout.addWidget(self.perFrameEmissionRate_label, 1, 0, 1, 1)
        ## label "max particle count"
        self.maxParticleCount_label = QtGui.QLabel(self.simulationParam_groupBox)
        self.maxParticleCount_label.setObjectName("maxParticleCount_label")
        self.maxParticleCount_label.setText(QtGui.QApplication.translate("instancerTool_Dialog", "Max Particle Count", None, QtGui.QApplication.UnicodeUTF8))
        self.simulationParam_gridLayout.addWidget(self.maxParticleCount_label, 0, 0, 1, 1)
        ## label "particle radius"
        self.particleRadius_label = QtGui.QLabel(self.simulationParam_groupBox)
        self.particleRadius_label.setObjectName("particleRadius_label")
        self.particleRadius_label.setText(QtGui.QApplication.translate("instancerTool_Dialog", "Particle Radius", None, QtGui.QApplication.UnicodeUTF8))
        self.simulationParam_gridLayout.addWidget(self.particleRadius_label, 2, 2, 1, 1)
        ## label "frame duration"
        self.frameDuration_label = QtGui.QLabel(self.simulationParam_groupBox)
        self.frameDuration_label.setObjectName("frameDuration_label")
        self.frameDuration_label.setText(QtGui.QApplication.translate("instancerTool_Dialog", "Frame Duration", None, QtGui.QApplication.UnicodeUTF8))
        self.simulationParam_gridLayout.addWidget(self.frameDuration_label, 1, 2, 1, 1)
        ## label "emission Overlap Pruning"
        self.emisOverlapPruning_label = QtGui.QLabel(self.simulationParam_groupBox)
        self.emisOverlapPruning_label.setObjectName("emisOverlapPruning_label")
        self.emisOverlapPruning_label.setText(QtGui.QApplication.translate("instancerTool_Dialog", "Emission Overlap Pruning", None, QtGui.QApplication.UnicodeUTF8))
        self.simulationParam_gridLayout.addWidget(self.emisOverlapPruning_label, 2, 0, 1, 1)
        #lineEdit "maxParticleCount"
        self.maxParticleCount_lineEdit = QtGui.QLineEdit(self.simulationParam_groupBox)
        self.maxParticleCount_lineEdit.setObjectName("maxParticleCount_lineEdit")
        self.maxParticleCount_lineEdit.setValidator(self.intValidator)
        self.maxParticleCount_lineEdit.setText(QtGui.QApplication.translate("instancerTool_Dialog", str(self.maxParticleCount), None, QtGui.QApplication.UnicodeUTF8))
        self.simulationParam_gridLayout.addWidget(self.maxParticleCount_lineEdit, 0, 1, 1, 1)
        #lineEdit "frame emission rate"
        self.perFrameEmissionRate_lineEdit = QtGui.QLineEdit(self.simulationParam_groupBox)
        self.perFrameEmissionRate_lineEdit.setObjectName("perFrameEmissionRate_lineEdit")
        self.perFrameEmissionRate_lineEdit.setValidator(self.intValidator)
        self.perFrameEmissionRate_lineEdit.setText(QtGui.QApplication.translate("instancerTool_Dialog", str(self.perFrameEmissionRate), None, QtGui.QApplication.UnicodeUTF8))
        self.simulationParam_gridLayout.addWidget(self.perFrameEmissionRate_lineEdit, 1, 1, 1, 1)
        #lineEdit "particle radius"
        self.particleRadius_lineEdit = QtGui.QLineEdit(self.simulationParam_groupBox)
        self.particleRadius_lineEdit.setObjectName("particleRadius_lineEdit")
        self.particleRadius_lineEdit.setValidator(self.floatValidator)
        self.particleRadius_lineEdit.setText(QtGui.QApplication.translate("instancerTool_Dialog", "0.2", None, QtGui.QApplication.UnicodeUTF8))
        self.simulationParam_gridLayout.addWidget(self.particleRadius_lineEdit, 2, 3, 1, 1)
        #lineEdit "frame duration"
        self.frameDuration_lineEdit = QtGui.QLineEdit(self.simulationParam_groupBox)
        self.frameDuration_lineEdit.setObjectName("frameDuration_lineEdit")
        self.frameDuration_lineEdit.setValidator(QtGui.QIntValidator(self))
        self.frameDuration_lineEdit.setText(QtGui.QApplication.translate("instancerTool_Dialog", str(self.frameDuration), None, QtGui.QApplication.UnicodeUTF8))
        self.simulationParam_gridLayout.addWidget(self.frameDuration_lineEdit, 1, 3, 1, 1)
        #lineEdit "emission Overlap Pruning"
        self.emisOverlapPruning_lineEdit = QtGui.QLineEdit(self.simulationParam_groupBox)
        self.emisOverlapPruning_lineEdit.setObjectName("emisOverlapPruning_lineEdit")
        self.emisOverlapPruning_lineEdit.setValidator(QtGui.QDoubleValidator(self))
        self.emisOverlapPruning_lineEdit.setText(QtGui.QApplication.translate("instancerTool_Dialog", str(self.emisOverlapPruning), None, QtGui.QApplication.UnicodeUTF8))
        self.simulationParam_gridLayout.addWidget(self.emisOverlapPruning_lineEdit, 2, 1, 1, 1)


####Group box "Scattering Variances"
        self.scatteringVariances_groupBox = QtGui.QGroupBox(self.tabWidgetPage1)
        self.scatteringVariances_groupBox.setObjectName("scatteringVariances_groupBox")
        self.scatteringVariances_groupBox.setTitle(QtGui.QApplication.translate("instancerTool_Dialog", "Scattering Variances", None, QtGui.QApplication.UnicodeUTF8))
        self.verticalLayout_tab1.addWidget(self.scatteringVariances_groupBox)
        self.scatteringVariances_verticalLayout = QtGui.QVBoxLayout(self.scatteringVariances_groupBox)
        self.scatteringVariances_verticalLayout.setObjectName("scatteringVariances_verticalLayout")
        ## grid layout "Scale and Elevation"
        self.scaleElevation_simulationParam_gridLayout = QtGui.QGridLayout()
        self.scaleElevation_simulationParam_gridLayout.setContentsMargins(0, 0, 0, -1)
        self.scaleElevation_simulationParam_gridLayout.setObjectName("scaleElevation_simulationParam_gridLayout")
        self.scatteringVariances_verticalLayout.addLayout(self.scaleElevation_simulationParam_gridLayout)
        ##label "minimum"
        self.minimum_label = QtGui.QLabel(self.scatteringVariances_groupBox)
        self.minimum_label.setTextFormat(QtCore.Qt.AutoText)
        self.minimum_label.setAlignment(QtCore.Qt.AlignCenter)
        self.minimum_label.setWordWrap(False)
        self.minimum_label.setObjectName("minimum_label")
        self.minimum_label.setText(QtGui.QApplication.translate("instancerTool_Dialog", "Minimum ", None, QtGui.QApplication.UnicodeUTF8))
        self.scaleElevation_simulationParam_gridLayout.addWidget(self.minimum_label, 0, 1, 1, 1)
        ##label "maximum"
        self.maximum_label = QtGui.QLabel(self.scatteringVariances_groupBox)
        self.maximum_label.setTextFormat(QtCore.Qt.AutoText)
        self.maximum_label.setAlignment(QtCore.Qt.AlignCenter)
        self.maximum_label.setObjectName("maximum_label")
        self.maximum_label.setText(QtGui.QApplication.translate("instancerTool_Dialog", "Maximum", None, QtGui.QApplication.UnicodeUTF8))
        self.scaleElevation_simulationParam_gridLayout.addWidget(self.maximum_label, 0, 2, 1, 1)
        ##label "Scale"
        self.scale_label = QtGui.QLabel(self.scatteringVariances_groupBox)
        self.scale_label.setObjectName("scale_label")
        self.scale_label.setText(QtGui.QApplication.translate("instancerTool_Dialog", "Scale", None, QtGui.QApplication.UnicodeUTF8))
        self.scaleElevation_simulationParam_gridLayout.addWidget(self.scale_label, 1, 0, 1, 1)
        ##label "elevation"
        self.elevation_label = QtGui.QLabel(self.scatteringVariances_groupBox)
        self.elevation_label.setObjectName("elevation_label")
        self.elevation_label.setText(QtGui.QApplication.translate("instancerTool_Dialog", "Elevation", None, QtGui.QApplication.UnicodeUTF8))
        self.scaleElevation_simulationParam_gridLayout.addWidget(self.elevation_label, 2, 0, 1, 1)
        #lineEdit "elevMaxVar"
        self.elevMaxVar_lineEdit = QtGui.QLineEdit(self.scatteringVariances_groupBox)
        self.elevMaxVar_lineEdit.setObjectName("elevMaxVar_lineEdit")
        self.elevMaxVar_lineEdit.setValidator(self.floatValidator)
        self.elevMaxVar_lineEdit.setText(QtGui.QApplication.translate("instancerTool_Dialog", "0", None, QtGui.QApplication.UnicodeUTF8))
        self.scaleElevation_simulationParam_gridLayout.addWidget(self.elevMaxVar_lineEdit, 2, 2, 1, 1)
        #lineEdit "sclMaxVar"
        self.sclMaxVar_lineEdit = QtGui.QLineEdit(self.scatteringVariances_groupBox)
        self.sclMaxVar_lineEdit.setObjectName("sclMaxVar_lineEdit")
        self.sclMaxVar_lineEdit.setValidator(self.floatValidator)
        self.sclMaxVar_lineEdit.setText(QtGui.QApplication.translate("instancerTool_Dialog", "1.2", None, QtGui.QApplication.UnicodeUTF8))
        self.scaleElevation_simulationParam_gridLayout.addWidget(self.sclMaxVar_lineEdit, 1, 2, 1, 1)
        #lineEdit "elevMinVar"
        self.elevMinVar_lineEdit = QtGui.QLineEdit(self.scatteringVariances_groupBox)
        self.elevMinVar_lineEdit.setObjectName("elevMinVar_lineEdit")
        self.elevMinVar_lineEdit.setValidator(self.floatValidator)
        self.elevMinVar_lineEdit.setText(QtGui.QApplication.translate("instancerTool_Dialog", "0", None, QtGui.QApplication.UnicodeUTF8))
        self.scaleElevation_simulationParam_gridLayout.addWidget(self.elevMinVar_lineEdit, 2, 1, 1, 1)
        #lineEdit "sclMinVar"
        self.sclMinVar_lineEdit = QtGui.QLineEdit(self.scatteringVariances_groupBox)
        self.sclMinVar_lineEdit.setObjectName("sclMinVar_lineEdit")
        self.sclMinVar_lineEdit.setValidator(self.floatValidator)
        self.sclMinVar_lineEdit.setText(QtGui.QApplication.translate("instancerTool_Dialog", "0.8", None, QtGui.QApplication.UnicodeUTF8))
        self.scaleElevation_simulationParam_gridLayout.addWidget(self.sclMinVar_lineEdit, 1, 1, 1, 1)
        ##Frame " break line"
        self.scattering_variance_line = QtGui.QFrame(self.scatteringVariances_groupBox)
        self.scattering_variance_line.setFrameShape(QtGui.QFrame.HLine)
        self.scattering_variance_line.setFrameShadow(QtGui.QFrame.Sunken)
        self.scattering_variance_line.setObjectName("scattering_variance_line")
        self.scatteringVariances_verticalLayout.addWidget(self.scattering_variance_line)
        ## grid layout "Orientation Inclinason"
        self.OrientationInclination_simulationParam_gridLayout = QtGui.QGridLayout()
        self.OrientationInclination_simulationParam_gridLayout.setObjectName("OrientationInclination_simulationParam_gridLayout")
        self.scatteringVariances_verticalLayout.addLayout(self.OrientationInclination_simulationParam_gridLayout)
        ##label "orientation"
        self.oriVar_label = QtGui.QLabel(self.scatteringVariances_groupBox)
        self.oriVar_label.setAlignment(QtCore.Qt.AlignCenter)
        self.oriVar_label.setObjectName("oriVar_label")
        self.oriVar_label.setText(QtGui.QApplication.translate("instancerTool_Dialog", "Orientation", None, QtGui.QApplication.UnicodeUTF8))
        self.OrientationInclination_simulationParam_gridLayout.addWidget(self.oriVar_label, 0, 0, 1, 1)
        ##label "inclination"
        self.incVar_label = QtGui.QLabel(self.scatteringVariances_groupBox)
        self.incVar_label.setAlignment(QtCore.Qt.AlignCenter)
        self.incVar_label.setObjectName("incVar_label")
        self.incVar_label.setText(QtGui.QApplication.translate("instancerTool_Dialog", "Inclination", None, QtGui.QApplication.UnicodeUTF8))
        self.OrientationInclination_simulationParam_gridLayout.addWidget(self.incVar_label, 0, 3, 1, 1)
        #line Edit "orientation"
        self.oriVar_lineEdit = QtGui.QLineEdit(self.scatteringVariances_groupBox)
        self.oriVar_lineEdit.setObjectName("oriVar_lineEdit")
        self.oriVar_lineEdit.setValidator(self.floatValidator)
        self.oriVar_lineEdit.setText(QtGui.QApplication.translate("instancerTool_Dialog", "360", None, QtGui.QApplication.UnicodeUTF8))
        self.OrientationInclination_simulationParam_gridLayout.addWidget(self.oriVar_lineEdit, 0, 2, 1, 1)
        #line Edit "inclination"
        self.incVar_lineEdit = QtGui.QLineEdit(self.scatteringVariances_groupBox)
        self.incVar_lineEdit.setObjectName("incVar_lineEdit")
        self.incVar_lineEdit.setValidator(self.floatValidator)
        self.incVar_lineEdit.setText(QtGui.QApplication.translate("instancerTool_Dialog", "20", None, QtGui.QApplication.UnicodeUTF8))
        self.OrientationInclination_simulationParam_gridLayout.addWidget(self.incVar_lineEdit, 0, 4, 1, 1)

####Group "Instantiate on Selected Mesh"
        self.instanciateOnMesh_groupBox = QtGui.QGroupBox(self.tabWidgetPage1)
        self.instanciateOnMesh_groupBox.setObjectName("instanciateOnMesh_groupBox")
        self.instanciateOnMesh_groupBox.setTitle(QtGui.QApplication.translate("instancerTool_Dialog", "Instantiate On Selected Mesh", None, QtGui.QApplication.UnicodeUTF8))
        self.verticalLayout_tab1.addWidget(self.instanciateOnMesh_groupBox)
        self.instanciateOnMesh_verticalLayout = QtGui.QVBoxLayout(self.instanciateOnMesh_groupBox)
        self.instanciateOnMesh_verticalLayout.setObjectName("instanciateOnMesh_verticalLayout")
        ## layout "subdivLevel_horizontalLayout"
        self.subdivLevel_horizontalLayout = QtGui.QHBoxLayout()
        self.subdivLevel_horizontalLayout.setObjectName("subdivLevel_horizontalLayout")
        self.instanciateOnMesh_verticalLayout.addLayout(self.subdivLevel_horizontalLayout)
        #spin box "subdivLevel_spinBox"
        self.subdivLevel_spinBox = QtGui.QSpinBox(self.instanciateOnMesh_groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.subdivLevel_spinBox.sizePolicy().hasHeightForWidth())
        self.subdivLevel_spinBox.setSizePolicy(sizePolicy)
        self.subdivLevel_spinBox.setMinimum(0)
        self.subdivLevel_spinBox.setMaximum(5)
        self.subdivLevel_spinBox.setProperty("value", 2)
        self.subdivLevel_spinBox.setObjectName("subdivLevel_spinBox")
        self.subdivLevel_horizontalLayout.addWidget(self.subdivLevel_spinBox)
        ## label "subdivLevel_label"
        self.subdivLevel_label = QtGui.QLabel(self.instanciateOnMesh_groupBox)
        self.subdivLevel_label.setTextFormat(QtCore.Qt.AutoText)
        self.subdivLevel_label.setObjectName("subdivLevel_label")
        self.subdivLevel_label.setText(QtGui.QApplication.translate("instancerTool_Dialog", "Emitter Subdivision  Level", None, QtGui.QApplication.UnicodeUTF8))
        self.subdivLevel_horizontalLayout.addWidget(self.subdivLevel_label)
        ## layout "instanciateButton_horizontalLayout"
        self.instanciateButton_horizontalLayout = QtGui.QHBoxLayout()
        self.instanciateButton_horizontalLayout.setObjectName("instanciateButton_horizontalLayout")
        self.instanciateOnMesh_verticalLayout.addLayout(self.instanciateButton_horizontalLayout)
        #push button  "instanciate"
        self.instanciate_pushButton = QtGui.QPushButton(self.instanciateOnMesh_groupBox)
        self.instanciate_pushButton.setObjectName("instanciate_pushButton")
        self.instanciate_pushButton.setText(QtGui.QApplication.translate("instancerTool_Dialog", "Transform Instance", None, QtGui.QApplication.UnicodeUTF8))
        self.instanciateButton_horizontalLayout.addWidget(self.instanciate_pushButton)
        #push button  "particle instanciate"
        self.parInstanciate_pushButton = QtGui.QPushButton(self.instanciateOnMesh_groupBox)
        self.parInstanciate_pushButton.setObjectName("parInstanciate_pushButton")
        self.parInstanciate_pushButton.setText(QtGui.QApplication.translate("instancerTool_Dialog", "Particle Instancer", None, QtGui.QApplication.UnicodeUTF8))
        self.instanciateButton_horizontalLayout.addWidget(self.parInstanciate_pushButton)

################### tab2 : "To Particle Instancer"
####Group "Create Particle Instancer"
        self.master2particles_groupBox = QtGui.QGroupBox(self.tabWidgetPage2)
        self.master2particles_groupBox.setObjectName("master2particles_groupBox")
        self.master2particles_groupBox.setTitle(QtGui.QApplication.translate("instancerTool_Dialog", "Create Particle Instancer", None, QtGui.QApplication.UnicodeUTF8))
        self.verticalLayout_tab2.addWidget(self.master2particles_groupBox)
        self.master2particles_verticalLayout = QtGui.QVBoxLayout(self.master2particles_groupBox)
        self.master2particles_verticalLayout.setObjectName("master2particles_verticalLayout")
        ## horizontal layout "create Particle Instancer"
        self.createParticleInstancer_horizontalLayout = QtGui.QHBoxLayout()
        self.createParticleInstancer_horizontalLayout.setObjectName("createParticleInstancer_horizontalLayout")
        self.master2particles_verticalLayout.addLayout(self.createParticleInstancer_horizontalLayout)
        #push button  "master to particles"
        self.master2particles_pushButton = QtGui.QPushButton(self.master2particles_groupBox)
        self.master2particles_pushButton.setObjectName("master2particles_pushButton")
        self.master2particles_pushButton.setText(QtGui.QApplication.translate("instancerTool_Dialog", "Master", None, QtGui.QApplication.UnicodeUTF8))
        self.createParticleInstancer_horizontalLayout.addWidget(self.master2particles_pushButton)
        #line Edit "master to particle"
        self.master2particles_lineEdit = QtGui.QLineEdit(self.master2particles_groupBox)
        self.master2particles_lineEdit.setReadOnly(True)
        self.master2particles_lineEdit.setObjectName("master2particles_lineEdit")
        self.master2particles_lineEdit.setPalette(self.readOnly_palette)
        self.createParticleInstancer_horizontalLayout.addWidget(self.master2particles_lineEdit)
        #push button  "create new"
        self.createNew_pushButton = QtGui.QPushButton(self.master2particles_groupBox)
        self.createNew_pushButton.setObjectName("createNew_pushButton")
        self.createNew_pushButton.setText(QtGui.QApplication.translate("instancerTool_Dialog", "Create New", None, QtGui.QApplication.UnicodeUTF8))
        self.master2particles_verticalLayout.addWidget(self.createNew_pushButton)

####Group "Append to  Particle "
        self.append2PartInstancer_groupBox = QtGui.QGroupBox(self.tabWidgetPage2)
        self.append2PartInstancer_groupBox.setObjectName("append2PartInstancer_groupBox")
        self.append2PartInstancer_groupBox.setTitle(QtGui.QApplication.translate("instancerTool_Dialog", "Append To Particle ", None, QtGui.QApplication.UnicodeUTF8))
        self.verticalLayout_tab2.addWidget(self.append2PartInstancer_groupBox)
        self.append2PartInstancer_verticalLayout = QtGui.QVBoxLayout(self.append2PartInstancer_groupBox)
        self.append2PartInstancer_verticalLayout.setObjectName("append2PartInstancer_verticalLayout")
        ## horizontal layout "select Particle Instancer"
        self.selectParticleInstancer_horizontalLayout = QtGui.QHBoxLayout()
        self.selectParticleInstancer_horizontalLayout.setObjectName("selectParticleInstancer_horizontalLayout")
        self.append2PartInstancer_verticalLayout.addLayout(self.selectParticleInstancer_horizontalLayout)
        #push button  "particle instancer"
        self.selectParticleInstancer_pushButton = QtGui.QPushButton(self.append2PartInstancer_groupBox)
        self.selectParticleInstancer_pushButton.setObjectName("selectParticleInstancer_pushButton")
        self.selectParticleInstancer_pushButton.setText(QtGui.QApplication.translate("instancerTool_Dialog", "Particle", None, QtGui.QApplication.UnicodeUTF8))
        self.selectParticleInstancer_horizontalLayout.addWidget(self.selectParticleInstancer_pushButton)
        #line Edit "particle instancer"
        self.selectedParticleInstancer_lineEdit = QtGui.QLineEdit(self.append2PartInstancer_groupBox)
        self.selectedParticleInstancer_lineEdit.setReadOnly(True)
        self.selectedParticleInstancer_lineEdit.setObjectName("selectedParticleInstancer_lineEdit")
        self.selectedParticleInstancer_lineEdit.setPalette(self.readOnly_palette)
        self.selectParticleInstancer_horizontalLayout.addWidget(self.selectedParticleInstancer_lineEdit)
        #push button  "append to"
        self.appendTo_pushButton = QtGui.QPushButton(self.append2PartInstancer_groupBox)
        self.appendTo_pushButton.setObjectName("appendTo_pushButton")
        self.appendTo_pushButton.setText(QtGui.QApplication.translate("instancerTool_Dialog", "Append Selected Instances To Particle", None, QtGui.QApplication.UnicodeUTF8))
        self.append2PartInstancer_verticalLayout.addWidget(self.appendTo_pushButton)


        
        #push button  "Extract"
        self.extractFrom_pushButton = QtGui.QPushButton(self.append2PartInstancer_groupBox)
        self.extractFrom_pushButton.setObjectName("extractFrom_pushButton")
        self.extractFrom_pushButton.setText(QtGui.QApplication.translate("instancerTool_Dialog", "Extract Selected Particles To Instances", None, QtGui.QApplication.UnicodeUTF8))
        self.verticalLayout_tab2.addWidget(self.extractFrom_pushButton)
        
        
        ## vertical spacer
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_tab2.addItem(spacerItem)

        self.create_connections()
        #QtCore.QMetaObject.connectSlotsByName(self)



    def create_connections(self):
        '''
        Create the signal/slot connections
        '''
        #---tab 1
        self.master2Instances_pushButton.clicked.connect(self.on_master2Instances_pushButton_pressed)
        
        self.maxParticleCount_lineEdit.editingFinished.connect(self.on_maxParticleCount_lineEdit_changed)
        self.perFrameEmissionRate_lineEdit.editingFinished.connect(self.on_perFrameEmissionRate_lineEdit_changed)
        self.frameDuration_lineEdit.editingFinished.connect(self.on_frameDuration_lineEdit_changed)
        self.particleRadius_lineEdit.editingFinished.connect(self.on_particleRadius_lineEdit_changed)
        self.emisOverlapPruning_lineEdit.editingFinished.connect(self.on_emisOverlapPruning_lineEdit_changed)
        
        self.sclMaxVar_lineEdit.editingFinished.connect(self.on_sclMaxVar_lineEdit_changed)
        self.sclMinVar_lineEdit.editingFinished.connect(self.on_sclMinVar_lineEdit_changed)
        self.elevMaxVar_lineEdit.editingFinished.connect(self.on_elevMaxVar_lineEdit_changed)
        self.elevMinVar_lineEdit.editingFinished.connect(self.on_elevMinVar_lineEdit_changed)
        self.oriVar_lineEdit.editingFinished.connect(self.on_oriVar_lineEdit_changed)
        self.incVar_lineEdit.editingFinished.connect(self.on_incVar_lineEdit_changed)
        
        self.subdivLevel_spinBox.valueChanged.connect(self.on_subdivLevel_spinBox_changed)
        self.instanciate_pushButton.clicked.connect(self.on_instantiate_pushButton_pressed)
        self.parInstanciate_pushButton.clicked.connect(self.on_parInstantiate_pushButton_pressed)
        
        #--- tab2
        self.master2particles_pushButton.clicked.connect(self.on_master2particles_pushButton_pressed)
        self.createNew_pushButton.clicked.connect(self.on_createNew_pushButton_pressed)
        
        self.selectParticleInstancer_pushButton.clicked.connect(self.on_selectParticleInstancer_pushButton_pressed)
        self.appendTo_pushButton.clicked.connect(self.on_appendTo_pushButton_pressed)
        
        self.extractFrom_pushButton.clicked.connect(self.on_extractFrom_pushButton_pressed)
        
        self.actionHelp.triggered.connect(self.on_actionHelp_triggered)
        

###############################################
#### SLOTS
################################################
    def on_actionHelp_triggered(self):
        import subprocess
        import os
        cwd = os.path.dirname(__file__)
        docFileName = "file:///"+cwd+"/instancerTools_help.html"
        print docFileName
        sCmd = "explorer {0}".format(docFileName)
        subprocess.Popen( sCmd, shell = True )

#------------------------    Tab1 : "Instance Scatter"
#---Group "Master"
    def on_master2Instances_pushButton_pressed(self):
        try :
            self.master2Instances= mc.ls(sl = True, l = True)[0]
        except IndexError:
            print "#### info: nothing selected"
            self.master2Instances = ""
        self.master2Instances_lineEdit.setText(QtGui.QApplication.translate("instancerTool_Dialog", str(self.master2Instances) , None, QtGui.QApplication.UnicodeUTF8))

#---Group "Simulation Parameters"
    def on_maxParticleCount_lineEdit_changed(self):
        previousValue = self.maxParticleCount
        self.maxParticleCount = self.maxParticleCount_lineEdit.text()
        try:
            self.maxParticleCount = int(self.maxParticleCount)
            if self.maxParticleCount <= 0 or self.maxParticleCount > 500000:
                raise ValueError
        except ValueError:
            print "#### error: input must be : 0 < integer <= 2500"
            self.maxParticleCount_lineEdit.setText(str(previousValue))

    def on_perFrameEmissionRate_lineEdit_changed(self):
        previousValue = self.perFrameEmissionRate
        self.perFrameEmissionRate = self.perFrameEmissionRate_lineEdit.text()
        try:
            self.perFrameEmissionRate = int(self.perFrameEmissionRate)
            if self.perFrameEmissionRate <= 0:
                raise ValueError
        except ValueError:
            print "#### error: input must be an integer >0 "
            self.perFrameEmissionRate_lineEdit.setText(str(previousValue))

    def on_frameDuration_lineEdit_changed(self):
        previousValue = self.frameDuration
        self.frameDuration = self.frameDuration_lineEdit.text()
        try:
            self.frameDuration = int(self.frameDuration)
            if self.frameDuration <= 0:
                raise ValueError
        except ValueError:
            print "#### error: input must be an integer >0 "
            self.frameDuration_lineEdit.setText(str(previousValue))

    def on_particleRadius_lineEdit_changed(self):
        previousValue = self.particleRadius
        self.particleRadius = self.particleRadius_lineEdit.text()
        try:
            self.particleRadius = float(self.particleRadius)
            if self.particleRadius <= 0:
                raise ValueError
        except ValueError:
            print "#### error: input must be a float >0 "
            self.particleRadius_lineEdit.setText(str(previousValue))

    def on_emisOverlapPruning_lineEdit_changed(self):
        previousValue = self.emisOverlapPruning
        self.emisOverlapPruning = self.emisOverlapPruning_lineEdit.text()
        try:
            self.emisOverlapPruning = float(self.emisOverlapPruning)
            if self.emisOverlapPruning < 0 or self.emisOverlapPruning > 1:
                raise ValueError
        except ValueError:
            print "#### error: input must be a   0 <= float <= 1 "
            self.emisOverlapPruning_lineEdit.setText(str(previousValue))

    def on_sclMaxVar_lineEdit_changed(self):
        previousValue = self.sclMaxVar
        self.sclMaxVar = self.sclMaxVar_lineEdit.text()
        try:
            self.sclMaxVar = float(self.sclMaxVar)
        except ValueError:
            print "#### error: float type expected"
            self.sclMaxVar_lineEdit.setText(str(previousValue))

    def on_sclMinVar_lineEdit_changed(self):
        previousValue = self.sclMinVar
        self.sclMinVar = self.sclMinVar_lineEdit.text()
        try:
            self.sclMinVar = float(self.sclMinVar)
        except ValueError:
            print "#### error: float type expected"
            self.sclMinVar_lineEdit.setText(str(previousValue))

    def on_elevMaxVar_lineEdit_changed(self):
        previousValue = self.elevMaxVar
        self.elevMaxVar = self.elevMaxVar_lineEdit.text()
        try:
            self.elevMaxVar = float(self.elevMaxVar)
        except ValueError:
            print "#### error: float type expected"
            self.elevMaxVar_lineEdit.setText(str(previousValue))

    def on_elevMinVar_lineEdit_changed(self):
        previousValue = self.elevMinVar
        self.elevMinVar = self.elevMinVar_lineEdit.text()
        try:
            self.elevMinVar = float(self.elevMinVar)
        except ValueError:
            print "#### error: float type expected"
            self.elevMinVar_lineEdit.setText(str(previousValue))

    def on_oriVar_lineEdit_changed(self):
        previousValue = self.oriVar
        self.oriVar = self.oriVar_lineEdit.text()
        try:
            self.oriVar = float(self.oriVar)
        except ValueError:
            print "#### error: float type expected"
            self.oriVar_lineEdit.setText(str(previousValue))

    def on_incVar_lineEdit_changed(self):
        previousValue = self.incVar
        self.incVar = self.incVar_lineEdit.text()
        try:
            self.incVar = float(self.incVar)
        except ValueError:
            print "#### error: float type expected"
            self.incVar_lineEdit.setText(str(previousValue))

#----Group "Instantiate On Selected Mesh"
    def on_subdivLevel_spinBox_changed(self):
        self.subdivLevel = int(self.subdivLevel_spinBox.text())

    def on_instantiate_pushButton_pressed(self):
        if self.maxParticleCount > 2400:
            msg = "#### Error: You cannot create more than 2400 instances at the same time, please set max particle count to a descent value to avoid freezing your computer"
            raise ValueError (msg)
        else:
            self.instanceEmitter(TransformInstanceType = True)
 
    def on_parInstantiate_pushButton_pressed(self):
        self.instanceEmitter(TransformInstanceType = False)

    def instanceEmitter(self, TransformInstanceType = False):
        '''
        This method uses a temp nParticle node to emit particles from the specified mesh object. The the given master is instantiated along every particle. 
        Some random values modulate the instances SRT according to the variance values.
        '''
        print ""
        print "##########    running: instantiate    ##########"
        if not self.master2Instances:
            print "#### error: no master selected"
            return
        selection = mc.ls(sl = True)
        savedSelection = list(selection)
        #################
        #### prepare "tempEmitterMesh" from the selection
        #################
        if selection:
            #If a transform has been selected but no components, duplicate the shape and smooth 
            if mc.objectType(selection[0])=="transform" and not re.search("\..{1,10}\[",selection[0]):
                if len(selection)>1:
                    print "#### warning: several objects selected, processing with the first selected obj: "+selection[0]
                descendent = mc.listRelatives (selection[0], noIntermediate = True, shapes = True, allDescendents = True)
                if len(descendent)==1 :
                    tempEmitterMesh = mc.duplicate(descendent[0],rr= True)[0]
                    tempEmitterMesh = mc.rename( tempEmitterMesh, "tempEmitterMesh")
                    mc.setAttr(tempEmitterMesh+".smoothLevel",0)
                    mc.setAttr(tempEmitterMesh+".useSmoothPreviewForRender",False)
                    mc.setAttr(tempEmitterMesh+".renderSmoothLevel",0)
                    mc.setAttr(tempEmitterMesh+".displaySmoothMesh",0)
                    mc.polySmooth( tempEmitterMesh, divisions=self.subdivLevel )
                else :
                    print "#### error: the number of descendent shape is different from 1"
                    
            #If a shape has been selected, just duplicate it and smooth        
            if mc.objectType(selection[0])=="mesh" and not re.search("\..{1,10}\[",selection[0]):
                if len(selection)>1:
                    print "#### warning: several objects selected, processing with the first selected obj: "+selection[0]
                tempEmitterMesh = mc.duplicate(selection[0],rr= True)[0]
                tempEmitterMesh = mc.rename( tempEmitterMesh, "tempEmitterMesh")
                mc.setAttr(tempEmitterMesh+".smoothLevel",0)
                mc.setAttr(tempEmitterMesh+".useSmoothPreviewForRender",False)
                mc.setAttr(tempEmitterMesh+".renderSmoothLevel",0)
                mc.setAttr(tempEmitterMesh+".displaySmoothMesh",0)
                mc.polySmooth( tempEmitterMesh, divisions=self.subdivLevel )
                tempEmitterMesh = mc.parent( tempEmitterMesh, world=True )[0]
                
            #If a set of grouped faces has been selected: gow the selection once, extract, smooth, reduce selection and extract again
            if re.search("\.f\[",selection[0]):
                mc.polySelectConstraint( type = 0x0008, pp=1 )
                selection = mc.ls(sl = True)
                sourceMesh = re.split("\.f\[",selection[0])[0]
                wipEmitterMesh = mc.duplicate(sourceMesh,rr= True)[0]
                i=0
                while i < len(selection):
                    selection[i] = selection[i].replace(sourceMesh,wipEmitterMesh)
                    i+=1
                mc.polyChipOff (selection,ch=False,kft=True)
                result = mc.polySeparate (wipEmitterMesh, ch=False)            
                if len(result)<=2:
                    mc.setAttr(result[1]+".smoothLevel",0)
                    mc.setAttr(result[1]+".useSmoothPreviewForRender",False)
                    mc.setAttr(result[1]+".renderSmoothLevel",0)
                    mc.setAttr(result[1]+".displaySmoothMesh",0)
                    mc.polySmooth( result[1], divisions=self.subdivLevel )
                    mc.select(result[1]+".f[:]")
                    i=0
                    while i<  self.subdivLevel*self.subdivLevel:
                        mc.polySelectConstraint( type = 0x0008, pp=2 )
                        i+=1
                    selection = mc.ls(sl = True)
                    mc.polyChipOff (selection,ch=False,kft=True)
                    result = mc.polySeparate (result[1], ch=False)
                    tempEmitterMesh = result[1]
                    tempEmitterMesh = mc.rename( tempEmitterMesh, "tempEmitterMesh")
                    tempEmitterMesh = mc.parent( tempEmitterMesh, world=True )[0]
                    mc.delete(wipEmitterMesh)
                else:
                    mc.delete(wipEmitterMesh)
                    tempEmitterMesh=""
                    mc.select(sourceMesh,savedSelection)
                    print ("#### error: selection is not valid. Some of the selected faces are not connected together, the selection must describe a single area of a mesh")
        else:
            print "#### warning: nothing selected"    
                    

        #################
        ####  emit particles on "tempEmitterMesh" ,  instantiate the master on on every particle and delete "tempEmitterMesh"
        #################

        if tempEmitterMesh:
            #generate nParticule system
            InitialNucleusList = mc.ls(exactType="nucleus")
            my_emitter = mc.emitter (tempEmitterMesh, name="myEmitter", type="surface",r= self.perFrameEmissionRate*25, sro=0, nuv=0, spd=0.001, srn=0)
            emitterNode = my_emitter[1]   #my_emitter[0] is the emitting surface
            my_nParticle = mc.nParticle(name="my_nParticle")
            my_nParticle = my_nParticle[0]  #my_nParticle[1] is the nParticleShape
            mc.connectDynamic (my_nParticle, em=emitterNode)
            mc.setAttr(my_nParticle+".ignoreSolverGravity",1)
            mc.setAttr(my_nParticle+".ignoreSolverWind",1)
            mc.setAttr(my_nParticle+".maxCount",self.maxParticleCount)
            mc.setAttr(my_nParticle+".radius",self.particleRadius)
            mc.setAttr(my_nParticle+".emissionOverlapPruning",self.emisOverlapPruning)
            mc.setAttr(my_nParticle+".collide",0)
            mc.setAttr(my_nParticle+".seed[0]",random.randint(1, 300))
            cTime = mc.currentTime(q=True)
            initTime = mc.currentTime(q=True)
            #mc.refresh(suspend = True)
            particleCount = 0
            a = 0
            while (a < self.frameDuration) and (particleCount < self.maxParticleCount):
                cTime = mc.currentTime(cTime+1)
                #print "cTime:",cTime
                if self.perFrameEmissionRate*a > self.maxParticleCount:
                    particleCount = mc.nParticle( my_nParticle, q=True, ct = True)
                    #print "particleCount:", particleCount
                a += 1

            particleCount = int(mc.nParticle( my_nParticle, q=True, ct = True))
            #mc.refresh(suspend = False)

            #################
            ####  Instantiate (transforms) the master and align the instances on every particle, 
            ####  orient it's Y axe along the velocity vector of the particle, 
            ####  and apply srt  random values according to user  inputs
            #################
            if TransformInstanceType:
                instanceList = []
                a = 0
                mc.refresh(suspend = True)
                while (a < particleCount):
                    positionList = mc.nParticle( my_nParticle, q=True, order = a, at = "position")
                    velocityList = mc.nParticle( my_nParticle, q=True, order = a, at = "velocity")
                    item = mc.instance (self.master2Instances, leaf=False)
                    instanceList.append(item[0])
                    angBet = mc.angleBetween (euler=True, v1=(0,1,0), v2=(velocityList[0],velocityList[1],velocityList[2]))
                    mc.rotate(angBet[0],angBet[1],angBet[2], item,a=True, ws=True)
                    mc.move( positionList[0],positionList[1],positionList[2], item, a=True)
                    if self.oriVar > 0:
                        mc.rotate(0,random.uniform(0,self.oriVar),0, item ,r=True, os=True)
                    if 0< self.incVar <= 90:
                        mc.rotate(random.uniform(-self.incVar,self.incVar),0,random.uniform(-self.incVar,self.incVar), item ,r=True, os=True)
                    if self.sclMinVar != self.sclMaxVar != 1:
                        randScale = random.uniform(self.sclMinVar,self.sclMaxVar)
                        mc.scale( randScale,randScale,randScale, item, a=True)
                    if self.elevMinVar != self.elevMaxVar != 0:
                        mc.move(0,random.uniform(self.elevMinVar,self.elevMaxVar),0, item ,r=True, os=True)
                    a += 1
                mc.refresh(suspend = False)
                instanceGroup = mc.group(instanceList, name=str(mc.ls(self.master2Instances)[0])+"_grp00")
                if  mc.listRelatives(instanceGroup, allParents = True):
                        mc.parent (instanceGroup,world =True)
                print "#### info: "+str(len(instanceList))+" instances scattered then grouped in "+instanceGroup

            #################                
            ####  Create a new nParticule static object, 
            ####  get the position and the velocity out of the first generated nParticule object, 
            ####  transform velocity vector into rototation axes
            ####  apply srt  random values according to user  inputs, 
            ####  and create a particule instancer attached to the new nParticle obj
            #################
            else:
                mc.refresh(suspend = True)
                initPosList =[]
                a=0
                while (a < particleCount):
                    initPosList.append([0,0,0])
                    a+=1
                particleNode = mc.nParticle(name = self.master2Instances.split("|")[-1]+"_particle00", position = initPosList)[0]
                particleNodeShape = mc.listRelatives(particleNode, type="shape", ad=True, ni=True,path = True)[0]
                mc.setAttr(particleNodeShape+".isDynamic",0,lock=True)
                mc.addAttr (particleNodeShape, ln='rotPP', dt='vectorArray')
                mc.addAttr (particleNodeShape, ln='rotPP0', dt='vectorArray')
                mc.addAttr (particleNodeShape, ln='sclPP', dt='vectorArray')
                mc.addAttr (particleNodeShape, ln='sclPP0', dt='vectorArray')
                
                a = 0
                while (a < particleCount):                    
                    positionList = mc.nParticle( my_nParticle, q=True, order = a, at = "position")
                    velocityList = mc.nParticle( my_nParticle, q=True, order = a, at = "velocity")
                    angBet = mc.angleBetween (euler=True, v1=(0,1,0), v2=(velocityList[0],velocityList[1],velocityList[2]))
                    if self.oriVar > 0:
                        angBet[1] = angBet[1]+random.uniform(0,self.oriVar)
                    if 0< self.incVar <= 90:
                        angBet[0] = angBet[0]+random.uniform(-self.incVar,self.incVar)
                        angBet[2] = angBet[2]+random.uniform(-self.incVar,self.incVar)
                    if self.sclMinVar != self.sclMaxVar:
                        randScale = random.uniform(self.sclMinVar,self.sclMaxVar)
                    else:
                        randScale = self.sclMinVar
                    if self.elevMinVar != self.elevMaxVar != 0:
                        positionList[1] = positionList[1]+random.uniform(self.elevMinVar,self.elevMaxVar)
                    mc.nParticle(particleNodeShape, e=True, at='position', order=a, vv=positionList)             
                    mc.nParticle(particleNodeShape, e=True, at='rotPP', order=a, vv=angBet)
                    mc.nParticle(particleNodeShape, e=True, at='sclPP', order=a, vv=[randScale,randScale,randScale])
                    a += 1
                mc.refresh(suspend = False)
                particuleInstancer = mc.particleInstancer(particleNodeShape, name=particleNode+"_instancer", addObject=True, rotationOrder = "YXZ", object=self.master2Instances ,position='worldPosition', rotation='rotPP', scale='sclPP')

            #clean scene
            mc.delete(tempEmitterMesh, emitterNode,my_nParticle)
            mc.currentTime(initTime)
            allNucleus = mc.ls(exactType="nucleus")
            nucleusToDelL = list(set(allNucleus) - set(InitialNucleusList))
            if nucleusToDelL: mc.delete(nucleusToDelL)

        else:
            print ("#### info: please make a valid selection")

#------------------------    Tab2 : "Instance Scatter"
#----Group "Master"
    def on_master2particles_pushButton_pressed(self):
        try :
            self.master2particles= mc.ls(sl = True, l = True)[0]
        except IndexError:
            print "#### info: nothing selected"
            self.master2particles = ""
        self.master2particles_lineEdit.setText(QtGui.QApplication.translate("instancerTool_Dialog", str(self.master2particles) , None, QtGui.QApplication.UnicodeUTF8))

#----Group "append to existing particle instancer"
    def on_selectParticleInstancer_pushButton_pressed(self):
        try :
            self.particleInstancer = mc.ls(sl=True)[0]
            if not (mc.listRelatives(self.particleInstancer, children = True,  type ="particle",path=True)or mc.nodeType(self.particleInstancer)=="particle"):
                print "#### error: no particle node selected"
                self.particleInstancer = ""
                return
        except IndexError:
            print "#### info: nothing selected"
            self.particleInstancer = ""
        self.selectedParticleInstancer_lineEdit.setText(QtGui.QApplication.translate("instancerTool_Dialog", str(self.particleInstancer) , None, QtGui.QApplication.UnicodeUTF8))

    def on_appendTo_pushButton_pressed(self):
        '''
        append the selected instances to the specified particle node
        '''
        print ""
        print "#### running : append to particle instancer system"
        self.append_instances_to_particle (self.particleInstancer )


    def on_createNew_pushButton_pressed(self):
        print ""
        print "#### running : create new particle instancer system"
        selection = mc.ls(sl=True, type = "transform")
        if not selection:
            print "#### error: no transform selected"
            return
        descendentTransform = mc.listRelatives (selection,allDescendents = True, type ="transform",path=True)
        if descendentTransform:
            myTransformList = list (selection + descendentTransform)
        else:
            myTransformList = list (selection)
        instanceRootList = self.get_instance_root(myTransformList)

        if instanceRootList :
            if not self.check_if_similar_hierarchy(instanceRootList):
                print "#### Error: at least one of the selected instance is different from the others, please select only one kind of instance at the time"
                return 
            else:
                toAppendList = instanceRootList
        else: 
            if user_agree("No instance could be found in your selection, do you want to proceed with shapes transforms instead ?","Warning: will fail with hierarchy, only 'transform + shape' couple will succeed"):
                toAppendList =[]
                for each in  myTransformList:
                    if mc.listRelatives (each, children = True, shapes = True ):
                        toAppendList.append(each)
                print "#### info: proceeding with shapes transforms"

        if not toAppendList:
            print "#### Error: no instance or shape transform in your selection"
            return

        if not self.master2particles:
            instanceRootChild =  mc.listRelatives (toAppendList[0], children = True,path=True)[0]
            defaultMaster = mc.listRelatives (instanceRootChild, allParents = True,path=True)
            defaultMaster.sort()
            if user_agree("No master specified, do you want to use the following object as master :", str(defaultMaster[0])):
                self.master2particles = defaultMaster[0]
                print "#### Info: proceeding with master: " + self.master2particles
            else :
                print "#### Error: no master specified"
                return
        if  self.master2particles == mc.ls(sl = True, l = True)[0]:
            print "#### Error: your master is selected"
            return
        if not self.check_if_similar_hierarchy([toAppendList[0],self.master2particles]):
            print "#### warning: the chosen master instance is different from the other instances",self.master2particles, toAppendList[0]
        particleNode, particuleInstancer = self.create_particule_and_instancer (self.master2particles.split("|")[-1], toAppendList)
        mc.selection(selection)
        print "#### info: particle node created: ",particleNode
        print "#### info: particle instancer created: ",particuleInstancer


    def on_extractFrom_pushButton_pressed(self):
        print ""
        print "#### running : extract instances from particle"
        #check selection
        selectedParticles =  mc.ls(sl=True, flatten =True, type="double3")
        if not selectedParticles :
            print "#### error: please select particles component first"
            return
        particleNodeShape = mc.listRelatives(selectedParticles[0],parent = True, shapes = True)[0]
        particleNode = mc.listRelatives(particleNodeShape,parent = True, type = "transform")[0]
        particleNodeCount = mc.nParticle (particleNode, q=True, count=True)
        print("#### info: initial particles number: "+ str(particleNodeCount))

        if mc.nodeType(particleNodeShape) not in ["particle", "nParticle"]:
            print "#### error: can only exctract from a 'nParticle' type object"
            return
        instancerNode = mc.listConnections(particleNodeShape, type = "instancer")
        if instancerNode:
            instancerNode = instancerNode[0]
            #particle2InstancerConnection = mc.listConnections(particleNodeShape, connections = True,plugs =True, type = "instancer")
        if not self.master2particles:
            master =  mc.listConnections(instancerNode+".inputHierarchy")
            if master :
                print "#### info: no master specified, using 'instancer.input Hierarchy[1]': ",master
            else : 
                print "#### error: no master specified, please select one"
        else:
            master = self.master2particles
        #get selected particle ids
        idToExtract = []
        for each in selectedParticles:
            if mc.listRelatives(each,parent = True)[0] != particleNodeShape:
                print "#### error: can only extract from one particle object at the time"
                return
            idToExtract.append(int(re.split("\.pt\[|\]", each)[1]))

        #get the S.R.T. values of  the selected particles
        forParticlePos =[]; forParticleRot =[]; forParticleScl =[]
        createdInstances = []
        a=0
        b=0 #in the id of the particle in the furtire particle node
        canNotGetRotPP = 0
        canNotGetSclPP = 0
        while a<particleNodeCount:
            if a not in idToExtract:
                forParticlePos.append(mc.nParticle(particleNode, q=True, vv = True, at='pos',  id=a))
                try:
                    forParticleRot.append(mc.nParticle(particleNode, q=True, vv = True, at='rotPP', id=a))
                except:
                    forParticleRot.append([0,0,0])
                    canNotGetRotPP = 1
                try: 
                    forParticleScl.append(mc.nParticle(particleNode, q=True, vv = True, at='sclPP', id=a))
                except:
                    forParticleScl.append([1,1,1])
                    canNotGetSclPP = 1
                b+=1
            else:
                forInstancePos = mc.nParticle(particleNode, q=True, at='pos', id=a)
                try:
                    forInstanceRot = mc.nParticle(particleNode, q=True, at='rotPP', id=a)
                except:
                    forInstanceRot = [0,0,0]
                    canNotGetRotPP = 1
                try: 
                    forInstanceScl = mc.nParticle(particleNode, q=True, at='sclPP', id=a)
                except:
                    forInstanceScl = [1,1,1]
                    canNotGetSclPP = 1
                item = mc.instance (master, leaf=False)
                createdInstances.append(item[0])
                mc.rotate(forInstanceRot[0],forInstanceRot[1],forInstanceRot[2], item,a=True, ws=True)
                mc.move( forInstancePos[0],forInstancePos[1],forInstancePos[2], item, a=True)
                mc.scale( forInstanceScl[0],forInstanceScl[1],forInstanceScl[2], item, a=True)
            a+=1

        if canNotGetRotPP == 1: 
            print "#### warning: rotPP could not be read from at least one of the particle "
        if canNotGetSclPP == 1: 
            print "#### warning: sclPP could not be read from at least one of the particle "

        mc.delete(particleNode)
        mc.delete(instancerNode)

        #create  new particle node
        particleNode = mc.nParticle(name = particleNode, position = forParticlePos)[0]
        particleNodeShape = mc.listRelatives(particleNode, type="shape", ad=True, ni=True)[0]
        mc.setAttr(particleNodeShape+".isDynamic",0,lock=True)
        mc.addAttr (particleNodeShape, ln='rotPP', dt='vectorArray')
        mc.addAttr (particleNodeShape, ln='rotPP0', dt='vectorArray')
        mc.addAttr (particleNodeShape, ln='sclPP', dt='vectorArray')
        mc.addAttr (particleNodeShape, ln='sclPP0', dt='vectorArray')
        #mc.saveInitialState (particleNode)
        particleNodeCount = mc.nParticle (particleNode, q=True, count=True)
        a=0
        while a<particleNodeCount:
            mc.nParticle(particleNode, e=True, at='rotPP', id=a, vv=forParticleRot[a])
            mc.nParticle(particleNode, e=True, at='sclPP', id=a, vv=forParticleScl[a])
            a+=1
        print("#### info: new particles number: "+ str(particleNodeCount))
        # create a new particle node and instancer
        mc.particleInstancer(particleNode, name=particleNode+"_instancer", addObject=True, object=master ,position='worldPosition', rotation='rotPP', scale='sclPP')
        instanceGroup = mc.group(createdInstances,name=str(mc.ls(master)[0])+"_grp00")
        if  mc.listRelatives(instanceGroup, allParents = True):
            mc.parent (instanceGroup,world =True)
        print "#### info: "+str(len(createdInstances))+" instances extracted then grouped in: "+instanceGroup
            

    def get_instance_root(self, objectList):
        '''
        returns the objects that have no more than one parent but their direct children have several parents.
        theses objects can be considered as instances roots
            inArgs: objectList (string list)
            outArgs: InstanceRootList (string list)
        '''
        InstanceRootList = []
        for item in objectList:
            itemParentList = mc.listRelatives (item,allParents = True,path=True)
            itemChildrenList = mc.listRelatives (item,children = True,path=True)
            if not itemParentList:
                itemParentList = []
            if len(itemParentList)<2 and itemChildrenList:
                childrenAreAllInstance = 1
                for eachChild in itemChildrenList:
                    if len(mc.listRelatives (eachChild,allParents = True,path=True))<2:
                        childrenAreAllInstance = 0
                if (item not in InstanceRootList) and childrenAreAllInstance == 1 :
                    InstanceRootList.append(item)
        return InstanceRootList

    def check_if_similar_hierarchy (self, objectList):
        '''
        compare the descendent shapes hierarchy of every given node in the list
        return False if one of them is different, return True otherwise
            inArgs: objectList (string list)
            outArgs: boolean
        '''
        if objectList:
            descendentShape = []
            instRootCount = len(objectList)
            a = 0
            while a < instRootCount:
                descendentShape.append(mc.listRelatives (objectList[a],allDescendents = True, shapes = True, ni=True))
                if a>0:
                    if descendentShape[a]!=descendentShape[a-1]:
                        return False
                a+=1
            return True
        else : return False

    def create_particule_and_instancer (self, masterTransform, instanceTransforms):
        """create a particle object from a Maya transform list.
        Rotation and scale values of the transform are passed thought per particles attributes rotPP and sclPP.
        inArgs: masterTransform (string), instanceTransforms (string list)
        outArgs: particleNode (string), particuleInstancer (string)"""
        InitialNucleusList = mc.ls(exactType="nucleus")
        #List the transformation values of  our instances transforms
        InstanceTransformsPos =[]; InstanceTransformsRot =[]; InstanceTransformsScl =[]
        for item in instanceTransforms:  
            if mc.xform (item, q=True, rotateOrder=True,ws=True) !="xyz" :
                print ("#### warning: the following transform rotation order is different from xyz: "+str(item))
            InstanceTransformsPos.append (mc.xform (item, q=True,translation=True,ws=True))
            InstanceTransformsRot.append (mc.xform (item, q=True, rotation=True,ws=True))
            InstanceTransformsScl.append (mc.xform (item, q=True, scale=True,ws=True))
        #Create a particle object, and set the position, rotPP, and sclPP of 
        particleNode = mc.nParticle(name = masterTransform+"_particle00", position = InstanceTransformsPos)[0]
        print "particleNode",particleNode
        particleNodeShape = mc.listRelatives(particleNode, type="shape", ad=True, ni=True,path = True)[0]
        print "particleNodeShape",particleNodeShape
        mc.setAttr(particleNodeShape+".isDynamic",0,lock=True)
        mc.addAttr (particleNodeShape, ln='rotPP', dt='vectorArray')
        mc.addAttr (particleNodeShape, ln='rotPP0', dt='vectorArray')
        mc.addAttr (particleNodeShape, ln='sclPP', dt='vectorArray')
        mc.addAttr (particleNodeShape, ln='sclPP0', dt='vectorArray')
        #mc.saveInitialState (particleNode)
        particleNodeCount = mc.nParticle (particleNode, q=True, count=True)
        a=0
        while a<particleNodeCount:
            mc.nParticle(particleNode, e=True, at='rotPP', id=a, vv=InstanceTransformsRot[a])
            mc.nParticle(particleNode, e=True, at='sclPP', id=a, vv=InstanceTransformsScl[a])
            a+=1
        print("#### info: number of particles created: "+ str(particleNodeCount))
        particuleInstancer = mc.particleInstancer(particleNode, name=particleNode+"_instancer", addObject=True, object=masterTransform ,position='worldPosition', rotation='rotPP', scale='sclPP')
        allNucleus = mc.ls(exactType="nucleus")
        nucleusToDelL = list(set(allNucleus) - set(InitialNucleusList))
        if nucleusToDelL: mc.delete(nucleusToDelL)
        return particleNode, particuleInstancer

    def append_instances_to_particle (self, particleNode):
        '''
        append a new particle to the given particle node, for every selected instances.
        '''
        InitialNucleusList = mc.ls(exactType="nucleus")
        selection = mc.ls(sl=True, type = "transform")
        if not selection:

            print "#### error: nothing selected or no transform in your selection"
            return
        if not particleNode :
            print "#### error: please specify a particle node first"
            return
        #get all the transforms in the selection hierarchy
        descendentTransform = mc.listRelatives (selection,allDescendents = True, type ="transform",path=True)
        if descendentTransform:
            transformList = list (selection + descendentTransform)
        else:
            transformList = list (selection)
            
        #get the instance Root List of the all the transform
        instanceRootList = self.get_instance_root(transformList)
        if instanceRootList :
            toAppendList = instanceRootList
        else: 
            if user_agree("No instance could be found in your selection, do you want to proceed with shapes transforms instead ?","Warning: will fail with hierarchy, only 'transform + shape' couple will succeed"):
                toAppendList =[]
                for each in  transformList:
                    if mc.listRelatives (each, children = True, shapes = True ):
                        toAppendList.append(each)
                print "#### info: proceeding with shapes transforms"

        #List the transformation values of the particles
        particleNodeCount = mc.nParticle (particleNode, q=True, count=True)
        particlePos =[]; particleRot =[]; particleScl =[]
        a=0
        while a<particleNodeCount:
            particlePos.append(mc.nParticle(particleNode, q=True, vv = True, at='pos',  id=a))
            particleRot.append(mc.nParticle(particleNode, q=True, vv = True, at='rotPP', id=a))
            particleScl.append(mc.nParticle(particleNode, q=True, vv = True, at='sclPP', id=a))
            a+=1
        #List the transformation values of our instances transforms
        transformPos =[]; transformRot =[]; transformScl =[]
        particleNotAdded = 0
        for item in toAppendList:  
            if mc.xform (item, q=True, rotateOrder=True,ws=True) !="xyz":
                print ("#### warning: the following transform rotation order is different from xyz: "+str(item))
            itemPos = mc.xform (item, q=True, translation=True,ws=True)
            itemRot = mc.xform (item, q=True, rotation=True,ws=True)
            itemScl = mc.xform (item, q=True, scale=True,ws=True)
            #check if the transformation does not match with an existing particle
            if (itemPos in particlePos) and (itemRot in particleRot) and (itemScl in particleScl):
                particleNotAdded += 1
            else:
                transformPos.append (itemPos)
                transformRot.append (itemRot)
                transformScl.append (itemScl)
        addedParIds = 0
        if transformPos:
            addedParIds = mc.emit (object=particleNode, position=transformPos)
        if addedParIds :
            addedParCount =  len (addedParIds)
            a=0
            while a<addedParCount:
                mc.nParticle(particleNode, e=True, at='rotPP', id=addedParIds[a], vv=transformRot[a])
                mc.nParticle(particleNode, e=True, at='sclPP', id=addedParIds[a], vv=transformScl[a])
                a+=1
            mc.saveInitialState (particleNode)
            cTime = mc.currentTime(q=True)
            mc.currentTime(cTime+1)
            mc.currentTime(cTime)
        else:
            addedParCount = 0

        # Clean
        mc.select(selection)
        allNucleus = mc.ls(exactType="nucleus")
        nucleusToDelL = list(set(allNucleus) - set(InitialNucleusList))
        if nucleusToDelL: mc.delete(nucleusToDelL)

        newParCount  = mc.nParticle (particleNode, q=True, count=True)
        if particleNotAdded > 0:
            print("#### info: some transforms/instances are already encapsulated, number of particles skipped: "+str(particleNotAdded))
        print("#### info: number of particles added: "+str(addedParCount))
        print("#### info: new particle count: "+str(newParCount))

def user_agree(text1,text2):
    '''
         open a a Qdialog asking to the user if he wishes to continue or cancel
         inArgs: 
            text1(string), first text line of the dialog
            text2(string),second text line of the dialog 
        outArgs: 
            InstanceRootList (boolean)
    '''
    try:
        ask_ui.deleteLater()
    except:
        pass
        
    ask_ui = ui.Ui_OkCancel()
    try:
        ask_ui.setupUi(text1,text2)
        ask_ui.exec_()
    except:
        #ask_ui.close()
        ask_ui.deleteLater()
        traceback.print_exc()
    return ask_ui.answer
################################################################################
################  MAIN
################################################################################


def run():
    # Development workaround for PySide winEvent error (in Maya 2014)
    # Make sure the UI is deleted before recreating
    try:
        my_ui.deleteLater()
    except:
        pass

    # Create minimal UI object
    my_ui = Ui_instancerTool_Dialog()

    # Delete the UI if errors occur to avoid causing winEvent
    # and event errors (in Maya 2014)
    try:
        my_ui.setupUi()
        my_ui.show()
    except:
        my_ui.deleteLater()
        traceback.print_exc()
