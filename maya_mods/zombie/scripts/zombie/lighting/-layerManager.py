import maya.cmds as mc

from dminutes import miscUtils
reload (miscUtils)

from dminutes import layerManager
reload (layerManager)

lm=layerManager.LayerManager()



#automatic layer
def buttonCreateAutoLayering(*args):
	mc.setAttr("defaultRenderLayer.renderable", 0)
	# enironemnt
	lm.createRndlayer(layerName="lyr_env0_bty", layerContentL=lm.envRndObjL, layerPosition = 0, disableLayer = False)

	# sets
	lm.createRndlayer(layerName="lyr_set0_bty", layerContentL=None, layerPosition = 1, disableLayer = False)
	notSetItem = []
	setItem = []
	for each in lm.layerMemberL:
		if not "set_" in each:
			notSetItem.append(each)
		else:
			setItem.append(each)
	lm.addItemToSet(rndItemL = notSetItem, setTypeI = 2 )
	lm.createRndlayer(layerName="lyr_set1_bty", layerContentL=None, layerPosition = 2, disableLayer = True)

	#asset
	lm.createRndlayer(layerName="lyr_ast0_bty", layerContentL=None, layerPosition = 3, disableLayer = False)
	lm.addItemToSet(rndItemL = setItem, setTypeI = 2 )
	lm.createRndlayer(layerName="lyr_ast1_bty", layerContentL=None, layerPosition = 4, disableLayer = True)
	lm.createRndlayer(layerName="lyr_ast2_bty", layerContentL=None, layerPosition = 5, disableLayer = True)


#layer member
def buttonAddSelectionToLayer(*args):
	lm.initRndItem()
	lm.initLayer()
	lm.layerMemberModifier(mode="add")
def buttonRemoveSelectionFromLayer(*args):
	lm.initRndItem()
	lm.initLayer()
	lm.layerMemberModifier(mode="remove")


#make selecetion visble, black matte, primary ray off
def buttonVisible(*args):
	lm.initRndItem()
	lm.initLayer()
	lm.addItemToSet( setTypeI = 0 )
def buttonBlackMatte(*args):
	lm.initRndItem()
	lm.initLayer()
	lm.addItemToSet( setTypeI = 1 )
def buttonPrimaRayOff(*args):
	lm.initRndItem()
	lm.initLayer()
	lm.addItemToSet( setTypeI = 2 )



# Make a new window


if mc.window( "layerManager", exists = True ):
    mc.deleteUI( "layerManager", window=True)


window = mc.window( "layerManager", title="layer manager", iconName='layer manager',toolbox = True, sizeable = False )
mc.window(window, e = True, widthHeight=(260, 240))

mc.columnLayout( columnAttach=('both', 5), rowSpacing=5, adjustableColumn = True,columnAlign = "center" )

#automatic layer
mc.separator(style = 'none', h = 1  )
mc.text(label="automatic layering", align='center')
mc.flowLayout( )
mc.button( label='create layers', recomputeSize = False, width = 250, c= buttonCreateAutoLayering )
mc.setParent( '..' )

#layer member
mc.separator(style = 'in', h = 5  )
mc.text(label="layer member", align='center')
mc.flowLayout( )
mc.button( label='add selection', c= buttonAddSelectionToLayer, recomputeSize = False, width = 125 )
mc.button( label='remove selection', c= buttonRemoveSelectionFromLayer, recomputeSize = False, width = 125 )
mc.setParent( '..' )


#make selecetion visble, black matte, primary ray off
mc.separator(style = 'in', h = 5  )
mc.text(label="Change selection state", align='center')
mc.flowLayout( )
mc.button( label='Black Matte', recomputeSize = False, width = 125, c= buttonBlackMatte )
mc.button( label='Prima Ray Off', recomputeSize = False, width = 125, c= buttonPrimaRayOff )
mc.setParent( '..' )
mc.flowLayout()
mc.button( label='Visible', recomputeSize = False, width = 250, c= buttonVisible )
mc.setParent( '..' )
mc.showWindow( window )


