# TODO
# ADD TARGET
# REMOVE TARGET
# FLOW MODE ( like skylanders )
# ADD BLINK


import maya.cmds as cmds
import maya.mel as mel

def createTesla(mode='1'):
    """
        Base procedure, call every other procedures
    """
    
    print ('[generateTesla.createTesla] - mode = ' + mode)

    #fxGroup = createFxGroup()
    teslaGroup = createTeslaGroup()
    print ('[generateTesla.createTesla] - teslaGroup name = ' + teslaGroup)
    setupTeslaGroup(teslaGroup)

    nodes = createBaseNodes(mode,teslaGroup)
    print nodes

    sourceMesh = nodes[0]
    targetMesh = nodes[1]
    curve = nodes[2]
    brush = nodes[3]
    stroke = nodes[4]
    mesh = nodes[5]
    distance = nodes[6]
    sourceLoc = nodes[7]
    targetLoc = nodes[8]
    midLoc = nodes[9]

    connectBaseNodes(sourceMesh,targetMesh,curve,brush,stroke,mesh)
    setupStroke(stroke,teslaGroup)
    setupStdBrush(brush,distance,teslaGroup)
    #animateBrush(brush,teslaGroup)
    wobble = addLocalWobble(mesh,distance,midLoc,teslaGroup)

    cmds.parent(curve,sourceMesh)
    cmds.parent(sourceMesh,teslaGroup)
    cmds.parent(targetMesh,teslaGroup)
    cmds.parent(stroke,teslaGroup)
    cmds.parent(mesh,teslaGroup)

    cmds.select(teslaGroup,r=True)

    return teslaGroup

def createTeslaGroup():

    groups = cmds.ls('Tesla_G*',type="transform")
    print ('[generateTesla.createTeslaGroup] - groups = ' + str(groups))
    j=1
    if groups:
        for i in xrange(len(groups)):
            print groups[i]
            if ('Tesla_G'+ str(j)) in groups[i]:
                j+=1

    teslaGroup = cmds.group(em=True,n='|Tesla_G'+str(j))
    print('[generateTesla.createTeslaGroup] - teslaGroup created with name ' + teslaGroup)
    return teslaGroup

def setupTeslaGroup(group):

    print ('[generateTesla.setupTeslaGroup] - input group = '+ group)
    
    ##group = group.split('|')[1]
    cmds.addAttr(group,ln=group,at='enum',enumName='_')
    cmds.setAttr(group+'.'+group,e=True,channelBox=True)

    cmds.addAttr(group,ln='BASIC',at='enum',enumName='_')
    cmds.setAttr(group+'.BASIC',e=True,channelBox=True)
    cmds.addAttr(group,ln='seed',min=0,dv=0,k=True,at='long')
    cmds.addAttr(group,ln='attractionMult',min=0,dv=1,k=True,at='double')
    cmds.addAttr(group,ln='attractionSamples',min=1,dv=5,k=True,at='double')
    cmds.addAttr(group,ln='startWidthMult',min=0,dv=1,k=True,at='double')
    cmds.addAttr(group,ln='endWidthMult',min=0,dv=0,k=True,at='double')
    cmds.addAttr(group,ln='flow',min=0,max=100,dv=0,k=True,at='double')

    cmds.addAttr(group,ln='BRANCHES',at='enum',enumName='_')
    cmds.setAttr(group+'.BRANCHES',e=True,channelBox=True)
    cmds.addAttr(group,ln='branchesIsActive',nn='isActive',dv=1,k=True,at='bool')
    cmds.addAttr(group,ln='splitBias',min=-.5,max=.5,dv=-.2,k=True,at='double')
    cmds.addAttr(group,ln='splitRand',min=-0,max=1,dv=.5,k=True,at='double')
    cmds.addAttr(group,ln='twistSpeedMult',min=0,dv=1,k=True,at='double')

    cmds.addAttr(group,ln='NOISE',at='enum',enumName='_')
    cmds.setAttr(group+'.NOISE',e=True,channelBox=True)
    cmds.addAttr(group,ln='noiseStrenghtMult',min=0,dv=1,k=True,at='double')
    cmds.addAttr(group,ln='noiseSpeedMult',min=-5,max=5,dv=1,k=True,at='double')
    cmds.addAttr(group,ln='noiseFreqMult',min=0,dv=1,k=True,at='double')
    

    cmds.addAttr(group,ln='WOBBLE',at='enum',enumName='_')
    cmds.setAttr(group+'.WOBBLE',e=True,channelBox=True)
    cmds.addAttr(group,ln='wobbleIsActive',nn='isActive',at='bool',dv=1,k=True)
    cmds.addAttr(group,ln='displayDeformer',at='bool',dv=0,k=True)
    cmds.addAttr(group,ln='strengthMult',at='double',min=0,dv=1,k=True)
    cmds.addAttr(group,ln='freqMult',at='double',min=0,dv=1,k=True)
    cmds.addAttr(group,ln='timeMult',at='double',min=0,dv=1,k=True)
    cmds.addAttr(group,ln='falloffMult',at='double',min=0,dv=1,k=True)
    cmds.addAttr(group,ln='falloffAmount',nn='wobbleFalloffAmount (%)',at='double',min=0,max=100,dv=30,k=True)
    
    cmds.addAttr(group,ln='BLINK',at='enum',enumName='_')
    cmds.setAttr(group+'.BLINK',e=True,channelBox=True)
    cmds.addAttr(group,ln='blink',at='bool',dv=0,k=True)
    cmds.addAttr(group,ln='blinkFrequency',at='double',min=0,dv=1,k=True)
    cmds.addAttr(group,ln='blinkDuration',at='double',dv=0,k=True)

