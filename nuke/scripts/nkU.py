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
        self.log = LogBuilder(gui=gui, logL = [], resultB = True)

        if not fileNameS:
            fileNameS = nuke.root().knob('name').value()
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
                print fileDataL
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
            privateDirS = os.environ["PRIV_ZOMB_SHOT_PATH"].replace("/$DAVOS_USER/","/"+self.user+"/")+"/"+self.seq+"/"+self.shot
            miscDirS = os.environ["ZOMB_MISC_PATH"]
            print ""
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

        filePathS = filePathS.replace("/left/", "/%V/")
        filePathS = filePathS.replace("/right/", "/%V/")

    return filePathS




def conformFileNode(readNodeL=[], gui=True, conformPathB = True):
    log = LogBuilder(gui=gui, funcName ="conformFileNode")

    filePathOrigS=""
    filePathNewS = ""
    unvalidNodeL = []

    for each in readNodeL:
        eachNameS = each['name'].getValue()
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
        filePathExpLeftS = ""
        filePathExpRightS = ""


        if "%V" in filePathExpS:
            filePathExpLeftS = filePathExpS.replace("%V","left")
            filePathExpRightS = filePathExpS.replace("%V","right")
            resultLeftD = getImgSeqInfo(filePathExpLeftS,gui=gui)
            resultRightD = getImgSeqInfo(filePathExpRightS,gui=gui)

            if eachTypeS=="Read":
                if not (resultLeftD["firstImgI"] == 0 and resultLeftD["lastImgI"] == 0):
                    if resultLeftD["frameNumberI"]!=resultRightD["frameNumberI"]:
                        log.printL("e","'{}' missmaching frame number: left {}, right {} ".format(eachNameS, resultLeftD["frameNumberI"], resultRightD["frameNumberI"]))

                    if resultLeftD["firstImgI"] == resultRightD["firstImgI"]:
                        each['first'].setValue(resultLeftD["firstImgI"])
                    else:
                        each['first'].setValue(min(resultLeftD["firstImgI"],resultRightD["firstImgI"]))
                        log.printL("e","'{}' has different first frame on left and right camera".format(eachNameS))

                    if resultLeftD["lastImgI"] == resultRightD["lastImgI"]:
                        each['last'].setValue(resultLeftD["lastImgI"])
                    else:
                        each['last'].setValue(min(resultLeftD["lastImgI"],resultRightD["lastImgI"]))
                        log.printL("e","'{}' has different last frame on left and right camera".format(eachNameS))

                    if resultLeftD["missingFrameL"]:
                        log.printL("e","'{}' missing frames found on left camera seq: {} ".format(eachNameS, resultLeftD["missingFrameL"]))
                        unvalidNodeL.append(each)
                    if resultRightD["missingFrameL"]:
                        log.printL("e","'{}' missing frames found on right camera seq: {} ".format(eachNameS, resultRightD["missingFrameL"]))
                        if each not in unvalidNodeL:
                            unvalidNodeL.append(each)
                else:
                    log.printL("w","'Skipping image sequence check: '{}'".format(eachNameS))

        else:
            resultD = getImgSeqInfo(filePathExpS,gui=gui)
            if eachTypeS=="Read":
                if not (resultD["firstImgI"] == 0 and resultD["lastImgI"] == 0):
                    each['first'].setValue(resultD["firstImgI"])
                    each['last'].setValue(resultD["lastImgI"])
                    if resultD["missingFrameL"]:
                        log.printL("e","'{}' missing frames found in seq: {} ".format(eachNameS, resultD["missingFrameL"]))
                        if each not in unvalidNodeL:
                            unvalidNodeL.append(each)
                else:
                    log.printL("w","'Skipping image sequence check: '{}'".format(eachNameS))

    return dict(resultB=log.resultB, logL=log.logL, unvalidNodeL=unvalidNodeL)






def getImgSeqInfo(filePathS = "", gui = True):
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
        log.printL("e","Could not find directory: '{}'".format(fileDirS))
        return dict(resultB=log.resultB, logL=log.logL, firstImgI=firstImgI, lastImgI=lastImgI, missingFrameL=missingFrameL, frameNumberI=len(imgNumL))
    if len(imgNameS.split("."))!=3:
        log.printL("w","could not find a 'name.####.ext' image sequence: '{}'".format(filePathS))
        return dict(resultB=log.resultB, logL=log.logL, firstImgI=0, lastImgI=0, missingFrameL=missingFrameL, frameNumberI=len(imgNumL))

    itemDirL = os.listdir(fileDirS)
    for each in itemDirL:
        eachSplitL = each.split(".")
        if  len(eachSplitL)==3 and eachSplitL[0]==imgRadS and eachSplitL[-1]==imgExtS:
            imgNumL.append(int(eachSplitL[1]))

    if not imgNumL:
        log.printL("e"," no sequ found in: '{}'".format(fileDirS))
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



def publishLayer(layerPathS = "//ZOMBIWALK/Projects/private/alexandreb/zomb/shot/sq6660/sq6660_sh0010a/08_render/render-v001/left/lyr_ast0_lgtPass",destination = "output", comment="test",dryRun=False, gui = True):
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



