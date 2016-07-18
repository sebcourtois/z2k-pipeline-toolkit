
#    __PYDOC__
#    [TITLE]
#    stxScriptMenu.py
#
#    [DESCRIPTION]
#    Just add a "nameYouWish.scriptMenu" file in one or several directory of MAYA_SCRIPT_PATH.
#    A "nameYouWish" menu will be added to maya's main window with all browsed scripts.
#
#    [CREATION INFO]
#    Author: Sebastien Courtois
#
#    __END__

import os
ospath = os.path
import time
import re
from fnmatch import fnmatch

import ConfigParser
from ConfigParser import SafeConfigParser

import pymel.core
pm = pymel.core

pathSep = ";" if os.name == "nt" else ":"

normpath = lambda p: ospath.normpath(p).replace("\\", "/")

bPrintPathWalk = False

CREATED_MENUS = []

sExcludeDirs = ["pymel"]

DEFAULT_SECTION = {
"menu_order": "1",
}

#===============================================================================
#  Utilities
#===============================================================================

def timer(func):

    def closure(*args, **kwargs):

        startTime = time.time()

        try:
            ret = func(*args, **kwargs)
        except Exception:
            delta = time.time() - startTime
            print '\n"{0}" failed in {1:f} seconds.\n'.format(func.__name__, delta)
            raise

        delta = time.time() - startTime
        print('\n"{0}" finished in {1:f} seconds.\n'.format(func.__name__, delta))
        return ret

    return closure

def pathJoin(*args):
    return normpath(ospath.join(*args))

def upperFirst(w):
    return w[0].upper() + w[1:]

def wordSplit(s, digits=False):
    '''    
        state bits:
        0: no yields
        1: lower yields
        2: lower yields - 1
        4: upper yields
        8: digit yields
        16: other yields
        32 : upper sequence mark
    '''

    digit_state_test = 8 if digits else 0
    si, ci, state = 0, 0, 0 # start_index, current_index

    for c in s:

        if c.islower():
            if state & 1:
                yield s[si:ci]
                si = ci
            elif state & 2:
                yield s[si:ci - 1]
                si = ci - 1
            state = 4 | 8 | 16
            ci += 1

        elif c.isupper():
            if state & 4:
                yield s[si:ci]
                si = ci
            if state & 32:
                state = 2 | 8 | 16 | 32
            else:
                state = 8 | 16 | 32

            ci += 1

        elif c.isdigit():
            if state & digit_state_test:
                yield s[si:ci]
                si = ci
            state = 1 | 4 | 16
            ci += 1

        else:
            if state & 16:
                yield s[si:ci]
            state = 0
            ci += 1  # eat ci
            si = ci
        #print(' : ', c, bin(state))
    if state:
        yield s[si:ci]

def labelify(s):
    return " ".join((upperFirst(w) for w in wordSplit(s)))

def camelJoin(words):

    if isinstance(words, basestring):
        return words

    return "".join((upperFirst(w) if i > 0 else w.lower() for i, w in enumerate(words)))

def srcTypeFromExt(sExt):

    if sExt == ".mel":
        return "mel"
    elif sExt in (".py", ".pyw"):
        return "python"
    else:
        return ""

def execScript(sScriptPath, sSourceType="", sMelProcToRun=""):

    assert ospath.isfile(sScriptPath), "No such file: '{0}'".format(sScriptPath)

    if not sSourceType:
        sSourceType = srcTypeFromExt(ospath.splitext(sScriptPath)[1])
    else:
        sSourceType = sSourceType.lower()

    if sSourceType == "mel":
        pm.mel.source(sScriptPath)
        pm.mel.eval(sMelProcToRun)

    elif sSourceType in ("py", "python"):
        with open(sScriptPath) as f:
            code = compile(f.read(), sScriptPath, 'exec')
            exec(code, {"__name__":"__main__"})
    else:
        raise TypeError, "Unknown script type: '{0}'".format(sSourceType)

def makeImportString(sModuleName):

    if '.' in sModuleName:
        sPackageName, sModuleName = sModuleName.rsplit('.', 1)
        return "from {0} import {1}\n".format(sPackageName, sModuleName)
    return "import {0}\n".format(sModuleName)

def isIgnored(sName, sPatternList):
    for sPattern in sPatternList:
        if fnmatch(sName, sPattern):
            return True
    return False

