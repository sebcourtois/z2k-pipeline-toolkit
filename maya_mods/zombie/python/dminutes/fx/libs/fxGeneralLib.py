import maya.cmds as cmds
import maya.mel as mel
import os, math

print '[FXLIBS] - Loading Lib : fxGeneralLib'

def getRenderableCams():
    cameras=cmds.ls(type='camera')
    renderableCams=[]
    
    for camera in cameras:
        if cmds.getAttr(camera+'.renderable'):
            renderableCams.append(camera)
            
    return renderableCams
            


def duplicateReferenceAndUnparent(item,unlock):
    '''
        DUPLICATE A REFERENCED MESH, UNLOCK it's transform, then parent it to WORLD 
    '''
    transformsAttr = ['tx','ty','tz','rx','ry','rz','sx','sy','sz','visibility']
    dupli = cmds.duplicate(item,rr=True,rc=True)
    
    if unlock:
        for attr in transformsAttr:
            cmds.setAttr(dupli[0]+'.'+attr,k=True)
            cmds.setAttr(dupli[0]+'.'+attr,lock=False)
            mel.eval('CBunlockAttr "'+dupli[0]+'.'+attr+'"')
        
    cmds.parent(dupli[0],w=True)
    
    return dupli[0]
    
    
def createSetFromSelection(items,name=None,type=None):
    cmds.select(cl=True)
    cmds.select(items)

    setName = ''
    if name:
        setName = cmds.sets(n=name)
    elif type:
        setName = cmds.sets(n='fx_'+type+'#')
    else:
        setName = cmds.sets(n='fx_set#')
    

def exportAlembic(itemList,startFrame,endFrame,path,name,frameRelativeSample='0',dataFormat='ogawa'):

    command = 'AbcExport -j "' #
    command += ' -frameRange ' + startFrame + ' ' + endFrame + ' -worldSpace '
    command += ' -dataFormat ' + dataFormat + ' ' 

    if frameRelativeSample:
        command += ' -frs -' + frameRelativeSample + ' -frs 0 -frs ' + frameRelativeSample + ' '
    
    for item in itemList:
        command+='-root ' + item + ' '
        
    command += '-file ' + path + '/' + name + '.abc"'
    print('[fxGeneralLib.exportAlembic] - command is ' + command)
    
    if not os.path.isdir(path):
        print('[fxGeneralLib.exportAlembic] - path to create is ' + path)    
        os.makedirs(path)
    
    mel.eval(command)
    return command
    

def importAlembic(path,name):

    #AbcImport -mode import "C:/Users/sebastienr/Desktop/bla.abc";
    print('[fxGeneralLib.importAlembic] - path to import from is ' + path + '/' + name) 
    abcNode = cmds.createNode('AlembicNode',n=name+'_abcFile')
    print('[fxGeneralLib.importAlembic] - abcNode = ' + abcNode)    
    cmds.connectAttr('time1.outTime',abcNode+'.time')
    cmds.setAttr(abcNode+'.abc_File',path+'/'+name+'.abc',type="string")
    
    return abcNode

def connectAlembic(abcNode,outMeshNumber,name):

    meshShape = cmds.createNode('mesh',n=name+'_abcShape')
    cmds.connectAttr(abcNode+'.outPolyMesh['+str(outMeshNumber)+']',meshShape+'.inMesh')

    print('[fxGeneralLib.connectAlembic] - meshShape = ' + meshShape)    
    meshParent = cmds.rename(cmds.listRelatives(meshShape,p=True)[0],name)
    print('[fxGeneralLib.connectAlembic] - meshParent = ' + meshParent)    

    return meshParent