def createBaseNodes(mode,parentName):
    """
        Create base nodes needed for tesla setup
    """
    
    sourceMesh = cmds.polySphere(n=parentName+'Source#')[0]
    cmds.setAttr(sourceMesh+'.sx',4)
    cmds.setAttr(sourceMesh+'.sy',4)
    cmds.setAttr(sourceMesh+'.sz',4)
    print ('[generateTesla.createBaseNodes] - sourceMesh created : ' + sourceMesh)
    if mode == '1':
        targetMesh = cmds.polySphere(n=parentName+'Target#')[0]
        cmds.setAttr(targetMesh+'.tx',160)
        cmds.setAttr(targetMesh+'.ty',95)
        cmds.setAttr(targetMesh+'.tz',-4)
        cmds.setAttr(targetMesh+'.sx',11)
        cmds.setAttr(targetMesh+'.sy',11)
        cmds.setAttr(targetMesh+'.sz',11)
    else:
        targetMesh = ''
    print ('[generateTesla.createBaseNodes] - targetMesh created : ' + targetMesh)

    curve = cmds.curve(n=parentName+'Curve#',d=1,p=[(0, 0, 0), ( 1, 0, 0)])
    print ('[generateTesla.createBaseNodes] - curve created : ' + curve)
    cmds.rename(cmds.listRelatives(curve,s=True)[0],curve+'Shape')

    outDimNodes = createDimensionTool(sourceMesh,targetMesh,parentName)

    brush = cmds.createNode('brush',n=parentName+'Brush#')
    print ('[generateTesla.createBaseNodes] - brush created : ' + brush)
    stroke = cmds.stroke(n=parentName+'Stroke#' )
    print ('[generateTesla.createBaseNodes] - stroke created : ' + stroke)
    cmds.rename(cmds.listRelatives(stroke,s=True)[0],stroke+'Shape')

    mesh = cmds.polySphere(n=parentName+'outMesh')
    print ('[generateTesla.createBaseNodes] - mesh created : ' + str(mesh))
    cmds.delete(mesh[1])
    mesh=mesh[0]

    #cmds.connectAttr(parentName+'.teslaVisibility',mesh+'.visibility')

    print ('[generateTesla.createBaseNodes] - baseNodes = %s,%s,%s,%s,%s,%s' % (sourceMesh,targetMesh,curve,brush,stroke,mesh))
    return [sourceMesh,targetMesh,curve,brush,stroke,mesh,outDimNodes[0],outDimNodes[1],outDimNodes[2],outDimNodes[3]]


