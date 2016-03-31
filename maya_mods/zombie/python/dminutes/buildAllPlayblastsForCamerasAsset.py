# Build all playblast for all cameras and concat them in one final movie.
import maya.cmds as cmds
from shotgun_api3 import shotgun
import os

SERVER_PATH = "https://zombillenium.shotgunstudio.com"
SCRIPT_NAME = 'dreamwall'
SCRIPT_KEY = 'cadd9ab033a932d7cdaea404c9c6e7e653367c0041ef6d49fcb7c070450f3c4e'

def shotgunConnect(): # connect to shotgun
    sg = shotgun.Shotgun(SERVER_PATH, SCRIPT_NAME, SCRIPT_KEY)
    return sg
    
sg=shotgunConnect()
projectId = 67 # Zombillenium

GRP_MOD_CAMS = "GRP_MOD_CAMS"
MIN_PLAYBLAST_TIME = 50 #
FFMPEG = r"Z:\tool\z2k-pipeline-toolkit\movSplitter\ffmpeg\bin\ffmpeg.exe" 

PATH_TMP = r"C:\tmp\zomb"

if not os.path.exists(PATH_TMP):
    os.makedirs(PATH_TMP)
    
listMovs = [] # list of movies path to delete at the end of the script.

listMoviesFilename = PATH_TMP + r"\listMovies.txt"
fo = open(listMoviesFilename, 'w') # open file list movies, overwrite if it exists.

sceneName = cmds.file(q=True, sceneName=True)
print sceneName
targetVideo = PATH_TMP + r"/" + os.path.basename(sceneName).split(".")[0] + "_allCamerasPlayblast.mov"
#print targetVideo

# list all cameras
cameras = cmds.listRelatives(GRP_MOD_CAMS, ad=True, type="camera")

allCameras = cmds.listCameras(perspective=True)
print allCameras
cameras = []
for camera in allCameras:
    if "cam_shot_default" in camera:
        cameras.append(camera)
        
print cameras

for camera in cameras:
    print camera
    #curves = cmds.listConnections(camera, t="animCurve") # Get all curves anim for this camera
    #print curves
    start = 101 # start is always 101
        
    shotName = camera.split(":")[0]
    infos = sg.find_one("Shot", [["project", "is", {"type":"Project", "id":projectId}], ['code', 'is', shotName]], ["code", "sg_cut_in", "sg_cut_out", "sg_cut_duration", "sg_sequence"])
    shotLen = int(infos["sg_cut_duration"])
    end = start + shotLen - 1
    
    print("\tstart = " + str(start) + " end = " + str(end))
    
    # playblast filename
    movFilename = PATH_TMP + r"/" + camera.split(":")[0] + ".mov"
    print("movFilename = " + str(movFilename))
    listMovs.append(movFilename)
                
    # make playblast with this camera
    cmds.lookThru(camera)
    cmds.refresh
    cmds.playblast(format='qt', filename=movFilename,
                   widthHeight=[960, 540],
                   st=start, et=end, 
                   percent=100, 
                   compression="jpg", quality=100,
                   fp=4, forceOverwrite=True, clearCache=True, showOrnaments=True, viewer=False,
                   )
    
    # check if playblast file exists
    
    # add to file listCameras.txt
    fo.write("file '"+movFilename+"'\n")  

fo.close()
# concat all movies
cmd = FFMPEG + " -f concat -y -i " + listMoviesFilename + " -c copy " + targetVideo
#cmd = r"Z:\tool\z2k-pipeline-toolkit\movSplitter\ffmpeg\bin\ffmpeg.exe -f concat -i C:\Users\STEPH\Desktop\listMovies.txt -c copy C:\Users\STEPH\Desktop\videoMerged2.mov"
cmdList = cmd.split(" ")
print ("cmd = " + str(cmdList))

try:
    process = subprocess.Popen(cmdList,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    #process = subprocess.Popen(["Z:\\tool\\z2k-pipeline-toolkit\\movSplitter\\ffmpeg\\bin\\ffmpeg.exe -f concat -i C:\\Users\\STEPH\\Desktop\\listMovies.txt -c copy C:\\Users\\STEPH\\Desktop\\videoMerged.mov"])
    for line in process.stdout:
        line = line.rstrip()
        print line
except OSError as e:
    print ("ERROR: ffmpeg concat", e) 

# delete all movies except the concat one.

print ("***** Done *****")
    
    