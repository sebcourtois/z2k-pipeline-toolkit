from zomblib.editing import getFinalImgSeq
import os

sInput = raw_input("sequences (comma separated):")
sSeqList = list(s.strip() for s in sInput.split(','))

iOutput = '1'
iOutput = raw_input("please choose the output dir:\n 1 (default) = d:\n 2 = c:\n 3 = "+os.environ["ZOMB_OUTPUT_PATH"]+" :\n")

if iOutput == '1' or not iOutput:
    outputDir = 'd:/' 
elif iOutput == '2':
    outputDir = 'c:/' 
elif iOutput == '3':
    outputDir = os.environ["ZOMB_OUTPUT_PATH"]
else:
    raise ValueError(iOutput+" is not a valid entry")

if not os.path.isdir(outputDir):
    raise ValueError(outputDir+" direcory could not be found")  

print "copying to--> "+outputDir


sInput = raw_input("stereo (False if empty):")
bStereoIn = sInput.strip()
if not bStereoIn:
    print "--> mono mode"
    bStereo = False
else:
    print "--> stereo mode"
    bStereo = True


getFinalImgSeq(sSeqList, bStereo=bStereo, outputDir=outputDir)
