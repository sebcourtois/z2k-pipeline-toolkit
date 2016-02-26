
from dminutes import sceneManagerUI
from pytd.util.sysutils import inDevMode
if inDevMode():
    from dminutes import sceneManager, maya_scene_operations
    reload(maya_scene_operations)
    reload(sceneManager)
    reload(sceneManagerUI)

sceneManagerUI.sceneManagerUI()
