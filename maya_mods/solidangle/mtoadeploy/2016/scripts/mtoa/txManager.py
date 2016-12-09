import maya.cmds as cmds
import maya.utils as utils
import os.path
import glob
import re
import sys, os
import subprocess
import threading
import makeTx
import platform
from arnold import *
import pymel.versions as versions

def isImage(file):
    ext = os.path.splitext(file)[1]
    if (ext == '.jpeg' or ext == '.jpg' or ext == '.tiff' or ext == '.tif' or
        ext == '.png' or ext == '.exr' or ext == '.hdr' or ext == '.bmp' or
        ext == '.tga'):
        return True
    return False
    
def updateProgressMessage(window, created, toCreate, errors):
    ctrlPath = '|'.join([window, 'groupBox_2', 'label_8']);
    cmds.text(ctrlPath, edit=True, label="Created: {0} of {1}".format(created,toCreate));
    if errors is not 0:
        ctrlPath = '|'.join([window, 'groupBox_2', 'label_9']);
        cmds.text(ctrlPath, edit=True, label="Warning: {0} errors".format(errors));
    else:
        ctrlPath = '|'.join([window, 'groupBox_2', 'label_9']);
        cmds.text(ctrlPath, edit=True, label="");

class MakeTxThread (threading.Thread):
    def __init__(self,manager):
        self.txManager = manager
        threading.Thread.__init__(self)
        self.filesCreated = 0
        self.createdErrors = 0
        
    def run (self):
        self.filesCreated = 0
        self.createdErrors = 0
        self.createTx()
        self.txManager.thread = []
    
    # create a .tx file with the provided options. It will wait until it is finished
    def runMakeTx(self, texture, space):

        ctrlPath = '|'.join([self.txManager.window, 'groupBox_2', 'lineEdit']);
        arg_options = utils.executeInMainThreadWithResult(cmds.textField, ctrlPath, query=True, text=True)
        status = utils.executeInMainThreadWithResult( makeTx.makeTx, texture, colorspace=space, arguments=arg_options)
        return status

    def createTx(self):
        if not self.txManager.selectedItems:
            return
            
        ctrlPath = '|'.join([self.txManager.window, 'groupBox_2', 'pushButton_7']);
        utils.executeDeferred(cmds.button,ctrlPath, edit=True, enable=True);
            
        for textureLine in self.txManager.selectedItems:
            texture = textureLine[0]
            
            # we could use textureLine[2] for the colorSpace
            # but in case it hasn't been updated correctly
            # it's still better to ask maya again what is the color space
            nodes = textureLine[3]
            colorSpace = 'auto'
            conflictSpace = False
            for node in nodes:
                nodeColorSpace = cmds.getAttr(node+'.colorSpace')
                if colorSpace != 'auto' and colorSpace != nodeColorSpace:
                    conflictSpace=True
                    
                colorSpace = nodeColorSpace

            if colorSpace == 'auto' and textureLine[2] != '':
                colorSpace = textureLine[2]
            if not texture:
                continue;
            # stopCreation has been called   
            if not self.txManager.process:
                break

            # if a conflict is found, pop-up a dialog
            if conflictSpace:
                msg = os.path.basename(texture)
                msg += '\n'
                msg += 'has conflicting Color Spaces.\n'
                msg += 'Use ('
                msg += colorSpace
                msg += ') ?'

                result = cmds.confirmDialog(
                    title='Conflicting Color Spaces',
                    message=msg,
                    button=['OK', 'Cancel'],
                    defaultButton='OK',
                    cancelButton='Cancel',
                    dismissString='Cancel')

                if result == 'Cancel':
                    break

            # Process all the files that were found previously for this texture (eventually multiple tokens)
            for inputFile in textureLine[4]:
                # here inputFile is already expanded, and only corresponds to existing files

                if not self.txManager.process:
                    # stopCreation has been called
                    break;

                status = self.runMakeTx(inputFile, colorSpace)
                self.filesCreated += status[0]
                self.createdErrors += status[2]
                    
                utils.executeDeferred(updateProgressMessage, self.txManager.window, self.filesCreated, self.txManager.filesToCreate, self.createdErrors) 

        
        ctrlPath = '|'.join([self.txManager.window, 'groupBox_2', 'pushButton_7']);
        utils.executeDeferred(cmds.button, ctrlPath, edit=True, enable=False);
        self.txManager.process = True
        utils.executeDeferred(self.txManager.updateList)


