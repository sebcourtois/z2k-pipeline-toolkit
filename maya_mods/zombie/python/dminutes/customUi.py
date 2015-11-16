import os
import re
import string
import maya.utils as utils


from PySide import QtCore
from PySide import QtGui
from shiboken import wrapInstance


import maya.cmds
mc = maya.cmds
import maya.OpenMayaUI as omui


def maya_main_window():
    '''
    Return the Maya main window widget as a Python object
    '''
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtGui.QWidget)



class MayaMenuGenerator(object):
    '''
    creates a maya menu
    '''
    def __init__(self, scriptsFolder = "", menuName = ""):
        if not scriptsFolder:
            print "#### error: no script folder provided!"
            return
        else:
            self.scriptsFolder = scriptsFolder
        if not menuName:
            self.menuName = self.getNiceName(os.path.basename(self.scriptsFolder))
        else:
            self.menuName = menuName
        print ""
        print "#### Info: Initiating maya menu: ",self.menuName 
        print "#### Info: From script folder tree: ",self.scriptsFolder



    def updateMenu(self,*args):
        print ""
        print "#### Info: Updating maya menu: ",self.menuName 
        print "#### Info: From script folder tree: ",self.scriptsFolder
        if mc.menu(self.scriptsMenu, exists=1):
            mc.deleteUI(self.scriptsMenu)
        self.generateMenuFromDirTree(update = True)



    def getNiceName(self, myString):
        if re.search("\_", myString):
            myCapitalisedSplitedString = [i.capitalize() for i in myString.split("_")]
            niceName = string.join(myCapitalisedSplitedString," ")
            return niceName
        elif re.search("[a-z0-9]+|[A-Z][a-z0-9]+", myString):
            myCapitalisedSplitedString = [i.capitalize() for i in re.findall("[a-z0-9]+|[A-Z][a-z0-9]+",myString)]
            niceName = string.join(myCapitalisedSplitedString," ")
            return niceName
        
        
    def generateMenuFromDirTree(self, update = False):
        """
        This method walk through the script folder and return generates a menu and submenu structure out of it.
        The first element of the tuple is the directory path of the script and the second element is the script name.
        Only the '.py' scripts and directories that do not start with an '_' will be considered.
        Only directories that have at least a '.py' file in one of their sub-folder will be processed.  
        """
        
        #generate the script menu in the maya window
        self.scriptsMenu = mc.menu(self.menuName, p="MayaWindow", to=1, l=self.menuName)
        mc.menuItem(p=self.scriptsMenu, l="Update Scripts Menu", c= self.updateMenu)

        # walk through the script folder to get the 'scriptsAddresses'
        self.scriptsAddresses = []
        for root, dirs, files in os.walk(self.scriptsFolder):
            toRemove = [dirs[i] for i, x in enumerate(dirs) if re.match(r'\_', x)]
            if toRemove:
                for each in toRemove:
                    dirs.remove(each)
            toRemove = [files[i] for i, x in enumerate(files) if not re.match(r'[a-zA-Z0-9]\w+\.py\Z', x)]
            if toRemove:
                for each in toRemove:
                    files.remove(each)
            if files:
                root = os.path.normpath(root).replace("\\", "/")
                self.scriptsAddresses.append([root, files])
            elif dirs:
                root = os.path.normpath(root).replace("\\", "/")
                for root2, dirs2, files2 in os.walk(root):
                    if files2:
                        for each in files2:
                            if re.match(r'[a-zA-Z0-9]\w+\.py\Z', each):
                                self.scriptsAddresses.append([root, files])
                                break
        #generate all the menu item according to the 'scriptsAddresses'
        oldRoot = ""
        for root,files in self.scriptsAddresses:
            if root == self.scriptsFolder:
                continue
            #load the package
            root = root.replace(self.scriptsFolder+"/","")
            packageName = os.path.basename(self.scriptsFolder)+"."+root.replace("/",".")
            while not oldRoot in root:
                oldRoot = "/".join(oldRoot.split("/")[0:-1])
                mc.setParent( "..", menu=True )
            subMenuName = self.getNiceName(root.split("/")[-1])
            mc.menuItem( subMenu=True, to = 1,label=subMenuName )
            #create the command item in the subMenu
            for each in files:
                moduleName = each.replace(".py","")
                toExec = "from "+packageName+" import "+moduleName
                utils.executeDeferred(str(toExec))
                print "#### info: "+toExec
                if update == True : 
                    toExec2 = "reload ("+moduleName+")"
                    print "#### info: "+toExec2
                    utils.executeDeferred(str(toExec2))
                commandToRun = each.replace(".py",".run()")
                commandlabel = self.getNiceName(each.replace(".py",""))
                mc.menuItem( subMenu=False, to = 0,label=commandlabel,command = commandToRun)
            oldRoot = str(root)
            



class Ui_OkCancel(QtGui.QDialog):
    '''
    creates a simple dialog window, that display 2 text lines and a couple of button ok/cancel
    '''
    def __init__(self, parent=maya_main_window()):
        super(Ui_OkCancel, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.answer = False
        
    def setupUi(self, text1, text2):
        '''
        setup the Ui_OkCancel
        '''
        self.setObjectName("yesNo")
        self.resize(355, 105)
        self.verticalLayout_2 = QtGui.QVBoxLayout(self)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.text1_label = QtGui.QLabel(self)
        self.text1_label.setAlignment(QtCore.Qt.AlignCenter)
        self.text1_label.setObjectName("text1_label")
        self.verticalLayout_2.addWidget(self.text1_label)
        self.text2_label = QtGui.QLabel(self)
        self.text2_label.setAlignment(QtCore.Qt.AlignCenter)
        self.text2_label.setObjectName("text2_label")
        self.verticalLayout_2.addWidget(self.text2_label)
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout_2.addWidget(self.buttonBox)
        self.setWindowTitle(QtGui.QApplication.translate("yesNo", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.text1_label.setText(QtGui.QApplication.translate("yesNo", text1, None, QtGui.QApplication.UnicodeUTF8))
        self.text2_label.setText(QtGui.QApplication.translate("yesNo", text2, None, QtGui.QApplication.UnicodeUTF8))
        self.create_connections()

    def create_connections(self):
        '''
        Create the signal/slot connections
        '''
        #--ask_ui
        self.buttonBox.accepted.connect(self.on_masterAccepeted_buttonBox_pressed)
        self.buttonBox.rejected.connect(self.on_masterRejected_buttonBox_pressed)

    def on_masterAccepeted_buttonBox_pressed(self):
        self.answer = True
        self.close()
        return self.answer

    def on_masterRejected_buttonBox_pressed(self):
        self.answer = False
        self.close()
        return self.answer


def ui2Py(uiFileName):
    """
    Compile a '.ui' file gererated with QTdesigner to ".py" python file
        input (string):  uiFileName : the complete '.ui' file name and path
        return (string): pyFileName : the complete '.py' file name and path
    """

    from pysideuic import compileUi
    if not uiFileName:
        print "#### error: no '.ui'  file given"
        return
    uiFileName = os.path.normpath(uiFileName).replace("\\", "/")
    if os.path.isfile(uiFileName):
        pyFileName  = uiFileName.replace(".ui", ".py")
        pyFile = open(pyFileName, 'w')
        compileUi(uiFileName, pyFile, False, 4, False)
        pyFile.close()
        print "#### info: compiled:",uiFileName
        print "#### info:       to:",pyFileName
        return pyFileName
    else:
        print "#### error: cannot open :", uiFileName
        return


