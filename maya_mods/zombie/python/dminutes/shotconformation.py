import maya.cmds as mc

from dminutes import miscUtils
reload (miscUtils)



def removeRefEditByAttr(inRefNodeL=[], attr="smoothDrawType", cmd="setAttr", GUI=True):
    resultB = True
    logL = []
    refNodeL = []

    sAttrList = attr if not isinstance(attr, basestring) else [attr]
    sCmdList = cmd if not isinstance(cmd, basestring) else [cmd]

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

        for sCmd in sCmdList:

            sNodeAttrList = mc.referenceQuery(eachRefNode, editCommand=sCmd,
                                              editNodes=True, editAttrs=True)

            sNodeAttrDct = dict()
            for sNodeAttr in sNodeAttrList:
                sAttr = sNodeAttr.rsplit(".", 1)[1]
                if sAttr in sAttrList:
                    sNodeAttrDct.setdefault(sAttr, set()).add(sNodeAttr)

            if not sNodeAttrDct:
                continue

            refIsLoaded = mc.referenceQuery(eachRefNode, isLoaded=True)
            if refIsLoaded:
                mc.file(unloadReference=eachRefNode)

            try:
                for sAttr, sNodeAttrSet in sNodeAttrDct.iteritems():
                    for sNodeAttr in sNodeAttrSet:
                        mc.referenceEdit(sNodeAttr, editCommand=sCmd, removeEdits=True,
                                         failedEdits=True, successfulEdits=True)
                    sMsg = ("#### {:>7}: 'removeRefEditByAttr': '{:>40}', {} '{} .{}' reference edit deleted"
                                  .format("Info", eachRefNode, len(sNodeAttrSet) , sCmd, sAttr))
                    print sMsg
                    logL.append(sMsg)
            finally:
                if refIsLoaded:
                    mc.file(loadReference=eachRefNode)

    if GUI == True:
        for each in logL:
            print each

    return resultB, logL


