import maya.cmds as mc
from mtoa import aovs

from dminutes import miscUtils
reload (miscUtils)


def setFxSettings(gui=True):

	log = miscUtils.LogBuilder(gui=gui, funcName="setFxSettings")

	mc.setAttr("defaultArnoldRenderOptions.AASamples", 2)
	mc.setAttr("defaultArnoldRenderOptions.GIVolumeSamples", 0)

	setFxAOV()
	setVolumeOptions()

	txt = "#### info: fx options are now production ready"
	log.printL("i", txt)

def setFxAOV():
	
	if mc.ls("defaultArnoldRenderOptions"):
		fxAOVs = aovs.AOVInterface()
		aovFxNameL = ["volume", "volume_default", "volume_direct", "volume_indirect", "volume_opacity"]
		aovFxCustomNameL = ["volume_fxDir1","volume_fxDir2","volume_fxSky","volume_fxDir3"]
		for each in aovFxNameL:
			if not mc.ls(each, type="aiAOV"):
				fxAOVs.addAOV(each, aovType='rgb')

		for each in aovFxCustomNameL:
			if not mc.ls(each, type="aiAOV"):
				fxAOVs.addAOV(each, aovType='rgba')

		aovs.refreshAliases()
		print "#### {:>7}: 'createFxAovs' has created {} aovs".format("Info", len(aovFxNameL) + len(aovFxCustomNameL))
	else:
		print "#### {:>7}: 'createFxAovs' no 'defaultArnoldRenderOptions' found in the scene cannot create aovs".format("Info")



def setVolumeOptions():
	fluids = mc.ls(type='fluidShape')
	#print fluids
	vdbs = mc.ls(type='BE_VDBArnoldRender')
	#print vdbs

	for fluid in fluids:
		mc.setAttr(fluid+'.aiStepSize',1)
		mc.setAttr(fluid+'.aiFilterType',2)

	for vdb in vdbs:
		mc.setAttr(vdb+'.UseStep',1)		
		mc.setAttr(vdb+'.stepSize',1)

