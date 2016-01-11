import maya.cmds as mc

from dminutes import shading
reload(shading)

from dminutes import rendering
reload(rendering)

from dminutes import assetconformation
reload(assetconformation)

from functools import partial


def buttonUnused(*args):
	shading.dmnToonPreset( preset = "")


#shading camera
def buttonDefaultShadingCamGet(*args):
	shading.referenceShadingCamera()
def buttonCharacterShadingCamGet(*args):
	shading.referenceShadingCamera(cameraName = "cam_shading_character")
def buttonDefaultShadingCamRemove(*args):
	shading.referenceShadingCamera( remove=True)

#Render Settings
def buttonSetRenderOption(*args):
	rendering.setArnoldRenderOption("png")
def buttonSetRenderOptionJpg(*args):
	rendering.setArnoldRenderOption("jpg")


#light rigs
def buttonImportLgtRigOutdoor(*args):
	shading.importLightRig(lgtRig = "lgtRig_outdoor")

#conform texture path
def buttonConformAllTexturePath(*args):
	shading.conformTexturePath( inConform = True)
def buttonCheckAllTexturePath(*args):
	shading.conformTexturePath( inConform = False)
def buttonPrintAllTexturePath(*args):
	shading.printTextureFileName(fileNodeList = "all")
def buttonPrintSelTexturePath(*args):
	shading.printTextureFileName(fileNodeList = "selection")


#Conform Shader Names
def buttonConformAllShaderName(*args):
	shading.conformShaderName(shadEngineList = 'all')
def buttonConformSelShaderName(*args):
	shading.conformShaderName(shadEngineList = 'selection')


#Conform Shader Masks
def buttonConformShaderMasks(*args):
	assetconformation.setShadingMask(selectFailingNodes = True, verbose = True, gui = True)

#Conform Preview Shader
def buttonConformAllPreviewShader(*args):
	shading.conformPreviewShadingTree(shadEngineList = 'all')
def buttonConformSelPreviewShader(*args):
	shading.conformPreviewShadingTree(shadEngineList = 'selection')

#Low Res .jpg
def buttonJpgGenerateAll(*args):
	shading.generateJpgForPreview(fileNodeList = 'all', updateOnly=False)
def buttonJpgGenerateSelection(*args):
	shading.generateJpgForPreview( fileNodeList = 'selection', updateOnly=False)
def buttonJpgUpdateAll(*args):
	shading.generateJpgForPreview( fileNodeList = 'all', updateOnly=True)
def buttonJpgUpdateSelection(*args):
	shading.generateJpgForPreview( fileNodeList = 'selection', updateOnly=True)

#Arnold .tx
def buttonTxGenerateAll(*args):
	shading.generateTxForRender( fileNodeList = 'all', updateOnly=False)
def buttonTxGenerateSelection(*args):
	shading.generateTxForRender( fileNodeList = 'selection', updateOnly=False)
def buttonTxUpdateAll(*args):
	shading.generateTxForRender( fileNodeList = 'all', updateOnly=True)
def buttonTxUpdateSelection(*args):
	shading.generateTxForRender( fileNodeList = 'selection', updateOnly=True)


#shading presets
def buttonDmnToonReflectingGlass(*args):
	shading.dmnToonPreset( preset = "reflectingGlass")
def buttonDmnToonConstant(*args):
	shading.dmnToonPreset( preset = "constant")
def buttonDmnToonOutline(*args):
	shading.dmnToonPreset( preset = "outline")



#shading presets
def buttonDmnToonSetIndoor(*args):
	shading.dmnToonMode( mode = "setIndoor")
def buttonDmnToonSetOutdoor(*args):
	shading.dmnToonMode( mode = "setOutdoor")
def buttonDmnToonPropsToon(*args):
	shading.dmnToonMode( mode = "propsToon")
def buttonDmnToonPropsLambert(*args):
	shading.dmnToonMode( mode = "propsLambert")
def buttonDmnToonPrpC2d(*args):
	shading.dmnToonMode( mode = "2Delement")


# Make a new window


if mc.window( "shadingToolBox", exists = True ):
    mc.deleteUI( "shadingToolBox", window=True)


window = mc.window( "shadingToolBox", title="Shading Toolbox", iconName='Shading',toolbox = True, sizeable = False )
mc.window(window, e = True, widthHeight=(260, 810))

mc.columnLayout( columnAttach=('both', 5), rowSpacing=5, adjustableColumn = True,columnAlign = "center" )

# shading camera
mc.separator(style = 'none', h = 1  )
mc.text(label="Shading Camera", align='center')
mc.flowLayout( )
mc.button( label='Default', recomputeSize = False, width = 125, c= buttonDefaultShadingCamGet )
mc.button( label='Characters', recomputeSize = False, width = 125, c= buttonCharacterShadingCamGet )
mc.setParent( '..' )
mc.flowLayout()
mc.button( label='Remove', recomputeSize = False, width = 250, c= buttonDefaultShadingCamRemove )
mc.setParent( '..' )


