import os, datetime

print '[FXLIBS] - Loading Lib : fxQtLib'

def buildUI(currentDir,dotui):
    import sys, pprint
    from pysideuic import compileUi

    dotpy = dotui.split('.')[0]+'.py'
    pyExists = os.path.isfile(currentDir+'/'+dotpy)

    if pyExists:
        pyTime = datetime.datetime.fromtimestamp(os.path.getmtime(currentDir+'/'+dotpy))
        uiTime = datetime.datetime.fromtimestamp(os.path.getmtime(currentDir+'/'+dotui))
        if pyTime<uiTime:
            print '[fxQtLib.buildUI] - deleting OLD UI'
            os.remove(currentDir+'/'+dotpy)
        else:
            print '[fxQtLib.buildUI] - UI is up to date - skipping build'
            return 0

    print '[fxQtLib.buildUI] - building UI'
    pyfile = open(currentDir+'/'+dotpy, 'w')
    compileUi(currentDir+'/'+dotui, pyfile, False, 4,False)
    print '[fxQtLib.buildUI] - UI build ok'
    pyfile.close()

    return currentDir+'/'+dotpy