def importAlembicStd(path,name):

    print('[fxGeneralLib.importAlembicStd] - path to import from is ' + path + '/' + name) 
    fullNodes = set(getTopNodes())
    print('[fxGeneralLib.importAlembicStd] - fullNodes ' + str(fullNodes))
    
    command = 'AbcImport -mode import "'
    command += '/'.join([path,name])+'.abc"'
    print('[fxGeneralLib.importAlembicStd] - command is ' + command)

    mel.eval(command)
    newfullNodes = set(getTopNodes())
    print('[fxGeneralLib.importAlembicStd] - newfullNodes ' + str(newfullNodes))

    newNodes = list(newfullNodes-fullNodes)
    print('[fxGeneralLib.importAlembicStd] - newNodes ' + str(newNodes))

    outTransform=[]
    outMeshes=[]
    outAbc=[]

    for item in newNodes:
        if cmds.nodeType(item) == 'transform':
            outTransform.append(item)
        elif cmds.nodeType(item) == 'AlembicNode':
            outAbc.append(item)
        elif cmds.listRelatives(item,s=True) and cmds.nodeType(cmds.listRelatives(item,s=True,f=True)[0]) == 'mesh':
            outMeshes.append(cmds.rename(item,name))

    print('[fxGeneralLib.importAlembicStd] - outTransform = ' + str(outTransform))
    print('[fxGeneralLib.importAlembicStd] - outMeshes = ' + str(outMeshes))
    print('[fxGeneralLib.importAlembicStd] - outAbc = ' + str(outAbc))
    return outMeshes,outAbc, outTransform


def exportSelectedtoSD(itemList,startFrame,endFrame,path,name,deformation,cam=None):
    print itemList
    cmds.select(itemList)
    command='realflow -exportSD -file "' + path + '/' + name + '.sd" -selected -startFrame ' + startFrame + ' -endFrame ' + endFrame + ' '
    if deformation:
        command+='-deformation '
    if cam:
        command += '-camera ' + cam
    print command
    mel.eval(command)
    

def importSD(itemLongName):
    command = 'realflow -importSD "' + itemLongName + '"'
    print command
    mel.eval(command)


def loadPlugin(pluginName):

    try:
        if not cmds.pluginInfo(pluginName,q=True,l=True):
            cmds.loadPlugin(pluginName)
            print ('[fxGeneralLib.loadPlugin] - ' + pluginName + ' successfully loaded')
        else:
            print ('[fxGeneralLib.loadPlugin] - ' + pluginName + ' already loaded - skipped')
        return 1
    except:
        print ('[fxGeneralLib.loadPlugin] - ERROR LOADING ' + pluginName + '  - CANCELED')
        return 0


def isFrameRounded(frame,fps):
    frame = float(frame)
    print ('[isFrameRounded] - given frame = ' + str(frame))
    tpf = ticksPerFrame(fps)
    print ('[isFrameRounded] - tpf = ' + str(tpf))
    exactTick = frame*tpf
    print ('[isFrameRounded] - exact tick number= ' + str(exactTick))
    mod = math.modf(exactTick)[0]
    print ('[isFrameRounded] - mod of tick = ' + str(mod))
    if mod >= 0.5:
        roundedTick = exactTick +(1.0-mod)
        print ('[isFrameRounded] - tick is rounded up = ' + str(roundedTick))
        return roundedTick
    else:
        roundedTick = exactTick - mod
        print ('[isFrameRounded] - tick is rounded down = ' + str(roundedTick))
        return roundedTick
    

def getExactFrameValue(roundedTick,fps):
    roundedTick = float(roundedTick)
    print ('[getExactFrameValue] - given (rounded) tick = ' + str(roundedTick))
    frame = float(fps)
    print ('[getExactFrameValue] - given frame = ' + str(frame))
    tpf = ticksPerFrame(fps)
    print ('[getExactFrameValue] - tpf = ' + str(tpf))
    exactFrame = roundedTick/tpf
    print ('[getExactFrameValue] - Exact frame is = ' + str(exactFrame))
    
    return exactFrame
    

def ticksPerFrame(fps):
    '''
       in Maya, the tickPerFrame (tpf) number is the smallest increment of time in Maya. It's equal to 6000
    '''
    tpf = 6000
    #print ('[ticksPerFrame] - tpf for a ' + str(fps) + ' frame per second is : ' + str(6000/fps))
    return float(6000/fps)

def getTopNodes():
    return [x for x in cmds.ls(l=True) if not cmds.listRelatives(x,p=True)]