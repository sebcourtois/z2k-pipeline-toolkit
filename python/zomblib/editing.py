
import os
import re
from datetime import datetime
from collections import OrderedDict
import subprocess
from zomblib import rvutils

import shutil


from zomblib import damutils
from davos.core.damproject import DamProject


osp = os.path

FPS = 24.0
TC_SEPARATOR = ":"


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
            if self.guiPopUp: mc.confirmDialog( title='Error: '+self.funcName, message=self.msg, button=['Ok'], defaultButton='Ok' )
            self.resultB = False
        elif self.style == "w":
            self.formMsg = "#### {:>7}: {}{}".format("Warning",self.funcName,self.msg)
            if self.guiPopUp: mc.confirmDialog( title='Warning: '+self.funcName, message=self.msg, button=['Ok'], defaultButton='Ok' )
        elif self.style == "i":
            self.formMsg = "#### {:>7}: {}{}".format("Info",self.funcName,self.msg)
            if self.guiPopUp: mc.confirmDialog( title='Info: '+self.funcName, message=self.msg, button=['Ok'], defaultButton='Ok' )
        else:
            self.formMsg = "{}{}".format(self.funcName,self.msg)


        print self.formMsg

        self.logL.append(self.formMsg)

def convertTcToSecondsTc(in_Tc, in_fps=FPS, in_iHoursOffset=0, in_iMinutesOffset=0,
                         in_iSecondsOffset=0, in_iFramesOffset=0):

    hours, minutes, seconds, frames = [int(val) for val in in_Tc.split(TC_SEPARATOR)]

    frames += in_iFramesOffset
    if frames < 0:
        frames += FPS
        in_iSecondsOffset -= 1
    elif frames >= FPS:
        frames -= FPS
        in_iSecondsOffset += 1

    seconds += in_iSecondsOffset
    if seconds < 0:
        seconds += 60
        in_iMinutesOffset -= 1
    elif seconds >= 60:
        seconds -= 60
        in_iMinutesOffset += 1

    minutes += in_iMinutesOffset
    if minutes < 0:
        minutes += 60
        in_iHoursOffset -= 1
    elif minutes >= 60:
        minutes -= 60
        in_iHoursOffset += 1

    hours += in_iHoursOffset

    #print "{0} {1} {2} {3}".format(hours, minutes, seconds, frames)

    return "{1}{0}{2}{0}{3}".format(TC_SEPARATOR, hours, minutes, seconds + frames / FPS)

def convertTcToSeconds(in_Tc, in_fps=FPS, in_iHoursOffset=0, in_iMinutesOffset=0,
                       in_iSecondsOffset=0, in_iFramesOffset=0):

    hours, minutes, seconds, frames = [int(val) for val in in_Tc.split(TC_SEPARATOR)]

    frames += in_iFramesOffset
    if frames < 0:
        frames += FPS
        in_iSecondsOffset -= 1
    elif frames >= FPS:
        frames -= FPS
        in_iSecondsOffset += 1

    seconds += in_iSecondsOffset
    if seconds < 0:
        seconds += 60
        in_iMinutesOffset -= 1
    elif seconds >= 60:
        seconds -= 60
        in_iMinutesOffset += 1

    minutes += in_iMinutesOffset
    if minutes < 0:
        minutes += 60
        in_iHoursOffset -= 1
    elif minutes >= 60:
        minutes -= 60
        in_iHoursOffset += 1

    hours += in_iHoursOffset

    return hours * 3600 + minutes * 60 + seconds + frames / FPS

def parseEdl(in_sEdlPath, in_sSeqFilter=None):

    shots = []

    with open(in_sEdlPath, 'r') as f:
        lines = f.readlines()

    tcRegEx = re.compile("(\d+)\s+GEN\s+V\s+C\s+\d{2}:\d{2}:\d{2}:\d{2}\s+\d{2}:\d{2}:\d{2}:\d{2}\s+(\d{2}:\d{2}:\d{2}:\d{2})\s+(\d{2}:\d{2}:\d{2}:\d{2})")
    shotRegEx = re.compile(".*FROM CLIP NAME:  (SQ\d{4}[a-zA-Z]?)\s+(P\d{4}[a-zA-Z]?)")
    seqRegEx = re.compile(".*FROM CLIP NAME:  (SQ\d{4}[a-zA-Z]?)")

    numLines = len(lines)

    for counter in range(numLines):
        matchObj = tcRegEx.match(lines[counter])
        if matchObj:
            shotMatchObj = shotRegEx.match(lines[counter + 1])

            if shotMatchObj:
                shots.append({
                            "index":matchObj.group(1).strip(),
                            "sequence":shotMatchObj.group(1).strip(),
                            "shot":shotMatchObj.group(2).strip(),
                            "start":matchObj.group(2).strip(),
                            "end":matchObj.group(3).strip()
                            })
            else:
                seqMatchObj = seqRegEx.match(lines[counter + 1])
                if seqMatchObj:
                    shots.append({
                                "index":matchObj.group(1).strip(),
                                "sequence":seqMatchObj.group(1).strip(),
                                "shot":'P0000A',
                                "start":matchObj.group(2).strip(),
                                "end":matchObj.group(3).strip()
                                })
                else:
                    print ("Error reading shot info for line {0} ({1})"
                            .format(counter, lines[counter + 1].replace('\n', '')))
                    return None
    return shots

