import os
import sys
import re
import shutil

def normPath(p):
    return os.path.normpath(p).replace("\\",'/')


def getLastVersionLayers(inDirS=""):
	allLayerL=[]
	for each in os.listdir(inDirS):
		if re.match('.*-v[0-9]{3}$', each):
			if not "-v000" in each:
				allLayerL.append(each)
	lastVersLayerL=[]
	baseNameDoneL=[]
	for each in allLayerL:
		lyrBaseNameS = each.split("-v")[0]
		layerTypeL = []
		if lyrBaseNameS not in baseNameDoneL:
			for eachItem in allLayerL:
				if lyrBaseNameS == eachItem.split("-v")[0]:
					layerTypeL.append(eachItem)
			layerTypeL.sort()
			lastVersLayerL.append(layerTypeL[-1])
			baseNameDoneL.append(lyrBaseNameS)
	return lastVersLayerL

def getExrCount(inDirS=""):
	exrCountI = 0
	if os.path.isdir(inDirS):
		for each in os.listdir(inDirS):
			if re.match('.*\.[0-9]{4}\.exr$', each):
				exrCountI +=1
	return exrCountI


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
            #shutil.move(layerPathS, versionDirS+"/"+layerNameNextVerS)
        except Exception,err:
            raise err

    return layerNameNextVerS






#print 'Argument List:', sys.argv
cwdS =  sys.argv[-1]

if "private" in cwdS:
	cwdElemL =normPath(cwdS).split("/private/")[-1].split("/")
	shotS = cwdElemL[-2]
	seqS = cwdElemL[-3]
else:
	err = "#### error: current working dir is not a 'private' directory structure: "+cwdS
	raise Exception(err)

privRight_pathS =  os.path.join(cwdS,"render","right")
if not os.path.exists(privRight_pathS):
	err = "#### error: no render right directory found, nothing to publish: "+privRight_pathS
	raise Exception(err)

outputS = os.environ["ZOMB_OUTPUT_PATH"]
outputLeftPathS =  normPath(os.path.join(outputS,seqS,shotS,"left","_version"))
outputRightPathS =  normPath(os.path.join(outputS,seqS,shotS,"right","_version"))

outLeft_lastVerLyrL = getLastVersionLayers(outputLeftPathS)
outRight_lastVerLyrL = getLastVersionLayers(outputRightPathS)

privRight_dirL=[]
for each in os.listdir(privRight_pathS):
	if os.path.isdir(privRight_pathS+"/"+each):
		privRight_dirL.append(each)



print "------------- publish right camera -------------"

for each in privRight_dirL:
	print ""
	print "--- "+each
	outLeft_lastVerDirS = ""
	for eachItem in outLeft_lastVerLyrL:
		if each in eachItem:
			outLeft_lastVerDirS = eachItem
			continue

	source_PathS = normPath(privRight_pathS+"/"+each)
	target_PathS = normPath(outputRightPathS+"/"+outLeft_lastVerDirS)

	privRight_exrCountI = getExrCount(inDirS=source_PathS)
	outLeft_exrCountI = getExrCount(inDirS=outputLeftPathS+"/"+outLeft_lastVerDirS)
	outRight_exrCountI = getExrCount(inDirS=target_PathS)

	if outLeft_exrCountI == 0:
		print "#### warning: nothing to publish, empty directory: "+source_PathS
		continue

	if outRight_exrCountI!=0:
		print "#### error: can't publish, right layer already exists: "+target_PathS
		continue

	elif os.path.isdir(target_PathS):
		try:
			shutil.rmtree(target_PathS, ignore_errors=False, onerror=None)
		except Exception,err:
			raise err

	try:
		if not os.path.isdir(privRight_pathS):
			os.makedirs(privRight_pathS)
		os.rename(source_PathS, target_PathS)
		#shutil.move(source_PathS, target_PathS)
		print "    move : '{}'".format(source_PathS)
		print "    to --> '{}'".format(target_PathS)
	except Exception,err:
		raise err
	


print ""
print "------------- listing -------------"

for each in outLeft_lastVerLyrL:
	print ""
	print "--- "+each


	left_pathS = normPath(outputLeftPathS+"/"+each)
	right_PathS = normPath(outputRightPathS+"/"+each)

	outLeft_exrCountI = getExrCount(inDirS=left_pathS)
	outRight_exrCountI = getExrCount(inDirS=right_PathS)

	if outLeft_exrCountI == outRight_exrCountI:
		print "OK"
	else:
		print "missmach frame number: left={}, right={}".format(outLeft_exrCountI,outRight_exrCountI)


# contenu du publishRightLayer.bat a creer dans le repertoire private
#rem set pythonFile="C:\Users\%USERNAME%\zombillenium\z2k-pipeline-toolkit\scripts\publishRightLayers.py"
#set pythonFile="C:\Users\%USERNAME%\DEVSPACE\git\z2k-pipeline-toolkit\scripts\publishRightLayers.py"
#set setup_env_tools="C:\Users\%USERNAME%\DEVSPACE\git\z2k-pipeline-toolkit\launchers\paris\setup_env_tools.py"

#C:\Python27\python.exe %setup_env_tools% launch C:\Python27\python.exe %pythonFile% %~dp0 %*
#pause