def createDimensionTool(sourceMesh,targetMesh,parentName):
    """
        Create dimension nodes needed for tesla setup
    """

    sourceLoc = cmds.spaceLocator(n=parentName+'DistSourceLoc#')[0]
    print ('[generateTesla.createDimensionTool] - sourceLoc created : ' + sourceLoc)
    targetLoc = cmds.spaceLocator(n=parentName+'DistTargetLoc#')[0]
    print ('[generateTesla.createDimensionTool] - targetLoc created : ' + targetLoc)
    distanceShape = cmds.createNode('distanceDimShape',n=parentName+'Dist#Shape')
    distance = cmds.rename(cmds.listRelatives(distanceShape,p=True)[0],parentName+'Dist#')
    distanceShape=cmds.listRelatives(distance,s=True)[0]
    cmds.setAttr(distance+'.overrideEnabled',1)
    cmds.setAttr(distance+'.overrideVisibility',0)
    print ('[generateTesla.createDimensionTool] - distanceShape : ' + distanceShape)

    cmds.parent(targetLoc,targetMesh,r=True)
    cmds.parent(sourceLoc,sourceMesh,r=True)

    cmds.connectAttr(cmds.listRelatives(sourceLoc,s=True)[0]+'.worldPosition[0]',distanceShape+'.startPoint')
    cmds.connectAttr(cmds.listRelatives(targetLoc,s=True)[0]+'.worldPosition[0]',distanceShape+'.endPoint')
    cmds.setAttr(sourceLoc+'.overrideEnabled',1)
    cmds.setAttr(targetLoc+'.overrideEnabled',1)
    cmds.setAttr(sourceLoc+'.overrideVisibility',0)
    cmds.setAttr(targetLoc+'.overrideVisibility',0)

    midLoc = cmds.spaceLocator(n=parentName+'DistMidLoc#')[0]
    print ('[generateTesla.createDimensionTool] - midLoc : ' + midLoc)
    cmds.pointConstraint(sourceLoc,midLoc)
    cmds.pointConstraint(targetLoc,midLoc)
    cmds.aimConstraint(sourceLoc,midLoc,aimVector=[0,1,0],)

    cmds.parent(distance,parentName)
    cmds.parent(midLoc,parentName)

    return [distance,sourceLoc,targetLoc,midLoc]


def connectBaseNodes(source,target,curve,brush,stroke,mesh):
    """
        Connect nodes created and returned by createBaseNodes():
    """
    print mesh

    sourceShape = cmds.listRelatives(source,s=True,f=True)[0]
    print ('[generateTesla.connectBaseNodes] - sourceShape = ' + sourceShape)
    targetShape = cmds.listRelatives(target,s=True,f=True)[0] 
    print ('[generateTesla.connectBaseNodes] - targetShape = ' + targetShape)
    curveShape = cmds.listRelatives(curve,s=True,f=True)[0]
    print ('[generateTesla.connectBaseNodes] - curveShape = ' + curveShape)
    strokeShape = cmds.listRelatives(stroke,s=True,f=True)[0]
    print ('[generateTesla.connectBaseNodes] - strokeShape = ' + strokeShape)
    meshShape = cmds.listRelatives(mesh,s=True,f=True)[0]
    print ('[generateTesla.connectBaseNodes] - meshShape = ' + meshShape)

    cmds.connectAttr(curveShape+'.worldSpace[0]',strokeShape+'.pathCurve[0].curve')
    cmds.connectAttr(brush+'.outBrush',strokeShape+'.brush')
    cmds.connectAttr(targetShape+'.worldMesh[0]',strokeShape+'.collisionObject[0]')
    cmds.connectAttr(strokeShape+'.worldMainMesh[0]',meshShape+'.inMesh')


def setupStroke(stroke,parentName):
    """
        Set stroke base attributes
    """

    print('[generateTesla.setupStroke] - START')
    strokeShape = cmds.listRelatives(stroke,s=True)[0]
    print ('[generateTesla.setupStroke] - strokeShape = ' + strokeShape)

    cmds.setAttr(strokeShape+'.useNormal',0)
    #cmds.setAttr(strokeShape+'.minimalTwist',1)

    cmds.connectAttr(parentName+'.seed',stroke+'.seed')

    print('[generateTesla.setupStroke] - END')


