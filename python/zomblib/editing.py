
import os
import re
from datetime import datetime
from collections import OrderedDict
import subprocess

osp = os.path

FPS = 24.0
TC_SEPARATOR = ":"

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
    shotRegEx = re.compile(".*FROM CLIP NAME:  (SQ\d{4}[a-zA-Z]?)\s\s(P\d{4}[a-zA-Z]?)")
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
    """

    sFfmpegPath = ffmpegAppPath()
    shotDir = osp.normpath(osp.join(os.environ["ZOMB_SHOT_LOC"], "zomb", "shot"))
    montageDir = "//Zombiwalk/z2k/11_EXCHANGE_MONTAGE"
    sSeqShotDict = OrderedDict()

    if shotStep in ("01_previz", "02_layout"):
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

            if  not osp.isdir(outDir):
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

