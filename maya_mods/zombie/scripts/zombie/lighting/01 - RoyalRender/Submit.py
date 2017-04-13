import os
import maya.mel
import maya.cmds as mc
import pymel.core as pm
from dminutes import sceneManager
from dminutes import rendering
reload (rendering)

from davos_maya.tool.general import infosFromScene
from davos.core.damproject import DamProject

scnInfos = infosFromScene()
shotName = scnInfos['name']
proj = DamProject("zombillenium")

dShotInfos = proj._shotgundb.sg.find_one('Shot', [['code', 'is', shotName]], ['id'])
filters = [
            ['entity', 'is', {'type':'Shot', 'id': dShotInfos['id']}],
            ['content', 'is', 'rendering']
           ]
fields = ['sg_keyframe']

result = proj._shotgundb.sg.find("Task", filters, fields)
sKeyframesL = result[0]['sg_keyframe'].replace(' ', '').split(',')
        
bPublishAction = True
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

paramStillsLeft = ["DefaultClientGroup=" + '1~FX',
                "CustomUserInfo=" + '1~0~Rendu Stills Left',
                "CompanyProjectName=" + '0~Stills',
                "Priority=" + '1~70',
                "CustomVersionName=" + '0~{}'.format(versionNumber),
                "Color_ID=" + '1~10']

paramStillsRight = ["DefaultClientGroup=" + '1~FX',
                "CustomUserInfo=" + '1~0~Rendu Stills Right',
                "CompanyProjectName=" + '0~Stills',
                "Priority=" + '1~70',
                "CustomVersionName=" + '0~{}'.format(versionNumber),
                "Color_ID=" + '1~10']

if bPublishAction:
    sRenderType = mc.confirmDialog(title='RR Submitter',
                                   message='Selectionnez le type de rendu !',
                                   button=['Stills Left', 'Stills Right', 'Left', 'Right', 'Stereo', 'Annuler'],
                                   defaultButton='Mono',
                                   cancelButton='Annuler',
                                   dismissString='Annuler',
                                   icon='question')

    if sRenderType == 'Stills Left':
        rendering.renderLeftCam()
        sStepFrameValue = int(mc.getAttr('defaultRenderGlobals.byFrameStep'))
        sStartFrameValue = int(mc.getAttr('defaultRenderGlobals.startFrame'))
        sEndFrameValue = int(mc.getAttr('defaultRenderGlobals.endFrame'))

        for keyFrame in sKeyframesL:
            if keyFrame and 'step' in keyFrame:
                steps = int(keyFrame.replace('step', ''))
                print '##### Set the step value {} #####'.format(steps)
                mc.setAttr('defaultRenderGlobals.byFrameStep', steps)

                ##### Submit with steps #####
                mc.rrSubmitZomb(noUI=True, parameter=paramStillsLeft)

        print '##### restore shot step value :: {} #####'.format(sStepFrameValue)
        mc.setAttr('defaultRenderGlobals.byFrameStep', sStepFrameValue)

        for keyFrame in sKeyframesL:
            if keyFrame and not 'step' in keyFrame:
                print '##### Send to Royal Render frame : ' + keyFrame + ' #####\n'
                mc.setAttr('defaultRenderGlobals.startFrame', keyFrame)
                mc.setAttr('defaultRenderGlobals.endFrame', keyFrame)

                mc.rrSubmitZomb(noUI=True, parameter=paramStills)

        print '##### restore shot start-end value :: {0} - {1} #####'.format(sStartFrameValue, sEndFrameValue)
        mc.setAttr('defaultRenderGlobals.startFrame', sStartFrameValue)
        mc.setAttr('defaultRenderGlobals.endFrame', sEndFrameValue)

    if sRenderType == 'Stills Right':
        rendering.createPublishRightBatch()
        rendering.renderRightCam()
        sStepFrameValue = int(mc.getAttr('defaultRenderGlobals.byFrameStep'))
        sStartFrameValue = int(mc.getAttr('defaultRenderGlobals.startFrame'))
        sEndFrameValue = int(mc.getAttr('defaultRenderGlobals.endFrame'))
        sName = mainFilePathS.rsplit('.')[0]
        if 'Right' not in sName:
            mc.file(mf=1)
            mc.file(rn=sName + '_Right.ma')
            mc.file(save=True)
        elif 'Right' in sName:
            mc.file(mf=1)
            mc.file(save=True)

        for keyFrame in sKeyframesL:
            if keyFrame and 'step' in keyFrame:
                steps = int(keyFrame.replace('step', ''))
                print '##### Set the step value {} #####'.format(steps)
                mc.setAttr('defaultRenderGlobals.byFrameStep', steps)

                ##### Submit with steps #####
                #maya.mel.eval('rrSubmitZomb -noUI')
                mc.rrSubmitZomb(noUI=True, parameter=paramStillsRight)

        print '##### restore shot step value :: {} #####'.format(sStepFrameValue)
        mc.setAttr('defaultRenderGlobals.byFrameStep', sStepFrameValue)

        for keyFrame in sKeyframesL:
            if keyFrame and not 'step' in keyFrame:
                print '##### Send to Royal Render frame : ' + keyFrame + ' #####\n'
                mc.setAttr('defaultRenderGlobals.startFrame', keyFrame)
                mc.setAttr('defaultRenderGlobals.endFrame', keyFrame)

                mc.rrSubmitZomb(noUI=True, parameter=paramStillsRight)

        print '##### restore shot start-end value :: {0} - {1} #####'.format(sStartFrameValue, sEndFrameValue)
        mc.setAttr('defaultRenderGlobals.startFrame', sStartFrameValue)
        mc.setAttr('defaultRenderGlobals.endFrame', sEndFrameValue)

    if sRenderType == 'Left':
        print '##### Initiate Left camera render #####'
        rendering.renderLeftCam()
        scnMng = sceneManager.SceneManager(scnInfos)
        sgVersData = {"sg_status_list":"rev"}
        scnMng.publish(comment=sComment, sgVersionData=sgVersData, dryRun=False)
        #maya.mel.eval('rrSubmitZomb -noUI')
        mc.rrSubmitZomb(noUI=True)

    if sRenderType == 'Right':
        print '##### Initiate Right camera render #####'
        rendering.renderRightCam()

        # Rename and save scene
        sName = mainFilePathS.rsplit('.')[0]
        if 'Right' not in sName:
            mc.file(mf=1)
            mc.file(rn=sName + '_Right.ma')
            mc.file(save=True)
            scnMng = sceneManager.SceneManager(scnInfos)
            sgVersData = {"sg_status_list":"rev"}
            scnMng.publish(comment=sComment, sgVersionData=sgVersData, dryRun=False)
            #maya.mel.eval('rrSubmitZomb -noUI')
            mc.rrSubmitZomb(noUI=True, parameter=paramRightCam)

        elif 'Right' in sName:
            mc.file(mf=1)
            mc.file(save=True)
#            scnMng = sceneManager.SceneManager(scnInfos)
#            sgVersData = {"sg_status_list":"rev"}
#            scnMng.publish(comment=sComment, sgVersionData=sgVersData, dryRun=False)
            #maya.mel.eval('rrSubmitZomb -noUI')
            mc.rrSubmitZomb(noUI=True)
        else:
            print "##### Please open your shot in edit mode !! ######"
            pass

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