def setupStdBrush(brush,distance,parentName):
    """
        Set standard brush attributs
        "Standard" means that the distance between source and target are base value ( eg : about 185 )
    """

    print('[generateTesla.SetupSTDBrush] - START')
    cmds.setAttr(brush+'.globalScale',10)
    cmds.setAttr(brush+'.tubes',1)
    cmds.setAttr(brush+'.twistRand',0)
    cmds.setAttr(brush+'.tubesPerStep',0)
    cmds.setAttr(brush+'.tubeRand',0)
    cmds.setAttr(brush+'.startTubes',1)
    cmds.setAttr(brush+'.segments',200)
    cmds.setAttr(brush+'.lengthMin',10)
    cmds.setAttr(brush+'.lengthMax',10)
    cmds.setAttr(brush+'.tubeWidth1',.2)
    cmds.setAttr(brush+'.tubeWidth2',.1)
    #cmds.setAttr(brush+'.widthRand',0)
    #cmds.setAttr(brush+'.widthBias',.4)
    cmds.setAttr(brush+'.segmentLengthBias',-1)
    #cmds.setAttr(brush+'.widthScale[0].widthScale_FloatValue',.16)
    cmds.setAttr(brush+'.widthScale[0].widthScale_Position',0)
    #cmds.setAttr(brush+'.widthScale[1].widthScale_FloatValue',0)
    cmds.setAttr(brush+'.widthScale[1].widthScale_Position',1)
    cmds.setAttr(brush+'.tubeDirection',1)
    cmds.setAttr(brush+'.elevationMin',0)
    cmds.setAttr(brush+'.elevationMax',0)
    cmds.setAttr(brush+'.azimuthMin',0)
    cmds.setAttr(brush+'.azimuthMax',0)

    cmds.setAttr(brush+'.branches',1)
    #cmds.setAttr(brush+'.startBranches',8)
    cmds.setAttr(brush+'.splitMaxDepth',3)
    #cmds.setAttr(brush+'.splitRand',.5)
    cmds.setAttr(brush+'.splitAngle',60)
    #cmds.setAttr(brush+'.splitTwist',0.2)
    cmds.setAttr(brush+'.splitSizeDecay',1)    
    #cmds.setAttr(brush+'.displacementDelay',0)
    #cmds.setAttr(brush+'.noise',.075)    
    #cmds.setAttr(brush+'.noiseFrequency',4.5)
    cmds.setAttr(brush+'.surfaceCollide',1)
    cmds.setAttr(brush+'.lengthFlex',.946)
    
    cmds.setAttr(brush+'.attractRadiusScale',0)
    cmds.setAttr(brush+'.attractRadiusOffset',2000000)
    cmds.setAttr(brush+'.occupyRadiusScale',0)
    cmds.setAttr(brush+'.surfaceSampleDensity',8)
    cmds.setAttr(brush+'.occupyBranchTermination',1)


    s= 'occupyAttraction = (' + cmds.listRelatives(distance,s=True)[0] + '.distance/4)*'+parentName+'.attractionMult;\n'
    s+= 'widthScale[0].widthScale_FloatValue = .16*' + parentName +'.startWidthMult;\n'
    s+= 'widthScale[1].widthScale_FloatValue = 0.01*' + parentName +'.endWidthMult;\n'
    s+= 'gapSize = ' + parentName+'.flow/100;\n'
    s+= 'numBranches = ' + parentName+'.branchesIsActive+1;\n'
    s+= 'noiseOffset = (-time*1.8)*' + parentName+'.noiseSpeedMult;\n'
    s+= 'noise = .075*' + parentName+'.noiseStrenghtMult;\n'
    s+= 'noiseFrequency = 4.5*' + parentName+'.noiseFreqMult;\n'
    s+= 'splitRand = ' + parentName+'.splitRand;\n'
    s+= 'splitTwist = time/4*' + parentName+'.twistSpeedMult;\n'

    #print s
    cmds.expression(o=brush,s=s,n=parentName+'baseExp')

    cmds.connectAttr(parentName+'.attractionSamples',brush+'.surfaceSampleDensity')
    cmds.connectAttr(parentName+'.splitBias',brush+'.splitBias')

    print('[generateTesla.SetupSTDBrush] - END')

