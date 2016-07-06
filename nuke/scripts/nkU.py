import os
import re
import subprocess
import datetime


def pathJoin(*args):
    return normPath(os.path.join(*args))

def normPath(p):
    return os.path.normpath(p).replace("\\",'/')





class LogBuilder():
    
    def __init__(self,gui=True, funcName ="", logL = None, resultB = True, logFile = ""):
        self.gui = gui
        if not logL:
            logL = []
        self.funcName = funcName
        self.logL = logL
        self.resultB = resultB
        self.logFile = logFile
        if self.funcName:
            self.funcName = "'"+self.funcName+"' "

        if self.logFile:
            print "toto"

    def printL(self,style = "i",msg = "", guiPopUp = False ):
        self.style = style
        self.msg = msg

        if not self.gui:
            self.guiPopUp = False
        else:
            self.guiPopUp = guiPopUp

      
        if self.style == "t":
            self.formMsg = '\n----------- '+self.msg    
        elif self.style == "e":
            self.formMsg = "#### {:>7}: {}{}".format("Error",self.funcName,self.msg)
            #if self.guiPopUp: mc.confirmDialog( title='Error: '+self.funcName, message=self.msg, button=['Ok'], defaultButton='Ok' )
            self.resultB = False
        elif self.style == "w":
            self.formMsg = "#### {:>7}: {}{}".format("Warning",self.funcName,self.msg)
            #if self.guiPopUp: mc.confirmDialog( title='Warning: '+self.funcName, message=self.msg, button=['Ok'], defaultButton='Ok' )
        elif self.style == "i":
            self.formMsg = "#### {:>7}: {}{}".format("Info",self.funcName,self.msg)
            #if self.guiPopUp: mc.confirmDialog( title='Info: '+self.funcName, message=self.msg, button=['Ok'], defaultButton='Ok' )
        else:
            self.formMsg = "{}{}".format(self.funcName,self.msg)


        print self.formMsg

        self.logL.append(self.formMsg)
    

class dataFile():
    def __init__(self, fileNameS= "", gui = True):
        fileNameS=normPath(fileNameS)

        if os.path.isfile(fileNameS):
            fileNameL=fileNameS.split("/")
            if "private" in fileNameL and "shot" in fileNameL:
                fileDataL = fileNameS.split("private/")[-1].split("/")
                self.location = "private"
                self.user = fileDataL[0]
                self.proj = fileDataL[1]
                self.typ = fileDataL[2]
                self.seq = fileDataL[3]
                self.shot = fileDataL[4]
                self.dep = fileDataL[5]
                self.depSub = fileDataL[6]
                if "render-v"in fileDataL[6]:
                    renderDir = fileDataL[6]
                    if len(fileDataL)>=6: self.passName = fileDataL[7]
                    if len(fileDataL)>=7: self.layerName = fileDataL[8]
                    if len(fileDataL)>=8: 
                        self.imageName = fileDataL[9]
                        self.imageFormat = fileDataL[9].split('.')[-1]
                        self.imageNumber = fileDataL[9].split('.')[-2]

        else:
            print "prout"

