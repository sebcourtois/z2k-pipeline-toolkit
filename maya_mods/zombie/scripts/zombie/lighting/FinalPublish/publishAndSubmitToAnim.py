
import maya.mel
from dminutes import sceneManagerUI

bUiCreated = sceneManagerUI.launch(refreshSceneAssets=False)
try:
    publishAction = sceneManagerUI.SCENE_MANAGER.publish()
finally:
    if bUiCreated:
        sceneManagerUI.kill()

if sceneManagerUI.isLaunched():
    sceneManagerUI.kill()
if publishAction:
    maya.mel.eval('rrSubmit')

