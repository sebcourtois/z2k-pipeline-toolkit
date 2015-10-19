#!/usr/bin/python
# -*- coding: utf-8 -*-

# TO DO
# - clean launch
# WIP add publish inside batch
# - think about gui
# - 
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# MAYAPI LAUNCHER FOR Z2K-----------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------


import os,sys
# add Z2K custom environ before launching mayapy
path="C:/Golaem/GolaemCrowd-4.2.0.1-Maya2016/plug-ins;C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/Toonkit_module/Maya2016/plug-ins;C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/solidangle/mtoadeploy/2016/plug-ins;C:/Program Files/Autodesk/Maya2016/bin/plug-ins;C:/Program Files/Autodesk/Maya2016/plug-ins/substance/plug-ins;C:/Program Files/Autodesk/Maya2016/plug-ins/xgen/plug-ins;C:/Program Files/Autodesk/Maya2016/plug-ins/bifrost/plug-ins;C:/Program Files/Autodesk/Maya2016/plug-ins/fbx/plug-ins;"
# os.environ["MAYA_PLUG_IN_PATH"] = path

curproj ="zombillenium"  # "zombtest" / "zombillenium" 
if curproj in ["zombillenium"]:
    theFolder= "zomb"
if curproj in ["zombtest"]:
    theFolder= "zombtest"

ENVS = {
        "ZOMB_ASSET_PATH":"\\\\ZOMBIWALK\\Projects\\"+theFolder+"\\asset",
        "ZOMB_SHOT_PATH":"\\\\ZOMBIWALK\\Projects\\"+theFolder+"\\shot",
        "ZOMB_OUTPUT_PATH":"\\\\ZOMBIWALK\\Projects\\"+theFolder+"\\output",
        "ZOMB_TOOL_PATH":"\\\\ZOMBIWALK\\Projects\\"+theFolder+"\\tool",

        "PRIV_ZOMB_PATH":"\\\\ZOMBIWALK\\Projects\\private\\$DAVOS_USER\\"+theFolder,
        "DAVOS_INIT_PROJECT":curproj,
        "DAVOS_CONF_PACKAGE":'zomblib.config',
        "MAYA_MODULE_PATH":"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods",
        "Z2K_PYTHON_SITES:":"C:/jipe_Local/z2k-pipeline-toolkit/python/mayapy-2016",

        }

for i,j in ENVS.iteritems():
    os.environ[i]=j


# append all sys path including the one loaded whith the modules
mayaSysPath= ["C:/Program Files/Autodesk/Maya2016/bin",
"C:/jipe_Local/z2k-pipeline-toolkit/python/pypeline-tool-devkit",
"C:/jipe_Local/z2k-pipeline-toolkit/python/davos-dev",
"C:/jipe_Local/z2k-pipeline-toolkit/python/mayapy-2016-site/pillow-3.0.0.dev0-py2.7-win-amd64.egg",
"C:/jipe_Local/z2k-pipeline-toolkit/python",
"C:/Program Files/Autodesk/Maya2016/plug-ins/bifrost/scripts/presets",
"C:/Program Files/Autodesk/Maya2016/plug-ins/bifrost/scripts",
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/Toonkit_module/Maya2016/scripts",
"C:/Program Files/Autodesk/Maya2016/plug-ins/fbx/scripts",
"C:/Golaem/GolaemCrowd-4.2.0.1-Maya2016/scripts",
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/solidangle/mtoadeploy/2016/scripts",
"C:/Program Files/Autodesk/Maya2016/plug-ins/substance/scripts",
"C:/Program Files/Autodesk/Maya2016/plug-ins/xgen/scripts/cafm",
"C:/Program Files/Autodesk/Maya2016/plug-ins/xgen/scripts/xgenm",
"C:/Program Files/Autodesk/Maya2016/plug-ins/xgen/scripts/xgenm/ui",
"C:/Program Files/Autodesk/Maya2016/plug-ins/xgen/scripts/xgenm/xmaya",
"C:/Program Files/Autodesk/Maya2016/plug-ins/xgen/scripts/xgenm/ui/brushes",
"C:/Program Files/Autodesk/Maya2016/plug-ins/xgen/scripts/xgenm/ui/dialogs",
"C:/Program Files/Autodesk/Maya2016/plug-ins/xgen/scripts/xgenm/ui/fxmodules",
"C:/Program Files/Autodesk/Maya2016/plug-ins/xgen/scripts/xgenm/ui/tabs",
"C:/Program Files/Autodesk/Maya2016/plug-ins/xgen/scripts/xgenm/ui/util",
"C:/Program Files/Autodesk/Maya2016/plug-ins/xgen/scripts/xgenm/ui/widgets",
"C:/Program Files/Autodesk/Maya2016/plug-ins/xgen/scripts",
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/zombie/scripts",
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/zombie/python",
"C:/Program Files/Autodesk/Maya2016/bin/python27.zip",
"C:/Program Files/Autodesk/Maya2016/Python/DLLs",
"C:/Program Files/Autodesk/Maya2016/Python/lib",
"C:/Program Files/Autodesk/Maya2016/Python/lib/plat-win",
"C:/Program Files/Autodesk/Maya2016/Python/lib/lib-tk",
"C:/Program Files/Autodesk/Maya2016/bin",
"C:/Program Files/Autodesk/Maya2016/Python",
"C:/Program Files/Autodesk/Maya2016/Python/lib/site-packages",
"C:/Program Files/Autodesk/Maya2016/Python/lib/site-packages/win32",
"C:/Program Files/Autodesk/Maya2016/Python/lib/site-packages/win32/lib",
"C:/Program Files/Autodesk/Maya2016/Python/lib/site-packages/Pythonwin",
"C:/jipe_Local/z2k-pipeline-toolkit/python/mayapy-2016-site",
"C:/Program Files/Autodesk/Maya2016/bin/python27.zip/lib-tk",
"C:/Users/jipe/Documents/maya/2016/prefs/scripts",
"C:/Users/jipe/Documents/maya/2016/scripts",
"C:/Users/jipe/Documents/maya/scripts",
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/Toonkit_module/Maya2016/scripts/../Python/lib/site-packages",
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/Toonkit_module/Maya2016/scripts/../../Python/Oscar",
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/Toonkit_module/Maya2016/scripts",
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/solidangle/mtoadeploy/2016/extensions",
"C:/jipe_Local/00_JIPE_SCRIPT/PythonTree/",
]

