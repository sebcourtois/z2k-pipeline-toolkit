
from zomblib.editing import h264ToProres

sInput = raw_input("sequences (comma separated):")
sSeqList = list(s.strip() for s in sInput.split(','))

sInput = raw_input("step directory ('01_previz' if empty):")
sStep = sInput.strip()
if not sStep:
    print "using '01_previz'"
    sStep = '01_previz'

h264ToProres(sSeqList, shotStep=sStep)
