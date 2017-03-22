import os
import maya.mel
import maya.cmds as mc
import pymel.core as pm
from dminutes import sceneManager
from dminutes import rendering
from davos_maya.tool.general import infosFromScene
from davos.core.damproject import DamProject

scnInfos = infosFromScene()
shotName = scnInfos['dam_entity'].name
proj = DamProject("zombillenium")
#damShot = proj._shotgundb.sg.find_one('Shot', [['code', 'is', shotName]], ['sg_keyframe'])

#keyFrames = list()
#frames = []
#if damShot['sg_keyframe'] != None :
#    keyFrames = damShot['sg_keyframe'].split(',')
#
#
#if keyFrames != None:
#    for each in keyFrames:
#        frames.append(each.replace(' ',''))
        
publishAction = 1
sComment = 'Final Anim'
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
                "Priority=" + '1~20',
                "CustomVersionName=" + '0~{}'.format(versionNumber),
                "Color_ID=" + '1~10']

paramStills = ["DefaultClientGroup=" + '1~ALL',
                "CustomUserInfo=" + '1~0~Rendu Stills',
                #"CompanyProjectName=" + '0~Stills',
                "Priority=" + '1~70',
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
#        startFrameOrig = mc.getAttr('defaultRenderGlobals.startFrame')
#        endFrameOrig = mc.getAttr('defaultRenderGlobals.endFrame')
#        if frames != None:
#            for frame in frames:
#                print '##### Send to Royal Render frame : ' + frame + ' #####\n'
#                mc.setAttr('defaultRenderGlobals.startFrame', frame)
#                mc.setAttr('defaultRenderGlobals.endFrame', frame)
        mc.rrSubmitZomb(noUI=True, parameter=paramStills)

#        mc.setAttr('defaultRenderGlobals.startFrame', startFrameOrig)
#        mc.setAttr('defaultRenderGlobals.endFrame', endFrameOrig)

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


