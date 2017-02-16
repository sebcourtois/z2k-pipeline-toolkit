import os
import re
import subprocess
import datetime
import nuke
import errno
#cat plante en mode nuke render
#from davos.core.damproject import DamProject
from pprint import pprint
import shutil


# rappel
# os.environ["ZOMB_ASSET_PATH"] = zombRootPath+"/zomb/asset"
# os.environ["ZOMB_SHOT_PATH"] = zombRootPath+"/zomb/shot"
# os.environ["ZOMB_OUTPUT_PATH"] = zombRootPath+"/zomb/output"
# os.environ["ZOMB_OUTPUT_PATH_BIS"] = '\\\\ZOMBIWALK\\Projects\\zomb\\outputBis'
# os.environ["ZOMB_MISC_PATH"] = zombRootPath+"/zomb/misc"
# os.environ["ZOMB_TOOL_PATH"] = zombRootPath+"/zomb/tool"
# os.environ["ZOMB_SHOT_LOC"] = zombRootPath+"/private/"+userName+"/zomb/shot"



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
            if self.guiPopUp: nuke.message("Error: "+self.msg)
            self.resultB = False
        elif self.style == "w":
            self.formMsg = "#### {:>7}: {}{}".format("Warning",self.funcName,self.msg)
            if self.guiPopUp: nuke.message("Warning: "+self.msg)
        elif self.style == "i":
            self.formMsg = "#### {:>7}: {}{}".format("Info",self.funcName,self.msg)
            if self.guiPopUp: nuke.message("Info: "+self.msg)
        else:
            self.formMsg = "{}{}".format(self.funcName,self.msg)


        print self.formMsg
        nuke.tprint(self.formMsg)

        self.logL.append(self.formMsg)
    

class dataFile():
    def __init__(self, fileNameS= "", gui = True):
        self.log = LogBuilder(gui=gui, logL = [])
        if not fileNameS:
            fileNameS = nuke.root().knob('name').value()
            if "finalLayoutTemplate.nk" in fileNameS:
                fileNameS=  nuke.root()["argv0"].getValue()

        if nuke.GUI:
			from zomblib import damutils
			from davos.core.damproject import DamProject
			proj = DamProject("zombillenium", empty=(not nuke.GUI))
			proj.loadEnviron()


        self.fileNameS=normPath(fileNameS)
        self.gui = gui

        self.location = ""
        self.user = []
        self.proj = []
        self.typ = []
        self.seq = []
        self.shot = []
        self.depDir = []
        self.depDirSub = []
        self.passName = ""
        self.layerName = ""
        self.imageName = ""
        self.imageFormat = ""
        self.imageNumber = ""
        self.ver = ""
        self.increment = ""
        self.stepS = ""

        #if os.path.isfile(self.fileNameS) or os.path.isdir(self.fileNameS):
        fileNameL=self.fileNameS.split("/")
        self.stepS = fileNameL[-1].split("-v")[0].split("_")[-1]
        if "private" in fileNameL and "shot" in fileNameL:
            fileDataL = self.fileNameS.split("private/")[-1].split("/")
            self.location = "private"
            self.user = fileDataL[0]
            self.proj = fileDataL[1]
            self.typ = fileDataL[2]
            self.seq = fileDataL[3]
            self.shot = fileDataL[4]
            self.depDir = fileDataL[5]
            self.depDirSub = fileDataL[6]
            if "render-v"in fileDataL[6]:
                renderDir = fileDataL[6]
                if len(fileDataL)>7: self.passName = fileDataL[7]
                if len(fileDataL)>8: self.layerName = fileDataL[8]
                if len(fileDataL)>9: 
                    self.imageName = fileDataL[9]
                    self.imageFormat = fileDataL[9].split('.')[-1]
                    self.imageNumber = fileDataL[9].split('.')[-2]
                self.ver = fileDataL[6].replace("render-v","")

            elif "compo-v" in fileDataL[6]:
                self.ver = fileDataL[6].split("compo-v")[-1].split(".")[0]
                self.increment = fileDataL[6].split("compo-v")[-1].split(".")[1]
            elif "stereo-v" in fileDataL[6]:
                self.ver = fileDataL[6].split("stereo-v")[-1].split(".")[0]
                self.increment = fileDataL[6].split("stereo-v")[-1].split(".")[1]
            elif "precomp-v" in fileDataL[6]:
                self.ver = fileDataL[6].split("precomp-v")[-1].split(".")[0]
                self.increment = fileDataL[6].split("precomp-v")[-1].split(".")[1]
        if nuke.GUI:
            damShot = proj.getShot(self.shot)
            sgShot = damShot.getSgInfo()
            duration = damutils.getShotDuration(sgShot)
            self.timeIn = 101
            self.timeOut = self.timeIn + (duration-1)
        else:
            self.timeIn = 0
            self.timeOut = 0
        #else:
            #txt = "is not a file: '{}'".format(self.fileNameS)
            #self.log.printL("e", txt)


    def printData(self):
        self.log = LogBuilder(gui=self.gui, funcName ="")
        self.log.printL("","fileNameS: '{}'".format(self.fileNameS))
        self.log.printL("","step: '{}'".format(self.stepS))
        self.log.printL("","location: '{}'".format(self.location))
        self.log.printL("","user: '{}'".format(self.user))
        self.log.printL("","proj: '{}'".format(self.proj))
        self.log.printL("","typ: '{}'".format(self.typ))
        self.log.printL("","seq: '{}'".format(self.seq))
        self.log.printL("","shot: '{}'".format(self.shot))
        self.log.printL("","depDir: '{}'".format(self.depDir))
        self.log.printL("","in: '{}'".format(self.timeIn))
        self.log.printL("","out: '{}'".format(self.timeOut))

        if "render-v"in self.depDirSub:
            self.log.printL("","passName: '{}'".format(self.passName))
            self.log.printL("","layerName: '{}'".format(self.layerName))
            self.log.printL("","imageName: '{}'".format(self.imageName))
            self.log.printL("","imageFormat: '{}'".format(self.imageFormat))
            self.log.printL("","imageNumber: '{}'".format(self.imageNumber))
            self.log.printL("","ver: '{}'".format(self.ver))
        elif "compo-v" in self.depDirSub or "stereo-v" in self.depDirSub:
            self.log.printL("","ver: '{}'".format(self.ver))
            self.log.printL("","increment: '{}'".format(self.increment))

    def initNukeEnvVar(self):
        if self.seq and self.shot and self.user and self.depDir:

            departementS =self.depDir

            if self.seq in ["sq0350","sq0520","sq0230","sq0530","sq0300","sq0150","sq0170","sq0450"]:
                try:
                    os.environ["ZOMB_OUTPUT_PATH"] = normPath(os.environ["ZOMB_OUTPUT_PATH_BIS"])
                except:
                    print "#### warning : 'ZOMB_OUTPUT_PATH_BIS' is not defined"
                    if  "zombidamas" in os.environ["ZOMB_OUTPUT_PATH"]:
                        print "#### warning : 'ZOMB_OUTPUT_PATH' = //JAKKU/zombillenium2/output"
                        os.environ["ZOMB_OUTPUT_PATH"] ="//JAKKU/zombillenium2/output"



            outputDirS = os.environ["ZOMB_OUTPUT_PATH"]+"/"+self.seq+"/"+self.shot
            shotDirS = os.environ["ZOMB_SHOT_PATH"]+"/"+self.seq+"/"+self.shot

            #privateDirS = os.environ["PRIV_ZOMB_SHOT_PATH"].replace("/$DAVOS_USER/","/"+self.user+"/")+"/"+self.seq+"/"+self.shot #PRIV_ZOMB_SHOT_PATH introuvable en batch
            privateDirS = normPath(os.environ["ZOMB_PRIVATE_LOC"])+"/private/"+self.user+"/zomb/shot/"+self.seq+"/"+self.shot
    

            miscDirS = os.environ["ZOMB_MISC_PATH"]
            self.log.printL("","initialising environnement variables")
            self.log.printL("","SEQ: "+self.seq)
            self.log.printL("","SHOT: "+self.shot)
            self.log.printL("","VER: "+self.ver)
            self.log.printL("","INC: "+self.increment)
            self.log.printL("","USER: "+self.user)
            self.log.printL("","DEP: "+departementS)
            self.log.printL("","OUTPUT_DIR: "+outputDirS)
            self.log.printL("","SHOT_DIR: "+shotDirS)
            self.log.printL("","PRIV_DIR: "+privateDirS)
            self.log.printL("","MISC_DIR: "+miscDirS)
            self.log.printL("","STEP: "+self.stepS)
            self.log.printL("","TIMEIN: '{}'".format(self.timeIn))
            self.log.printL("","TIMEOUT: '{}'".format(self.timeOut))
            os.environ["SEQ"] = self.seq
            os.environ["VER"] = self.ver
            os.environ["INC"] = self.increment
            os.environ["SHOT"] = self.shot
            os.environ["USER"] = self.user
            os.environ["DEP"] = departementS
            os.environ["OUTPUT_DIR"] = outputDirS
            os.environ["SHOT_DIR"] = shotDirS
            os.environ["PRIV_DIR"] = privateDirS
            os.environ["MISC_DIR"] = miscDirS
            os.environ["STEP"] = self.stepS
            os.environ["TIMEIN"] = str(self.timeIn)
            os.environ["TIMEOUT"] = str(self.timeOut)

            if nuke.GUI:
                nuke.Root()['first_frame'].setValue(self.timeIn)
                nuke.Root()['last_frame'].setValue(self.timeOut)

                self.log.printL("","setting 'first_frame={}', 'first_frame={}' : ".format(self.timeIn,self.timeOut))

        else:
            txt = "one of the variable 'seq', 'shot', 'user' or 'dep' is undefined, could not set nuke proj environment var".format(self.fileNameS)
            self.log.printL("e", txt)
            self.log.printL("e", "Make sure your nuke scropt is saved in a valid private directory")
            nuke.message("Error: cannot initialise Nuke environnement variable, make sure your nuke scropt is saved in a valid private directory")



