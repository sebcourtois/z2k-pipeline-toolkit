import maya.cmds as mc

from dminutes import shading
reload(shading)

from functools import partial


#conform texture path
def buttonConformAllTexturePath(*args):
	shading.conformTexturePath( inConform = True)
def buttonPrintAllTexturePath(*args):
	shading.conformTexturePath( inConform = False)

#Conform Shader Names
def buttonConformAllShaderName(*args):
	shading.conformShaderName(shadEngineList = 'all')
def buttonConformSelShaderName(*args):
	shading.conformShaderName(shadEngineList = 'selection')

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

#publish textures files
def buttonPublishTexturePrint(*args):
	shading.getTexturesToPublish (verbose = True)

# Make a new window
window = mc.window( title="Shading Toolbox", iconName='Shading',toolbox = True ,widthHeight=(260, 495), sizeable = False )
mc.columnLayout( columnAttach=('both', 5), rowSpacing=5, adjustableColumn = True,columnAlign = "center" )
mc.separator(style = 'none', h = 5  )

#conform texture path
mc.text(label="File Texture Path", align='center')
mc.button( label='Comform All', c= buttonConformAllTexturePath)
mc.button( label='Print All', c=  buttonPrintAllTexturePath)

#Conform Shader Names
mc.separator(style = 'in', h = 5  )
mc.text(label="Shader Names", align='center')
mc.button( label='Comform All', c= buttonConformAllShaderName)
mc.button( label='Comform Selection', c= buttonConformSelShaderName)

#Conform Preview Shader
mc.separator(style = 'in', h = 5  )
mc.text(label="Preview Shader", align='center')
mc.button( label='Comform All', c = buttonConformAllPreviewShader)
mc.button( label='Comform Selection', c = buttonConformSelPreviewShader)

#Low Res .jpg
mc.separator(style = 'in', h = 10  )
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
mc.separator(style = 'in', h = 10  )
mc.text(label="Arnold .tx", align='center')
mc.flowLayout( )
mc.button( label='Generate All', recomputeSize = False, width = 125, c= buttonTxGenerateAll )
mc.button( label='Generate Selection', recomputeSize = False, width = 125, c= buttonTxGenerateSelection )
mc.setParent( '..' )
mc.flowLayout()
mc.button( label='Update All', recomputeSize = False, width = 125, c=buttonTxUpdateAll )
mc.button( label='Update Selection',  recomputeSize = False, width = 125, c= buttonTxUpdateSelection )
mc.setParent( '..' )

#publish textures files
mc.separator(style = 'in', h = 10  )
mc.text(label="publish textures files", align='center')
mc.button( label='Print',  c= buttonPublishTexturePrint )

mc.showWindow( window )


