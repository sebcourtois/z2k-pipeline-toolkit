import sys, os
import maya.cmds as cmds
import maya.mel as mel

print '[FXLIBS] - Loading Lib : fxHoudiniEngineLib'


otlsPath = '//fx_server/projets/fx/houdini/otls'
if otlsPath not in sys.path:
    sys.path.insert(0,otlsPath)

def loadAsset(assetName):

    assetPath = os.path.join(otlsPath,assetName)
    print assetPath
    print '[fxHoudiniEngineLib.loadAsset] - assetName is ' + assetName
    hda = cmds.createNode('houdiniAsset')
    print hda
    cmds.setAttr(hda+'.assetName',assetName,type='string')
    cmds.setAttr(hda+'.otlFilePath',otlsPath+'/'+assetName+'.otl',type='string')
    mel.eval('houdiniEngine_syncAsset '+hda)

def listAllHda():
    hdas = cmds.ls(type='houdiniAsset')
    return hdas

def listAllVolumes(hdas):

    volumes=[]
    for hda in hdas:
        if cmds.getAttr(asset+'.assetType')=='volumes':
            volumes.append(asset)

    return volumes

def assetSetAttr(assets,attr,value):
    print type(value)
    for asset in assets:
        if cmds.attributeQuery('houdini_'+attr,exists=True):
            if type(value) == 'string':
                cmds.setAttr(asset+'.'+attr,value,type='string')    
            else:
                cmds.setAttr(asset+'.'+attr,value)
        else:
            print '[fxHoudiniEngineLib] - attribute "houdini_' + attr + ' doesn\'t exists - skipped]'

def assetListAllAttr(asset):
    houAttrs = cmds.listAttr(asset,s=True,st='houdini*')
    attrs = [attr.split('_')[1] for attr in houAttrs]
    return attrs
        