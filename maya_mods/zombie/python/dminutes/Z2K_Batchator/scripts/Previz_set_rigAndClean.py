import maya.cmds as mc
import pymel.core as pc

from dminutes import miscUtils
reload (miscUtils)
from dminutes import rendering
reload (rendering)
from dminutes import modeling
reload (modeling)
from dminutes import assetconformation
reload (assetconformation)

import dminutes.jipeLib_Z2K as jpZ
reload(jpZ)


DebugPrintFile= '//zombiwalk/Z2K/06_PARTAGE/DEBUG_FILES/BATCHATOR/Previz_SET_rigAndClean.txt'
BDebugBoard = ""


# decorators ---------------------------
def Z2KprintDeco( func, *args, **kwargs):
    print "func=", func.__name__
    def deco(*args, **kwargs):
        # print u"Exécution de la fonction '%s'." % func.__name__
        func(toScrollF=BDebugBoard, toFile = DebugPrintFile, GUI=False, *args, **kwargs)
    return deco


def printF( toPrint="", st="main", toScrollF="", toFile = "", inc=False, GUI= True,
    openMode="a+", *args, **kwargs):
    """ Description: printer avec mise en forme integrer et link vers file or maya layout
        Return : [BOOL,LIST,INTEGER,FLOAT,DICT,STRING]
        Dependencies : cmds - 
    """

    def subPrint (text="", st=st, toScrollF=toScrollF, toFile = toFile, inc=False, GUI= GUI, openMode=openMode):
	    stringToPrint=""

	    text = str(object=text)
	    if st in ["title","t"]:
	        stringToPrint += "\n"+text.center(40, "-")+"\n"
	    if  st in ["main","m"]:
	        stringToPrint += ""+text+"\n"
	    if st in ["result","r"]:
	        stringToPrint += " -RESULT: "+text.upper()+"\n"

	    if not toFile in [""] and not GUI:
	        # print the string to a file
	        with open(toFile, openMode) as f:
	            f.write( stringToPrint )
	            print stringToPrint
	    else:
	        # print to textLayout
	        #mc.scrollField(toScrollF, e=1,insertText=stringToPrint, insertionPosition=0, font = "plainLabelFont")
	        print stringToPrint

    if isinstance(toPrint, (list,tuple,set)):
        for each in toPrint:
        	subPrint (text = each)
    else:
    	subPrint (text = toPrint)




# decorating functions
printF= Z2KprintDeco(printF)


def reRigAndClean():
	# print scene NAME
    infoDict = jpZ.infosFromMayaScene()
    printF("ASSET_NAME: {0}  -Version: {1}    - Categorie: {2}".format( infoDict["assetName"],infoDict["version"], infoDict["assetCat"] ) , st="t")
    msg = "'reRigAndClean' running"
    printF(msg, st="t")
    resultB = True
    myAsset = pc.ls("|asset", r = True)[0]
    if myAsset:
        modeling.cleanSet(myAsset)

        tmpResB, tmpLogL = rendering.deleteAovs()
        if tmpResB == False: resultB = False
        printF(tmpLogL, st="m") 

        tmpResB, tmpLogL = miscUtils.deleteUnknownNodes( GUI = False)
        if tmpResB == False: resultB = False
        printF(tmpLogL, st="m") 

        resL = assetconformation.fixMaterialInfo(GUI = False)
        if resL[0] == False: resultB = False
        printF(resL[1], st="m")

        tmpResB, tmpLogL = miscUtils.deleteAllColorSet(GUI = False)
        if tmpResB == False: resultB = False
        printF(tmpLogL, st="m")

        tmpResB, tmpLogL = modeling.geoGroupDeleteHistory(GUI = False)
        if tmpResB == False: resultB = False
        printF(tmpLogL, st="m")

        tmpResB, tmpLogL = modeling.makeAllMeshesUnique(inParent="|asset|grp_geo", GUI = False)
        if tmpResB == False: resultB = False
        printF(tmpLogL, st="m")

        modeling.meshShapeNameConform(inParent = "|asset|grp_geo", GUI = False)


        tmpResB, tmpLogL = assetconformation.softClean(keepRenderLayers = False, GUI = False)
        if tmpResB == False: resultB = False
        printF(tmpLogL, st="m")
        
        modeling.rigSet(myAsset)


        msg = "#### {:>7}: 'reRigAndClean' donne properly".format("Info")
        printF(msg, st="m")
    else:
        msg =  "#### {:>7}: 'reRigAndClean' could not proceed, no '|asset' found in the scene".format("Error")
        printF(msg, st="m")
        resultB = False
        

    msg = "'reRigAndClean' result: {}".format( resultB)
    printF(msg, st="m")
    printF("", st="m")

    return resultB
    
    
    
result = reRigAndClean()