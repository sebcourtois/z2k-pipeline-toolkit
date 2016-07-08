import os
import nuke

os.environ["USER_NAME"] = "alexandreb"

zombRootPath = r"//ZOMBIWALK/Projects"
os.environ["DAVOS_SITE"] = "dmn_paris"

os.environ["ZOMB_ROOT_PATH"] = zombRootPath
nuke.pluginAddPath(zombRootPath+"/zomb/tool/z2k-pipeline-toolkit/nuke/scripts")




