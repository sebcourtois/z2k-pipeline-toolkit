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

            fileO =  nkU.dataFile(fileNameS = firstFrameS)

            wavFileName = nkU.pathJoin(os.environ["ZOMB_SHOT_PATH"],fileO.seq,fileO.shot,"00_data",fileO.shot+"_sound.wav")
            if not os.path.isfile(wavFileName):
                    txt = "wav file does not exists: '{}'".format(wavFileName)
                    log.printL("e", txt)
                    raise ValueError(txt)


            movFileName = nkU.pathJoin(os.environ["ZOMB_ROOT_PATH"],"private",fileO.user,"zomb","shot",fileO.seq,fileO.shot,fileO.depDir,fileO.depDirSub,fileO.shot+"_"+fileO.layerName+".mov")
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


