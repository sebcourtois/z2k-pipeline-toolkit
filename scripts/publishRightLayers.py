import os
import sys
import re
from zomblib import shutiloptim as shutil
from collections import OrderedDict
osp = os.path
from datetime import datetime

from zomblib import damutils
from davos.core.damproject import DamProject

renderPath =  sys.argv[-1]
print 'renderPath',renderPath



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
    

def normPath(p):
    return os.path.normpath(p).replace("\\",'/')


def getImgSeqInfo(lyrPathS = "",  gui = False):
    log = LogBuilder(gui=gui, funcName ="getImgSeqInfo")
    missingFrameL =[]
    frameNumberI = 0
    lastImgI = 0
    firstImgI = 0

    exrL = []
    imgNumL = []
    imgRadicalL=[]
    for each in os.listdir(lyrPathS):
        if re.match('^[a-zA-Z0-9_]{0,128}.[0-9]{4}.exr$', each):
            if each.split(".")[0] not in imgRadicalL:
                imgRadicalL.append(each.split(".")[0])
            exrL.append(each)
            imgNumL.append(int(each.split(".")[1]))

    if not exrL:
        return dict(resultB=log.resultB, logL=log.logL, firstImgI=0, lastImgI=0, missingFrameL=missingFrameL, frameNumberI=0)

    if len(imgRadicalL)!=1:
        log.printL("e","'{}' several 'name.####.ext' image sequence found in: '{}'".format(lyrPathS))
        return dict(resultB=log.resultB, logL=log.logL, firstImgI=0, lastImgI=0, missingFrameL=missingFrameL, frameNumberI=0)

    exrL.sort()
    imgNumL.sort()
    imgNameS = exrL[0]
    imgRadS = imgNameS.split(".")[0]
    imgExtS = imgNameS.split(".")[-1]

    firstImgI = int(exrL[0].split(".")[1])
    lastImgI= int(exrL[-1].split(".")[1])

    missingFrameI = lastImgI-firstImgI+1-len(exrL)
    missingFrameL = []
    if missingFrameI:
        n = int (firstImgI)
        while n<lastImgI:
            if n not in imgNumL:
                missingFrameL.append(n)
            n+=1
    return dict(resultB=log.resultB, logL=log.logL, firstImgI=firstImgI, lastImgI=lastImgI, missingFrameL=missingFrameL, frameNumberI=len(exrL))



def getLayerInfo(layerPathS="", gui = False, lastVerOnly = True, specificLayerOnlyL =[]):
    log = LogBuilder(gui=gui, funcName ="getLayerInfo")
    layerInfoD = OrderedDict()
    if  not osp.isdir(layerPathS):
        txt = "Directory could not be found: '{}'\n".format(layerPathS)
        log.printL("e", txt)
        logFile.write("####   Error: "+txt + "\n")
        return layerInfoD
    else:
        versDirL = os.listdir(layerPathS)
        versDirL.sort()
        proccedLayerPairL = []
        for each in versDirL:
            if specificLayerOnlyL and each not in specificLayerOnlyL:
                continue

            if re.match('^lyr_[a-zA-Z0-9_]{0,128}-v[0-9]{3}$', each):
                #get the last version published
                lastVerS=""
                lastVersLyrS=""        

                lyrBaseNameS=each.split("-v")[0]
                if lyrBaseNameS not in proccedLayerPairL:
                    layerPairL = []
                    for eachItem in versDirL:
                        if lyrBaseNameS == eachItem.split("-v")[0]:
                            layerPairL.append(eachItem)
                    layerPairL.sort()
                    if layerPairL and lastVerOnly:
                        lastVersLyrS = layerPairL[-1]
                        lastVerS = str(lastVersLyrS.split("-v")[-1])
                        resultD = getImgSeqInfo(lyrPathS = osp.normpath(osp.join(layerPathS,lastVersLyrS)),  gui = False)
                        imgSeqDataD = {'firstFrame': resultD["firstImgI"], 'lastFrame': resultD["lastImgI"], 'frameNumber': resultD["frameNumberI"], "missingFrameL": resultD["missingFrameL"] }
                        layerInfoD[lastVersLyrS] = dict(imgSeqDataD)
                        proccedLayerPairL.append(each)

        return layerInfoD 


