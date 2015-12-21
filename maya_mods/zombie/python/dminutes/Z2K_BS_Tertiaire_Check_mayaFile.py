# check maya file, for consistency with .bsd file

import maya.mel as mel
import os,ast
import maya.cmds as cmds

# getFile and read
filename = cmds.fileDialog2(fileMode=1, caption="Select the .bsd corresponding with the actual mayaFile", fileFilter="", dialogStyle=1, okc="OPEN")[0]
print "filename=", filename
WrongObjNameL =[]
if os.path.isfile(filename):
    print"read"
    content=""
    with open(filename, 'rU') as f:
        for line in f.readlines():
            if "#" not in line[0]:
                content+= line.strip()
    print ( content )
    bsDictL = ast.literal_eval(content)

    for i in bsDictL:
        for k,l in i.iteritems():
            #print k,l
            dicoTmp= l.get('drivenMesh',l["attrN"])
            if not isinstance(dicoTmp,str):
                for i,j in dicoTmp.iteritems():
                   for listTmp in j[1:]:
                       for pair in listTmp:
                           obj= pair[-1]
                           if not cmds.objExists(obj):
                               WrongObjNameL.append(obj)
                           
if len(WrongObjNameL):
    for k in WrongObjNameL:
        print "Not found:",k
    cmds.confirmDialog( title='bsd check', message="The blendShape Names are NOT conform with the selected .bsd file\n    {0}".format(WrongObjNameL),
                         button=['OK'], defaultButton='OK', cancelButton='OK', dismissString='OK' )
else:

    cmds.confirmDialog( title='bsd check', message="The blendShape Names are conform with the selected .bsd file",
                         button=['OK'], defaultButton='OK', cancelButton='OK', dismissString='OK' )

 
    
    