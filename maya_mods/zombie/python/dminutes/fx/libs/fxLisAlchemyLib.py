import os, sys, warnings, collections
import fxPythonLib as fxpy
import fxPythonLib as fxpy
fxpy.cleanInsertPath('//fx_server/projets/fx/fx_maya/scripts/python/thirdparty')
fxpy.cleanInsertPath('//srv-bin/bin/python/LisartAlchemy')

print '[FXLIBS] - Loading Lib : fxLisAlchemy'

from lisAlchemy import *
la = LisAlchemy()

from LisartAlchemy import *
lart = LisartAlchemy()

def getItemType(fileLongName):
    file = la.getFileFromPath(fileLongName)
    filephItem = file.phItem
    return filephItem.g_type
    
    
def buildCacheDirFromFilename(fileLongName):

    fileShortName = fileLongName.split('/')[-1].split('.')[0]
    print fileShortName
    file = la.getFileFromPath(fileLongName)
    print file
    filePublish = file.publish
    print filePublish
    filephItem = file.phItem
    print filephItem
    itemName = filephItem.name
    print itemName
    episodeName = ''
    
    if filephItem.g_type == 'shot':
        shotphItem, shotObj = la.getShotById(phId=filephItem.id)
        episodeName = shotObj.episode.name
    
    fileState=''
    if int(filePublish):
        fileState = 'publish'
    else:
        fileState = 'work'
        
    format = ''

    cachePath=['cache']
    if filephItem.g_type == 'shot':
        cachePath.extend([episodeName,episodeName+'-'+itemName,fileState,fileShortName])
    elif filephItem.g_type == 'model':
        cachePath.extend([fileState,fileShortName])
    cachePath = '/'.join( cachePath )
    
    return cachePath
    

def getShotFromFilename(fileLongName):
    file = la.getFileFromPath(fileLongName)
    filephItem = file.phItem
    shotphItem, shotObj = la.getShotById(phId=filephItem.id)
    return [shotphItem, shotObj]
    

def getEpisodeFromShot(shotObj):
    return shotObj.episode.name
        

def getProjectFromFilename(fileLongName):
    shot = getShotFromFilename(fileLongName)
    projectId = shot[0].project_id
    project = la.getProjectInfoFromId(projectId)
    return project.name
    

def isShotFx(project,episode,shot):
    breakdown = la.getBreakdown(project,episode,shot)
    if [item for item in breakdown if 'FX_SHOT' in item.name]:
        return 1
    else:
        return 0


def isShotFxInLisart(project,episode,shot,type):
    shot = lart.getShot(project,episode,shot)
    tasks = lart.getTasksByShotId(shot.id)
    task = [task for task in lart.getTasksByShotId(shot.id) if type in task.task_name]
    if task:
        return 1
    else:
        return 0

    
def getShotSteps(project,episode,shot):

    steps=[]
    projectPath = la.getProjectInfo(project).maya_project_path[:-1]+'/scenes'
    prodCode=getProdCode(project)

    if project=='SOFIA':
        ep = '231S-'+episode
        animPublish = projectPath+'/'+ep+'/scene-'+shot+'/elements/animation/scene/'+ep+'_'+shot+'_v001.ma'
        if os.path.isfile(animPublish):
            steps.append(animPublish)
        floPublish = projectPath+'/'+ep+'/scene-'+shot+'/elements/flo/scene/'+ep+'_'+shot+'_flo_v001.ma'
        if os.path.isfile(floPublish):
            steps.append(floPublish)
        lightPublish = projectPath+'/'+ep+'/scene-'+shot+'/elements/lighting/scene/'+ep+'_'+shot+'_lights_v001.ma'
        if os.path.isfile(lightPublish):
            steps.append(lightPublish)
        fxBuild = projectPath+'/'+ep+'/scene-'+shot+'/elements/fx/scene/work/'+ep+'_'+shot+'_fx_v001.ma'
        if os.path.isfile(fxBuild):
            steps.append(fxBuild)
    else:
        animPublish = os.path.join(projectPath,'animation',episode,episode+'_'+shot,'publish',prodCode+'_animation_'+episode+'_'+shot+'_v000.ma')
        #print '[fxLisAlchemyLib.getShotSteps] - anim scene is : ' + animPublish
        if os.path.isfile(animPublish):
            steps.append(animPublish)
        else:
            steps.append(None)

        lightPublish = os.path.join(projectPath,'render',episode,episode+'_'+shot,'publish',prodCode+'_render_'+episode+'_'+shot+'_v000.ma')
        #print '[fxLisAlchemyLib.getShotSteps] - light scene is : ' + lightPublish
        if os.path.isfile(lightPublish):
            steps.append(lightPublish)
        else:
            steps.append(None)

        fxBuild = os.path.join(projectPath,'fx-sim',episode,episode+'_'+shot,'work',prodCode+'_fx-sim_'+episode+'_'+shot+'_v000.ma')
        #print '[fxLisAlchemyLib.getShotSteps] - fx scene is : ' + fxBuild
        if os.path.isfile(fxBuild):
            steps.append(fxBuild)
        else:
            steps.append(None)
    
    #print steps
    return steps