def ffmpegAppPath():
    p = osp.normpath(osp.join(os.environ["Z2K_LAUNCH_SCRIPT"].split("launchers")[0], "movSplitter", "ffmpeg", "bin", "ffmpeg.exe"))
    if not osp.isfile(p):
        raise EnvironmentError("FFMPEG command-line tool not found: '{}'.".format(p))

    return p

def h264ToProres(inSeqList, shotStep='01_previz'):
    """
    There are 4 profiles that exist within Prores: Proxy, LT, SQ and HQ (and then optionally 4444). In ffmpeg these profiles are assigned numbers (0 is Proxy and 3 is HQ)
    ex:
    from zomblib import editing
    reload (editing)
    editing.h264ToProres(["sq0140"], shotStep='04_anim')
    """

    sFfmpegPath = ffmpegAppPath()
    shotDir = osp.normpath(osp.join(os.environ["ZOMB_SHOT_LOC"], "zomb", "shot"))
    montageDir = "//Zombiwalk/z2k/11_EXCHANGE_MONTAGE"
    sSeqShotDict = OrderedDict()

    if shotStep in ("01_previz", "02_layout", "04_anim", "06_finalLayout", "07_fx3d", "10_compo"):
        profile = 0
        shotExt = shotStep.split("_")[-1]
    else:
        raise ValueError("shotStep is not valid: '{}'.".format(shotStep))

    for eachSeq in os.listdir(shotDir):
        if re.match('^sq[0-9]{4}$', eachSeq) and (eachSeq in inSeqList or not inSeqList):
            for eachShot in os.listdir(osp.normpath(osp.join(shotDir, eachSeq))):
                if re.match('^sq[0-9]{4}_sh[0-9]{4}a$', eachShot):
                    #sSeqShotDict[eachSeq].append(eachShot)
                    sSeqShotDict.setdefault(eachSeq, []).append(eachShot)

    for each in inSeqList:
        if each not in sSeqShotDict.keys():
            raise ValueError("'{}' sequence could not be found".format(each))

    sTmpBatPath = osp.normpath(osp.join(os.environ["temp"], "conv2prores.bat"))
    print "#### {:>7}: writing temp batch file: '{}'".format("Info", sTmpBatPath)

    oDate = datetime.today()

    with open(sTmpBatPath, "w") as tmpBatFile:

        for seqName, shotNameList in sSeqShotDict.items():

            sDate = str(oDate.year) + "-" + str(oDate.month) + "-" + str(oDate.day)
            outDir = osp.normpath(osp.join(montageDir, shotStep, seqName, sDate))

            tmpBatFile.write("\n")

            if not osp.isdir(outDir):
                #print "#### {:>7}: Create directory: '{}'".format("Info",outDir )
                os.makedirs(outDir)

            for shotName in shotNameList:
                inDir = osp.normpath(osp.join(shotDir, seqName, shotName, shotStep, "_version"))
                if  not osp.isdir(inDir):
                    print "#### {:>7}: Directory could not be found: '{}'".format("Error", inDir)
                    continue
                videoList = []
                for each in os.listdir(inDir):
                    if re.match('^sq[0-9]{4}_sh[0-9]{4}[a-z]{1}_[a-zA-Z0-9\-]{1,24}.mov$', each):
                        videoList.append(each)
                if len (videoList) < 2:
                    print "#### {:>7}: no video found in directory: '{}'".format("Warning", inDir)
                    continue
                videoList.sort()
                inFile = osp.normpath(osp.join(inDir, videoList[-1]))
                outFile = osp.normpath(osp.join(outDir, videoList[-1]))
                finalCommand = ("{0} -i {1} -c:v prores_ks -profile:v {2} {3}"
                                .format(sFfmpegPath, inFile, profile, outFile))
                tmpBatFile.write(finalCommand + "\n")

        tmpBatFile.write("\n")
        tmpBatFile.write("pause\n")

    subprocess.call("explorer /select, {}".format(sTmpBatPath))