def setupLongBrush(brush,distance,parentName):
    """
        Set long brush attributs
        "Standard" means that the distance between source and target are base value ( eg : about 185 )
    """

    print('[generateTesla.SetupLongBrush] - START')
    cmds.setAttr(brush+'.globalScale',10)
    cmds.setAttr(brush+'.tubes',1)
    cmds.setAttr(brush+'.twistRand',0)
    cmds.setAttr(brush+'.tubesPerStep',0)
    cmds.setAttr(brush+'.tubeRand',0)
    cmds.setAttr(brush+'.startTubes',1)
    cmds.setAttr(brush+'.segments',200)
    cmds.setAttr(brush+'.lengthMin',10)
    cmds.setAttr(brush+'.lengthMax',10)
    cmds.setAttr(brush+'.tubeWidth1',.2)
    cmds.setAttr(brush+'.tubeWidth2',.2)
    #cmds.setAttr(brush+'.widthRand',0)
    #cmds.setAttr(brush+'.widthBias',.4)
    cmds.setAttr(brush+'.segmentLengthBias',-1)
    cmds.setAttr(brush+'.widthScale[1].widthScale_FloatValue',1)
    cmds.setAttr(brush+'.widthScale[1].widthScale_Position',1)
    cmds.setAttr(brush+'.elevationMin',0)
    cmds.setAttr(brush+'.elevationMax',0)
    cmds.setAttr(brush+'.azimuthMin',0)
    cmds.setAttr(brush+'.azimuthMax',0)
    cmds.setAttr(brush+'.tubeDirection',1)
    cmds.setAttr(brush+'.branches',1)
    #cmds.setAttr(brush+'.startBranches',8)
    cmds.setAttr(brush+'.splitMaxDepth',2)
    cmds.setAttr(brush+'.splitRand',.5)
    cmds.setAttr(brush+'.splitAngle',45)
    cmds.setAttr(brush+'.splitTwist',0.2)
    cmds.setAttr(brush+'.splitSizeDecay',.9)    
    #cmds.setAttr(brush+'.displacementDelay',0)
    cmds.setAttr(brush+'.noise',.35)    
    cmds.setAttr(brush+'.noiseFrequency',3)
    cmds.setAttr(brush+'.surfaceCollide',1)
    cmds.setAttr(brush+'.lengthFlex',.946)
    cmds.setAttr(brush+'.attractRadiusScale',0)
    cmds.setAttr(brush+'.attractRadiusOffset',2000000)
    cmds.setAttr(brush+'.occupyRadiusScale',0)
    cmds.setAttr(brush+'.surfaceSampleDensity',8)
    cmds.setAttr(brush+'.occupyBranchTermination',0)


    s= 'occupyAttraction = (' + cmds.listRelatives(distance,s=True)[0] + '.distance/6.5)*'+parentName+'.attractionMult;\n'
    s+= 'widthScale[0].widthScale_FloatValue = 1*' + parentName +'.startWidthMult;\n'
    s+= 'widthScale[1].widthScale_FloatValue = 0.01*' + parentName +'.endWidthMult;\n'
    s+= 'gapSize = ' + parentName+'.flow/100;\n'
    s+= 'numBranches = ' + parentName+'.branchesIsActive+1;\n'
    s+= 'noiseOffset = (-time*1.8)*' + parentName+'.noiseSpeedMult;\n'
    s+= 'noise = .15*' + parentName+'.noiseStrenghtMult;\n'
    s+= 'noiseFrequency = 4.5*' + parentName+'.noiseFreqMult;\n'
    s+= 'splitRand = ' + parentName+'.splitRand;\n'
    s+= 'splitTwist = time/4*' + parentName+'.twistSpeedMult;\n'

    #print s
    cmds.expression(o=brush,s=s,n=parentName+'baseExp')

    cmds.connectAttr(parentName+'.attractionSamples',brush+'.surfaceSampleDensity')
    cmds.connectAttr(parentName+'.splitBias',brush+'.splitBias')

    print('[generateTesla.SetupLongBrush] - END')

def animateBrush(brush,parentName):
    
    """
        Set base brush animation
    """

    print('[generateTesla.animateBrush] - START')
    print('[generateTesla.animateBrush] - END')


