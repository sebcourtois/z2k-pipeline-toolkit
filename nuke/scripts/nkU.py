import os
import re
import subprocess
import datetime
import nuke
import errno
#cat plante en mode nuke render
#from davos.core.damproject import DamProject
from pprint import pprint



# rappel
# os.environ["ZOMB_ASSET_PATH"] = zombRootPath+"/zomb/asset"
# os.environ["ZOMB_SHOT_PATH"] = zombRootPath+"/zomb/shot"
# os.environ["ZOMB_OUTPUT_PATH"] = zombRootPath+"/zomb/output"
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

        if os.path.isfile(self.fileNameS) or os.path.isdir(self.fileNameS):
            fileNameL=self.fileNameS.split("/")
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
                elif "precomp-v" in fileDataL[6]:
                    self.ver = fileDataL[6].split("precomp-v")[-1].split(".")[0]
                    self.increment = fileDataL[6].split("precomp-v")[-1].split(".")[1]
        else:
            txt = "is not a file: '{}'".format(self.fileNameS)
            self.log.printL("e", txt)


    def printData(self):
        self.log = LogBuilder(gui=self.gui, funcName ="printData")
        self.log.printL("i","fileNameS: '{}'".format(self.fileNameS))
        self.log.printL("i","location: '{}'".format(self.location))
        self.log.printL("i","user: '{}'".format(self.user))
        self.log.printL("i","proj: '{}'".format(self.proj))
        self.log.printL("i","typ: '{}'".format(self.typ))
        self.log.printL("i","seq: '{}'".format(self.seq))
        self.log.printL("i","shot: '{}'".format(self.shot))
        self.log.printL("i","depDir: '{}'".format(self.depDir))

        if "render-v"in self.depDirSub:
            self.log.printL("i","passName: '{}'".format(self.passName))
            self.log.printL("i","layerName: '{}'".format(self.layerName))
            self.log.printL("i","imageName: '{}'".format(self.imageName))
            self.log.printL("i","imageFormat: '{}'".format(self.imageFormat))
            self.log.printL("i","imageNumber: '{}'".format(self.imageNumber))
            self.log.printL("i","ver: '{}'".format(self.ver))
        elif "compo-v" in self.depDirSub:
            self.log.printL("i","ver: '{}'".format(self.ver))
            self.log.printL("i","increment: '{}'".format(self.increment))

    def initNukeEnvVar(self):
        if self.seq and self.shot and self.user and self.depDir:
            departementS =self.depDir
            outputDirS = os.environ["ZOMB_OUTPUT_PATH"]+"/"+self.seq+"/"+self.shot
            shotDirS = os.environ["ZOMB_SHOT_PATH"]+"/"+self.seq+"/"+self.shot
            #privateDirS = os.environ["PRIV_ZOMB_SHOT_PATH"].split("/$DAVOS_USER/")[0]
            try:
                privateDirS = os.environ["PRIV_ZOMB_SHOT_PATH"].replace("/$DAVOS_USER/","/"+self.user+"/")+"/"+self.seq+"/"+self.shot
            except:
                privateDirS = ""

            miscDirS = os.environ["ZOMB_MISC_PATH"]
            self.log.printL("i","initialising environnement variables")
            self.log.printL("i","SEQ: "+self.seq)
            self.log.printL("i","SHOT: "+self.shot)
            self.log.printL("i","VER: "+self.ver)
            self.log.printL("i","INC: "+self.increment)
            self.log.printL("i","USER: "+self.user)
            self.log.printL("i","DEP: "+departementS)
            self.log.printL("i","OUTPUT_DIR: "+outputDirS)
            self.log.printL("i","SHOT_DIR: "+shotDirS)
            self.log.printL("i","PRIV_DIR: "+privateDirS)
            self.log.printL("i","MISC_DIR: "+miscDirS)
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

        else:
            txt = "one of the variable 'seq', 'shot', 'user' or 'dep' is undefined, could not set nuke proj environment var".format(self.fileNameS)
            self.log.printL("e", txt)
            self.log.printL("e", "Make sure your nuke scropt is saved in a valid private directory")
            nuke.message("Error: cannot initialise Nuke environnement variable, make sure your nuke scropt is saved in a valid private directory")



def initNukeShot(fileNameS= ""):
    try:
        df=dataFile(fileNameS)
        df.printData()
        df.initNukeEnvVar()
    except:
        pass



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

    filePathS = filePathS.replace("/left/", "/%V/")
    filePathS = filePathS.replace("/right/", "/%V/")

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




