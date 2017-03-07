
import sys
import shutil
import os

print sys.argv
seqS = sys.argv[1]
exrDirS = sys.argv[2]
partageDirS = sys.argv[3]


print "seq ", seqS
print "exrDirS", exrDirS
print "partageDirS", partageDirS




iOutput = '1'
iOutput = raw_input("please choose a destination dir:\n 1 (default) = review\n 2 = review\\approved\n")

if iOutput == '1' or not iOutput:
	outputDir = partageDirS+'/'+seqS+'/review' 
elif iOutput == '2':
	outputDir = partageDirS+'/'+seqS+'/review/approved'
else:
	raise ValueError(iOutput+" is not a valid entry")

if not os.path.isdir(partageDirS):
	raise ValueError(partageDirS+" direcory could not be found")



desLayerS=outputDir+'/'+os.path.basename(exrDirS)
if os.path.isdir(desLayerS):
	print "removing: "+desLayerS
	shutil.rmtree(desLayerS)


if not os.path.isdir(outputDir):
	os.makedirs(outputDir)

print "copying: "+exrDirS
print "     --> "+outputDir
shutil.copytree(exrDirS,desLayerS)

if os.path.isdir(desLayerS):
	for eachFile in os.listdir(desLayerS):
		if ".json" in eachFile:
			os.remove(desLayerS+'/'+eachFile)





