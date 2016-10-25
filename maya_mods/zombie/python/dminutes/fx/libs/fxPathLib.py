import os,sys

def TeamToPaths():
    lisAlchemyPath = '//fx_server/projets/fx/fx_maya/scripts/python/thirdparty'
    lisartAlchemyPath = '//srv-bin/bin/python/LisartAlchemy'
    fxLibs = '//fx_server/projets/fx/tools/libs'
    TT_file_management = '//srv-bin/bin/python/TT_file_management'
    fxTools = '//fx_server/projets/fx/tools/generic/python/tools'
    homes = '//srv-home/homes'
    
    return [lisAlchemyPath,lisartAlchemyPath,fxLibs,TT_file_management,fxTools]

def insertPaths(paths):
    for path in paths:
        if path not in sys.path:
            sys.path.insert(0,path)
            print'[fxPathLib.insertTTPaths] - "' + path + '" inserted at index 0'
        else:
            print'[fxPathLib.insertTTPaths] - "' + path + '" already in sys.path'
            
def openDirectory(path):
    os.startfile(path)