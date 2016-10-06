import os
import pymel.core as pm
from mtoa.core import createOptions

createOptions()

def createLightRigFromShot():
    fileTexL = pm.ls(type='file')
    [pm.setAttr(fileTex + '.aiAutoTx', 0) for fileTex in fileTexL]
    characterList = pm.PyNode('shot|grp_character').getChildren()
    grp = pm.group(name='lgt_rig_persos')
    print characterList
    for each in characterList : # Acces to character asset list
        chrName = each.split('_')[1]
        pm.createReference(os.environ['ZOMB_MISC_PATH'] + '/shading/lightRigs/lgt_rig_character.ma', namespace='lgt_' + chrName)
        vertexLoc = []
        locatorPerso = pm.spaceLocator(n=chrName + '_pos')
        for char in each.getChildren()[0].getChildren() : # Accces the actual character's geo
            if char.split(':')[1] == 'geo_LeftEye' or char.split(':')[1] == 'geo_RightEye':
                vertexLoc.append(pm.ls(char.getShape().vtx[1561])[0])
            if char.split(':')[1] == 'geo_Skull':
                vertexLoc.append(pm.ls(char.getShape().vtx[45])[0])

#        pm.select(vertexLoc[0], vertexLoc[1], locatorPerso)
        pm.select(vertexLoc[0], locatorPerso)
        pm.mel.PointOnPolyConstraint()
        pm.select(chrName + '_pos', 'lgt_' + chrName + ':lgt_Rig_Character')
        pm.pointConstraint()
        pm.select('cam*:cam_shot_default', 'lgt_' + chrName + ':lgt_Light2D')
        pm.aimConstraint()
        pm.select(chrName + '_pos', 'lgt_' + chrName + ':lgt_Rig_Character', grp)
        pm.parent(pm.ls(sl=True))
        pm.setAttr('lgt_' + chrName + ':lgt_offsetRotLight.rotateY', -90)
        del vertexLoc
        pm.select(grp, 'grp_light')
        pm.parent(pm.ls(sl=True))
        pm.lightlink(light=('lgt_' + chrName + ':lgt_key'), object=(each.split(':')[0] + ':grp_geo'))
        pm.lightlink(light=('lgt_' + chrName + ':lgt_rim'), object=(each.split(':')[0] + ':grp_geo'))
        pm.lightlink(light=('lgt_' + chrName + ':lgt_lightpass'), object=(each.split(':')[0] + ':grp_geo'))

createLightRigFromShot()
