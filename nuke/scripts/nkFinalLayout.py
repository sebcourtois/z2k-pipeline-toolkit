import nkU
import os
import nuke





def compileLayerQuickTime(renderDirS="", passNameL= ["lay_finalLayout_00"], aovNameL= ["beauty", "arlequin"], gui= False):
    log = nkU.LogBuilder(gui=gui, funcName ="'compileLayerQuickTime'")

    outNodeL = []
    outBoundL = []
    fFrameRangeD = {}
    outD = {}
    smallestFFrameI= 99999999
    bigestLFrameI=0

    if not renderDirS:
        renderDirS = nuke.root()["argv0"].getValue()
    if not os.path.isdir(renderDirS):
            txt = "input render directory does not exists: '{}'".format(renderDirS)
            log.printL("e", txt)
            raise ValueError(txt)

    for eachPass in passNameL:
        for eachAov in aovNameL:
            imageDirS = nkU.pathJoin(renderDirS,eachPass,eachAov)

            ### get first and last frame number
            ### get first image file name
            dirList = os.listdir(imageDirS)
            #print "imageDirS :", imageDirS
            imageSeq = []
            for eachFile in dirList:
                if len(eachFile.split("."))==3:
                    imageName=eachFile.split(".")[0]
                    imageFormat=eachFile.split(".")[-1]
                    imagePattern=imageName+imageFormat
                    #break
            for eachFile in dirList:                    
                if eachFile.split(".")[0] + eachFile.split(".")[-1] == imagePattern:
                    imageSeq.append(eachFile)
            imageSeq.sort()
            fFrameS = imageSeq[0].split(".")[-2]
            lFrameS = imageSeq[-1].split(".")[-2]
            fFrameRangeD[nkU.pathJoin(imageDirS,imageSeq[0])] = [int(fFrameS), int(lFrameS)]
            if int(fFrameS)<smallestFFrameI:
                smallestFFrameI= int(fFrameS)
            if int(lFrameS)>bigestLFrameI:
                bigestLFrameI= int(lFrameS)

    nuke.root()["first_frame"].setValue(smallestFFrameI)
    nuke.root()["last_frame"].setValue(bigestLFrameI)

    for firstFrameS, rangeL in fFrameRangeD.items():
        firstFrameS = nkU.normPath(firstFrameS)
        if os.path.isfile(firstFrameS):
            print "-----"
            txt = "'{}', range to compile: '{}'".format(rangeL,firstFrameS)
            log.printL("i", txt)

            fileO =  dataFile(fileNameS = firstFrameS)

            wavFileName = nkU.pathJoin("//ZOMBIWALK/Projects/zomb/shot",fileO.seq,fileO.shot,"00_data",fileO.shot+"_sound.wav")
            if not os.path.isfile(wavFileName):
                    txt = "wav file does not exists: '{}'".format(wavFileName)
                    log.printL("e", txt)
                    raise ValueError(txt)


            movFileName = nkU.pathJoin("//ZOMBIWALK/Projects","private",fileO.user,"zomb","shot",fileO.seq,fileO.shot,fileO.depDir,fileO.depDirSub,fileO.shot+"_"+fileO.layerName+".mov")
            txt = "output movie: '{}'".format(movFileName)
            log.printL("i", txt)
            txt = "sound file: '{}'".format(wavFileName)
            log.printL("i", txt)

            ### get first and last frame
            dirList = os.listdir(os.path.dirname(firstFrameS))
            imagePattern = fileO.imageName.split(".")[0] + fileO.imageName.split(".")[-1]
            imageSeq = []
            for eachFile in dirList:
                if eachFile.split(".")[0] + eachFile.split(".")[-1] == imagePattern:
                    imageSeq.append(eachFile)
            imageSeq.sort()
            fFrameS = imageSeq[0].split(".")[-2]
            lFrameS = imageSeq[-1].split(".")[-2]

            inFileName = firstFrameS.replace("."+fFrameS+".", ".%04d.")

            inNode = nuke.toNode( "in_"+fileO.layerName )
            inNode["file"].setValue(inFileName)
            outNode = nuke.toNode( "out_"+fileO.layerName )
            outNode["file"].setValue(movFileName)
            outNode["mov64_audiofile"].setValue(wavFileName)
            outNode["mov32_audiofile"].setValue(wavFileName)
            outNode["use_limit"].setValue(True)
            outNode["first"].setValue(rangeL[0])
            outNode["last"].setValue(rangeL[1])

            
            outNodeL.append(outNode)
            outBoundL.append([int(fFrameS),int(lFrameS),1])

        else:
            txt = "Could not find file, or not in a private directory structure: '{}'".format(firstFrameS)
            log.printL("e", txt)

        #nuke.executeMultiple  (outNodeL,outBoundL)

    return dict(resultB=log.resultB, logL=log.logL )



class dataFile():
    def __init__(self, fileNameS= "", gui = False):
        self.log = nkU.LogBuilder(gui=gui, logL = [])
        if not fileNameS:
            fileNameS = nuke.root().knob('name').value()
            if "finalLayoutTemplate.nk" in fileNameS:
                fileNameS=  nuke.root()["argv0"].getValue()


        self.fileNameS=nkU.normPath(fileNameS)
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

        if os.path.isfile(self.fileNameS) or os.path.isdir(self.fileNameS):
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
            self.timeIn = 101
            self.timeOut = 101
        else:
            txt = "is not a file: '{}'".format(self.fileNameS)
            self.log.printL("e", txt)


    def printData(self):
        self.log = LogBuilder(gui=self.gui, funcName ="printData")
        self.log.printL("i","fileNameS: '{}'".format(self.fileNameS))
        self.log.printL("i","step: '{}'".format(self.stepS))
        self.log.printL("i","location: '{}'".format(self.location))
        self.log.printL("i","user: '{}'".format(self.user))
        self.log.printL("i","proj: '{}'".format(self.proj))
        self.log.printL("i","typ: '{}'".format(self.typ))
        self.log.printL("i","seq: '{}'".format(self.seq))
        self.log.printL("i","shot: '{}'".format(self.shot))
        self.log.printL("i","depDir: '{}'".format(self.depDir))
        self.log.printL("i","in: '{}'".format(self.timeIn))
        self.log.printL("i","out: '{}'".format(self.timeOut))

        if "render-v"in self.depDirSub:
            self.log.printL("i","passName: '{}'".format(self.passName))
            self.log.printL("i","layerName: '{}'".format(self.layerName))
            self.log.printL("i","imageName: '{}'".format(self.imageName))
            self.log.printL("i","imageFormat: '{}'".format(self.imageFormat))
            self.log.printL("i","imageNumber: '{}'".format(self.imageNumber))
            self.log.printL("i","ver: '{}'".format(self.ver))
        elif "compo-v" in self.depDirSub or "stereo-v" in self.depDirSub:
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
            self.log.printL("i","STEP: "+self.stepS)

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



        else:
            txt = "one of the variable 'seq', 'shot', 'user' or 'dep' is undefined, could not set nuke proj environment var".format(self.fileNameS)
            self.log.printL("e", txt)
            self.log.printL("e", "Make sure your nuke scropt is saved in a valid private directory")
            nuke.message("Error: cannot initialise Nuke environnement variable, make sure your nuke scropt is saved in a valid private directory")