def layerScan(inRenderDirS= "",  outputDir = "", rmRightPubLayerB=False, dryRun = False):
    log = LogBuilder(gui=False, funcName ="")
    if dryRun:
        rmRightPubLayerB=False

    proj = DamProject("zombillenium", user="rrender", password="arn0ld&r0yal", standalone=True)
    proj.loadEnviron()
    inRenderDirS =normPath(inRenderDirS)

    def moveLayer(sourcePathS="", targetPathS="", dryRun= False):
        if not dryRun:
            try:
                logS = "rename  '{}'\n    ->  '{}'".format(sourcePathS, targetPathS)
                os.rename(sourcePathS, targetPathS)
            except OSError:
                logS = "copying '{}'\n    ->  '{}'".format(sourcePathS, targetPathS)
                shutil.copytree(sourcePathS, targetPathS, symlinks=False, ignore=None)
                #shutil.move(sourcePathS, targetPathS)
        else:
            logS = "dry run '{}' -> to -> '{}'".format(sourcePathS, targetPathS)
        return logS


    #shotDir = osp.normpath(osp.join(os.environ["ZOMB_SHOT_LOC"], "zomb", "shot"))
    if not outputDir:
        outputDir = os.environ["ZOMB_OUTPUT_PATH"]

    seqNameS = inRenderDirS.split("/")[-5]
    shotNameS = inRenderDirS.split("/")[-4]

    leftLayerInfoD = getLayerInfo(layerPathS = osp.normpath(osp.join(outputDir, seqNameS, shotNameS, 'left', "_version")))
    rightLayerInfoD = getLayerInfo(layerPathS = osp.normpath(osp.join(outputDir, seqNameS, shotNameS, 'right', "_version")))
    rightUnPubLayerInfoD = getLayerInfo(layerPathS = inRenderDirS)
    #print 'leftLayerInfoD', leftLayerInfoD
    #print 'rightLayerInfoD', rightLayerInfoD

    unusedLayerL =[]
    pubLyrNameNkL = []
    unPubLyrPathNkL = []
    publishLogL = []

    damShot = proj.getShot(shotNameS)
    sgShot = damShot.getSgInfo()
    sgDurationI = damutils.getShotDuration(sgShot)
    sgFirstFrameI = 101
    sgLastFrameI = sgDurationI + 100
    sgRangeL = [sgFirstFrameI, sgLastFrameI]


    oDate = datetime.today()
    sDate = str(oDate.year) + "-" + str(oDate.month) + "-" + str(oDate.day)
    logFilePathS = osp.normpath(osp.join(os.path.dirname(os.path.dirname(inRenderDirS)), "log_rightLayerPublish_"+seqNameS+"_"+sDate+".txt"))
    with open(logFilePathS, "w") as logFile:
        log.printL("", shotNameS+' '+str(sgRangeL))
        logFile.write(shotNameS+' '+str(sgRangeL)+ "\n")
        for leftLayerKeyS, leftLayerValueD in leftLayerInfoD.iteritems():
            if leftLayerKeyS not in pubLyrNameNkL and pubLyrNameNkL:
                unusedLayerL.append(leftLayerKeyS)
                continue
            txt = "    {}".format(leftLayerKeyS)
            log.printL("", txt)
            logFile.write(txt + "\n")

            validLeftLyrB = False
            if leftLayerInfoD[leftLayerKeyS]['frameNumber']==0:
                txt = "        left  : {}".format('Empty layer, frameNumber = 0')
                log.printL("", txt)
                logFile.write(txt + "")
            elif leftLayerInfoD[leftLayerKeyS]['missingFrameL']:
                txt = "        left  : Missing frames {}'".format(leftLayerInfoD[leftLayerKeyS]['missingFrameL'])
                log.printL("", txt)
                logFile.write(txt + "\n")
            else :
                if leftLayerInfoD[leftLayerKeyS]['frameNumber'] != sgDurationI:
                    layerRangeL = [leftLayerInfoD[leftLayerKeyS]['firstFrame'], leftLayerInfoD[leftLayerKeyS]['lastFrame']]
                    txt = "        left  : {}".format('OK '+str(layerRangeL))
                    log.printL("", txt)
                    logFile.write(txt + "\n")
                    validLeftLyrB = True
                else:
                    txt = "        left  : {}".format('OK')
                    log.printL("", txt)
                    logFile.write(txt + "\n")
                    validLeftLyrB = True

            validRightLyrB = False
            publishStateS = ""

            if  leftLayerKeyS in rightUnPubLayerInfoD.keys():
                targetPathS=normPath(osp.join(outputDir, seqNameS, shotNameS, 'right', "_version",leftLayerKeyS))
                removedtargetDirB = False
                if not os.listdir(targetPathS):
                    removedtargetDirB = True
                    shutil.rmtree(targetPathS)

                if not leftLayerKeyS in rightLayerInfoD.keys() or removedtargetDirB:
                    logS = moveLayer(sourcePathS=normPath(osp.join(inRenderDirS,leftLayerKeyS)), targetPathS=targetPathS, dryRun= dryRun)
                    publishLogL.append(logS)
                    rightLayerInfoD = getLayerInfo(layerPathS = osp.normpath(osp.join(outputDir, seqNameS, shotNameS, 'right', "_version")))
                    publishStateS = "        ### published succesfully ###"
                else:
                    publishStateS = "        ### layer available for publish in your private ###"


            if not leftLayerKeyS in rightLayerInfoD.keys():
                txt = "        right : {}{}".format('missing layer',publishStateS)
                log.printL("", txt)
                logFile.write(txt + "\n")
            elif rightLayerInfoD[leftLayerKeyS]['frameNumber']==0:
                txt = "        right : {}{}".format('Empty layer, frameNumber = 0',publishStateS)
                log.printL("", txt)
                logFile.write(txt + "\n")
            elif rightLayerInfoD[leftLayerKeyS]['missingFrameL']:
                txt = "        right : Missing frames {}{}".format(rightLayerInfoD[leftLayerKeyS]['missingFrameL'],publishStateS)
                log.printL("", txt)
                logFile.write(txt + "\n")
            else :
                if rightLayerInfoD[leftLayerKeyS]['frameNumber'] != sgDurationI:
                    layerRangeL = [rightLayerInfoD[leftLayerKeyS]['firstFrame'], rightLayerInfoD[leftLayerKeyS]['lastFrame']]
                    txt = "        right : {}{}".format('OK '+str(layerRangeL), publishStateS)
                    log.printL("", txt)
                    logFile.write(txt + "\n")
                    validRightLyrB = True
                else:
                    txt = "        right : {}{}".format('OK', publishStateS)
                    log.printL("", txt)
                    logFile.write(txt + "\n")
                    validRightLyrB = True


            if not validLeftLyrB or not validRightLyrB:
                txt = "        stereo: {}".format('check failed, one of your layer is not valid')
                log.printL("", txt)
                logFile.write(txt + "\n")
            else:
                if rightLayerInfoD[leftLayerKeyS]['frameNumber'] == leftLayerInfoD[leftLayerKeyS]['frameNumber']:
                    txt = "        stereo: {}".format('OK')
                    log.printL("", txt)
                    logFile.write(txt + "\n")
                else:
                    txt = "        stereo: {}".format('check failed, left and right have a different frame number')
                    log.printL("", txt)
                    logFile.write(txt + "\n")

            if unPubLyrPathNkL:
                txt = "        Unpublished layers: {}".format(unPubLyrPathNkL)
                log.printL("", txt)
                logFile.write(txt + "\n")
            if unusedLayerL:
                txt = "        Unused layers: {}".format(unusedLayerL)
                log.printL("", txt)
                logFile.write(txt + "\n")
        

            #print leftLayerKeyS, rightLayerInfoD[leftLayerKeyS]
            #print "" 
        print ""
        logFile.write("\n")
        print ""
        logFile.write("\n")

        if publishLogL:
            txt = "publish log:"
            log.printL("", txt)
            logFile.write(txt + "\n")
            for each in publishLogL:
                log.printL("", each)
                logFile.write(each + "\n")




	
layerScan(inRenderDirS= renderPath)