#import light rigs
mc.separator(style = 'in', h = 5  )
mc.text(label="shading light rigs", align='center')
mc.flowLayout( )
mc.button( label='import outdoor', c= buttonImportLgtRigOutdoor, recomputeSize = False, width = 125 )
mc.button( label='unused', c= buttonUnused, recomputeSize = False, width = 125 )
mc.setParent( '..' )


#Render Settings
mc.separator(style = 'in', h = 5  )
mc.text(label="Set Render Options", align='center')
mc.flowLayout( )
mc.button( label='png', c= buttonSetRenderOption, recomputeSize = False, width = 125 )
mc.button( label='jpg', c= buttonSetRenderOptionJpg, recomputeSize = False, width = 125 )
mc.setParent( '..' )


#conform texture path
mc.separator(style = 'in', h = 5  )
mc.text(label="File Texture Path", align='center')
mc.flowLayout( )
mc.button( label='Comform All', recomputeSize = False, width = 125, c= buttonConformAllTexturePath)
mc.button( label='Check All', recomputeSize = False, width = 125, c=  buttonCheckAllTexturePath)
mc.setParent( '..' )
mc.flowLayout( )
mc.button( label='Print All', recomputeSize = False, width = 125, c= buttonPrintAllTexturePath)
mc.button( label='Print Selection', recomputeSize = False, width = 125, c=  buttonPrintSelTexturePath)
mc.setParent( '..' )

#Conform Shader Names
mc.separator(style = 'in', h = 5 )
mc.text(label="Conform Shader Name", align='center')
mc.flowLayout( )
mc.button( label='All', recomputeSize = False, width = 125, c= buttonConformAllShaderName)
mc.button( label='Selection', recomputeSize = False, width = 125, c= buttonConformSelShaderName)
mc.setParent( '..' )

#Conform Shader Amsks
mc.separator(style = 'in', h = 5 )
mc.text(label="Conform Masks", align='center')
mc.button( label='All', recomputeSize = False, width = 250, c= buttonConformShaderMasks)




#Conform Shader Structure
mc.separator(style = 'in', h = 5  )
mc.text(label="Conform Shader Structure", align='center')
mc.flowLayout( )
mc.button( label='All', recomputeSize = False, width = 125, c = buttonConformAllPreviewShader)
mc.button( label='Selection', recomputeSize = False, width = 125, c = buttonConformSelPreviewShader)
mc.setParent( '..' )

#Low Res .jpg
mc.separator(style = 'in', h = 5  )
mc.text(label="Low Res .jpg", align='center')
mc.flowLayout( )
mc.button( label='Generate All', recomputeSize = False, width = 125, c= buttonJpgGenerateAll )
mc.button( label='Generate Selection', recomputeSize = False, width = 125, c=  buttonJpgGenerateSelection )
mc.setParent( '..' )
mc.flowLayout()
mc.button( label='Update All', recomputeSize = False, width = 125, c=  buttonJpgUpdateAll )
mc.button( label='Update Selection',  recomputeSize = False, width = 125, c= buttonJpgUpdateSelection )
mc.setParent( '..' )

#Arnold .tx
mc.separator(style = 'in', h = 5  )
mc.text(label="Arnold .tx", align='center')
mc.flowLayout( )
mc.button( label='Generate All', recomputeSize = False, width = 125, c= buttonTxGenerateAll )
mc.button( label='Generate Selection', recomputeSize = False, width = 125, c= buttonTxGenerateSelection )
mc.setParent( '..' )
mc.flowLayout()
mc.button( label='Update All', recomputeSize = False, width = 125, c=buttonTxUpdateAll )
mc.button( label='Update Selection',  recomputeSize = False, width = 125, c= buttonTxUpdateSelection )
mc.setParent( '..' )


#shading presets
mc.separator(style = 'in', h = 5  )
mc.text(label="shading presets (selected dmnToon)", align='center')
mc.flowLayout( )
mc.button( label='Reflecting Glass', recomputeSize = False, width = 125, c= buttonDmnToonReflectingGlass )
mc.button( label='Constant', recomputeSize = False, width = 125, c= buttonDmnToonConstant )
mc.setParent( '..' )
mc.flowLayout()
mc.button( label='Outline', recomputeSize = False, width = 125, c=buttonDmnToonOutline )
mc.button( label='unused',  recomputeSize = False, width = 125, c=buttonUnused )
mc.setParent( '..' )

#shading modes
mc.separator(style = 'in', h = 5  )
mc.text(label="shading modes (all dmnToon)", align='center')
mc.flowLayout( )
mc.button( label='set Indoor', recomputeSize = False, width = 125, c= buttonDmnToonSetIndoor )
mc.button( label='set Outdoor', recomputeSize = False, width = 125, c= buttonDmnToonSetOutdoor )
mc.setParent( '..' )
mc.flowLayout()
mc.button( label='prp vhl Toon', recomputeSize = False, width = 125, c=buttonDmnToonPropsToon )
mc.button( label='prp vhl Lambert', recomputeSize = False, width = 125, c=buttonDmnToonPropsLambert )
mc.setParent( '..' )
mc.flowLayout()
mc.button( label='env c2d', recomputeSize = False, width = 125, c=buttonDmnToonPrpC2d )
mc.button( label='unused',  recomputeSize = False, width = 125, c=buttonUnused )

mc.showWindow( window )