def conformFileNode(readNodeL=[], gui=True, conformPathB = True):
    log = LogBuilder(gui=gui, funcName ="conformFileNode")

    filePathOrigS=""
    filePathNewS = ""
    unvalidNodeL = []

    for each in readNodeL:
        eachNameS = each['name'].getValue()

        if 'read_exr' in eachNameS:
            log.printL("i","skipping output node: '{}'".format(eachNameS))
            continue

        eachTypeS = nuke.getNodeClassName(each)

        #log.printL("i", "node: '{}'".format(eachNameS))
        filePathOrigS= each['file'].getValue()
        filePathNewS = conformFilePath(filePathS = filePathOrigS, gui = gui)
        if filePathNewS and conformPathB:
            if filePathNewS !=filePathOrigS:
                log.printL("i","'{}' {}".format(eachNameS, filePathOrigS))
                log.printL("i","'{}' --> {}".format(eachNameS, filePathNewS))
                each['file'].setValue(filePathNewS)


        filePathExpS = nuke.filename(each)
        if not filePathExpS:
            log.printL("e","Undefined file path: '{}'".format(eachNameS))
            if each not in unvalidNodeL: unvalidNodeL.append(each)
            continue


        if "%V" in filePathExpS:
            filePathExpLeftS = filePathExpS.replace("%V","left")
            filePathExpRightS = filePathExpS.replace("%V","right")

            if not os.path.isdir(os.path.dirname(filePathExpRightS)):
                os.makedirs(os.path.dirname(filePathExpRightS))


            if eachTypeS=="Read":
                resultLeftD = getImgSeqInfo(filePathExpLeftS, nodeNameS= eachNameS,gui=gui)
                resultRightD = getImgSeqInfo(filePathExpRightS, nodeNameS= eachNameS,gui=gui)
                if not (resultLeftD["firstImgI"] == 0 and resultLeftD["lastImgI"] == 0) and not (resultRightD["firstImgI"] == 0 and resultRightD["lastImgI"] == 0):
                    if resultLeftD["frameNumberI"]!=resultRightD["frameNumberI"]:
                        log.printL("e","'{}' missmaching frame number: left {}, right {} ".format(eachNameS, resultLeftD["frameNumberI"], resultRightD["frameNumberI"]))
                        if each not in unvalidNodeL: unvalidNodeL.append(each)

                    if resultLeftD["firstImgI"] == resultRightD["firstImgI"]:
                        each['first'].setValue(resultLeftD["firstImgI"])
                    else:
                        each['first'].setValue(min(resultLeftD["firstImgI"],resultRightD["firstImgI"]))
                        log.printL("e","'{}' has different first frame on left and right camera".format(eachNameS))
                        if each not in unvalidNodeL: unvalidNodeL.append(each)

                    if resultLeftD["lastImgI"] == resultRightD["lastImgI"]:
                        each['last'].setValue(resultLeftD["lastImgI"])
                    else:
                        each['last'].setValue(min(resultLeftD["lastImgI"],resultRightD["lastImgI"]))
                        log.printL("e","'{}' has different last frame on left and right camera".format(eachNameS))
                        if each not in unvalidNodeL: unvalidNodeL.append(each)

                    if resultLeftD["missingFrameL"]:
                        log.printL("e","'{}' missing frames found on left camera seq: {} ".format(eachNameS, resultLeftD["missingFrameL"]))
                        if each not in unvalidNodeL: unvalidNodeL.append(each)
                    if resultRightD["missingFrameL"]:
                        log.printL("e","'{}' missing frames found on right camera seq: {} ".format(eachNameS, resultRightD["missingFrameL"]))
                        if each not in unvalidNodeL: unvalidNodeL.append(each)


        else:
            if eachTypeS=="Read":
                resultD = getImgSeqInfo(filePathExpS, nodeNameS= eachNameS, gui=gui)
                if not (resultD["firstImgI"] == 0 and resultD["lastImgI"] == 0):
                    each['first'].setValue(resultD["firstImgI"])
                    each['last'].setValue(resultD["lastImgI"])
                    if resultD["missingFrameL"]:
                        log.printL("e","'{}' missing frames found in seq: {} ".format(eachNameS, resultD["missingFrameL"]))
                        if eachNameS not in unvalidNodeL: unvalidNodeL.append(eachNameS)

    if gui:
        unvalidNodeNameL=[]
        if unvalidNodeL:
            for each  in unvalidNodeL:
                unvalidNodeNameL.append(each['name'].getValue())
                each['selected'].setValue(True)

            txt1 = "'{}' unvalid nodes found: {} ".format(len(unvalidNodeNameL), unvalidNodeNameL)
            nuke.message("Info:\n"+txt1+"\nPlease read the log for more details")


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

    fileDirS = os.path.dirname(filePathS)
    if not os.path.isdir(fileDirS):
        log.printL("e","'{}' Could not find directory: '{}'".format(nodeNameS,fileDirS))
        return dict(resultB=log.resultB, logL=log.logL, firstImgI=firstImgI, lastImgI=lastImgI, missingFrameL=missingFrameL, frameNumberI=len(imgNumL))
    if len(imgNameS.split("."))!=3:
        log.printL("w","'{}' Could not find a 'name.####.ext' image sequence: '{}'".format(nodeNameS,filePathS))
        return dict(resultB=log.resultB, logL=log.logL, firstImgI=0, lastImgI=0, missingFrameL=missingFrameL, frameNumberI=len(imgNumL))

    itemDirL = os.listdir(fileDirS)
    for each in itemDirL:
        eachSplitL = each.split(".")
        if  len(eachSplitL)==3 and eachSplitL[0]==imgRadS and eachSplitL[-1]==imgExtS:
            imgNumL.append(int(eachSplitL[1]))

    if not imgNumL:
        if "/right/" in fileDirS:
            log.printL("w","'{}' No sequ found in right cam: '{}'".format(nodeNameS, fileDirS))
            return dict(resultB=log.resultB, logL=log.logL, firstImgI=firstImgI, lastImgI=firstImgI, missingFrameL=missingFrameL, frameNumberI=len(imgNumL))
        else:
            log.printL("e","'{}' No sequ found in: '{}'".format(nodeNameS, fileDirS))
            return dict(resultB=log.resultB, logL=log.logL, firstImgI=firstImgI, lastImgI=lastImgI, missingFrameL=missingFrameL, frameNumberI=len(imgNumL))

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



