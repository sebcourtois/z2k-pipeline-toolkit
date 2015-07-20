
import sys
import os
import re
import csv

from PySide import QtGui

from pytd.util.fsutils import joinPath, iterPaths, ignorePatterns, copyFile
from pytd.util.sysutils import toStr

ospth = os.path

sZombiDir = r"\\Diskstation\z2k\05_3D\zombillenium"
sAstTemplateDir = joinPath(sZombiDir, r"tool\template\asset_template")
sAllAssetsDir = joinPath(sZombiDir, "asset")

def assertStr(sWord, sRegexp, **kwargs):

    sErrorMsg = ""

    sInvalidChars = re.sub(sRegexp, "", sWord)
    if sInvalidChars:

        sInvalidChars = ", ".join("'{0}'".format(toStr(c)) for c in set(sInvalidChars))
        sErrorMsg += '\t- contains invalid characters: {0}\n\n'.format(sInvalidChars.replace("' '", "'space'"))

    if sErrorMsg:
        sErrorMsg = 'Invalid string: "{0}"\n'.format(toStr(sWord)) + sErrorMsg
        raise AssertionError, sErrorMsg

def createAssetDirectories(sCsvFilePath, **kwargs):

    bDryRun = kwargs.get("dry_run", False)
    iMaxCount = kwargs.get("maxCount", -1)

    with open(sCsvFilePath, 'rb') as csvFile:

        dialect = csv.Sniffer().sniff(csvFile.read(4096))
        csvFile.seek(0)

        reader = csv.reader(csvFile, dialect)

        iNameColumn = -1
        iHeaderRow = 0

        for row in reader:

            try:
                iNameColumn = row.index("Asset Name")
            except ValueError:
                pass
            else:
                break

            iHeaderRow += 1

        assert iNameColumn != -1, '"Asset Name" field missing from "{0}" !'.format(sCsvFilePath)

        csvFile.seek(0)
        for _ in xrange(iHeaderRow + 1):
            reader.next()

        sAstNameList = []
        sErrorList = []
        for row in reader:
            sAstName = row[iNameColumn]
            try:
                assertStr(sAstName, r'[\w]')
            except AssertionError, e:
                sErrorList.append(toStr(e))
                continue

            sAstNameList.append(sAstName)

        if sErrorList:
            raise AssertionError, "".join(sErrorList)

        count = 0
        for sAstName in sAstNameList:

            if count == iMaxCount:
                break

            sAstNameParts = sAstName.split("_")
            sAstType = sAstNameParts[0]
            #sAstBaseName = sAstNameParts[1]
            #sAstVariation = sAstNameParts[2] if len(sAstNameParts) == 3 else ""

            sAstTypeDir = joinPath(sAllAssetsDir, sAstType)
            assert ospth.isdir(sAstTypeDir), "Unknown asset type: '{0}'".format(sAstType)

            print '\nCreating directory of "{0}":'.format(sAstName)
            sDestAstDir = joinPath(sAstTypeDir, sAstName)

            if not (bDryRun or ospth.isdir(sDestAstDir)):
                os.mkdir(sDestAstDir)

            for sSrcPath in iterPaths(sAstTemplateDir, ignoreFiles=ignorePatterns("*.db", ".*")):
                sDestPath = sSrcPath.replace(sAstTemplateDir, sDestAstDir).replace("type_nom_variation", sAstName)

                if not ospth.exists(sDestPath):
                    print "\t", sDestPath

                    if not bDryRun:
                        if sDestPath.endswith("/"):
                            os.mkdir(sDestPath)
                        else:
                            copyFile(sSrcPath, sDestPath, **kwargs)

            count += 1

if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)

    sCsvFilePath, _ = QtGui.QFileDialog.getOpenFileName(filter="*.csv")
    if sCsvFilePath:
        createAssetDirectories(sCsvFilePath, dry_run=False)

    sys.exit(app.exec_())