def initNukeShot(fileNameS= ""):
    try:
        print "runing: 'initNukeShot()'"
        df=dataFile(fileNameS)
        df.printData()
        df.initNukeEnvVar()
    except Exception,err:
        print "warning: error while running 'initNukeShot()'"
        print err


def createCompoBatchFiles():
    initNukeShot()
    if os.environ["DEP"] == '08_render' or os.environ["DEP"] == '10_compo':
        createNukeBatchMovie(gui=False)
        createPublishBat(gui=False)



def conformFilePath(filePathS = "", gui = True):
    log = LogBuilder(gui=gui, funcName ="formatImagePath")

    fileNameS = filePathS.split("/")[-1]
    if len(fileNameS.split(".")) == 3 and fileNameS.split(".")[-1] != "mov":
        newFileNameS = fileNameS.split(".")[0]+".%04d."+fileNameS.split(".")[2]
        filePathS= filePathS.replace(fileNameS,newFileNameS)

    insensitive_projWinDir = re.compile(re.escape("P:/"), re.IGNORECASE)
    filePathS =  insensitive_projWinDir.sub("//ZOMBIWALK/Projects/", filePathS)

    insensitive_z2kWinDir = re.compile(re.escape("Z:/"), re.IGNORECASE)
    filePathS =  insensitive_z2kWinDir.sub("//ZOMBIWALK/z2k/", filePathS)

    filePathS = filePathS.replace("left", "%V")
    filePathS = filePathS.replace("right", "%V")

    filePathOrigS = str(filePathS)
    if "output" in filePathS:
        insensitive_outShotDir = re.compile(re.escape(os.environ["OUTPUT_DIR"]), re.IGNORECASE)
        filePathS =  insensitive_outShotDir.sub("[getenv OUTPUT_DIR]", filePathS)

        insensitive_outMiscDir = re.compile(re.escape(os.environ["MISC_DIR"]), re.IGNORECASE)
        filePathS =  insensitive_outMiscDir.sub("[getenv MISC_DIR]", filePathS)

        insensitive_zombOutPath = re.compile(re.escape(os.environ["ZOMB_OUTPUT_PATH"]), re.IGNORECASE)
        filePathS =  insensitive_zombOutPath.sub("[getenv ZOMB_OUTPUT_PATH]", filePathS)

        insensitive_shotDir = re.compile(re.escape(os.environ["SHOT"]), re.IGNORECASE)
        filePathS =  insensitive_shotDir.sub("[getenv SHOT]", filePathS)

    return filePathS




