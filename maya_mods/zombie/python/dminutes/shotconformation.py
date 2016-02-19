import maya.cmds as mc

def removeRefEditByAttr(inRefNodeL=[], attr="smoothDrawType", GUI=True):
    resultB = True
    logL = []
    refNodeL = []

    if not inRefNodeL:
        inRefNodeL = mc.ls(references=True)

    for each in inRefNodeL:
        try:
            mc.referenceQuery(each, filename=True)
        except RuntimeError as e:
            mc.warning(e.message.strip())
        else:
            refNodeL.append(each)

    for eachRefNode in refNodeL:
        myAttrRefEditL = []
        allRefEditL = mc.referenceQuery(eachRefNode, editStrings=True)
        refIsLoaded = mc.referenceQuery(eachRefNode, isLoaded=True)

        for eachRefEdit in allRefEditL:
            if "." + attr in eachRefEdit:
                myAttrRefEditL.append(eachRefEdit.split(" ")[1])

        if refIsLoaded and myAttrRefEditL : mc.file(unloadReference=eachRefNode)
        for each in myAttrRefEditL:
            mc.referenceEdit(each, failedEdits=True, successfulEdits=True, editCommand='setAttr', removeEdits=True)
        if refIsLoaded and myAttrRefEditL: mc.file(loadReference=eachRefNode)

        logMessage = "#### {:>7}: 'removeRefEditByAttr': '{:>40}', {} '{}' reference edit deleted".format("Info", eachRefNode, len(myAttrRefEditL), attr)
        logL.append(logMessage)

    if GUI == True:
        for each in logL:
            print each
    return resultB, logL





