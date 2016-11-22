
from zomblib.editing import getFinalImgSeq

sInput = raw_input("sequences (comma separated):")
sSeqList = list(s.strip() for s in sInput.split(','))

sInput = raw_input("stereo (False if empty):")
bStereoIn = sInput.strip()
if not bStereoIn:
    print "--> mono mode"
    bStereo = False
else:
    print "--> stereo mode"
    bStereo = True


getFinalImgSeq(sSeqList, bStereo=bStereo)
