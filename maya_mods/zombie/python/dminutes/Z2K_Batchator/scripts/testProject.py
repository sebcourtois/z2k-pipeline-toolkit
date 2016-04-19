# TEST PROJECT ENV
import os
toReturnB = False
import dminutes.Z2K_Batchator.Z2K_Release_Batch_CONFIG_v14 as Batch_CONFIG
reload(Batch_CONFIG)
from dminutes.Z2K_Batchator.Z2K_Release_Batch_CONFIG_v14 import *

def printF(texta="",openMode = "a",printN=True,*args,**kwargs):
    debugFile=DEBUGFILE
    with open(debugFile, openMode) as the_file:
            the_file.write( str(texta)+ u"\r" )
    if printN:
        print  str(texta)



printF(texta="TEST_PROJECT()", openMode="a", printN=True)
try:
    curproj = os.environ.get("DAVOS_INIT_PROJECT")
    printF(texta="curproj={0}".format(curproj), openMode="a", printN=True)
except Exception,err:
    printF(texta="ERROR_curproj:\r\t{0}".format(err), openMode="a", printN=True)
   


if curproj:
    toReturnB = True

result= toReturnB