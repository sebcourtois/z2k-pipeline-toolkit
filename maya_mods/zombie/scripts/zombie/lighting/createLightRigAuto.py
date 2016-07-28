import os
from pymel.core import *

def createLightRigFromShot():
    characterList = PyNode('shot|grp_character').getChildren()
    grp = group( name='lgt_rig_persos' )
    print characterList
    for each in characterList : # Acces to character asset list
        chrName = each.split('_')[1]
        ref = createReference('//zombiwalk/Projects/zomb/misc/shading/lightRigs/lgt_rig_character.ma', namespace='lgt_' + chrName)
        vertexLoc = []
        locatorPerso = spaceLocator(n=chrName + '_pos')
        for char in each.getChildren()[0].getChildren() : # Accces the actual character's geo
            if  char.split(':')[1] == 'geo_LeftEye' or char.split(':')[1] == 'geo_RightEye':
                vertexLoc.append(ls(char.getShape().vtx[1561])[0])
        select(vertexLoc[0], vertexLoc[1], locatorPerso)
        runtime.PointOnPolyConstraint()
        select(chrName + '_pos', 'lgt_' + chrName + ':lgt_Rig_Character')
        pointConstraint()
        select('cam*:Local_SRT', 'lgt_' + chrName + ':lgt_Light2D')
        aimConstraint()
        select(chrName + '_pos', 'lgt_' + chrName + ':lgt_Rig_Character', grp)
        parent(ls(sl=True))
        setAttr('lgt_' + chrName + ':lgt_offsetRotLight.rotateY', -90)
        del vertexLoc

createLightRigFromShot()
