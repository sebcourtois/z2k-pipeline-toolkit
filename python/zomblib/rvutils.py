
import os
import os.path as osp
import subprocess

def sessionExists(sTag):

    bRvFound = True

    p = r"C:\Program Files\Shotgun\RV 6.2.6\bin\rvpush.exe"
    if not osp.isfile(p):
        raise EnvironmentError("RVPUSH command-line utility not found: '{}'.".format(p))

    os.environ["RVPUSH_RV_EXECUTABLE_PATH"] = "none"
    try:
        sLauncherLoc = osp.dirname(os.environ["Z2K_LAUNCH_SCRIPT"])
        p = osp.join(sLauncherLoc, "rvpush.bat")
        sCmd = p + " -tag {} py-eval 'print coucou'".format(sTag)
        subprocess.check_call(sCmd, shell=True)
    except subprocess.CalledProcessError as e:
        if e.returncode == 11:
            bRvFound = False
        else:
            raise
    finally:
        del os.environ["RVPUSH_RV_EXECUTABLE_PATH"]

    return bRvFound

def openToSgSequence(sequenceId, tag="playblast", source=None):

    sMuCmd = ('shotgun_review_app.theMode().setServer("https://zombillenium.shotgunstudio.com");\
    shotgun_review_app.theMode().launchTimeline([(string, string)] {{("entity_type", "Sequence"), ("entity_id", "{}")}});'
    .format(sequenceId))

    if source:
        sMuCmd += 'addSource("{}");'.format(source)

    sLauncherLoc = osp.dirname(os.environ["Z2K_LAUNCH_SCRIPT"])
    p = osp.join(sLauncherLoc, "rvpush.bat")
    sCmdAgrs = [p, "-tag", tag, "mu-eval", sMuCmd]

    return subprocess.call(sCmdAgrs)
