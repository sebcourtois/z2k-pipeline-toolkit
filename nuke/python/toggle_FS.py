import nuke
import nukescripts

def FullscreenViewer():
    m = nuke.menu( 'Viewer' ).findItem( 'Toolbars/Bottom' )
    m.invoke()
    m = nuke.menu( 'Viewer' ).findItem( 'Toolbars/Top' )
    m.invoke()
    
# print nuke.activeViewer().node().knobs()