for p in mayaSysPath:
    sys.path.append(p)

import maya.standalone
maya.standalone.initialize(name='python')

# load pour de vrai tout les sys pasth deja present dans le os .env mais pas dans sys path
# for p in os.environ["PYTHONPATH"].split(";"):

#     if os.path.normpath(p) not in os.environ:
#         sys.path.append(p)
#     else:
#         print "all ready"



# set python path for special lib in custom python path
execfile(r"C:/jipe_Local/00_JIPE_SCRIPT/PythonTree/Maya_jipeLib_Setter_v0.3.py")

# std import
import RIG_WORKGROUP.jipe_lib.lib.mayaFunc as jpm
reload (jpm)
import RIG_WORKGROUP.jipe_lib.lib.jipe_IO as jpIO
reload (jpIO)

import maya.cmds as cmds
import maya.mel as mel






# load all plugins
# cmds.loadPlugin( allPlugins=True)


# ---------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------
#  releaze tool batch -------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------


from davos.core import damproject
reload(damproject)
from davos.core.damtypes import DamAsset
import os
import dminutes.Z2K_ReleaseTool.Z2K_ReleaseTool as z2kR
reload (z2kR)








# -----------------jipe functions -------------------------
def printF(texta="",openMode = "a",*args,**kwargs):
    debugFile="C:/jipe_Local/00_JIPE_SCRIPT/PythonTree/RIG_WORKGROUP/tools/batchator_Z2K/Release_debug.txt"
    with open(debugFile, openMode) as the_file:
            the_file.write( str(texta)+ u"\r" )


def jipeExec(scriptPath="",*args,**kwargs):
        # exec file function
        # scriptPath = os.path.normpath(scriptPath)

        with open(scriptPath) as f:
            fData =f.read()
        
        # executing as mel script or python script
        ns = {}
        if ".mel" in scriptPath[-4:]:
            print "\t","# MEL script mode"
            mel.eval(fData) in ns
        
        if ".py" in scriptPath[-3:]:
            print "\t","# PYTHON script mode"
            exec (fData) in ns
            # execfile(scriptPath)

        return ns


# --------------------------------------------------------------------


curproj = os.environ.get("DAVOS_INIT_PROJECT")
print "curproj=", curproj