def getFinalImgSeq(inSeqList, bStereo=False, outputDir = ""):
    log = LogBuilder(gui=False, funcName ="")
    proj = DamProject("zombillenium", user="rrender", password="arn0ld&r0yal", standalone=True)
    proj.loadEnviron()

    shotDir = osp.normpath(osp.join(os.environ["ZOMB_SHOT_LOC"], "zomb", "shot"))
    if not outputDir:
        outputDir = os.environ["ZOMB_OUTPUT_PATH"]
    sSeqShotDict = OrderedDict()
    oDate = datetime.today()
    sDate = str(oDate.year) + "-" + str(oDate.month) + "-" + str(oDate.day)
    slogSeqPath=""

    def deleteDir(toDelete =""):
        txt = "delete '{}'".format(toDelete)
        log.printL("i", txt)
        logFile.write(txt + "\n")
        shutil.rmtree(toDelete)

    def copySeqDir(inSeqDir="", outSeqDir=""):

        versPkg = proj.entryFromPath(inSeqDir)
        headPkg = versPkg.getHeadFile(dbNode=False)
        headPkgLyrName = os.path.split(versPkg.absPath())[-1]

        if os.path.split(inSeqDir)[-1]!= headPkgLyrName:
            txt = "version mismatch, last output found: '{}', last published version: {}".format(inSeqDir,headPkgLyrName)
            log.printL("e", txt)
            logFile.write(txt + "\n")
            return

        if os.path.isdir(outSeqDir):
            txt = "is up to date:'{}'".format(outSeqDir)
            log.printL("i", txt)
            logFile.write(txt + "\n")
        else:
            try:
                shutil.copytree(inSeqDir, outSeqDir)
            except:
                raise
            txt = "copy '{}' --> '{}'".format(inSeqDir,outSeqDir)
            log.printL("i", txt)
            logFile.write(txt + "\n")
        if os.path.isdir(outSeqDir):
            exrL=[]
            for eachFile in os.listdir(outSeqDir):
                if ".json" in eachFile:
                    os.remove(osp.normpath(osp.join(outSeqDir, eachFile)))
                if ".exr" in eachFile:
                    exrL.append(eachFile)

            shotS = osp.normpath(inSeqDir).split("shot")[-1].split("\\")[2]
            damShot = proj.getShot(shotS)
            sgShot = damShot.getSgInfo()
            duration = damutils.getShotDuration(sgShot)
            if duration != len(exrL):
                txt = "wrong frame number, {} '.exr' found, but shotgun duration is {} \n".format(len(exrL),duration)
                log.printL("e", txt)
                logFile.write("####   Error: "+txt + "\n")

        
    for eachSeq in os.listdir(shotDir):
        if re.match('^sq[0-9]{4}$', eachSeq) and (eachSeq in inSeqList or not inSeqList):
            for eachShot in os.listdir(osp.normpath(osp.join(shotDir, eachSeq))):
                if re.match('^sq[0-9]{4}_sh[0-9]{4}a$', eachShot):
                    #sSeqShotDict[eachSeq].append(eachShot)
                    sSeqShotDict.setdefault(eachSeq, []).append(eachShot)

    for each in inSeqList:
        if each not in sSeqShotDict.keys():
            raise ValueError("'{}' sequence could not be found".format(each))

    for seqName, shotNameList in sSeqShotDict.items():
        shotNameList.sort()
        if bStereo:
            outDir = osp.normpath(osp.join(outputDir, 'final_stereo', seqName))
        else:
            outDir = osp.normpath(osp.join(outputDir, 'final_mono', seqName))

        if not osp.isdir(outDir):
            os.makedirs(outDir)
        outDirL = os.listdir(outDir)

        slogSeqPath = osp.normpath(osp.join(outDir, "log_"+sDate+".txt"))
        with open(slogSeqPath, "w") as logFile:
            for shotName in shotNameList:
                log.printL("i", shotName)
                logFile.write(shotName + "\n")

                inDir = osp.normpath(osp.join(shotDir, seqName, shotName, '10_compo', "_version"))
                if  not osp.isdir(inDir):
                    txt = "Directory could not be found: '{}'\n".format(inDir)
                    log.printL("e", txt)
                    logFile.write("####   Error: "+txt + "\n")
                    continue

                imgSeqList = []
                imgSeqLeftList = []
                imgSeqRightList = []
                for each in os.listdir(inDir):
                    if bStereo:
                        if re.match('^lyr_sq[0-9]{4}_sh[0-9]{4}[a-z]{1}_left-v[0-9]{3}$', each):
                            if not "-v000" in each:
                                imgSeqLeftList.append(each)
                        elif re.match('^lyr_sq[0-9]{4}_sh[0-9]{4}[a-z]{1}_right-v[0-9]{3}$', each):
                            if not "-v000" in each:
                                imgSeqRightList.append(each)
                    else:
                        if re.match('^lyr_sq[0-9]{4}_sh[0-9]{4}[a-z]{1}-v[0-9]{3}$', each):
                            if not "-v000" in each:
                                imgSeqList.append(each)

                if bStereo:
                    if len (imgSeqLeftList) < 1 or len (imgSeqRightList) < 1:
                        txt = "One or Both eyes missing in directory: '{}'\n".format(inDir)
                        log.printL("w", txt)
                        logFile.write("#### Warning: "+txt + "\n")
                        continue

                    imgSeqLeftList.sort()
                    inSeqLeftDir = osp.normpath(osp.join(inDir, imgSeqLeftList[-1]))
                    outSeqLeftDir = osp.normpath(osp.join(outDir, imgSeqLeftList[-1]))
                    for eachOut in outDirL:
                        if imgSeqLeftList[-1].split("-v")[0] in eachOut and eachOut != imgSeqLeftList[-1]:
                            deleteDir(toDelete = osp.normpath(osp.join(outDir, eachOut)))
                    copySeqDir(inSeqDir=inSeqLeftDir, outSeqDir=outSeqLeftDir)

                    imgSeqRightList.sort()
                    inSeqRightDir = osp.normpath(osp.join(inDir, imgSeqRightList[-1]))
                    outSeqRightDir = osp.normpath(osp.join(outDir, imgSeqRightList[-1]))
                    if imgSeqRightList[-1].split("-v")[0] in eachOut and eachOut != imgSeqRightList[-1]:
                        deleteDir(toDelete = osp.normpath(osp.join(outDir, eachOut)))
                    copySeqDir(inSeqDir=inSeqRightDir, outSeqDir=outSeqRightDir)
                else:
                    if len (imgSeqList) < 1:
                        txt = "Nothing found in directory: '{}'\n".format(inDir)
                        log.printL("w", txt)
                        logFile.write("#### Warning: "+txt + "\n")
                        continue
                    imgSeqList.sort()
                    inSeqDir = osp.normpath(osp.join(inDir, imgSeqList[-1]))
                    outSeqDir = osp.normpath(osp.join(outDir, imgSeqList[-1]))


                    for eachOut in outDirL:
                        if imgSeqList[-1].split("-v")[0] in eachOut and eachOut != imgSeqList[-1]:
                            deleteDir(toDelete = osp.normpath(osp.join(outDir, eachOut)))
                    copySeqDir(inSeqDir=inSeqDir, outSeqDir=outSeqDir)

                print ""
                logFile.write("\n")