def conformReadNode(readNodeL=[], gui=True, conformPathB = True, createEmptyRightLayers = False, changeOnErrorI = 99, switchToLastVer = False):
    log = LogBuilder(gui=gui, funcName ="conformReadNode")

    #0 : error
    #1 : black
    #2 : checkerboard
    #3 : nearest frame
    #99: do not change

    filePathOrigS=""
    filePathNewS = ""
    unvalidNodeL = []
    validNodeL = []


    def setAsUnvalid(errorMsgS = "",nodeNameS = ""):
        log.printL("e","{}: '{}'".format(errorMsgS,nodeNameS))
        each['tile_color'].setValue(3631284479) # orange
        nuke.toNode(nodeNameS).setName("Read")
        each['label'].setValue(errorMsgS)



    def setAsMono(monoB=False, nodeO=""):
        labelS = nodeO['label'].getValue()
        if not "MONO" in labelS and monoB:
            nodeO['label'].setValue("MONO\n"+labelS)
        if "MONO" in labelS and not monoB:
            nodeO['label'].setValue(labelS.replace("MONO",""))
           


    for each in readNodeL:
        eachNameS = each['name'].getValue()
        isMonoB=False
        if changeOnErrorI != 99:
            eachOnErrorI = changeOnErrorI
            each['on_error'].setValue(eachOnErrorI)

        else:
            eachOnErrorI = int(each['on_error'].getValue()) #0 : error  #1 : black #2 : checkerboard #3 : nearest frame

        if 'read_exr' in eachNameS or 'read_comp' in eachNameS:
            log.printL("i","skipping output node: '{}'".format(eachNameS))
            continue
        if each['disable'].getValue() == 1:
            log.printL("i","skipping disabled node: '{}'".format(eachNameS))
            continue

        filePathExpS = nuke.filename(each)
        if not filePathExpS:
            setAsUnvalid(errorMsgS = "Undefined file path",nodeNameS = eachNameS)
            unvalidNodeL.append(each)
            continue

        imgNameS = os.path.basename(filePathExpS)
        if len(imgNameS.split("."))!=3:
            setAsUnvalid(errorMsgS = "Wrong image format",nodeNameS = eachNameS)
            unvalidNodeL.append(each)
            continue


        # conform node name and label
        layerDirS= filePathExpS.split("/")[-2]
        if "-v" in layerDirS:
            verS = str(layerDirS.split("-v")[-1])
        else:
            verS = ""

        newEachNameS = str(layerDirS.split("-v")[0])
        nuke.toNode(eachNameS).setName(newEachNameS+"_0")
        newEachNameS=each['name'].getValue()


        #get the last version published
        lastVerS=""
        lastVersLyrS=""        
        if "_version" in filePathExpS and "/output/" in filePathExpS:
            filePathExpTmpS = filePathExpS.replace("%V","left")
            versionPathS = os.path.dirname(os.path.dirname(filePathExpTmpS))
            itemDirL = os.listdir(versionPathS)
            lyrBaseNameS=layerDirS.split("-v")[0]
            layerDirL = []
            for eachItem in itemDirL:
                if lyrBaseNameS == eachItem.split("-v")[0]:
                    layerDirL.append(eachItem)
            layerDirL.sort()
            if layerDirL:
                lastVersLyrS = layerDirL[-1]
                lastVerS = str(lastVersLyrS.split("-v")[-1])

        # conform file path
        filePathOrigS = each['file'].getValue()
        filePathNewS = conformFilePath(filePathS = filePathOrigS, gui = gui)
        if switchToLastVer and lastVerS and lastVerS!=verS:
            filePathNewS=filePathNewS.replace(verS,lastVerS)
            verS = str(lastVerS)



        if filePathNewS and conformPathB:
            if filePathNewS !=filePathOrigS:
                log.printL("i","'{}' {}".format(newEachNameS, filePathOrigS))
                log.printL("i","'{}' --> {}".format(newEachNameS, filePathNewS))
                each['file'].setValue(filePathNewS)


        if "%V" in filePathExpS or "/left/" in filePathExpS or "/right/" in filePathExpS:
            filePathExpLeftS = filePathExpS.replace(r"%V","left")
            filePathExpRightS = filePathExpS.replace(r"%V","right").replace("/left/","/right/")
            #create empty right directory if missing
            fileDirS = os.path.dirname(filePathExpRightS)
            if not os.path.isdir(fileDirS):
                os.makedirs(fileDirS)


            if createEmptyRightLayers:
                if not os.path.isdir(os.path.dirname(filePathExpRightS)) and not  "/output/" in filePathExpRightS:
                    os.makedirs(os.path.dirname(filePathExpRightS))

            fileDirS = os.path.dirname(filePathExpLeftS)
            if not os.path.isdir(fileDirS):
                setAsUnvalid(errorMsgS = "missing left directory",nodeNameS = newEachNameS)
                unvalidNodeL.append(each)
                continue


            resultLeftD = getImgSeqInfo(filePathExpLeftS, nodeNameS= newEachNameS,gui=gui)
            resultRightD = getImgSeqInfo(filePathExpRightS, nodeNameS= newEachNameS,gui=gui)

            each['first'].setValue(resultLeftD["firstImgI"])
            each['last'].setValue(resultLeftD["lastImgI"])

            if resultRightD["frameNumberI"]==0:                   
                setAsMono(monoB=True, nodeO=each)
                isMonoB =True
            else:
                setAsMono(monoB=False, nodeO=each)
                isMonoB =False

            if resultLeftD["frameNumberI"]==0:
                txt="No left frames found"
                setAsUnvalid(errorMsgS = txt,nodeNameS = newEachNameS)
                unvalidNodeL.append(each)
                continue

            if resultLeftD["frameNumberI"]!=resultRightD["frameNumberI"] and not isMonoB:
                txt="'{}' missmaching frame number: left '{}', right '{}'' ".format(newEachNameS, resultLeftD["frameNumberI"], resultRightD["frameNumberI"])
                setAsUnvalid(errorMsgS = txt,nodeNameS = newEachNameS)
                unvalidNodeL.append(each)
                continue

            if resultLeftD["firstImgI"] != resultRightD["firstImgI"]and not isMonoB:                   
                txt="First frame stereo missmach: left '{}', right '{}'' ".format(newEachNameS, resultLeftD["firstImgI"], resultRightD["firstImgI"])
                setAsUnvalid(errorMsgS = txt,nodeNameS = newEachNameS)
                unvalidNodeL.append(each)
                continue

            if resultLeftD["lastImgI"] != resultRightD["lastImgI"]and not isMonoB:
                txt="Last frame stereo missmach: left '{}', right '{}'' ".format(newEachNameS, resultLeftD["lastImgI"], resultRightD["lastImgI"])
                setAsUnvalid(errorMsgS = txt,nodeNameS = newEachNameS)
                unvalidNodeL.append(each)
                continue

            if resultLeftD["missingFrameL"] and eachOnErrorI == 0:
                txt="'{}' missing frames left seq: {} ".format(newEachNameS, resultLeftD["missingFrameL"])
                setAsUnvalid(errorMsgS = txt,nodeNameS = newEachNameS)
                unvalidNodeL.append(each)
                continue

            if resultRightD["missingFrameL"] and eachOnErrorI == 0:
                txt="'{}' missing frames right seq: {} ".format(newEachNameS, resultRightD["missingFrameL"])
                setAsUnvalid(errorMsgS = txt,nodeNameS = newEachNameS)
                unvalidNodeL.append(each)
                continue

        else:
            resultD = getImgSeqInfo(filePathExpS, nodeNameS= newEachNameS, gui=gui)

            if resultD["frameNumberI"]==0:
                txt="No frames found"
                setAsUnvalid(errorMsgS = txt,nodeNameS = newEachNameS)
                unvalidNodeL.append(each)
                continue

            each['first'].setValue(resultD["firstImgI"])
            each['last'].setValue(resultD["lastImgI"])
            if resultD["missingFrameL"] and eachOnErrorI == 0:
                txt="'{}' missing frames: {} ".format(newEachNameS, resultD["missingFrameL"])
                setAsUnvalid(errorMsgS = txt,nodeNameS = newEachNameS)
                unvalidNodeL.append(each)
                continue

            fileDirS = os.path.dirname(filePathExpS)
            if not os.path.isdir(fileDirS):
                setAsUnvalid(errorMsgS = "Unvalid file path",nodeNameS = eachNameS)
                unvalidNodeL.append(each)
                continue


        if verS :
            newLabelS="v"+verS
        else:
            newLabelS = ""
        labelS = each['label'].getValue()
        if not "MONO" in labelS:
            each['label'].setValue(newLabelS)
        if "MONO" in labelS:
           each['label'].setValue("MONO\n"+newLabelS)


        # conform node color
        # print nuke.selectedNode()['tile_color'].getValue()
        if "/output/" in filePathExpS:
            if lastVerS == verS: 
                each['tile_color'].setValue(13172991) # vert
            else:
                each['tile_color'].setValue(5832959) # vert fonce
        elif "/private/" in filePathExpS:
            each['tile_color'].setValue(640082175) #bleu
        else:
            each['tile_color'].setValue(0) #gris neutre 

        validNodeL.append(each)

    if gui:
        unvalidNodeNameL=[]
        validNodeNameL=[]
        if unvalidNodeL:
            for each  in unvalidNodeL:
                unvalidNodeNameL.append(each['name'].getValue())
        if validNodeL:
            for each  in validNodeL:
                validNodeNameL.append(each['name'].getValue())
        if unvalidNodeNameL:
            txt1 = "'{}' unvalid nodes found".format(len(unvalidNodeNameL))
            txt2 = "'{}' nodes checked succesfully".format(len(validNodeNameL))
            nuke.message("Error:\n"+txt1+"\n"+txt2+"\nPlease read the log for more details")
        else:
            txt1 = "'{}' nodes checked succesfully".format(len(validNodeNameL))
            nuke.message("Info:\n"+txt1+"\nPlease read the log for more details")

        print ""
        print "---- LOG RESUME"
        txt = "'{}' unvalid nodes found: {} ".format(len(unvalidNodeNameL), unvalidNodeNameL)
        log.printL("i",txt)
        txt = "'{}' nodes checked succesfully: {} ".format(len(validNodeNameL), validNodeNameL)
        log.printL("i",txt)

    return dict(resultB=log.resultB, logL=log.logL)