def Z2K_ReleaseBatch(  sceneL =[] , openInMaya=True, readOnly=True, publishMayaFile=False, releaseMayaFile =False,  backupfiles=True,
    preRelease_pyScriptL=[], prePublish_pyScriptL=[], backupSuffix= "_backup", deleteBackuped=True,
    sourceAsset="chr_aurelien_manteau", SourceAssetType="previz_scene", assetCat = "chr",
    destinationAsset="chr_aurelien_manteau", destinationAssetType= "previz_ref",
    projConnectB= True, theProject="zombtest",
    theComment= "Auto_Release_rockTheCasbah !",
    debug= False,
    ):
    print "Z2K_ReleaseBatch()"
    counter = 0
    result = False
    outputD = {}
    okL = []
    failL=[]
    releasedL=[]
    resultL = []
    # little printing
    print "#"*120
    for l in sceneL:
        print "\t*",l
    print "TOTAL: %s" % len(sceneL)
    print "#"*120

    # get zomb project
    curproj = os.environ.get("DAVOS_INIT_PROJECT")
    print "curproj=", curproj
    basePath = [x for x in os.environ.get("MAYA_MODULE_PATH").split(";") if "maya_mods" in x][0]
    print "basePath=", basePath
    baseAssetPath =  os.environ.get("ZOMB_ASSET_PATH")
    print "baseAssetPath=",baseAssetPath

    # intantiate class Release tool
    Z2K_ReleaseToolI = z2kR.Z2K_ReleaseTool(sourceAsset=sourceAsset, SourceAssetType=SourceAssetType, assetCat =assetCat,
                            destinationAsset=destinationAsset, destinationAssetType= destinationAssetType,
                            projConnectB= projConnectB, theProject=theProject,
                            theComment= theComment,
                            debug= debug ,
                            )


    # BATCH loop --------------------------------------------------------------------------------
    for scene in sceneL:
        outputD[scene]= {}
        resultL.append(scene)
        result=False
        counter +=1
        print "\n\n","*"*80,"\n","scene = %s" %( scene ),"\n","*"*80,"\n",

        
        # opening the file or not -----------------------------------------------
        if openInMaya in [True,1]:
            # open file / edit
            path_private_toEdit=Z2K_ReleaseToolI.openAsset(sourceAsset=scene, SourceAssetType=SourceAssetType, readOnly=readOnly,)
            printF(texta="@@@@@@@@@@@@@@@@@@@@@@ OPENED: "+scene +" @@@@@@@@@@@@@@@@@@@@@@@@@@@@", openMode="a")
            outputD[scene]["opened"]=True

        # backup handling to another folder  ------------------------------------
        if backupfiles in [True,1]:
            print "\t","backupfiles: TRUE"
            BACKUP_tmp_file = path_private_toEdit + backupSuffix 
            shutil.copy(path_private_toEdit, BACKUP_tmp_file )
            outputD[scene]["backuped"]=True



        
        # ----------------------------------------------------------------------------------------------------------------------------
        # execution des PRE-PUBLISH SCRIPTS  WIP------------------------------------------------------------------------------------------
        # ----------------------------------------------------------------------------------------------------------------------------
        try:
            scrResultL=[]
            result = False
            outputD[scene]["prePublish_pyScriptL"]=prePublish_pyScriptL
            for script in prePublish_pyScriptL:
                
                printF( texta="    scriptName= {0}".format( os.path.normpath( script ).rsplit(os.sep,1)[-1])  )
                printF( texta="-"*40 )
                
                resultD = jipeExec(scriptPath=script)
                tmpResult = resultD["result"]
                scrResultL.append(tmpResult)
                print "    ->result=",result, script.rsplit(os.sep,1)[-1]
                printF( texta="    ->result={0}".format(tmpResult) )

            

            if not False in scrResultL:
                result =True
                text = "    OK:"
                resultL.append(text )
                okL.append(scene)
            else:
                result= False
                text = "    BAD:"
                resultL.append(text)   
                failL.append(scene) 
        except Exception,err:
            result =False
            text = "    ERROR:"+str(err)
            resultL.append(text)
            failL.append(scene) 


        printF( texta="*"*80 )
        printF( texta="    SCRIPTS RESULT= {0}".format(result) )
        printF( texta="*"*80 )
        outputD[scene]["scripts_result"]=text        



        # PUBLISH file ---------------------------------------------------------

        # WIP TO DO




        # ----------------------------------------------------------------------------------------------------------------------------
        # execution des PRE-RELEASE SCRIPTS ------------------------------------------------------------------------------------------
        # ----------------------------------------------------------------------------------------------------------------------------

        try:
            scrResultL=[]
            result = False
            outputD[scene]["preRelease_pyScriptL"]=preRelease_pyScriptL
            for script in preRelease_pyScriptL:
                
                printF( texta="    scriptName= {0}".format( os.path.normpath( script ).rsplit(os.sep,1)[-1])  )
                printF( texta="-"*40 )
                
                resultD = jipeExec(scriptPath=script)
                tmpResult = resultD["result"]
                scrResultL.append(tmpResult)
                print "    ->result=",result, script.rsplit(os.sep,1)[-1]
                printF( texta="    ->result={0}".format(tmpResult) )

            

            if not False in scrResultL:
                result =True
                text = "    OK:"
                resultL.append(text )
                okL.append(scene)
            else:
                result= False
                text = "    BAD:"
                resultL.append(text)   
                failL.append(scene) 
        except Exception,err:
            result =False
            text = "    ERROR:"+str(err)
            resultL.append(text)
            failL.append(scene) 


        printF( texta="*"*80 )
        printF( texta="    preRelease SCRIPTS RESULT= {0}".format(result) )
        printF( texta="*"*80 )
        outputD[scene]["scripts_result"]=text        

        # release file ---------------------------------------------------------
        if releaseMayaFile in [True,1]:
            if result:
                print "\n","* RELEASING"
                Z2K_ReleaseToolI.release_Asset(destinationAsset=scene, destinationAssetType = destinationAssetType,
                                                theComment=theComment)
                releasedL.append(scene)
                outputD[scene]["released"]=True        

        # deleting the backuped_File
        if deleteBackuped in [True,1]:
            print "\t","DELETING Backuped File"
            if os.path.isfile(BACKUP_tmp_file):
                os.remove( BACKUP_tmp_file )
                outputD[scene]["backup_deleted"]=True   


    # print results
    print "resultL=", resultL
    print "scrResultL=", scrResultL

    printF(texta="@"*120 ,openMode="a")
    printF(texta="@"*120 ,openMode="a")
    printF(texta="@"*120 ,openMode="a")
    
    for i,dico in outputD.iteritems():
        printF(texta=i, openMode="a")
        for k,l in dico.iteritems():
            printF(texta="    {0} = {1}".format(k,l) ,openMode="a")

    printF( texta="resultL={0}".format(resultL), openMode="a")
    printF( texta="scrResult= {0}".format(scrResultL), openMode="a")

    printF ( texta="@ Result = {0} / {1}   released:{2}".format( len(okL),counter,len(releasedL) ) )
    printF ( texta="failL:\r{0}".format(failL), openMode="a")
    printF ( texta="releasedL:\r{0}".format(releasedL), openMode="a")