def makeFilePath(sDirPath, sBaseFileName, sExt, frame=None, padding=4):

    sFrameExt = ""
    if isinstance(frame, int):
        sFrameExt = "{:0{}d}".format(frame, padding)
    elif isinstance(frame, basestring):
        sFrameExt = padding * frame

    sFilename = ".".join((sBaseFileName, sFrameExt, sExt))
    return osp.normpath(osp.join(sDirPath, sFilename)).replace("\\", "/")

def movieToJpegSequence(sMoviePath, sOutDirPath, sBaseFileName, padding=4):

    sFfmpegPath = ffmpegAppPath()
    sBaseFileName = sBaseFileName.split('.', 1)[0]
    sExt = "jpg"
    sFilename = ".".join((sBaseFileName, "%0{}d".format(padding), sExt))
    sOutFilePath = osp.normpath(osp.join(sOutDirPath, sFilename))
    cmdArgs = [sFfmpegPath, "-i", osp.normpath(sMoviePath), "-q:v", "2", sOutFilePath]

    subprocess.check_call(cmdArgs)

    sFilename = ".".join((sBaseFileName, "{:0{}d}".format(1, padding), sExt))
    return makeFilePath(sOutDirPath, sBaseFileName, sExt, frame=1, padding=padding)

def convToH264(sInputPath, sOutputPath):

    cmdArgs = [ffmpegAppPath(),
               '-y', '-i',
               osp.normpath(sInputPath),
               '-c:v', 'libx264',
               '-vf', 'colormatrix=bt601:bt709',
               '-preset', 'medium',
               '-crf', '14',
               '-pix_fmt', 'yuv420p',
               '-c:a', 'copy',
               osp.normpath(sOutputPath)]

    return subprocess.check_call(cmdArgs)

def playMovie(sMoviePath, pushToRv="", sequenceId=None):

    sCmd = ""
    bShell = False
    if pushToRv:
        sTag = pushToRv
        if not rvutils.sessionExists(sTag):
            return rvutils.openToSgSequence(sequenceId, tag=sTag, source=sMoviePath)
        else:
            sLauncherLoc = osp.dirname(os.environ["Z2K_LAUNCH_SCRIPT"])
            p = osp.join(sLauncherLoc, "rvpush.bat")
            sCmd = p + " -tag {} merge {}".format(sTag, osp.normpath(sMoviePath))

    if not sCmd:
        sCmd = "start {}".format(osp.normpath(sMoviePath))
        bShell = True

    return subprocess.call(sCmd, shell=bShell)
