import maya.cmds as mc
import pymel.core as pm
from dminutes import assetconformation
reload (assetconformation)
      


from functools import partial

r2a = assetconformation.Asset_File_Conformer()


#reference file
def buttonRefPrevizFile(*args):
	r2a.cleanFile()
	r2a.loadFile(sourceFile ="previz" , reference = True)
def buttonRefModelingFile(*args):
	r2a.cleanFile()
	r2a.loadFile(sourceFile ="modeling" , reference = True)
def buttonRefAnimFile(*args):
	r2a.cleanFile()
	r2a.loadFile(sourceFile ="anim" , reference = True)
def buttonRefAnimRefFile(*args):
	r2a.cleanFile()
	r2a.loadFile(sourceFile ="animRef" , reference = True)
def buttonRefRenderFile(*args):
	r2a.cleanFile()
	r2a.loadFile(sourceFile ="render" , reference = True)
def buttonRefRenderRefFile(*args):
	r2a.cleanFile()
	r2a.loadFile(sourceFile ="renderRef" , reference = True)
def buttonRemoveAll(*args):
	r2a.cleanFile()



# Make a new window
if mc.window( "fileComparator", exists = True ):
    mc.deleteUI( "fileComparator", window=True)


window = mc.window( "fileComparator", title="File Comparator", iconName='file Comparator',toolbox = True, sizeable = False )
mc.window(window, e = True, widthHeight=(260, 140))

mc.columnLayout( columnAttach=('both', 5), rowSpacing=5, adjustableColumn = True,columnAlign = "center" )

# shading camera
mc.separator(style = 'none', h = 1  )
mc.text(label="Reference File", align='center')
mc.flowLayout( )
mc.button( label='Previz', recomputeSize = False, width = 125, c= buttonRefPrevizFile )
mc.button( label='Modeling', recomputeSize = False, width = 125, c= buttonRefModelingFile )
mc.setParent( '..' )
mc.flowLayout( )
mc.button( label='Anim', recomputeSize = False, width = 125, c= buttonRefAnimFile )
mc.button( label='Anim Ref', recomputeSize = False, width = 125, c= buttonRefAnimRefFile )
mc.setParent( '..' )
mc.flowLayout( )
mc.button( label='Render', recomputeSize = False, width = 125, c= buttonRefRenderFile )
mc.button( label='Render Ref', recomputeSize = False, width = 125, c= buttonRefRenderRefFile )
mc.setParent( '..' )
mc.flowLayout()
mc.button( label='Remove All', recomputeSize = False, width = 250, c= buttonRemoveAll )
mc.setParent( '..' )


mc.showWindow( window )