def getImgSeqInfo(filePathS = "", nodeNameS ="", gui = True):
    log = LogBuilder(gui=gui, funcName ="getImgSeqInfo")
    imgNumL= []
    missingFrameL =[]
    frameNumberI = 0
    lastImgI = 0
    firstImgI = 0
    imgNameS = os.path.basename(filePathS)
    imgRadS = imgNameS.split(".")[0]
    imgExtS = imgNameS.split(".")[-1]

    if len(imgNameS.split("."))!=3:
        log.printL("e","'{}' Could not find a 'name.####.ext' image sequence: '{}'".format(nodeNameS,filePathS))
        return dict(resultB=log.resultB, logL=log.logL, firstImgI=0, lastImgI=0, missingFrameL=missingFrameL, frameNumberI=0)

    fileDirS = os.path.dirname(filePathS)
    itemDirL = os.listdir(fileDirS)
    for each in itemDirL:
        eachSplitL = each.split(".")
        if  len(eachSplitL)==3 and eachSplitL[0]==imgRadS and eachSplitL[-1]==imgExtS:
            try:
                imgNumL.append(int(eachSplitL[1]))
            except Exception,err:
                txt = "eachSplitL : {} ".format(eachSplitL)
                log.printL("e",txt)

    if not imgNumL:
        if not "/right/" in filePathS:
            log.printL("e","'{}' No sequ found in: '{}'".format(nodeNameS, fileDirS))
        else:
            log.printL("w","'{}' No sequ found for right camera: '{}'".format(nodeNameS, fileDirS))
        return dict(resultB=log.resultB, logL=log.logL, firstImgI=firstImgI, lastImgI=lastImgI, missingFrameL=missingFrameL, frameNumberI=0)

    imgNumL.sort()
    firstImgI = imgNumL[0]
    lastImgI= imgNumL[-1]

    missingFrameI = lastImgI-firstImgI+1-len(imgNumL)
    missingFrameL = []
    if missingFrameI:
        n = int (firstImgI)
        while n<lastImgI:
            if n not in imgNumL:
                missingFrameL.append(n)
            n+=1

    return dict(resultB=log.resultB, logL=log.logL, firstImgI=firstImgI, lastImgI=lastImgI, missingFrameL=missingFrameL, frameNumberI=len(imgNumL))