class MtoATxManager(object):
    use=None;
    def __init__(self):
        MtoATxManager.use = self;
        path = os.path.dirname(os.path.abspath(__file__))
        self.uiFile = os.path.join(path,'txManager.ui');
        self.window = '';
        self.txItems = []   # arrays [texture_name, status, colorSpace, nodeList, inputFiles] 
                            # where status is:
                            #   -1 (does not exists),
                            #    0 (.tx file),
                            #    1 (has a processed .tx file),
                            #    2 (does not have a processed .tx file)
        self.listElements = []
        self.selectedItems = []
        self.filesToCreate = 0
        
        self.filesCreated = 0
        self.createdErrors = 0
        self.deletedFiles = 0
        
        self.thread = []
        self.process = True
        self.lineIndex = {}
        
    def create(self):
        if cmds.window(self.window, exists=True):
            cmds.deleteUI(self.window);
        self.window = cmds.loadUI(uiFile=self.uiFile, verbose=False)
        
        cmds.showWindow(self.window);
        try:
            initPos = cmds.windowPref( self.window, query=True, topLeftCorner=True )
            if initPos[0] < 0:
                initPos[0] = 0
            if initPos[1] < 0:
                initPos[1] = 0
            cmds.windowPref( self.window, edit=True, topLeftCorner=initPos )
        except :
            pass
        
        ctrlPath = '|'.join([self.window, 'radioButton']);
        cmds.radioButton(ctrlPath, edit=True, select=True);
        
        ctrlPath = '|'.join([self.window, 'groupBox_4']);
        cmds.control(ctrlPath, edit=True, enable=False);
        
        ctrlPath = '|'.join([self.window, 'groupBox_2', 'pushButton_7']);
        cmds.button(ctrlPath, edit=True, enable=False);
        
        ctrlPath = '|'.join([self.window, 'groupBox_2', 'lineEdit']);
        cmds.textField(ctrlPath, edit=True, text="-v -u --unpremult --oiio");
        
    # Update the Scroll List with the texture files in the scene and check its status
    def updateList(self):
        self.txItems = []
        
        texturesList = []
        colorSpaces = []
        nodes = []

        list = cmds.ls(type='file')
        for node in list:
            texture = cmds.getAttr(node+'.fileTextureName')
            if texture:
                texturesList.append(texture)
                colorSpace = cmds.getAttr(node+'.colorSpace')
                colorSpaces.append(colorSpace)
                nodes.append(node)
                                    
        list = cmds.ls(type='aiImage')
        for node in list:
            texture = cmds.getAttr(node+'.filename')
            if texture:
                texturesList.append(texture)
                colorSpace = cmds.getAttr(node+'.colorSpace')
                colorSpaces.append(colorSpace)
                nodes.append(node)
        
        list = cmds.ls(type='imagePlane')
        for node in list:
            texture = cmds.getAttr(node+'.imageName')
            if texture:
                texturesList.append(texture)
                colorSpace = cmds.getAttr(node+'.colorSpace')
                colorSpaces.append(colorSpace)
                nodes.append(node)
            
        totalFiles = 0
        missingFiles = 0

        textureSearchPaths = cmds.getAttr('defaultArnoldRenderOptions.texture_searchpath')
        searchPaths = []

        if platform.system().lower() == 'windows':
            searchPaths = textureSearchPaths.split(';')    
        else:
            searchPaths = textureSearchPaths.split(':')
        
        for i in range(len(texturesList)):

            inputFiles = makeTx.expandFilename(texturesList[i])
            
            if len(inputFiles) == 0:
                # file not found, need to search in the Texture Search Paths
                for searchPath in searchPaths:
                    if searchPath.endswith('/'):
                        currentSearchTexture = searchPath + texturesList[i]
                    else:
                        currentSearchTexture = searchPath + '/'+texturesList[i]
                
                    inputFiles = makeTx.expandFilename(currentSearchTexture)
                    if len(inputFiles) > 0:
                        break
            
            totalFiles += len(inputFiles)
            
            txFlag = 0

            if len(inputFiles) == 0:
                # missing input file
                txFlag = -1
                missingFiles += 1
            else:
                ext = os.path.splitext(texturesList[i])[1]
                # A .tx texture
                if(ext == '.tx'):
                    txFlag = 0
                else:
                    # Not a .tx texture
                    # loop over files since we need to make sure each expanded texture has its .tx version
                    txFlag = 1
                    for inputFile in inputFiles:
                        # note that inputFile is already expanded here
                        outputTx = os.path.splitext(inputFile)[0]+'.tx'
                        outputTxFiles = makeTx.expandFilename(outputTx)

                        if len(outputTxFiles) == 0:
                            # un-processed File
                            txFlag = 2
                            break

            # set textures element as a list : [filename, txFlag, textureColorSpace, node]
            nodesList = [nodes[i]]
            self.txItems.append([texturesList[i], txFlag, colorSpaces[i], nodesList, inputFiles])


        ctrlPath = '|'.join([self.window, 'groupBox', 'listWidget']);

        listSize = cmds.textScrollList(ctrlPath, query=True, numberOfItems=True);
        for x in range(listSize,0,-1):
            cmds.textScrollList(ctrlPath, edit=True, removeIndexedItem=x);
        
        textureIndex = 0
        self.lineIndex = {}

        for txItem in self.txItems:

            texturePrefix = ''

            if(txItem[1] == 0):
                texturePrefix = '[tx] '
            elif(txItem[1] == 1):
                texturePrefix = '(tx) '
            elif(txItem[1] == 2):
                texturePrefix = '       '
            elif(txItem[1] == -1):
                texturePrefix = '~~  '

            textureLine = texturePrefix+txItem[0] 

            maya_version = versions.shortName()
            if int(float(maya_version)) >= 2017:
                textureLine +=' ('+txItem[2]+')'
                
            if textureLine not in self.lineIndex:
                cmds.textScrollList(ctrlPath, edit=True, append=[textureLine]);
                self.lineIndex[textureLine] = textureIndex
                textureIndex += 1    
            else:
                prevIndex = self.lineIndex[textureLine]
                if prevIndex < len(self.txItems):
                    self.txItems[prevIndex][3].append(txItem[3][0])

        self.listElements = cmds.textScrollList(ctrlPath, query=True, ai=True);
                
        ctrlPath = '|'.join([self.window, 'groupBox', 'label_5']);
        cmds.text(ctrlPath, edit=True, label="Total Files: {0}".format(totalFiles));
        
        ctrlPath = '|'.join([self.window, 'groupBox', 'label_6']);
        if(missingFiles > 0):
            cmds.text(ctrlPath, edit=True, label="<font color=#FE6565>Missing Files: {0}</font>".format(missingFiles));
        else:
            cmds.text(ctrlPath, edit=True, label="");
    
    def stopCreation(self, *args):
        self.process = False
    
    # Updates the Scroll List and also the process progress message
    # Only to be used when a refresh button is pressed, as it will remove any progress information shown
    def refreshList(self, *args):
        self.updateList()   
        
        #Only update this text when button is pressed, not when called from createTx or deleteTx    
        updateProgressMessage(self.window, 0, 0, 0)
        ctrlPath = '|'.join([self.window, 'groupBox_3', 'label_10']);
        cmds.text(ctrlPath, edit=True, label="");
            
    def selectAll(self, *args):
        self.updateList()
        if self.listElements:
            all_idx = [i+1 for i, texture in enumerate(self.listElements) if texture.startswith('       ') or texture.startswith('(tx) ')]
            ctrlPath = '|'.join([self.window, 'groupBox', 'listWidget']);
            cmds.textScrollList(ctrlPath, edit=True, deselectAll=True);
            cmds.textScrollList(ctrlPath, edit=True, selectIndexedItem=all_idx);
            
            self.selectedFilesFromList()
        
    # Select all textures that does not have a processed .tx file
    def selectNonTx(self, *args):
        self.updateList()
        if self.listElements:
            all_idx = [i+1 for i, texture in enumerate(self.listElements) if texture.startswith('       ')]
            ctrlPath = '|'.join([self.window, 'groupBox', 'listWidget']);
            cmds.textScrollList(ctrlPath, edit=True, deselectAll=True);
            cmds.textScrollList(ctrlPath, edit=True, selectIndexedItem=all_idx);
            
            self.selectedFilesFromList()
    
    def selectChange(self, *args):
        self.selectedFilesFromList()
        
    def selectLine(self, *args):
        ctrlPath = '|'.join([self.window, 'groupBox', 'listWidget']);
        
        selectedList = cmds.textScrollList(ctrlPath, query=True, si=True);
        
        lineText = selectedList[0];
        lineIndex = self.lineIndex[lineText]

        if lineIndex >= len(self.txItems):
            return

        selectedItem = self.txItems[lineIndex]
        nodes = selectedItem[3]

        cmds.select(clear=True)

        print (selectedItem[0] + '('+selectedItem[2]+')')
        print 'Used by file node(s) : '

        for node in nodes:
            if node:
                print ('  '+node)
                cmds.select(node, add=True)

    
    # Set the variables self.selectedItems, self.filesToCreate, self.filesCreated and self.createdErrors
    #  from the Scroll List selection
    def selectedFilesFromList(self):

        ctrlPath = '|'.join([self.window, 'groupBox', 'listWidget']);
        selectedLines = cmds.textScrollList(ctrlPath, query=True, si=True);
        selectedLinesIdx = cmds.textScrollList(ctrlPath, query=True, sii=True);
        
        self.filesToCreate = 0
        self.filesCreated = 0
        self.createdErrors = 0
        self.selectedItems = []
        
        if not selectedLines:
            updateProgressMessage(self.window, 0, 0, 0)    
            return
        
        list = cmds.textScrollList(ctrlPath, query=True, ai=True);
        lineIndex = 0

        for i in range(len(selectedLines)):
            lineText = selectedLines[i]
            
            #if python allows a better way to do this (find the index of this element), please get rid of this hash
            lineIndex = self.lineIndex[lineText]

            # all my information is in self.txItems[lineIndex]
            if lineIndex >= len(self.txItems):
                # shouldn't happen !
                continue

            self.selectedItems.append(self.txItems[lineIndex])
            texture = self.selectedItems[i][0]
            
            self.filesToCreate += len(self.selectedItems[i][4])
            
        updateProgressMessage(self.window, self.filesCreated, self.filesToCreate, 0)
        ctrlPath = '|'.join([self.window, 'groupBox_3', 'label_10']);
        cmds.text(ctrlPath, edit=True, label="");
        
    # Set the variables self.selectedItems, self.filesToCreate, self.filesCreated and self.createdErrors
    #  from the Folder selected
    def selectedFilesFromFolder(self, *args):
        ctrlPath = '|'.join([self.window, 'groupBox_4', 'lineEdit_2']);
        folder = cmds.textField(ctrlPath, query=True, text=True);
        
        self.selectedItems = []
        
        self.filesToCreate = 0
        self.filesCreated = 0
        self.createdErrors = 0
        
        ctrlPath = '|'.join([self.window, 'groupBox_4', 'checkBox']);
        recursive = cmds.checkBox(ctrlPath, query=True, value=True);
        
        self.selectedItems = []
        if os.path.isdir(folder):
            if recursive:
                for root, dirs, files in os.walk(folder):
                    for texture in files:
                        if (isImage(texture)):
                            inputFile = os.path.join(folder, texture)
                            colorSpace = cmds.colorManagementFileRules(evaluate=inputFile)
                            item = [os.path.join(root, texture), 0, colorSpace, '', [inputFile]]
                            self.selectedItems.append(item)
                            self.filesToCreate += 1
            else:
                files = os.listdir(folder)
                for texture in files:
                    if (isImage(texture)):
                        inputFile = os.path.join(folder, texture)
                        colorSpace = cmds.colorManagementFileRules(evaluate=inputFile)
                        item = [os.path.join(folder, texture), 0, colorSpace, '', [inputFile]]
                        self.selectedItems.append(item)
                        self.filesToCreate += 1
                
        updateProgressMessage(self.window, self.filesCreated, self.filesToCreate, 0)
        ctrlPath = '|'.join([self.window, 'groupBox_3', 'label_10']);
        cmds.text(ctrlPath, edit=True, label="");


    # Open a dialog to select a folder and update the information about it
    def selectFolder(self, *args):
        ctrlPath = '|'.join([self.window, 'groupBox_4', 'lineEdit_2']);
        folder = cmds.textField(ctrlPath, query=True, text=True);
        if not os.path.isdir(folder):
            folder = cmds.workspace(query=True, directory=True)     
        ret = cmds.fileDialog2(cap='Select Folder',okc='Select',fm=2, startingDirectory=folder)
        if ret is not None and len(ret):
            ctrlPath = '|'.join([self.window, 'groupBox_4', 'lineEdit_2']);
            cmds.textField(ctrlPath, edit=True, text=ret[0]);
            self.selectedFilesFromFolder()
    

    # Delete the processed .tx files selected
    def deleteTx(self, *args):
        ctrlPath = '|'.join([self.window, 'radioButton']);
        selection = cmds.radioButton(ctrlPath, query=True, select=True);
        
        self.deletedFiles = 0
        ctrlPath = '|'.join([self.window, 'groupBox_3', 'label_10']);
        
        if selection:
            self.selectedFilesFromList()
        else:
            self.selectedFilesFromFolder()

        if not self.selectedItems:
            cmds.text(ctrlPath, edit=True, label="Deleted: {0}".format(self.deletedFiles));
            return
            
        for textureLine in self.selectedItems:
            texture = textureLine[0]
            if not texture:
                continue;

            # loop over the previously listed files
            for inputFile in textureLine[4]:
                txFile = os.path.splitext(inputFile)[0]+".tx"
                if os.path.isfile(txFile):
                    AiTextureInvalidate(txFile)
                    os.remove(txFile)
                    self.deletedFiles += 1

            cmds.text(ctrlPath, edit=True, label="Deleted: {0}".format(self.deletedFiles));
        self.updateList()
   
    # Create the processed .tx files in another thread to avoid locking the UI
    def createTx(self, *args):
        if not self.thread:
            self.thread = MakeTxThread(self)
            self.thread.start()