def toTuple(arg):

    if not arg:
        return tuple()
    elif isinstance(arg, basestring):
        return (arg,)
    else:
        return arg

def patternsStrToList(sPattern):
    return re.findall(r'[\w\[\]\?\*\.]+', sPattern)


class StxConfigParser(SafeConfigParser):

    def get(self, section, option, **kwargs):
        try:
            value = SafeConfigParser.get(self, section, option, **kwargs)
        except ConfigParser.NoSectionError:
            value = SafeConfigParser.get(self, "DEFAULT", option, **kwargs)

        return value

''
#===============================================================================
#  Core
#===============================================================================


def remove():

    global CREATED_MENUS

    for menu in CREATED_MENUS[:]:
        #If the MEL menu already exists, delete it
        if pm.menu(menu, q=True, exists=True):
            print "deleted ", menu
            CREATED_MENUS.remove(menu)
            pm.deleteUI(menu)

    pm.refresh()

def iterBuildMenuArgs():

    sMayaScriptPaths = os.getenv("MAYA_SCRIPT_PATH", "")

    sProjectPath = str(pm.workspace(q=True, rd=True)[:-1])

    visitedPathList = []

    print ""

    for sScriptsPath in sMayaScriptPaths.split(pathSep):

        sScriptsPath = normpath(sScriptsPath)

        if ((sScriptsPath == sProjectPath) or ("Autodesk" in sScriptsPath)
            or (sScriptsPath in visitedPathList)):
            continue

        if bPrintPathWalk:
            print "\n", sScriptsPath

        for sCurDirPath, sDirNames, sFileNames in os.walk(sScriptsPath):

            sCurDirPath = normpath(sCurDirPath)

            if sCurDirPath in visitedPathList:
                del sDirNames[:] #don't walk further
                continue

            for sDir in sDirNames[:]:
                if sDir.startswith(".") or (sDir in sExcludeDirs):
                    sDirNames.remove(sDir)

            if bPrintPathWalk:
                print "\t", "." + sCurDirPath.split(sScriptsPath, 1)[1]

            try:
                i = sFileNames.index("script_menu.conf")
            except ValueError:
                pass
            else:

                visitedPathList.append(sCurDirPath)
                del sDirNames[:] #don't walk further

                oMenuConf = StxConfigParser(DEFAULT_SECTION)

                sMenuCfgFile = pathJoin(sCurDirPath, sFileNames[i])
                oMenuConf.read(sMenuCfgFile)

                iPriority = oMenuConf.getint("general", "menu_order")

                yield iPriority, sCurDirPath, oMenuConf

        visitedPathList.append(sScriptsPath)

@timer
def install(*args):

    global MAYA_WIN_NAME, MENU_CMD_FORMAT

    if pm.about(batch=True):
        pm.displayInfo("Can't install stxScriptMenus in bacth mode !")
        return

    remove()

    MAYA_WIN_NAME = pm.mel.eval('$tempMelVar=$gMainWindow')
    MENU_CMD_FORMAT = makeImportString(__name__) + "stxScriptMenu.execScript('{0}', '{1}', '{2}')"

    for _, sMenuDirPath, oMenuConf in sorted(iterBuildMenuArgs(), key=lambda x: x[0]):
        buildMenu(sMenuDirPath, oMenuConf)

    for uiScriptMenu in CREATED_MENUS:
        #Create the 'Rebuild This Menu' menu item
        pm.menuItem(divider=True, parent=uiScriptMenu)
        pm.menuItem(parent=uiScriptMenu, label="Rebuild Menu", command=install)

def buildMenu(sMenuDirPath, oMenuConf):

    global CREATED_MENUS, MAYA_WIN_NAME

    try:
        sMenuLabel = oMenuConf.get("general", "menu_title")
    except ConfigParser.Error:
        sMenuLabel = labelify(ospath.basename(sMenuDirPath))

    sMenuName = camelJoin(wordSplit(sMenuLabel + "Menu"))

    #If the MEL menu already exists, delete it
    if pm.menu(sMenuName, q=True, exists=True):
        print "merging '{}' menu from '{}'".format(sMenuLabel, sMenuDirPath)
        uiScriptMenu = pm.uitypes.PyUI(sMenuName)
    else:
        print "creating '{}' menu from '{}'".format(sMenuLabel, sMenuDirPath)

        #Create the MEL menu
        uiScriptMenu = pm.menu(sMenuName, parent=MAYA_WIN_NAME, tearOff=True,
                               aob=True, label=sMenuLabel)
        CREATED_MENUS.append(uiScriptMenu)

    #Call the proc that will build the menu
    addMenuItems(sMenuDirPath, uiScriptMenu, oMenuConf)

    #print '"{0}" menu created successfully.'.format( uiScriptMenu )

    return True