def publishLayer(layerPathS = "",destination = "output", comment="my comment", gui = True, dryRun = False):
    log = LogBuilder(gui=gui, funcName ="publishLayer")
    from davos.core.damproject import DamProject

    def moveLayer2output(layerPathS="", publishDirS="", gui = True):
        publishedLayerL=[]
        layerNameS = os.path.basename(layerPathS)
        versionDirS = publishDirS+"/_version"

        #get the nextversion layer name
        if not os.path.isdir(versionDirS):
            os.makedirs(versionDirS)
            nextVersionS = "v001"
            layerNameNextVerS = layerNameS+"-v001"
        else:
            itemDirL = os.listdir(versionDirS)
            for each in itemDirL:
                if layerNameS+"-v" in each:
                    publishedLayerL.append(each)
            publishedLayerL.sort()
            if publishedLayerL:
                verI = int(publishedLayerL[-1].split("-v")[-1])
                nextVersionS = "v"+'{0:03d}'.format(verI+1)
                layerNameNextVerS = layerNameS+"-"+nextVersionS
            else:
                layerNameNextVerS = layerNameS+"-v001"
            
        if not dryRun:
            try:
                os.rename(layerPathS, versionDirS+"/"+layerNameNextVerS)
            except OSError:
                shutil.move(layerPathS, versionDirS+"/"+layerNameNextVerS)
        return layerNameNextVerS

    proj = DamProject("zombillenium")
    outLib=proj.getLibrary("public","output_lib")
    shotLib=proj.getLibrary("public","shot_lib")

    #damShot = proj.getShot("sq6660_sh0010a")
    #publishDir.dbPath()

    if "/left/" in layerPathS:
        camDirS = "/left"
    elif "/right/" in layerPathS:
        camDirS = "/right"
    else:
        camDirS = ""

    if destination ==  "output":
        outDirS = os.environ["OUTPUT_DIR"]+camDirS
        if not os.path.isdir(outDirS):
            os.makedirs(outDirS)
        #publishDir = outLib.getEntry(outDirS)
        lib=outLib
        publishDirS = outDirS
    elif destination ==  "shot":
        shotDirS = os.environ["SHOT_DIR"]+"/"+os.environ["DEP"]+camDirS
        if not os.path.isdir(shotDirS):
            os.makedirs(shotDirS)
        #publishDir = shotLib.getEntry(shotDirS)
        publishDirS = shotDirS
        lib = shotLib

    #publishHeadDir = publishDir.absPath()

    newVersion = None
    if destination != "output":
        publishDir = lib.getEntry(publishDirS)
        _ , newVersion = publishDir.publishFile(layerPathS, autoLock=True, autoUnlock=True, comment=comment, dryRun=dryRun, saveChecksum=False, version=int(os.environ["VER"]))
        publishLastVersDir = newVersion.absPath() #publishDir.absPath()+"/_version/"+newVersion.name
    else:
        newVersionNameS = moveLayer2output(layerPathS, publishDirS)
        publishLastVersDir = publishDirS+"/_version/"+newVersionNameS


    log.printL("i","Published layer: '{}'".format(publishDirS)) 
    return dict(resultB=log.resultB, logL=log.logL, publishHeadDir = publishDirS, publishLastVersDir= publishLastVersDir, publishedVersion=newVersion)





def publishFile(fileNameS = "", comment="test",dryRun=False, gui = True):
    log = LogBuilder(gui=gui, funcName ="publishFile")
    from davos.core.damproject import DamProject

    proj = DamProject("zombillenium")
    shotLib=proj.getLibrary("public","shot_lib")

    #damShot = proj.getShot("sq6660_sh0010a")
    #publishDir.dbPath()


    shotDirS = os.environ["SHOT_DIR"]+"/"+os.environ["DEP"]
    if not os.path.isdir(shotDirS):
        os.makedirs(shotDirS)
    publishDir = shotLib.getEntry(shotDirS)


    _ , newVersion = publishDir.publishFile(fileNameS, autoLock=True, autoUnlock=True, comment=comment, dryRun=dryRun, saveChecksum=False)

    publishHeadDir = publishDir.absPath()
    publishLastVersDir = publishDir.absPath()+"/_version/"+newVersion.name
    log.printL("i","Published file: '{}'".format(publishHeadDir))

    return dict(resultB=log.resultB, logL=log.logL, publishHeadDir = publishHeadDir, publishLastVersDir= publishLastVersDir)




def publishNode(readNodeL=[],dryRun=False, destination = "output", gui = True, guiPopUp = False, commentS = "", conformFirstB = False):
    log = LogBuilder(gui=gui, funcName ="publishNode")

    toPubNodeL=[]
    publishedNodeL = []
    publishedNodeNameL = []
    skippedNodeNameL = []
    resultD={"publishedVersion":""}

    allViewerL = nuke.allNodes('Viewer')
    for each in allViewerL:
        nuke.delete(each)

    for each in readNodeL:
        eachNameS = each['name'].getValue()

        filePathExpS = nuke.filename(each)
        if not filePathExpS:
            log.printL("i","skipping, undefined file path: '{}'".format(eachNameS))
            skippedNodeNameL.append(eachNameS)
            continue

        if each['disable'].getValue() == 1:
            log.printL("i","skipping disabled node: '{}'".format(eachNameS))
            skippedNodeNameL.append(eachNameS)
            continue

        lyrDirNameS = os.path.dirname(filePathExpS)

        if "%V" in lyrDirNameS:
            lyrDirNameLeftS = lyrDirNameS.replace("%V","left")
            if not os.path.isdir(lyrDirNameLeftS):
                log.printL("i","skipping, missing directory: '{}', '{}'".format(eachNameS,lyrDirNameLeftS))
                skippedNodeNameL.append(eachNameS)
                continue
            lyrDirNameRightS = lyrDirNameS.replace("%V","right")
            if not os.path.isdir(lyrDirNameRightS):
                #os.makedirs(os.path.dirname(filePathRightS))
                log.printL("i","skipping, missing directory: '{}', '{}'".format(eachNameS,lyrDirNameRightS))
                skippedNodeNameL.append(eachNameS)
                continue
        else:
            if not os.path.isdir(lyrDirNameS):
                log.printL("i","skipping, missing directory: '{}', '{}'".format(eachNameS,filePathExpS))
                skippedNodeNameL.append(eachNameS)
                continue

        if os.environ["OUTPUT_DIR"] in filePathExpS:
            log.printL("i","skipping, already published: '{}', '{}'".format(eachNameS,filePathExpS))
            skippedNodeNameL.append(eachNameS)
        elif not "lyr_" in lyrDirNameS:
            log.printL("i","skipping, not a layer: '{}', '{}'".format(eachNameS,filePathExpS))
            skippedNodeNameL.append(eachNameS)
        elif "compo-v" in filePathExpS and destination == "output":
            log.printL("i","skipping, '.../compo-vxx/...' has to be published in the 'shot' structure: '{}', '{}'".format(eachNameS,lyrDirNameS))
            skippedNodeNameL.append(eachNameS)
        elif not "/private/" in filePathExpS:
            log.printL("i","skipping, layer must be in a 'private' directory structure: '{}', '{}'".format(eachNameS,lyrDirNameS))
            skippedNodeNameL.append(eachNameS)
        elif "preComp-v" in filePathExpS and destination == "output":
            log.printL("i","skipping, '.../preComp-vxx/...' has to be published in the 'shot' structure: '{}', '{}'".format(eachNameS,lyrDirNameS))
            skippedNodeNameL.append(eachNameS)
        else:
            toPubNodeL.append(each)

    if conformFirstB:
        resultD = conformFileNode(readNodeL=toPubNodeL, gui=gui, conformPathB = False)
        if not resultD["resultB"] or not log.resultB:
            txt= "Can't Publish, some of the nodes are pointing toward unvalid sequences. Please read the log for more detail"
            log.printL("e",txt)
            nuke.message("Error: "+txt)
            return dict(resultB=log.resultB, logL=log.logL)

    if destination == "output":
        commentS == ""
    elif toPubNodeL and not commentS:
        commentS = nuke.getInput("Please enter a publish comment", "")
        if not commentS:
            log.printL("i"," Publish canceled")
            raise RuntimeError("Publish canceled")

    for each in toPubNodeL:
        filePathExpS = nuke.filename(each)
        fileNameS = os.path.basename(filePathExpS)
        layerPathS = os.path.dirname(filePathExpS)
        eachNameS = each['name'].getValue()

        if "left"in layerPathS:
            layerPathS.replace("left","%V")
        elif "right"in layerPathS:
            layerPathS.replace("right","%V")
        
        if "%V"in layerPathS:
            filePathLeftS = layerPathS.replace("%V","left")
            filePathRightS = layerPathS.replace("%V","right")

            resultD = publishLayer(layerPathS = filePathLeftS,comment=commentS,dryRun=dryRun,destination=destination, gui = True)
            publishLayer(layerPathS = filePathRightS,comment=commentS,dryRun=dryRun,destination=destination, gui = True)
            log.printL("i","Publishing stereo layers: '{}', '{}'".format(eachNameS,filePathExpS))
        else:
            resultD = publishLayer(layerPathS = layerPathS,comment=commentS,dryRun=dryRun,destination=destination, gui = True)
            log.printL("i","Publishing: '{}', '{}'".format(eachNameS,filePathExpS))

        publishedNodeL.append(each)
        publishedNodeNameL.append(eachNameS)

        if destination == "output":
            newFileDirExpS = conformFilePath(filePathS=resultD["publishLastVersDir"], gui=gui)
            insensitive_shotDir = re.compile(re.escape(os.environ["SHOT"]), re.IGNORECASE)
            fileNameS =  insensitive_shotDir.sub("[getenv SHOT]", fileNameS)
            newFilePathExpS = newFileDirExpS+"/"+fileNameS
            each['file'].setValue(newFilePathExpS)
            log.printL("i","New path: '{}', '{}'".format(eachNameS,newFilePathExpS))

    conformReadNode(readNodeL=publishedNodeL, gui=False, conformPathB = True)
    print ""
    print "---- LOG RESUME"
    for each in log.logL:
        print each

    print ""
    publishedMsg = "{} file node published : '{}'".format(len(publishedNodeNameL),publishedNodeNameL)
    skippedMsg = "{} file node skipped : '{}'".format(len(skippedNodeNameL),skippedNodeNameL)
    log.printL("i",publishedMsg)
    log.printL("i",skippedMsg)

    #log.printL("i","Nothing to publish", guiPopUp = guiPopUp)
    if guiPopUp:
        nuke.message("Info:\n"+publishedMsg+"\n"+skippedMsg+"\nPlease read the log for more details")

    return dict(resultB=log.resultB, logL=log.logL, publishedVersion=resultD.get("publishedVersion"))




