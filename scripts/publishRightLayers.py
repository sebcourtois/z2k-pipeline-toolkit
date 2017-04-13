import os
import sys
import re
from zomblib import shutiloptim as shutil
from collections import OrderedDict
import subprocess
osp = os.path
from datetime import datetime

from zomblib import damutils
from davos.core.damproject import DamProject
from pytd.util.fsutils import jsonWrite, jsonRead

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
        #logFile.write("####   Error: "+txt + "\n")
        return layerInfoD
    else:
        versDirL = os.listdir(layerPathS)
        versDirL.sort()
        proccedLayerPairL = []
        for each in versDirL:
            if specificLayerOnlyL: 
                if each in specificLayerOnlyL:
                    resultD = getImgSeqInfo(lyrPathS = osp.normpath(osp.join(layerPathS,each)),  gui = False)
                    imgSeqDataD = {'firstFrame': resultD["firstImgI"], 'lastFrame': resultD["lastImgI"], 'frameNumber': resultD["frameNumberI"], "missingFrameL": resultD["missingFrameL"] }
                    layerInfoD[each] = dict(imgSeqDataD)
                    proccedLayerPairL.append(each)
            else:
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


def layerScan(inRenderDirS= "",  outputDir = "", rmRightPubLayerB=False, useBreakDown = True, dryRun = False):
    log = LogBuilder(gui=False, funcName ="")
    if dryRun:
        rmRightPubLayerB=False

    proj = DamProject("zombillenium", user="rrender", password="arn0ld&r0yal", standalone=True)
    proj.loadEnviron()

    inRenderDirS =normPath(inRenderDirS)
    if not outputDir:
        outputDir = os.environ["ZOMB_OUTPUT_PATH"]
    outputTrashDirS = normPath(osp.join(osp.dirname(outputDir),"outputTrash"))



    def renameDir(sourcePathS="", targetPathS="", dryRun= False, verboseB = False):
        log = LogBuilder(gui=False, funcName ="renameDir")
        logL = []

        if os.path.isdir(targetPathS):
            if os.listdir(targetPathS):
                txt = "target dir is a non empty directory: {}".format(targetPathS)
                log.printL("e", txt)
                return  dict(resultB=log.resultB, logL=log.logL)
            else:
                try:
                    os.rmdir(targetPathS)
                except Exception as err:
                    txt = "target directory already exists and could not be removed: {}".format(targetPathS)
                    log.printL("e", txt)
                    log.printL("e", err)
                    return dict(resultB=log.resultB, logL=log.logL)
        try:
            os.rename(sourcePathS,sourcePathS)
        except Exception as err:
            txt = "could not rename directory: {}".format(sourcePathS)
            log.printL("e", txt)
            log.printL("e", err)
            return dict(resultB=log.resultB, logL=log.logL)

        if not dryRun:
                os.rename(sourcePathS,targetPathS)
                txt = "rename: {}\n{}".format(sourcePathS,targetPathS)
                log.printL("i", txt)
        else:
            txt = "dryRun rename: {}\n{}".format(sourcePathS,targetPathS)
            log.printL("i", txt)

        return dict(resultB=log.resultB, logL=log.logL)


    def renameDirContent(sourcePathS="", targetPathS="", dryRun= False, verboseB= False):
        log = LogBuilder(gui=False, funcName ="renameDirContent")
        logL = []

        if os.path.isdir(targetPathS):
            if os.listdir(targetPathS):
                txt = "target dir is a non empty directory: {}".format(targetPathS)
                log.printL("e", txt)
                return  dict(resultB=log.resultB, logL=log.logL)
        else:
            os.makedirs(targetPathS)

        sourcePathContentL = os.listdir(sourcePathS)
        if sourcePathContentL:
            failedElemL = []
            for each in sourcePathContentL:
                if "." in each:
                    try:
                        os.rename(normPath(osp.join(sourcePathS, each)),normPath(osp.join(sourcePathS, each)))
                    except Exception as err:
                        txt = "could not rename: {}".format(normPath(osp.join(sourcePathS, each)))
                        log.printL("e", txt)
                        log.printL("e", err)
                        failedElemL.append(each)

            if failedElemL:
                return  dict(resultB=log.resultB, logL=log.logL)


        if not dryRun:
            for each in sourcePathContentL:
                if "." in each:
                    os.rename(normPath(osp.join(sourcePathS, each)),normPath(osp.join(targetPathS, each)))
            if not os.listdir(sourcePathS):
                try:
                    os.rmdir(sourcePathS)
                except:
                    pass
            if verboseB:
                txt = "rename: {}\n{}".format(sourcePathS,targetPathS)
                log.printL("i", txt)

        else:
            txt = "dryRun rename: {}\n{}".format(sourcePathS,targetPathS)
            log.printL("i", txt)

        return dict(resultB=log.resultB, logL=log.logL)


    def pubRightLayer(sourcePathS="", targetPathS="", trashRootS="",dryRun= dryRun):
        log = LogBuilder(gui=False, funcName ="pubRightLayer")


        sourcePathS = normPath(sourcePathS)
        targetPathS = normPath(targetPathS)
        trashRootS = normPath(trashRootS)

        if not osp.isdir(trashRootS):
            os.makedirs(trashRootS)

        if osp.isdir(targetPathS):
            if os.listdir(targetPathS):
                trashContentL = os.listdir(trashRootS)
                sourceNameS= osp.basename(sourcePathS)
                inTrashL=[]
                for each in trashContentL:
                    if sourceNameS in each and "-t" in each:
                        inTrashL.append(each)
                if inTrashL:
                    inTrashL.sort()
                    lastTrashVersionI= int(inTrashL[-1].split("-t")[-1])
                    nextTrashVersionS = "t"+'{0:03d}'.format(lastTrashVersionI+1)
                else:
                    nextTrashVersionS = "t001"

                trashPathS = normPath(osp.join(trashRootS, sourceNameS+"-"+nextTrashVersionS))
                resultD = renameDir(sourcePathS=targetPathS, targetPathS=trashPathS, dryRun= dryRun)
                log.logL.extend(resultD['logL'])
                if not resultD["resultB"]:
                    result2D = renameDirContent(sourcePathS=targetPathS, targetPathS=trashPathS, dryRun= dryRun)
                    log.logL.extend(result2D['logL'])
                    if not result2D["resultB"]:
                        txt = "could not move old published layer to trash: {}".format(targetPathS)
                        log.printL("e", txt)     
                        return dict(resultB=log.resultB, logL=log.logL)


        resultD = renameDir(sourcePathS=sourcePathS, targetPathS=targetPathS, dryRun= dryRun)
        log.logL.extend(resultD['logL'])
        if not resultD["resultB"]:
            result2D = renameDirContent(sourcePathS=sourcePathS, targetPathS=targetPathS, dryRun= dryRun)
            log.logL.extend(result2D['logL'])
            if not result2D["resultB"]:
                txt = "could not move layer to target directory: {}".format(targetPathS)
                log.printL("e", txt)     
                return dict(resultB=log.resultB, logL=log.logL)

        return dict(resultB=log.resultB, logL=log.logL)




    seqNameS = inRenderDirS.split("/")[-5]
    shotNameS = inRenderDirS.split("/")[-4]


    publishedLayersD = {}
    unPublishedLayersD = {}
    layerBreakdown_json = normPath(osp.join(outputDir, seqNameS, shotNameS, 'layerBreakdown.json'))
    if osp.isfile(layerBreakdown_json):
        layerBreakdownD = jsonRead(layerBreakdown_json)
        publishedLayersD = layerBreakdownD['publishedLayersD']
        unPublishedLayersD = layerBreakdownD['unPublishedLayersD']
  
    if not publishedLayersD.keys() and useBreakDown:
        txt = "no breakdown file or empty published layer list: {}".format(layerBreakdown_json)
        log.printL("e", txt)
        return


    leftLayerInfoD = getLayerInfo(layerPathS = osp.normpath(osp.join(outputDir, seqNameS, shotNameS, 'left', "_version")),specificLayerOnlyL = publishedLayersD.keys())
    rightLayerInfoD = getLayerInfo(layerPathS = osp.normpath(osp.join(outputDir, seqNameS, shotNameS, 'right', "_version")),specificLayerOnlyL = publishedLayersD.keys())
    rightUnPubLayerInfoD = getLayerInfo(layerPathS = inRenderDirS,specificLayerOnlyL = publishedLayersD.keys())


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
        logList = []
        for leftLayerKeyS, leftLayerValueD in leftLayerInfoD.iteritems():
            if leftLayerKeyS not in pubLyrNameNkL and pubLyrNameNkL:
                unusedLayerL.append(leftLayerKeyS)
                continue
            txt = "    {}".format(leftLayerKeyS)
            logList.append(txt)
            logFile.write(txt + "\n")

            validLeftLyrB = False
            if leftLayerInfoD[leftLayerKeyS]['frameNumber']==0:
                txt = "        left  : {}".format('Empty layer, frameNumber = 0')
                logList.append(txt)
                logFile.write(txt + "")
            elif leftLayerInfoD[leftLayerKeyS]['missingFrameL']:
                txt = "        left  : Missing frames {}'".format(leftLayerInfoD[leftLayerKeyS]['missingFrameL'])
                logList.append(txt)
                logFile.write(txt + "\n")
            else :
                if leftLayerInfoD[leftLayerKeyS]['frameNumber'] != sgDurationI:
                    layerRangeL = [leftLayerInfoD[leftLayerKeyS]['firstFrame'], leftLayerInfoD[leftLayerKeyS]['lastFrame']]
                    txt = "        left  : {}".format('OK '+str(layerRangeL))
                    logList.append(txt)
                    logFile.write(txt + "\n")
                    validLeftLyrB = True
                else:
                    txt = "        left  : {}".format('OK')
                    logList.append(txt)
                    logFile.write(txt + "\n")
                    validLeftLyrB = True

            validRightLyrB = False
            publishStateS = ""

            if  leftLayerKeyS in rightUnPubLayerInfoD.keys():
                targetPathS=normPath(osp.join(outputDir, seqNameS, shotNameS, 'right', "_version",leftLayerKeyS))
                resultD = pubRightLayer(sourcePathS=normPath(osp.join(inRenderDirS,leftLayerKeyS)), targetPathS=targetPathS, trashRootS=osp.normpath(osp.join(outputTrashDirS, seqNameS, shotNameS, 'right', "_version")),dryRun= dryRun)
                if not resultD["resultB"]:
                    publishLogL.extend(resultD["logL"])
                    publishStateS = "        ### published failed:    "+resultD["logL"][-1]
                else:
                    publishStateS = "        ### published succesfully ###"

                rightLayerInfoD = getLayerInfo(layerPathS = osp.normpath(osp.join(outputDir, seqNameS, shotNameS, 'right', "_version")),specificLayerOnlyL = publishedLayersD.keys())


            if not leftLayerKeyS in rightLayerInfoD.keys():
                txt = "        right : {}{}".format('missing layer',publishStateS)
                logList.append(txt)
                logFile.write(txt + "\n")
            elif rightLayerInfoD[leftLayerKeyS]['frameNumber']==0:
                txt = "        right : {}{}".format('Empty layer, frameNumber = 0',publishStateS)
                logList.append(txt)
                logFile.write(txt + "\n")
            elif rightLayerInfoD[leftLayerKeyS]['missingFrameL']:
                txt = "        right : Missing frames {}{}".format(rightLayerInfoD[leftLayerKeyS]['missingFrameL'],publishStateS)
                logList.append(txt)
                logFile.write(txt + "\n")
            else :
                if rightLayerInfoD[leftLayerKeyS]['frameNumber'] != sgDurationI:
                    layerRangeL = [rightLayerInfoD[leftLayerKeyS]['firstFrame'], rightLayerInfoD[leftLayerKeyS]['lastFrame']]
                    txt = "        right : {}{}".format('OK '+str(layerRangeL), publishStateS)
                    logList.append(txt)
                    logFile.write(txt + "\n")
                    validRightLyrB = True
                else:
                    txt = "        right : {}{}".format('OK', publishStateS)
                    logList.append(txt)
                    logFile.write(txt + "\n")
                    validRightLyrB = True


            if not validLeftLyrB or not validRightLyrB:
                txt = "        stereo: {}".format('check failed, one of your layer is not valid')
                logList.append(txt)
                logFile.write(txt + "\n")
            else:
                if rightLayerInfoD[leftLayerKeyS]['frameNumber'] == leftLayerInfoD[leftLayerKeyS]['frameNumber']:
                    txt = "        stereo: {}".format('OK')
                    logList.append(txt)
                    logFile.write(txt + "\n")
                else:
                    txt = "        stereo: {}".format('check failed, left and right have a different frame number')
                    logList.append(txt)
                    logFile.write(txt + "\n")

            if unPubLyrPathNkL:
                txt = "        Unpublished layers: {}".format(unPubLyrPathNkL)
                logList.append(txt)
                logFile.write(txt + "\n")
            if unusedLayerL:
                txt = "        Unused layers: {}".format(unusedLayerL)
                logList.append(txt)
                logFile.write(txt + "\n")
        


        print ""
        logFile.write("\n")
        print ""
        logFile.write("\n")

        for each in logList:
            print each
        print ""
        print ""

        if publishLogL:
            txt = "publish log detail:"
            print txt
            logFile.write(txt + "\n")
            for each in publishLogL:
                log.printL("", each)
                logFile.write(each + "\n")




	
layerScan(inRenderDirS= renderPath)