def publishLayer(layerPathS = "",destination = "output", comment="my comment",dryRun=False, gui = True):
    log = LogBuilder(gui=gui, funcName ="publishLayer")
    from davos.core.damproject import DamProject

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
        publishDir = outLib.getEntry(outDirS)
    elif destination ==  "shot":
        shotDirS = os.environ["SHOT_DIR"]+"/"+os.environ["DEP"]+camDirS
        if not os.path.isdir(shotDirS):
            os.makedirs(shotDirS)
        publishDir = shotLib.getEntry(shotDirS)


    _ , newVersion = publishDir.publishFile(layerPathS, autoLock=True, autoUnlock=True, comment=comment, dryRun=dryRun, saveChecksum=False)

    publishHeadDir = publishDir.absPath()
    publishLastVersDir = publishDir.absPath()+"/_version/"+newVersion.name

    log.printL("i","Published layer: '{}'".format(publishHeadDir))

    return dict(resultB=log.resultB, logL=log.logL, publishHeadDir = publishHeadDir, publishLastVersDir= publishLastVersDir)



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
    skippedNodeL = []

    for each in readNodeL:
        eachNameS = each['name'].getValue()

        filePathExpS = nuke.filename(each)
        if not filePathExpS:
            log.printL("i","skipping, undefined file path: '{}'".format(eachNameS))
            skippedNodeL.append(eachNameS)
            continue

        lyrDirNameS = os.path.dirname(filePathExpS)

        if "%V" in lyrDirNameS:
            lyrDirNameLeftS = lyrDirNameS.replace("%V","left")
            if not os.path.isdir(lyrDirNameLeftS):
                log.printL("i","skipping, missing directory: '{}', '{}'".format(eachNameS,lyrDirNameLeftS))
                skippedNodeL.append(eachNameS)
                continue
            lyrDirNameRightS = lyrDirNameS.replace("%V","right")
            if not os.path.isdir(lyrDirNameRightS):
                log.printL("i","skipping, missing directory: '{}', '{}'".format(eachNameS,lyrDirNameRightS))
                skippedNodeL.append(eachNameS)
                continue
        else:
            if not os.path.isdir(lyrDirNameS):
                log.printL("i","skipping, missing directory: '{}', '{}'".format(eachNameS,filePathExpS))
                skippedNodeL.append(eachNameS)
                continue

        if os.environ["OUTPUT_DIR"] in filePathExpS:
            log.printL("i","skipping, already published: '{}', '{}'".format(eachNameS,filePathExpS))
            skippedNodeL.append(eachNameS)
        elif not "lyr_" in lyrDirNameS:
            log.printL("i","skipping, not a layer: '{}', '{}'".format(eachNameS,filePathExpS))
            skippedNodeL.append(eachNameS)
        elif "compo-v" in filePathExpS and destination == "output":
            log.printL("i","skipping, '.../compo-vxx/...' has to be published in the 'shot' structure: '{}', '{}'".format(eachNameS,lyrDirNameS))
            skippedNodeL.append(eachNameS)
        elif "preComp-v" in filePathExpS and destination == "output":
            log.printL("i","skipping, '.../preComp-vxx/...' has to be published in the 'shot' structure: '{}', '{}'".format(eachNameS,lyrDirNameS))
            skippedNodeL.append(eachNameS)
        else:
            toPubNodeL.append(each)

    if conformFirstB:
        resultD = conformFileNode(readNodeL=toPubNodeL, gui=gui, conformPathB = False)
        if not resultD["resultB"] or not log.resultB:
            txt= "Can't Publish, some of the nodes are pointing toward unvalid sequences. Please read the log for more detail"
            log.printL("e",txt)
            nuke.message("Error: "+txt)
            return

    if toPubNodeL and not commentS:
        commentS = nuke.getInput("Please enter a publish comment", "")
        if not commentS:
            log.printL("i"," Publish canceled")
            raise RuntimeError("Publish canceled")

    for each in toPubNodeL:
        filePathExpS = nuke.filename(each)
        fileNameS = os.path.basename(filePathExpS)
        layerPathS = os.path.dirname(filePathExpS)
        eachNameS = each['name'].getValue()
        
        if "/%V/"in layerPathS:
            filePathLeftS = layerPathS.replace("/%V/","/left/")
            filePathRightS = layerPathS.replace("/%V/","/right/")
            resultD = publishLayer(layerPathS = filePathLeftS,comment=commentS,dryRun=dryRun,destination=destination, gui = True)
            resultD = publishLayer(layerPathS = filePathRightS,comment=commentS,dryRun=dryRun,destination=destination, gui = True)
            log.printL("i","Publishing stereo layers: '{}', '{}'".format(eachNameS,filePathExpS))
        else:
            resultD = publishLayer(layerPathS = layerPathS,comment=commentS,dryRun=dryRun,destination=destination, gui = True)
            log.printL("i","Publishing: '{}', '{}'".format(eachNameS,filePathExpS))

        publishedNodeL.append(eachNameS)

        if destination == "output":
            newFileDirExpS = conformFilePath(filePathS=resultD["publishLastVersDir"], gui=gui)
            insensitive_shotDir = re.compile(re.escape(os.environ["SHOT"]), re.IGNORECASE)
            fileNameS =  insensitive_shotDir.sub("[getenv SHOT]", fileNameS)
            newFilePathExpS = newFileDirExpS+"/"+fileNameS
            each['file'].setValue(newFilePathExpS)
            log.printL("i","New path: '{}', '{}'".format(eachNameS,newFilePathExpS))

    print ""
    print "---- LOG RESUME"
    for each in log.logL:
        print each

    print ""
    publishedMsg = "{} file node published : '{}'".format(len(publishedNodeL),publishedNodeL)
    skippedMsg = "{} file node skipped : '{}'".format(len(skippedNodeL),skippedNodeL)
    log.printL("i",publishedMsg)
    log.printL("i",skippedMsg)

    #log.printL("i","Nothing to publish", guiPopUp = guiPopUp)
    nuke.message("Info:\n"+publishedMsg+"\n"+skippedMsg+"\nPlease read the log for more details")





