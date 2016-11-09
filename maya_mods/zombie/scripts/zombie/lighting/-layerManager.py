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
	lm.createRndlayer(layerName="lyr_env0_bty", layerContentL=lm.envRndObjL, disableLayer = False)

	# sets
	lm.createRndlayer(layerName="lyr_set0_bty", layerContentL=None, disableLayer = False)
	notSetItem = []
	setItem = []
	for each in lm.layerMemberL:
		if not "set_" in each:
			notSetItem.append(each)
		else:
			setItem.append(each)
	lm.addItemToSet(rndItemL = notSetItem, setTypeI = 2 )
	lm.createRndlayer(layerName="lyr_set1_bty", layerContentL=None, disableLayer = True)

	#asset
	lm.createRndlayer(layerName="lyr_ast0_bty", layerContentL=None, disableLayer = False)
	lm.addItemToSet(rndItemL = setItem, setTypeI = 2 )
	lm.createRndlayer(layerName="lyr_ast1_bty", layerContentL=None, disableLayer = True)
	lm.createRndlayer(layerName="lyr_ast2_bty", layerContentL=None, disableLayer = True)
	lm.initLayerDisplay()


def buttonCreateCustomLayer(*args):

	result = mc.promptDialog(title='Create Custom Render layer', message='Enter Layer Name: lyr_...._.........', text="lyr_cust_", button=['OK', 'Cancel'], defaultButton='OK', cancelButton='Cancel', dismissString='Cancel')

	if result == 'OK':
		layerNameS = mc.promptDialog(query=True, text=True)
		layerNameL = layerNameS.split("_")
		if layerNameL[0] != "lyr" or len(layerNameL)!=3 or len(layerNameL[1])!=4:
		    log.printL("e", "Wrong layer naming convention, the layer name must have 2 '_' separators, the prefix must be 'lyr', the second part must have 4 characters, the third part is up to you. ex: 'lyr_cust_totoEtTata'", guiPopUp = True)
		    return 
	else:
		return
	lm.createRndlayer(layerName=layerNameS, layerContentL=lm.astRndObjL, disableLayer = False)


def buttonDuplicateLayer(*args):
	lm.initLayer()
	lm.duplicateLayer(layerName= "", rndItemL = None)

def buttonCreateLightPass(*args):
	lm.initLayer()
	lm.createLightPass()

def buttonCreateFxsPass(*args):
	lm.initLayer()
	lm.createFxsPass()

def buttonUtilsPass(*args):
	layerManager.setUtlAovs()
	layerManager.createCryptomatteLayer()
	layerManager.setCryptoAov()

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
	lm.initLayerDisplay()

def buttonBlackMatte(*args):
	lm.initRndItem()
	lm.initLayer()
	lm.addItemToSet( setTypeI = 1 )
	lm.initLayerDisplay()

def buttonPrimaRayOff(*args):
	lm.initRndItem()
	lm.initLayer()
	lm.addItemToSet( setTypeI = 2 )
	lm.initLayerDisplay()



# Make a new window


if mc.window( "layerManager", exists = True ):
    mc.deleteUI( "layerManager", window=True)


window = mc.window( "layerManager", title="layer manager", iconName='layer manager',toolbox = True, sizeable = False )
mc.window(window, e=True, widthHeight=(260, 335))

mc.columnLayout( columnAttach=('both', 5), rowSpacing=5, adjustableColumn = True,columnAlign = "center" )

# create layers
mc.separator(style = 'none', h = 1  )
mc.text(label="Create Layers", align='center')
mc.flowLayout( )
mc.button( label='automatic layering', recomputeSize = False, width = 250, c= buttonCreateAutoLayering )
mc.setParent( '..' )
mc.flowLayout()
mc.button( label='create custom layer', recomputeSize = False, width = 250, c= buttonCreateCustomLayer )
mc.setParent( '..' )
mc.flowLayout()
mc.button( label='duplicate layer', recomputeSize = False, width = 250, c= buttonDuplicateLayer )
mc.setParent( '..' )
mc.flowLayout()
mc.button( label='create light pass', recomputeSize = False, width = 250, c= buttonCreateLightPass )
mc.setParent( '..' )
mc.flowLayout()
mc.button(label='create utls 16 + 32 pass', recomputeSize=False, width=250, c=buttonUtilsPass)
mc.setParent('..')
mc.flowLayout()
mc.button(label='create fxs pass', recomputeSize=False, width=250, c=buttonCreateFxsPass)
mc.setParent('..')
#layer member
mc.separator(style = 'in', h = 5  )
mc.text(label="Layer Members", align='center')
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


