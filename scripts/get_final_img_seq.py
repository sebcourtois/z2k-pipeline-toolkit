from zomblib.editing import getFinalImgSeq
import os

sInput = raw_input("sequences (comma separated):")
sSeqList = list(s.strip() for s in sInput.split(','))

iOutput = '1'
iOutput = raw_input("please choose the output dir:\n 1 (default) = f:\n 2 = e:\n 3 = d:\n 4 = c:\n 5 = "+os.environ["ZOMB_OUTPUT_PATH"]+" :\n")

if iOutput == '1' or not iOutput:
    outputDir = 'f:/' 
elif iOutput == '2':
    outputDir = 'e:/'
elif iOutput == '3': 
    outputDir = 'd:/' 
elif iOutput == '4':
    outputDir = 'c:/' 
elif iOutput == '5':
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
