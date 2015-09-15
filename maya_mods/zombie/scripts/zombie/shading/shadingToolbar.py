import maya.cmds as mc

from dminutes import shading
reload(shading)


# Make a new window
window = mc.window( title="Shading Toolbox", iconName='Shading',toolbox = True ,widthHeight=(260, 405), sizeable = False )
mc.columnLayout( columnAttach=('both', 5), rowSpacing=5, adjustableColumn = True,columnAlign = "center" )
mc.separator(style = 'none', h = 5  )

#conform texture path
mc.text(label="File Texture Path", align='center')
mc.button( label='Comform All', c= "shading.conformTexturePath(inVerbose = True, inConform = True, inCopy =False)" )
mc.button( label='Print All', c= "shading.conformTexturePath(inVerbose = True, inConform = False, inCopy =False)" )

#Conform Shader Names
mc.separator(style = 'in', h = 5  )
mc.text(label="Shader Names", align='center')
mc.button( label='Comform All', c= "shading.conformShaderName(shadEngineList = 'all')" )
mc.button( label='Comform Selection', c= "shading.conformShaderName(shadEngineList = 'selection')"  )

#Conform Preview Shader
mc.separator(style = 'in', h = 5  )
mc.text(label="Preview Shader", align='center')
mc.button( label='Comform All', c = "shading.conformPreviewShadingTree(shadEngineList = 'all')" )
mc.button( label='Comform Selection', c = "shading.conformPreviewShadingTree(shadEngineList = 'selection')" )

#Low Res .jpg
mc.separator(style = 'in', h = 10  )
mc.text(label="Low Res .jpg", align='center')
mc.flowLayout( )
mc.button( label='Generate All', recomputeSize = False, width = 125, c= "shading.generateJpgForPreview(fileNodeList = 'all', updateOnly=False)" )
mc.button( label='Generate Selection', recomputeSize = False, width = 125, c= "shading.generateJpgForPreview(fileNodeList = 'selection', updateOnly=False)" )
mc.setParent( '..' )
mc.flowLayout()
mc.button( label='Update All', recomputeSize = False, width = 125, c= "shading.generateJpgForPreview(fileNodeList = 'all', updateOnly=True)" )
mc.button( label='Update Selection',  recomputeSize = False, width = 125, c= "shading.generateJpgForPreview(fileNodeList = 'selection', updateOnly=True)" )
mc.setParent( '..' )

#Arnold .tx
mc.separator(style = 'in', h = 10  )
mc.text(label="Arnold .tx", align='center')
mc.flowLayout( )
mc.button( label='Generate All', recomputeSize = False, width = 125, c= "shading.generateTxForRender(fileNodeList = 'all', updateOnly=False)" )
mc.button( label='Generate Selection', recomputeSize = False, width = 125, c= "shading.generateTxForRender(fileNodeList = 'selection', updateOnly=False)" )
mc.setParent( '..' )
mc.flowLayout()
mc.button( label='Update All', recomputeSize = False, width = 125, c= "shading.generateTxForRender(fileNodeList = 'all', updateOnly=True)" )
mc.button( label='Update Selection',  recomputeSize = False, width = 125, c= "shading.generateTxForRender(fileNodeList = 'selection', updateOnly=True)" )
mc.setParent( '..' )


mc.showWindow( window )
