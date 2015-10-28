import sys,os
import dminutes.Z2K_ReleaseTool.modules.Z2K_ASSET_replacer as Z2K_replaceA
reload(Z2K_replaceA)

import dminutes.Z2K_Batchator.Z2K_Release_Batch_CONFIG as Batch_CONFIG
reload(Batch_CONFIG)
from dminutes.Z2K_Batchator.Z2K_Release_Batch_CONFIG import *

print "DEBUGFILE=", DEBUGFILE


print "-"*80
print "replaceAndPublishAsset_batch_v001"
print "-"*80
curproj = os.environ.get("DAVOS_INIT_PROJECT")
print "curproj=", curproj


sourceFolder = BATCH_SOURCEFOLDER #"Z:/06_PARTAGE/jp/ENVOI/150928/" test

resultBool = False

def printF(texta="",openMode = "a",printN=True,*args,**kwargs):
    debugFile=DEBUGFILE
    with open(debugFile, openMode) as the_file:
            the_file.write( str(texta)+ u"\r" )
    if printN:
        print  str(texta)



try:
    Z2KR = Z2K_replaceA.Z2K_ASSET_replacer(theProject=curproj,
        currentSceneP="", 
        replacingScene="",
        )

    printF("Z2KR.currentSceneP={0}".format(Z2KR.currentSceneP) )
    if sourceFolder[-1] not in ["/"]:
        sourceFolder = sourceFolder + "/"
    replacingSceneP =sourceFolder + os.path.normpath(Z2KR.currentSceneP).rsplit(os.sep,1)[1].rsplit("-v",1)[0] +".ma"
    print "replacingSceneP=", replacingSceneP
    printF(texta="replacingSceneP={0}".format(replacingSceneP), openMode="a", printN=True)
    if os.path.isfile(replacingSceneP):
        # replace
        Z2KR.replace(currentSceneP= Z2KR.currentSceneP,
                 replacingSceneP=replacingSceneP,
                 )
        printF(texta="    Replaced", openMode="a", printN=True)
        # publish
        # Z2KR.publishScene(pathType="scene_previz", comment="First_publish_RockTheCasbah", sgTask="Rig")
        resultBool = True

except Exception,err:
    resultBool = False
    printF(texta="    ERROR={0}".format(err), openMode="a", printN=True)
    print err

print "resultBool=", resultBool
result= resultBool