#--------------------------------------------------------------------------------------------------------------------
# ----------------- EXEC --------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------

sourceFolder = "Z:/06_PARTAGE/jp/ENVOI/150928/"

# construct scenelist from folder
fileL = os.listdir(sourceFolder)
assetToReleaseL = []
for f in sorted(fileL):
    print f
    asset = f.rsplit("_",1)[0]
    print "   ",asset
    assetToReleaseL.append(asset)

print "!!!!!!!!!!!!!!!!!!!!!!!!!! curproj=", curproj

# launch the batch
# DON'T FORGET TO SET WELL THE PROJECT AND OPTIONS
Z2K_ReleaseBatch(  sceneL =assetToReleaseL , 
    openInMaya=1, readOnly=1, 
    publishMayaFile=0, 
    releaseMayaFile =0,  
    backupfiles=0, deleteBackuped=0,
    prePublish_pyScriptL = [
    "C:/jipe_Local/00_JIPE_SCRIPT/PythonTree/RIG_WORKGROUP/tools/batchator_Z2K/scripts/test01.py",
    ],
    preRelease_pyScriptL=[
    "C:/jipe_Local/00_JIPE_SCRIPT/PythonTree/RIG_WORKGROUP/tools/batchator_Z2K/scripts/replaceAndPublishAsset_batch_v001.py",
    "C:/jipe_Local/00_JIPE_SCRIPT/PythonTree/RIG_WORKGROUP/tools/batchator_Z2K/scripts/previz_check_batch.py",
    ],
    
    backupSuffix= "_backup", 
    sourceAsset="chr_aurelien_manteau", SourceAssetType="previz_scene", assetCat = "chr",
    destinationAsset="chr_aurelien_manteau", destinationAssetType= "previz_ref",
    projConnectB= True, theProject=curproj,
    theComment= "Auto_Release_rockTheCasbah !",
    )