def publishNode(readNodeL=[],dryRun=False, destination = "output", gui = True, guiPopUp = False, commentS = ""):
    log = LogBuilder(gui=gui, funcName ="publishNode")

    toPubNodeL=[]
    publishedNodeL = []

    for each in readNodeL:
        filePathExpS = nuke.filename(each)
        lyrDirNameS = os.path.basename(os.path.dirname(filePathExpS))
        eachNameS = each['name'].getValue()
        if os.environ["OUTPUT_DIR"] in filePathExpS:
            log.printL("i","skipping, already published: '{}', '{}'".format(eachNameS,filePathExpS))
        elif not "lyr_" in lyrDirNameS:
            log.printL("e","skipping, not a layer: '{}', '{}'".format(eachNameS,filePathExpS))
        elif "compo-v" in filePathExpS and destination == "output":
            log.printL("i","skipping, '.../compo-vxx/...' has to be published in the 'output' structure: '{}', '{}'".format(eachNameS,lyrDirNameS))
        else:
            toPubNodeL.append(each)

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
            log.printL("i","Publishing: '{}', '{}'".format(eachNameS,filePathExpS))
            resultD = publishLayer(layerPathS = layerPathS,comment=commentS,dryRun=dryRun,destination=destination, gui = True)
            publishedNodeL.append(each['name'].getValue())

            if destination == "output":
                newFileDirExpS = conformFilePath(filePathS=resultD["publishLastVersDir"], gui=gui)
                insensitive_shotDir = re.compile(re.escape(os.environ["SHOT"]), re.IGNORECASE)
                fileNameS =  insensitive_shotDir.sub("[getenv SHOT]", fileNameS)
                newFilePathExpS = newFileDirExpS+"/"+fileNameS
                each['file'].setValue(newFilePathExpS)
                log.printL("i","New path: '{}', '{}'".format(eachNameS,newFilePathExpS))
        log.printL("i","{} file node published : '{}'".format(len(publishedNodeL),publishedNodeL, guiPopUp = guiPopUp))
    else:
        log.printL("i","Nothing to publish", guiPopUp = guiPopUp)



def publishCompo(dryRun=False, gui = True):

    log = LogBuilder(gui=gui, funcName ="publishCompo")
    stereoB = isStereo()
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
        seqPathS = os.environ["PRIV_DIR"]+"/"+depS+"/compo-v"+verS+"/lyr_"+shotS+"/"+shotS+".0101.exr"
    elif depS == "08_render":
        nukeDepSufS = "precomp"
        movDepSufS = "render"
        seqPathS = ""
    elif depS == "07_fx3d":
        nukeDepSufS = "fx3d"
        movDepSufS = "compo"
        seqPathS = ""
    

    nkExpectedFileNameS = shotS+"_"+nukeDepSufS+"-v"+verS
    if nKFileNameS.split(".")[0] != nkExpectedFileNameS:
        log.printL("e","Publish failed, Nuke file name is different from expected name: '{}'".format(nkExpectedFileNameS),guiPopUp = True)
        nuke.message("Error: "+txt)
        return

    if nKFileNameS.split(".")[-1] != "nk":
        log.printL("e","Publish failed, Nuke file extention must be 'nk', not : '{}'".format( nKFileNameS.split(".")[-1]),guiPopUp = True)
        return

    if stereoB:
        print "not ready yet"
        return
    else:
        movFilePathS = os.path.dirname(nKFilePathS)+"/"+shotS+"_"+movDepSufS+"-v"+verS+"."+incS+".mov"
        if not os.path.isfile(movFilePathS):
            log.printL("e","Publish failed, missing '.mov' : '{}'".format(movFilePathS),guiPopUp = True)
            return
        if seqPathS:
            resultD = getImgSeqInfo(seqPathS,gui=gui)
            if not resultD["resultB"]:
                for each in resultD["logL"]:
                    print each
                    log.printL("e","Publish failed, sequence or dirctory not valid, please check the log '{}'".format( seqPathS),guiPopUp = True)
                    return

    commentS = nuke.getInput("Please enter a publish comment", "")
    if not commentS:
        log.printL("i","Pubish canceled")
        raise RuntimeError("Publish canceled")


    try:
        resultD =  proj.publishEditedVersion(nKFilePathS, comment=commentS, returnDict=True)
    except Exception as err:
        log.printL("e","Nuke file publish failed: '{}'".format( err),guiPopUp = True)
        pprint(resultD)
        raise

    # try:
    #     pubMovFile = proj.getShot(shotS.lower()).getRcFile("public","compo_movie")
    #     pubMovFile.publishVersion(movFilePathS, comment=commentS, autoLock=True)
    #     #publishFile(fileNameS = movFilePathS, comment=commentS,dryRun=dryRun, gui = gui)
    # except Exception as err:
    #     log.printL("e","Movie file publish failed: '{}'".format( err),guiPopUp = True)
    #     raise

    if depS == "10_compo":
        try:
            publishLayer(layerPathS = os.path.dirname(seqPathS),destination = "shot", comment=commentS,dryRun=dryRun, gui = gui)
        except Exception as err:
            log.printL("e","Final Layer publish failed: '{}'".format( err),guiPopUp = True)
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
  # cope with the directory existing already by ignoring that exception
  try:
    os.makedirs( osdir )
  except OSError, e:
    if e.errno != errno.EEXIST:
      raise