def publishCompo(dryRun=False, gui = True, commentS="", sgVersionData=None):
    log = LogBuilder(gui=gui, funcName ="publishCompo")

    stepS = os.environ["STEP"]

    from davos.core.damproject import DamProject
    proj = DamProject("zombillenium")
    shotLib=proj.getLibrary("public","shot_lib")

    depS = os.environ["DEP"]
    shotS = os.environ["SHOT"]
    verS = os.environ["VER"]
    incS = os.environ["INC"]

    nKFilePathS = nuke.root().knob('name').value()
    nKFileNameS = os.path.basename(nKFilePathS)

    nuke.scriptSave()

    if depS == "10_compo":
        if stepS == "stereo":
            nukeDepSufS = "stereo"
        else:
            nukeDepSufS = "compo"
        movDepSufS = "compo"
    elif depS == "08_render":
        nukeDepSufS = "precomp"
        movDepSufS = "render"
    elif depS == "07_fx3d":
        nukeDepSufS = "fx3d"
        movDepSufS = "compo"

    # testing nuke file name
    nkExpectedFileNameS = shotS+"_"+nukeDepSufS+"-v"+verS
    if nKFileNameS.split(".")[0] != nkExpectedFileNameS:
        txt = "Publish failed, Nuke file name is different from expected name: '{}'".format(nkExpectedFileNameS)
        log.printL("e",txt, guiPopUp = True)
        return

    # testing nuke file extention
    if nKFileNameS.split(".")[-1] != "nk":
        txt = "Publish failed, Nuke file extention must be 'nk', not : '{}'".format( nKFileNameS.split(".")[-1])
        log.printL("e",txt, guiPopUp = True)
        return

    # checking the nuke version is not published already 
    NukePublicFileLastVerS = os.environ["SHOT_DIR"]+"/"+depS+"/_version/"+nkExpectedFileNameS+".nk"
    if os.path.isfile(NukePublicFileLastVerS):
        txt = "Publish failed, this Nuke version is already pubished : '{}'".format(NukePublicFileLastVerS)
        log.printL("e",txt, guiPopUp = True)
        return

    # testing .mov file existence
    if stepS == "stereo":
        movFilePathS = os.path.dirname(nKFilePathS)+"/"+shotS+"_left-v"+verS+"."+incS+".mov"
        if not os.path.isfile(movFilePathS):
            log.printL("e","Publish failed, missing '.mov' : '{}'".format(movFilePathS),guiPopUp = True)
            return
        movFilePathS = os.path.dirname(nKFilePathS)+"/"+shotS+"_right-v"+verS+"."+incS+".mov"
        if not os.path.isfile(movFilePathS):
            log.printL("e","Publish failed, missing '.mov' : '{}'".format(movFilePathS),guiPopUp = True)
            return
    else:
        movFilePathS = os.path.dirname(nKFilePathS)+"/"+shotS+"_"+movDepSufS+"-v"+verS+"."+incS+".mov"
        if not os.path.isfile(movFilePathS):
            log.printL("e","Publish failed, missing '.mov' : '{}'".format(movFilePathS),guiPopUp = True)
            return

    # testing presence of the 'read_exr' node presence (only one alowed) 
    readExrL=[]
    if depS == "10_compo":
        allReadNodeL = nuke.allNodes('Read')
        for each in allReadNodeL:
            eachNameS = each['name'].getValue()
            if "read_exr" in eachNameS or "read_comp" in eachNameS :
                readExrL.append(each)
        if len(readExrL)!=1:
            log.printL("e","Publish failed, several or none 'read_exr/read_comp' node found: '{}'".format( nKFileNameS.split(".")[-1]),guiPopUp = True)
            return

        readNode = readExrL[0]
        readNodeName = readNode['name'].getValue()
        filePathExpS = nuke.filename(readNode)
        if not filePathExpS:
            log.printL("e","Publish failed, undefined file path: '{}'".format(readNodeName),guiPopUp = True)
            return

        if readNode['disable'].getValue() == 1:
            log.printL("e","Publish failed, disabled node: '{}'".format(readNodeName),guiPopUp = True)
            return

        lyrDirNameS = os.path.dirname(filePathExpS)
        if stepS == "stereo":
            if not "%V" in lyrDirNameS:
                log.printL("e","Publish failed, '%V' pattern not found in the 'read_exr' file path : '{}'".format(lyrDirNameS),guiPopUp = True)
                return
            lyrDirNameLeftS = lyrDirNameS.replace("%V","left")
            if not os.path.isdir(lyrDirNameLeftS):
                log.printL("e","Publish failed, missing directory: '{}', '{}'".format(readNodeName,lyrDirNameLeftS),guiPopUp = True)
                return
            lyrDirNameRightS = lyrDirNameS.replace("%V","right")
            if not os.path.isdir(lyrDirNameRightS):
                log.printL("e","Publish failed, missing directory: '{}', '{}'".format(readNodeName,lyrDirNameRightS),guiPopUp = True)
                return
        else:
            if not os.path.isdir(lyrDirNameS):
                log.printL("e","Publish failed, missing directory: '{}', '{}'".format(readNodeName,filePathExpS),guiPopUp = True)
                return
    
    if not commentS:
        commentS = nuke.getInput("Please enter a publish comment", "")
    if not commentS:
        log.printL("i","Publish canceled")
        raise RuntimeError("Publish canceled")

    sgVersionD = None
    try:
        resultD =  proj.publishEditedVersion(nKFilePathS, comment=commentS, returnDict=True, uploadApart=False, sgVersionData=sgVersionData)
        sgVersionD = resultD["sg_version"]
    except Exception as err:
        log.printL("e","Nuke file publish failed: '{}'".format(err),guiPopUp = True)
        raise

    if depS == "10_compo":
        try:
            resultD = publishNode(readNodeL=readExrL,dryRun=False, destination = "shot", gui = True, guiPopUp = False, commentS = commentS)
            if not resultD["resultB"]:
                raise RuntimeError("Publish failed, please read the log for more info")

            pubVersion = resultD["publishedVersion"]
            if sgVersionD and pubVersion:
                p = pubVersion.envPath()+"/"+os.environ["SHOT"]+".@@@@.exr"
                proj.updateSgEntity(sgVersionD, sg_path_to_frames=p)


        except Exception as err:
            log.printL("e","Seq output node publish failed: '{}'".format(err),guiPopUp = True)
            raise
  
    log.printL("i","Published successfully",guiPopUp = True)
    # print pubFile.getLockOwner(refresh=False)