def filterScriptsAndDirs(sDirPath, ignoreDirs=None, ignoreScripts=None):

    sDirNameList = []
    sMenuItemParamsList = []

    sIgnoreDirs = toTuple(ignoreDirs)
    sIgnoreScripts = toTuple(ignoreScripts)

    for sFileOrDirName in sorted(os.listdir(sDirPath)):

        sScriptName, sExt = ospath.splitext(sFileOrDirName)
        if sExt:

            sSourceType = srcTypeFromExt(sExt)
            if sSourceType:

                if isIgnored(sFileOrDirName, sIgnoreScripts):
                    continue

                sFileOrDirPath = pathJoin(sDirPath, sFileOrDirName)
                sMenuItemParamsList.append((sScriptName, sFileOrDirPath, sSourceType))
        else:
            if isIgnored(sFileOrDirName, sIgnoreDirs):
                continue

            sDirNameList.append(sFileOrDirName)

    return sMenuItemParamsList, sDirNameList

def addMenuItems(sItemDirPath, parentMenu, oMenuConf, **kwargs):

    global MENU_CMD_FORMAT

    bSubMenu = kwargs.pop("subMenu", False)

    sIgnoreDirs = patternsStrToList(oMenuConf.get("filters", "ignore_dirs"))
    sIgnoreScripts = patternsStrToList(oMenuConf.get("filters", "ignore_scripts"))

    sMenuItemParamsList, sDirNameList = filterScriptsAndDirs(sItemDirPath, sIgnoreDirs, sIgnoreScripts)
    if not (sMenuItemParamsList or sDirNameList):
        return

    if bSubMenu:

        sMenuName = ospath.basename(sItemDirPath)
        sMenuLabel = labelify(sMenuName)
        sFullName = parentMenu.name() + "|" + sMenuName

        if isinstance(parentMenu, pm.ui.Menu):

            if pm.menuItem(sFullName, q=True, exists=True):
                parentMenu = pm.ui.CommandMenuItem(sFullName)
            else:
                parentMenu = pm.menuItem(sMenuName,
                                         parent=parentMenu,
                                         subMenu=True,
                                         tearOff=True,
                                         allowOptionBoxes=False,
                                         label=sMenuLabel)
        else:
            if not pm.menuItem(sFullName, q=True, exists=True):
                pm.menuItem(sMenuName, divider=True, parent=parentMenu,
                            dividerLabel=sMenuLabel, bld=True, enable=False)

    for sScriptName, sScriptPath, sSourceType in sMenuItemParamsList:

        sCmd = MENU_CMD_FORMAT.format(sScriptPath, sSourceType, sScriptName)
        sFullName = parentMenu.name() + "|" + sScriptName

        sItemName = sScriptName
        sItemLabel = labelify(sScriptName)
        if pm.menuItem(sFullName, q=True, exists=True):
            for i in xrange(1, 10):
                sNameExt = "_" + str(i)
                sFullName += sNameExt
                if not pm.menuItem(sFullName, q=True, exists=True):
                    sItemName += sNameExt
                    if "/scripts/" in sScriptPath.lower():
                        p = re.split("/scripts/", sScriptPath,
                                             flags=re.IGNORECASE)[0]
                        sLabelExt = " ( {} )".format(ospath.basename(p))
                    else:
                        sLabelExt = " ( {} )".format(i)
                    sItemLabel += sLabelExt
                    break

        pm.menuItem(sItemName, parent=parentMenu, label=sItemLabel,
                    command=sCmd, ann=sScriptPath)

    for sDirName in sDirNameList:
        sNextDirPath = pathJoin(sItemDirPath, sDirName)
        addMenuItems(sNextDirPath, parentMenu, oMenuConf, subMenu=True)

    return