def publishCompo(dryRun=False, gui = True):
    log = LogBuilder(gui=gui, funcName ="publishCompo")

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
    movFilePathS = os.path.dirname(nKFilePathS)+"/"+shotS+"_"+movDepSufS+"-v"+verS+"."+incS+".mov"
    if not os.path.isfile(movFilePathS):
        log.printL("e","Publish failed, missing '.mov' : '{}'".format(movFilePathS),guiPopUp = True)
        return

    # testing presence of the 'read_exr' node presence (only one alowed) 
    readExrL=[]
    if depS == "10_compo":
        allReadNodeL = nuke.allNodes('Read')
        for each in allReadNodeL:
            if "read_exr" in each['name'].getValue():
                readExrL.append(each)
        if len(readExrL)!=1:
            log.printL("e","Publish failed, several or none 'read_exr' node fond: '{}'".format( nKFileNameS.split(".")[-1]),guiPopUp = True)
            return
    

    commentS = nuke.getInput("Please enter a publish comment", "")
    if not commentS:
        log.printL("i","Pubish canceled")
        raise RuntimeError("Publish canceled")

    if depS == "10_compo":
        try:
            publishNode(readNodeL=readExrL,dryRun=False, destination = "shot", gui = True, guiPopUp = False, commentS = commentS)
        except Exception as err:
            log.printL("e","Seq output node publish failed: '{}'".format(err),guiPopUp = True)
            raise

    try:
        resultD =  proj.publishEditedVersion(nKFilePathS, comment=commentS, returnDict=True)
    except Exception as err:
        log.printL("e","Nuke file publish failed: '{}'".format(err),guiPopUp = True)
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
  file = nuke.filename(nuke.thisNode())
  dir = os.path.dirname( file )
  osdir = nuke.callbacks.filenameFilter( dir )

  if "%V" in osdir:
    try:                        
        os.makedirs( osdir.replace("/%V/","/left/") )        
        os.makedirs( osdir.replace("/%V/","/right/") )
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