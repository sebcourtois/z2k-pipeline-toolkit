import os
import studiolibrary as stl
reload(stl)



# get user infos
user=os.getenv('USERNAME')
localdir=("C:/Users/"+user+"/Documents/Studiolib_LocalLIB/")
print "localdir=",localdir

# try to create the local user folder
try: 
   os.makedirs(localdir)
except OSError:
   if not os.path.isdir(localdir):
       raise

# production dependant part
import os
print os.environ["ZOMB_TOOL_PATH"]
Z2K_ToolPath = (os.environ["ZOMB_TOOL_PATH"]).replace("\\","/")



print "Z2K_ToolPath=", Z2K_ToolPath
name = "Studio Lib Previz Common"
root="Z:/06_PARTAGE/StudioLib/Previz"
previzPath = "studiolib_LIB/Previz"
#root = Z2K_ToolPath + "/" + (previzPath)
print "commonDir=",root
superusers = ["jipe"]

# test if root exists
if os.path.isdir(root):
    finalRoot=root
else:
    finalRoot = ""
print "finalRoot=",finalRoot
#finally launch the lib interfaces
stl.main( name=name,root=finalRoot, superusers=superusers, lockFolder="Approved", show=True, analytics=False)
stl.main( name="My Local", root=localdir,show=False, analytics=False)