def isStereo():
    viewKnob = nuke.root().knob('views')
    viewKnobS = viewKnob.toScript()
    if "left" in viewKnobS and "right" in viewKnobS:
        stereoB = True
    else:
        stereoB = False
    return stereoB


def createWriteDir():
    initNukeShot()
    myFile = nuke.filename(nuke.thisNode())
    myDir = os.path.dirname( myFile )
    osdir = nuke.callbacks.filenameFilter( myDir )

    if osdir:
        if "%V" in osdir:
            try:                        
                os.makedirs( osdir.replace("%V","left") )        
                os.makedirs( osdir.replace("%V","right") )
            except OSError, e:
                if e.errno != errno.EEXIST:
                    raise
        else:
            try:
                os.makedirs( osdir )
            except OSError, e:
                if e.errno != errno.EEXIST:
                    raise



def inportOutTemplate(template = "compo"):
    if template == "compo":
        nuke.scriptReadFile(os.environ["ZOMB_TOOL_PATH"]+"/template/nuke/outputTemplate.nk")
    elif template == "renderprecomp":
        nuke.scriptReadFile(os.environ["ZOMB_TOOL_PATH"]+"/template/nuke/renderPreCompTemplate.nk")
    elif template == "stereo":
        nuke.scriptReadFile(os.environ["ZOMB_TOOL_PATH"]+"/template/nuke/stereoTemplate.nk")

    for each in nuke.allNodes('Read'):
        eachNameS = each['name'].value()
        if 'read_exr' in eachNameS or 'read_comp'in eachNameS:
            each['first'].setValue(int(os.environ["TIMEIN"]))
            each['last'].setValue(int(os.environ["TIMEOUT"]))
            each['origfirst'].setValue(int(os.environ["TIMEIN"]))
            each['origlast'].setValue(int(os.environ["TIMEOUT"]))



def getStereoInfo(gui = True):
    from pytd.util.fsutils import jsonWrite, jsonRead
    log = LogBuilder(gui=gui, funcName ="getStereoInfo")

    jsonStereoFileS = os.environ["ZOMB_SHOT_PATH"]+"/"+os.environ["SEQ"]+"/"+os.environ["SHOT"]+"/01_stereo/"+os.environ["SHOT"]+"_stereoInfo.json"
    if not os.path.isfile(jsonStereoFileS):
        txt = "missig file : '{}'".format(jsonStereoFileS)
        log.printL("e",txt, guiPopUp = False)
        raise RuntimeError(txt)

    jsonStereoD = jsonRead(jsonStereoFileS)
    txt = "reading : '{}'".format(jsonStereoFileS)
    log.printL("i",txt, guiPopUp = False)

    pprint (jsonStereoD)

    oNode = nuke.nodes.StickyNote(name="stereoInfo", label ="stereo info",tile_color = 3372271103)

    camConv = nuke.Array_Knob("camConv", "convergence")
    camZeroPar = nuke.Array_Knob("camZeroPar", "zeroParallax")
    camSep = nuke.Array_Knob("camSep", "separation")
    camInter = nuke.Array_Knob("camInter", "interaxial")
    oNode.addKnob(camInter)
    oNode.addKnob(camSep)
    oNode.addKnob(camZeroPar)
    oNode.addKnob(camConv)


    camInter.setAnimated()
    camConv.setAnimated()
    camZeroPar.setAnimated()
    camSep.setAnimated()


    for k, v in jsonStereoD.items():
        #print k,v["convergence"], v["zeroParallax"], v["separation"]
        camConv.setValueAt( float(v["convergence"]), float(k) )
        camZeroPar.setValueAt( float(v["zeroParallax"]), float(k) )
        camSep.setValueAt( float(v["separation"]), float(k) )
        camInter.setValueAt( float(v["separation"])*2, float(k) )

    txt = "created node : '{}'".format(oNode['name'].getValue())
    log.printL("i",txt)

    return dict(resultB=log.resultB, logL=log.logL)