def getTaskByTypeByShot(project,episode,shot,type):
    shot = lart.getShot(project,episode,shot)
    task = [task for task in lart.getTasksByShotId(shot.id) if type in task.task_name]
    if task:
        return task[0]
    else:
        return None


def getProdCode(project):
    prodCode=''
    if project == 'SOFIA':
        prodCode='SOF'
    elif project == 'skylanders':
        prodCode = 'SKY'
    elif project == 'oh-brave-knight':
        prodCode = 'OBK'
    else:
        prodCode = project
    return prodCode


def getWorkerFromFxTask(project,episode,shot):
    prodCode = getProdCode(project)

    task = getTaskByTypeByShot(project,episode,shot,prodCode+'_FX')
    #print 'task is ' + str(task)
    if task:
        person = lart.getPersonById(task.task_worker_person_id)
        #print 'person is ' + str(person)
        if person:
            return [(person.person_first_name+'.'+person.person_last_name).lower(),task]
        else:
            #print '[fxLisAlchemy.getWorkerFxTask] - No worker found for task ' + task.task_name
            return [None,task]
    else:
        #print '[fxLisAlchemy.getWorkerFxTask] - No task found for ' + project + ' ' + episode + ' ' + shot 
        return None

def getShotsInfos(project,episode):
    #print 'project is ' + project
    #print 'episode is ' + episode
    shots = lart.getShotList(project,episode)
    print '[fxLisAlchemy.getShotsInfos] - getting ' + str(len(shots)) + ' shots informations from LISA(RT)...could take a while...'
    
    prodCode = getProdCode(project)

    shotsDict={}   
    for i in xrange(len(shots)):
        shot=shots[i]
        #print shot.shot_label
        #print shot.shot_label
        shotsDict[shot.shot_label]=['','','']
        fxShot = isShotFxInLisart(project,episode,shot.shot_label,prodCode+'_FX')
        #print fxShot
        workerTask = getWorkerFromFxTask(project,episode,shot.shot_label)
        #print workerTask
        
        noTask = 'NO TASK'
        noAssign = 'NOT ASSIGNED'
        if fxShot:
            shotsDict[shot.shot_label][0]='FX_SHOT'
            if workerTask:
                #print workerTask
                if workerTask[1]:
                    #print 'task found'
                    #print workerTask[1]
                    shotsDict[shot.shot_label][1]=workerTask[1].task_status
                    if workerTask[0]:
                        #print 'user found'
                        #print workerTask[0]
                        shotsDict[shot.shot_label][2]=workerTask[0]
                    else:
                        #print 'no user found'
                        shotsDict[shot.shot_label][2]=noAssign
                else:
                    #print 'task found but no user found'
                    shotsDict[shot.shot_label]=['FX_SHOT',workerTask[1].task_status,noAssign]
            else:
                shotsDict[shot.shot_label]=['FX_SHOT',noTask,noAssign]

    print '[fxLisAlchemy.getShotsInfos] - getting informations done...'        
    return collections.OrderedDict(sorted(shotsDict.items()))