def addLocalWobble(mesh,distance,midLoc,parentName):

    #add wobble falloff expression based on distance

    print('[generateTesla.addLocalWobble] - START')

    if not cmds.pluginInfo('wobble-2016',q=True,l=True):
        try:
            cmds.loadPlugin('wobble-2016')
        except:
            message = '[generateTesla.addLocalWobble] - Can\'t find Wobble plugin - script canceled'
            mel.eval('warning('+message+')')

    wobble = cmds.deformer(type='wobble')
    cmds.deformer(wobble[0],e=True,g=mesh)
    cmds.setAttr(wobble[1]+'.rz',-90)
    #cmds.setAttr(wobble[1]+'.overrideEnabled',1)
    #cmds.setAttr(wobble[1]+'.overrideVisibility',0)

    cmds.parent(wobble[1],midLoc,r=True)

    cmds.setAttr(wobble[0]+'.Strength',60)
    cmds.setAttr(wobble[0]+'.freqScale',0.02)
    cmds.setAttr(wobble[0]+'.falloffType',2)
    #falloffAmount = distance/6
    cmds.setAttr(wobble[0]+'.falloffAmount',31)
    
    s='Strength=10*' + parentName+'.strengthMult;\n'
    s+='freqScale=0.02*' + parentName+'.freqMult;\n'
    s+='falloffDistance = (.95*' + cmds.listRelatives(distance,s=True)[0] + '.distance/2)*'+ parentName+'.falloffMult;\nif (falloffDistance>'+cmds.listRelatives(distance,s=True)[0] + '.distance/2)\n    falloffDistance='+cmds.listRelatives(distance,s=True)[0] + '.distance/2;\n'
    s+='falloffAmount= 0.9*' + parentName+'.falloffAmount;\n'
    s+='timeFrequency= ' + parentName+'.timeMult;\n'

    cmds.expression(o=wobble[0],s=s,n=parentName+'wobbleSpaceOffset')
    cmds.expression(o=wobble[0],s='spaceOffsetY = noise(time*5)*5',n=parentName+'wobbleSpaceOffset')

    cmds.connectAttr(parentName+'.wobbleIsActive',wobble[0]+'.envelope')
    cmds.connectAttr(parentName+'.displayDeformer',wobble[1]+'.lodVisibility')
    
    print('[generateTesla.addLocalWobble] - END')
    return wobble


def addTarget(teslaGroup,newTarget):

    childs = cmds.listRelatives(teslaGroup,c=True)

    strokeShape = cmds.listRelatives([x for x in childs if 'Stroke' in x][0],s=True)[0]
    newTargetShape = cmds.listRelatives(newTarget,s=True)

    connections = cmds.listConnections(strokeShape+'.collisionObject')

    if newTargetShape and cmds.nodeType(newTargetShape[0]) == "nParticle":
        mesh = cmds.createNode('mesh')
        cmds.connectAttr(newTargetShape[0]+'.outMesh',mesh+'.inMesh')
        cmds.connectAttr(mesh+'.outMesh',strokeShape+'.collisionObject['+str(len(connections))+']')
    elif newTargetShape and cmds.nodeType(newTargetShape[0]) == "mesh":
        cmds.connectAttr(newTargetShape[0]+'.worldMesh[0]',strokeShape+'.collisionObject['+str(len(connections))+']')
   
   
def removeTarget(teslaGroup,target):

    childs = cmds.listRelatives(teslaGroup,c=True)

    strokeShape = cmds.listRelatives([x for x in childs if 'Stroke' in x][0],s=True)[0]
    newTargetShape = cmds.listRelatives(target,s=True)

    if newTargetShape and cmds.nodeType(newTargetShape[0]) == "nParticle":
        connections = cmds.connectionInfo(newTargetShape[0]+'.outMesh',dfs=True)
        print connections
        cmds.disconnectAttr(newTargetShape[0]+'.outMesh',connections[0]+'.collision')

    elif newTargetShape and cmds.nodeType(newTargetShape[0]) == "mesh":
        connections = cmds.connectionInfo(newTargetShape[0]+'.worldMesh[0]',dfs=True)
        print connections
        cmds.disconnectAttr(newTargetShape[0]+'.worldMesh[0]',connections[0])