def pointToPrivate(readNodeL=[], gui=True, postConformB=True):
    log = LogBuilder(gui=gui, funcName ="pointToPrivate")

    filePathExpS=""
    filePathNewS = ""
    unvalidNodeL = []
    validNodeL = []


    for each in readNodeL:
        eachNameS = each['name'].getValue()

        if 'read_exr' in eachNameS or 'read_comp' in eachNameS:
            log.printL("i","skipping output node: '{}'".format(eachNameS))
            continue
        if each['disable'].getValue() == 1:
            log.printL("i","skipping disabled node: '{}'".format(eachNameS))
            continue

        filePathExpS = nuke.filename(each)
        print filePathExpS
        if not filePathExpS:
            log.printL("e","Undefined file path: '{}'".format(eachNameS))
            unvalidNodeL.append(each)
            continue

        if not os.environ["OUTPUT_DIR"]in filePathExpS:
            log.printL("e","unvalid file path, could not find '[getenv OUTPUT_DIR]' string in file path: '{}'".format(eachNameS))
            unvalidNodeL.append(each)
            continue


        #filePathOrigS="[getenv OUTPUT_DIR]/%V/_version/lyr_00_bty_room-v005/sq0300_sh0020a.%04d.exr"
        imageNameS=filePathExpS.split("/")[-1]
        layerNameS=filePathExpS.split("/")[-2].split("-v")[0]


        #"//zombiwalk/Projects/private/alexandreb/zomb/shot/sq6660/sq6660_sh0020a/08_render/render/%V/lyr_00_bty_room/sq0300_sh0020a.%04d.exr"
        filePathNewS = normPath(os.environ["PRIV_DIR"]+"/08_render/render/%V/"+layerNameS+"/"+imageNameS)
        #filePathNewS = os.environ["PRIV_DIR"]+"/08_render/render/%V/"+layerNameS+"/"+imageNameS

        each['file'].setValue(filePathNewS)
        log.printL("i","read node  : '{}'".format(eachNameS))
        log.printL("i","old path -> '{}'".format(filePathExpS))
        log.printL("i","new path -> '{}'".format(filePathNewS))

    if postConformB :
        conformReadNode(readNodeL=readNodeL, gui=gui, conformPathB = True) 

    return dict(resultB=log.resultB, logL=log.logL)


def nukeRenderNodeList(nukeScriptS="", nodeList=[], gui=True):
    log = LogBuilder(gui=gui, funcName ="nukeRenderNodeList")

    filePathExpS=""
    filePathNewS = ""
    unvalidNodeL = []
    validNodeL = []

    if not os.path.isfile(nukeScriptS) or not ".nk" in nukeScriptS:
        log.printL("e","'{}' is not a '.nk' file or doesn't exist".format(nukeScriptS))
        return

    nukeCommand = normPath(os.path.join(os.path.split(os.environ["Z2K_LAUNCH_SCRIPT"])[0],"nuke10.bat"))

    for each in nodeList:
        subprocess.call(['start', 'cmd', '/C', nukeCommand, "-X"+each, nukeScriptS],shell=True)
        #subprocess.call([nukeCommand, "-X"+each, nukeScriptS],shell=True)

    return dict(resultB=log.resultB, logL=log.logL)


def createNukeBatchMovie(nodeList=[], gui=True):
    log = LogBuilder(gui=gui, funcName ="createNukeBatchMovie")

    nukeScriptS = nuke.root().knob('name').value()

    if not nodeList:
        if "_stereo" in nukeScriptS:
            nodeList=['out_movie_stereo']
        else:
            nodeList=['out_movie']

    workingDir = os.path.dirname(nukeScriptS)
    renderBatchFile = normPath(os.path.join(workingDir,"nukeBatch.bat"))

    renderBatch_obj = open(renderBatchFile, "w")

    if os.environ["davos_site"] == "dmn_paris":
         renderBatch_obj.write(r'''set nuke="C:\Users\%USERNAME%\zombillenium\z2k-pipeline-toolkit\launchers\paris\nuke10.bat"'''+"\n")
    elif os.environ["davos_site"] == "dmn_angouleme":
        renderBatch_obj.write(r'''set nuke="C:\Users\%USERNAME%\zombillenium\z2k-pipeline-toolkit\launchers\angouleme\nuke10.bat"'''+"\n")
    else:
        renderBatch_obj.write(r'''set nuke="C:\Users\%USERNAME%\zombillenium\z2k-pipeline-toolkit\launchers\????????\nuke10.bat"'''+"\n")

    renderBatch_obj.write(r'''set nukeScript='''+nukeScriptS+"\n")

    for each in nodeList:
        renderBatch_obj.write(r'''%nuke% -X '''+each+r''' %nukeScript%''')

    renderBatch_obj.close()
    print "#### Info: nukeBatch.bat created: {}".format(os.path.normpath(renderBatchFile))


    return dict(resultB=log.resultB, logL=log.logL)



def createPublishBat(gui=True):
    log = LogBuilder(gui=gui, funcName ="createPublishBat")

    nukeScriptS = nuke.root().knob('name').value()
    workingDir = os.path.dirname(nukeScriptS)
    publishBatFile = normPath(os.path.join(workingDir,"publish.bat"))

    renderBatch_obj = open(publishBatFile, "w")

    if os.environ["davos_site"] == "dmn_paris":
         renderBatch_obj.write(r'''set nuke="C:\Users\%USERNAME%\zombillenium\z2k-pipeline-toolkit\launchers\paris\nuke10.bat"'''+"\n")
    elif os.environ["davos_site"] == "dmn_angouleme":
        renderBatch_obj.write(r'''set nuke="C:\Users\%USERNAME%\zombillenium\z2k-pipeline-toolkit\launchers\angouleme\nuke10.bat"'''+"\n")
    else:
        renderBatch_obj.write(r'''set nuke="C:\Users\%USERNAME%\zombillenium\z2k-pipeline-toolkit\launchers\????????\nuke10.bat"'''+"\n")

    renderBatch_obj.write(r'''set pythonFile="C:\Users\%USERNAME%\zombillenium\z2k-pipeline-toolkit\nuke\scripts\publish.py"'''+"\n")
    renderBatch_obj.write(r'''set nukeScript='''+nukeScriptS+"\n")
    renderBatch_obj.write(r'''%nuke% -t %pythonFile% %nukeScript%'''+"\n")
    renderBatch_obj.write(r'''pause'''+"\n")

    renderBatch_obj.close()
    print "#### Info: publish.bat created: {}".format(os.path.normpath(publishBatFile))


    return dict(resultB=log.resultB, logL=log.logL)



