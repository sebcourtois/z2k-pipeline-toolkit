import nkU
import os
import nuke




firstFrameFileNameL = [r"//ZOMBIWALK/Projects/private/alexandreb/zomb/shot/sq0300/sq0300_sh0040a/06_finalLayout/render-v003/lay_finalLayout_00/arlequin/sq0300_sh0040a.0101.jpeg", r"//ZOMBIWALK/Projects/private/alexandreb/zomb/shot/sq0300/sq0300_sh0040a/06_finalLayout/render-v003/lay_finalLayout_00/beauty/sq0300_sh0040a.0101.jpeg"]
renderDirS = r"//ZOMBIWALK/Projects/private/alexandreb/zomb/shot/sq0300/sq0300_sh0040a/06_finalLayout/render-v003"

def compileLayerQuickTime(firstFrameFileNameL = firstFrameFileNameL, renderDirS=renderDirS, passNameL= ["lay_finalLayout_00"], aovNameL= ["beauty", "arlequin"], gui= False):
    log = nkU.LogBuilder(gui=gui, funcName ="'compileLayerQuickTime'")
    outNodeL = []
    outBoundL = []
    fFrameRangeD = {}
    outD = {}

    for eachPass in passNameL:
        for eachAov in aovNameL:
            imageDirS = nkU.pathJoin(renderDirS,eachPass,eachAov)

            ### get first and last frame
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

    for firstFrameS, rangeL in fFrameRangeD.items():
        print "firstFrameS: ", firstFrameS
        print "rangeL: ",rangeL

    # for each in firstFrameFileNameL:
    #     each = nkU.normPath(each)
    #     if os.path.isfile(each):
    #         fileO =  nkU.dataFile(fileNameS = each)

    #         wavFileName = nkU.pathJoin(os.environ["ZOMB_SHOT_PATH"],fileO.seq,fileO.shot,fileO.dep,"00_data",fileO.shot+"_sound.wav")
    #         movFileName = nkU.pathJoin(os.environ["ZOMB_SHOT_LOC"],fileO.seq,fileO.shot,fileO.dep,fileO.depSub,fileO.shot+"_"+fileO.layerName+".mov")

    #         ### get first and last frame
    #         dirList = os.listdir(os.path.dirname(each))
    #         imagePattern = fileO.imageName.split(".")[0] + fileO.imageName.split(".")[-1]
    #         imageSeq = []
    #         for eachFile in dirList:
    #             if eachFile.split(".")[0] + eachFile.split(".")[-1] == imagePattern:
    #                 imageSeq.append(eachFile)
    #         imageSeq.sort()
    #         fFrameS = imageSeq[0].split(".")[-2]
    #         lFrameS = imageSeq[-1].split(".")[-2]

    #         inFileName = each.replace("."+fFrameS+".", ".%04d.")

    #         inNode = nuke.toNode( "in_"+fileO.layerName )
    #         inNode["file"].setValue(inFileName)
    #         outNode = nuke.toNode( "out_"+fileO.layerName )
    #         outNode["file"].setValue(movFileName)

            
    #         outNodeL.append(outNode)
    #         outBoundL.append([int(fFrameS),int(lFrameS),1])
    #         outD["out_"+fileO.layerName] = [int(fFrameS), int(lFrameS), movFileName ]

    #     else:
    #         txt = "Could not find file, or not in a private directory structure: '{}'".format(each)
    #         log.printL("e", txt)

    if outNodeL:
        for key,value in outD.items():
            txt = "creating movie: range'{}-{}', '{}'".format(value[0],value[1],value[2],)
            log.printL("i", txt)

        #nuke.executeMultiple  (outNodeL,outBoundL)

    return dict(resultB=log.resultB, logL=log.logL )


#"//ZOMBIWALK/Projects/zomb/shot/sq0300\sq0300_sh0040a\00_data\sq0300_sh0040a_sound.wav"

def compileLayerQuickTime_temp():
    projSetO = nuke.root()
    argv0 = projSetO.knob('argv0').value()
    argv1 = projSetO.knob('argv1').value()
    print "argv0: ",argv0
    print "argv1: ",argv1
