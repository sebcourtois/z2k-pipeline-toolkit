import os
import maya.mel
import maya.cmds as mc
import pymel.core as pm
from dminutes import sceneManager
from dminutes import rendering
from davos_maya.tool.general import infosFromScene

publishAction = 1
sComment = 'Final Anim'
scnInfos = infosFromScene()

mainFilePathS = pm.sceneName()
if '08_render' in mainFilePathS:
    try:
        versionNumber = os.path.basename(mainFilePathS).split("-")[1]
        versionNumber = versionNumber.split(".")[0]
    except Exception as e:
        pm.displayError(e.message)
        versionNumber = "v000"

paramRightCam = ["DefaultClientGroup=" + '1~ALL',
                "CustomUserInfo=" + '1~0~Rendu Cam Right',
                "CompanyProjectName=" + '0~tlm2',
                "Priority=" + '1~10',
                "CustomVersionName=" + '0~{}'.format(versionNumber),
                "Color_ID=" + '1~10']

if publishAction:
    sRenderType = mc.confirmDialog(title='RR Submitter',
                                   message='Selectionnez le type de rendu !',
                                   button=['Stills', 'Mono' , 'Stereo', 'Annuler'],
                                   defaultButton='Mono',
                                   cancelButton='Annuler',
                                   dismissString='Annuler',
                                   icon='question')

    if sRenderType == 'Stills':
        mc.rrSubmitZomb()

    if sRenderType == 'Mono':
        print '##### Initiate Left camera render (Mono) #####'
        rendering.renderLeftCam()
        scnMng = sceneManager.SceneManager(scnInfos)
        sgVersData = {"sg_status_list":"rev"}
        scnMng.publish(comment=sComment, sgVersionData=sgVersData, dryRun=False)
        #maya.mel.eval('rrSubmitZomb -noUI')
        mc.rrSubmitZomb(noUI=True)

    elif sRenderType == 'Stereo':
        print '##### Initiate Left and Right cameras renders (Stereo) #####'
        rendering.renderLeftCam()
        scnMng = sceneManager.SceneManager(scnInfos)
        sgVersData = {"sg_status_list":"rev"}
        scnMng.publish(comment=sComment, sgVersionData=sgVersData, dryRun=False)
        # Submit to Left Cam to RR
        mc.rrSubmitZomb(noUI=True)

        # Set camera output for right eye
        rendering.renderRightCam()

        # Rename and save scene
        sName = mainFilePathS.rsplit('.')[0]
        mc.file(mf=1)
        mc.file(rn=sName + '_Right.ma')
        mc.file(save=True)
        # Submit to Right Cam to RR
        mc.rrSubmitZomb(noUI=True, parameter=paramRightCam)
    else:
        print r'##### Not a conform scene, need to be in form sqXXXX_shXXXXx_render-v000.000 (edit mode) #####'
        pass


