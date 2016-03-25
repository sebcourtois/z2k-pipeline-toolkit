import pymel.core as pm
#import maya.cmds as cmds
#import dminutes.maya_scene_operations as mop

from davos.core.damproject import DamProject
from davos.core.damtypes import DamAsset
proj = DamProject("zombillenium")

oSetsHoldersL = pm.ls(os=True)
# print(cmds.ls(os=True))

for oSetHolder in oSetsHoldersL:
    # locator dans objet pyMel
    # on ote la partie du nom correspondant au groupe
    removeGroup = oSetHolder.name().rsplit("|", 1)[-1]
    # extraction du nom de l'asset
    setToLoadName = removeGroup.split("_")
    sAstName = setToLoadName[1] + "_" + setToLoadName[2] + "_" + setToLoadName[3]
    ast = DamAsset(proj, name=sAstName)
    mrcFile = ast.getResource("public", "anim_ref")
    #chargement des assets et replacement
    if mrcFile:
        p = mrcFile.envPath()
        newNodes = pm.createReference(p, namespace=sAstName + "_1", returnNewNodes=True)
        oAsset = pm.ls(newNodes, assemblies=True)[0]
        sNmspace = oAsset.namespace()
        print sNmspace
        oGlobalSRT = pm.PyNode(sNmspace + ":Global_SRT")
        # print oGlobalSRT.getTranslation(space='world')
        # print oSetHolder.getTranslation(space='world')
        print oGlobalSRT
        print oSetHolder
        oSetHolderT = oSetHolder.getTranslation(space='world')
        oSetHolderR = oSetHolder.getRotation(space='world')
        oGlobalSRT.setTranslation([oSetHolderT[0], oSetHolderT[1], oSetHolderT[2]], space='world')
        oGlobalSRT.setRotation([oSetHolderR[0], oSetHolderR[1], oSetHolderR[2]], space='world')
