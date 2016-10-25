import os, sys

print '[FXLIBS] - Loading Lib : fxPythonLib'

def cleanInsertPath(path):
    if path not in sys.path:
        sys.path.insert(0,path)

def listDir(path,mode='dir',ext='*'):
    """
        list the content of path in given mode ( dir or file+ext )
    """
    returnList = []
    if mode == 'dir':
        if os.path.isdir(path):
            for dir in os.listdir(path):
                if os.path.isdir(os.path.join(path, dir)):
                    returnList.append(dir)
        else :
            print path + ' does not exists - skipped'
            return 0   
    elif mode == 'file':   
        returnList = sorted(glob.glob(path+'/*.'+ext))
        
    return returnList