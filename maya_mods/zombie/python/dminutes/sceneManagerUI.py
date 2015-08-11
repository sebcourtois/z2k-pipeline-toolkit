import os
import pymel.core as pc

from pytd.util.fsutils import pathJoin
from davos.core import damproject
reload(damproject)

PROJECTNAME = "zombillenium"
PROJECT = None

def sceneManagerUI():
    global PROJECT

    if (pc.window('sceneManagerUI', q=True, exists=True)):
        pc.deleteUI('sceneManagerUI')

    dirname, filename = os.path.split(os.path.abspath(__file__))
    ui = pc.loadUI(uiFile=dirname + "/UI/sceneManagerUI.ui")
    connectCallbacks()

    #Initialize DAVOS
    DamProject = damproject.DamProject

    PROJECT = DamProject(PROJECTNAME)

    if PROJECT == None:
        pc.error("Cannot initialize project '{0}'".format(PROJECTNAME))

    initialize()
    pc.showWindow(ui)


def initialize():
    #User info
    print PROJECT._shotgundb.currentUser
    pc.textField('sm_user_bt', edit=True, text=PROJECT._shotgundb.currentUser['name'])

    #pc.textScrollList("sm_step_dd", edit=True, removeAll=True)

    items = pc.optionMenu('sm_step_dd', query=True, itemListShort=True)
    for item in items:
        pc.deleteUI(item)

    for allowedstep in PROJECT._shotgundb.currentUser['sg_allowedsteps']:
        pc.menuItem("sm_step_" + allowedstep['name'], label= allowedstep['name'], parent='sm_step_dd')

#Callbacks management

def connectCallbacks():
    print 'connectCallbacks'
    pc.button('sm_disconnect_bt', edit=True, c=doDisconnect)

def doDisconnect(*args):
    print 'doDisconnect'
    PROJECT._shotgundb.logoutUser()
    sceneManagerUI()