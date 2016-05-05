import pymel.core as pc
import tkMayaCore as tkc
import pymel.core.datatypes as dt
import pymel.core.runtime as pmr

import maya.cmds as cmds

import re
import os
import string
import math

from dminutes import miscUtils
reload (miscUtils)
import dminutes.jipeLib_Z2K as jpm
reload(jpm)

'''
Temporary module to manage modeling


identified checks
-namespace|shortname
-names equality
-name structure : type_characterName_variation[eventually]_step
-hierarchy

'''

SPECNAMES = {"grp_geo":"Local_SRT","global_srt":"Global_SRT", "big_daddy":"BigDaddy"}
CTRLS_SIZE = 1.0

CTRL_SETNAME = "set_control"
CACHE_SETNAME = "set_meshCache"
GEOMETRIES_LAYERNAME = "geometry"
CTRLS_LAYERNAME = "control"

DISPLAYS_CACHE_ATTRNAME = "rig_displays"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def getObj(in_sName):
    obj = None
    try:
        obj = pc.PyNode(in_sName)
    except Exception, e:
        print e
    return obj
 

def showErrors(in_errorsList, in_stoppedDef=None):
    if in_stoppedDef != None:
        pc.error(in_stoppedDef + " has stopped with errors:\n" + "\n".join(in_errorsList))
    else:
        pc.warning("\n".join(in_errorsList))

# ---------------------------------------------------------------------------
# createBS
# ---------------------------------------------------------------------------

def createBS():
    sel = pc.ls(sl=True)

    if len(sel) == 0:
        pc.warning("Please select the root of your rig !")
        return
    
    #Check we have everything we need.
    errors = []
    root = sel[0]
    
    ns = root.namespace()
    name = root.stripNamespace()
    
    if ns == "":
        errors.append("The given root don't have any namespce !")
        showErrors(errors, "createBS")
    else:
        ns = ns[:-1]

    if ns != name:
        errors.append("Namespace and root are supposed to be the same ! (%s != %s)" % (ns, name))
        showErrors(errors, "createBS")
        return
    
    #detect variables from name.
    splitName = name.split("_")
    if len(splitName) != 3 and len(splitName) != 4:
         errors.append( "Naming convention is not respected, incorrect occurences of \
                        chunks split by '_' found (%i, should be 3 or 4) !" % len(splitName))
         showErrors(errors, "createBS")
         
    variation = ""
    assetType, characterName, variation, step = ["unknown", "unknown", "unknown", "unknown"]

    if len(splitName) == 3:
        assetType, characterName, step = splitName
    elif len(splitName) > 3:
        assetType, characterName, variation, step = (chunk for chunk in splitName)

    if assetType != "chr":
        errors.append("Detected type is unknown ('%s')" % assetType)
        showErrors(errors)
    
    #Make sure that "Geometries" exists.
    objname = "%s:%s" % (ns, "Geometries")
    geoRoot = getObj(objname)
    if geoRoot == None:
        errors.append("Geometries root cannot be found ('%s')" % objname)
        showErrors(errors, "createBS")
    
    #Make sure that "BS" exists...
    objname = "%s:%s" % (ns, "grp_BS")
    bsRoot = getObj(objname)
    if bsRoot == None:
        errors.append("BlendShapes root cannot be found ('%s')" % objname)
        showErrors(errors, "createBS")
    
    #...and that is is a direct child of "Geometries"
    if bsRoot.getParent() != geoRoot:
        errors.append("BlendShapes root must be a child of 'Geometries' root")
        showErrors(errors, "createBS")
        
    #Verify BS root contains all needed targets.
    targets = ["eye_surprise", "eye_angry", "eye_sad", "mth_happy", "mth_sad", "mth_wideOpen"]
    unfoundTargets = list(targets)
    unknownTargets = []
    bsTargets = []


    children = bsRoot.getChildren()
    for child in children:
        shortName = child.stripNamespace()
        if shortName in unfoundTargets:
            unfoundTargets.remove(shortName)
            bsTargets.append(child)
        else:
            unknownTargets.append(shortName)
    
    if len(unfoundTargets) + len(unknownTargets) > 0:
        if len(unfoundTargets) > 0:
            errors.append("Some needed targets were not found ('%s')" % ", ".join(unfoundTargets))
        if len(unknownTargets) > 0:
            errors.append(  "Some targets were not expected, maybe they don't fit naming \
                            conventions ('%s' not found in '%s')" % (", ".join(unknownTargets), ",".join(targets)))

        showErrors(errors, "createBS")
        
    #Make sure the source exists.
    objname = "%s:geo_%s_head" % (ns, characterName)
    bsSource = getObj(objname)
    if bsSource == None:
        errors.append("BlendShape source cannot be found ('%s')" % objname)
        showErrors(errors, "createBS")
    
    #We're almost ready, just check if blendshape nodes already exists, and delete them if needed.
    bsNodes = pc.listHistory(bsSource, type="blendShape")
    if len(bsNodes) > 0:
        pc.warning( "blendShapes nodes were found and removed \
                    ('%s')" % ", ".join([n.stripNamespace() for n in bsNodes]))
        pc.delete(bsNodes)
        
    #At last, create the blendShape Node.
    bsArgs = [bsSource]
    bsArgs.extend(bsTargets)
    pc.blendShape(bsArgs, name="BS_chr_miranda_preMod")
    
    #And delete "BS" group.
    pc.delete(bsRoot)

# ---------------------------------------------------------------------------
# RigSet
# ---------------------------------------------------------------------------

def cleanSet(inRoot):
    try:
        doNotDelete = cmds.getAttr('|asset|grp_rig.doNotDelete')
        print 'True'
    except:
        doNotDelete = False
        print 'False'

    if doNotDelete:
        msg =  "#### {:>7}: 'cleanSet': cannot delete the rig, '|asset|grp_rig.doNotDelete' attr is True".format("Error")
        raise ValueError (msg)


    children = tkc.getChildren(inRoot, False)
    
    for child in children:
        if child.name() == "grp_rig":
            #Save the rig data (displays) and serialize a dictionary of disctionaries in a custom attribute of root
            dispDict = {}
            if pc.objExists(CTRL_SETNAME):
                ctrls = pc.sets(CTRL_SETNAME, query=True)

                for ctrl in ctrls:
                    disp = tkc.getDisplay(ctrl)
                    if disp != None:
                        #disp = ([(disp[0][0][0], disp[0][0][1], disp[0][0][2]), (disp[0][1][0], disp[0][1][1], disp[0][1][2]), disp[0][2]], disp[1], disp[2])
                        dispDict[ctrl.name()] = (disp, pc.getAttr(ctrl.getShape().name() + ".overrideColor"))

            if not pc.attributeQuery(DISPLAYS_CACHE_ATTRNAME, node=inRoot, exists=True):
                inRoot.addAttr(DISPLAYS_CACHE_ATTRNAME, dt="string")

            pc.setAttr(inRoot.name() + "." + DISPLAYS_CACHE_ATTRNAME, str(dispDict))

            #delete the geometry layer 
            if pc.objExists(GEOMETRIES_LAYERNAME):
                pc.delete(GEOMETRIES_LAYERNAME)

            #delete the cache set 
            if pc.objExists(CACHE_SETNAME):
                pc.delete(CACHE_SETNAME)

            #Finally delete the rig Root 
            pc.delete(child)
            return

    return

def createSetControlRecur(inGrp, inRoot, b_inRecursive=True):
    createdObjs = ([], [],[],[])
    
    ctrlName = inGrp.name().replace("grp_", "ctrl_")
    icon = None

    isRootControl = False
    
    if inGrp.name() in SPECNAMES:
        if inGrp.name() == 'grp_geo':
            isRootControl = True

        ctrlName = SPECNAMES[inGrp.name()]
        icon = tkc.createCubeIcon(ctrlName, size=CTRLS_SIZE, scale=(3, 0.001, 3))
        tkc.setObjectColor(icon, [255, 255, 0, 0])
    else:
        icon = tkc.createRingsIcon(ctrlName, size=CTRLS_SIZE)
        tkc.setObjectColor(icon, [255, 128, 255, 0])
    
    pc.parent(icon, inRoot)
    tkc.matchTRS(icon, inGrp)
    tkc.setNeutralPose(icon)
    createdObjs[2].append( tkc.constrain(inGrp, icon, "Pose") )
    createdObjs[2].append( tkc.constrain(inGrp, icon, "Scaling") )

    


    if isRootControl:
        global_srt = tkc.createCubeIcon(SPECNAMES['global_srt'], size=CTRLS_SIZE, scale=(4, 0.001, 4))
        tkc.setObjectColor(global_srt, [255, 255, 0, 0])
        pc.parent(global_srt, inRoot)
        tkc.matchTRS(global_srt, inGrp)
        tkc.setNeutralPose(global_srt)
        tkc.parent(icon, global_srt)
        createdObjs[0].append(global_srt)

        big_daddy = tkc.createCubeIcon(SPECNAMES['big_daddy'], size=CTRLS_SIZE, scale=(5, 0.001, 5))
        tkc.setObjectColor(big_daddy, [255, 255, 0, 0])
        #connect vis
        if not cmds.objExists( "grp_rig.SHOW_BIGDADDY"): 
            cmds.addAttr("grp_rig", longName="SHOW_BIGDADDY", attributeType = "long",keyable=1,
                                         min = 0,max=1) 
            cmds.setAttr("grp_rig.SHOW_BIGDADDY",0)
        big_daddyShape = big_daddy.getShape()
        cmds.connectAttr("grp_rig.SHOW_BIGDADDY",big_daddyShape+".v",f=1)
        # pc.setAttr('{0}.visibility'.format(big_daddy.getShape().name()), False)
        pc.parent(big_daddy, inRoot)
        tkc.matchTRS(big_daddy, inGrp)
        tkc.setNeutralPose(big_daddy)
        tkc.parent(global_srt, big_daddy)
        createdObjs[0].append(big_daddy)

    createdObjs[0].append(icon)
    

    if b_inRecursive:
        children = tkc.getChildren(inGrp, False)
        grpsChildren = []
        for child in children:
            shape = child.getShape()
            if child.name()[:4] == "grp_" and shape == None:
                grpsChildren.append(child) 
            elif shape !=None and shape.type() == "mesh":
                createdObjs[1].append(child)
            else:
                pc.warning('Unmanaged object {}'.format(child.name()))

        for grpChild in grpsChildren:
            print "grpChild=", grpChild
            subCreatedObjs = createSetControlRecur(grpChild, icon)
            createdObjs[0].extend(subCreatedObjs[0])
            createdObjs[1].extend(subCreatedObjs[1])
            createdObjs[2].extend(subCreatedObjs[2])

            
             


    return createdObjs

def rigSet(inRoot):
    children = tkc.getChildren(inRoot, False)
    
    valid = True
    
    if not "grp_geo" in [a.name() for a in children]:
        pc.warning("Root is supposed to have at least one 'grp_geo' child !")
        valid=False

    for child in children:
        if child.name() != "grp_geo" and child.name() != "grp_placeHolders" and child.name() != "grp_rig"and child.name() != "grp_particles":
            pc.warning("Unexpected asset root child {0} (expected 'grp_geo', and eventually 'grp_placeHolders', 'grp_rig' or 'grp_particles')".format(child.name()))
            valid=False

    if not valid:
        return None
    
    cleanSet(inRoot)
    
    grp_rig = pc.group(name="grp_rig", empty=True, parent=inRoot)
    
    ctrls, geos,cstL,grpL = createSetControlRecur(children[0], grp_rig)

    # add and connect the visibility attributes on the CTR of each groups -------------------------
    for ctr in ctrls: 
        

        conL=cmds.listConnections(ctr+".parentMatrix[0]",d=1,)
        if conL:
            if len(conL):
                con=conL[0]
           
                theSource = cmds.listConnections(con.split(".",1)[0], d=1)[0]
                # print ctr,"->",theSource
                    
                theAttr = "camera_visibility"
                if not cmds.objExists(ctr+"."+theAttr):
                    print "creating visibility Attr"
                    cmds.addAttr( str(ctr), longName=theAttr, attributeType= "long", min=0, dv=1, max=1, keyable=True,) 
                    cmds.setAttr(str(ctr) + "."+theAttr, l=False,)
                    # connect attr
                    print "connecting visibility"
                    cmds.connectAttr(ctr+"."+theAttr,theSource+".v",f=1)
                
                theAttr = "global_visibility"
                if not cmds.objExists(str(ctr)+"."+theAttr):
                    cmds.addAttr( str(ctr), longName=theAttr, attributeType= "long", min=0, dv=1, max=1, keyable=True,) 
                    cmds.setAttr(str(ctr) + "."+theAttr, l=False,)



    #We can try to reApply displays if saved ------------------------------------------------------------
    if pc.attributeQuery(DISPLAYS_CACHE_ATTRNAME, node=inRoot, exists=True):
        try:
            displaysDict = eval(pc.getAttr(inRoot.name() + "." + DISPLAYS_CACHE_ATTRNAME))
            for ctrl in ctrls:
                if ctrl.name() in displaysDict:
                    display, color = displaysDict[ctrl.name()]
                    tkc.setDisplay(ctrl, trs=display[0], size=display[1], select=False, displayName=display[2])
                    realColor = tkc.getColorFromMayaColor(color)
                    tkc.setObjectColor(ctrl, realColor)
        except:
            pc.warning('Cannot reapply displays !')





    #Put all controls in a set
    if pc.objExists(CTRL_SETNAME):
        pc.delete(CTRL_SETNAME)

    pc.sets(ctrls, name=CTRL_SETNAME)

    #Put all groups in a set for caching
    groups=[]

    for geo in geos:
        group = geo.getParent()
        if not group in groups:
            groups.append(group)

    if pc.objExists(CACHE_SETNAME):
        pc.delete(CACHE_SETNAME)

    pc.sets(groups, name=CACHE_SETNAME)

    #Clean old layers
    oldLayers = pc.ls("layer_*", type="displayLayer")
    if len(oldLayers) > 0:
        pc.delete(oldLayers)

    #Put all geometries in a layer, and set it to "reference"
    if pc.objExists(GEOMETRIES_LAYERNAME):
        pc.delete(GEOMETRIES_LAYERNAME)

    pc.select(geos)
    newLayer = pc.createDisplayLayer(name=GEOMETRIES_LAYERNAME)
    pc.setAttr(newLayer + ".displayType", 2)

    #Put all controls in a layer
    if pc.objExists(CTRLS_LAYERNAME):
        pc.delete(CTRLS_LAYERNAME)

    pc.select(ctrls)
    newLayer = pc.createDisplayLayer(name=CTRLS_LAYERNAME, noRecurse=True)

    pc.select(clear=True)


def addRigVisibAttr():

    oParent = "|asset|grp_rig|BigDaddy_NeutralPose|BigDaddy|Global_SRT_NeutralPose|Global_SRT|Local_SRT_NeutralPose|Local_SRT"
    if not cmds.ls(oParent):
        msg= "#### {:>7}: 'addRigVisibAttr': {} is missing in the scene, Rig could not be found".format("Error", oParent)
        raise ValueError (oParent+"")

    nurbsL = cmds.ls(cmds.listRelatives(oParent, allDescendents = True, fullPath = True, type = "nurbsCurve"), noIntermediate = True, l=True)
    ctrls = cmds.listRelatives (nurbsL, parent = True, fullPath = True, type = "transform")
   
    # add and connect the visibility attributes on the CTR of each groups -------------------------
    for ctr in ctrls: 
        
        conL=cmds.listConnections(ctr+".parentMatrix[0]",d=1,)
        if conL:
            if len(conL):
                con=conL[0]
           
                theSource = cmds.listConnections(con.split(".",1)[0], d=1)[0]
                # print ctr,"->",theSource
                    
                theAttr = "camera_visibility"
                if not cmds.objExists(ctr+"."+theAttr):
                    print "creating visibility Attr"
                    cmds.addAttr( str(ctr), longName=theAttr, attributeType= "long", min=0, dv=1, max=1, keyable=True,) 
                    cmds.setAttr(str(ctr) + "."+theAttr, l=False,)
                    # connect attr
                    print "connecting visibility"
                    cmds.connectAttr(ctr+"."+theAttr,theSource+".v",f=1)
                
                theAttr = "global_visibility"
                if not cmds.objExists(str(ctr)+"."+theAttr):
                    cmds.addAttr( str(ctr), longName=theAttr, attributeType= "long", min=0, dv=1, max=1, keyable=True,) 
                    cmds.setAttr(str(ctr) + "."+theAttr, l=False,)


def doNotDeleteRigAttr():
    if not cmds.listAttr( '|asset|grp_rig',string = "doNotDelete") and cmds.ls("|asset|grp_rig"):
        cmds.addAttr("|asset|grp_rig",ln = "doNotDelete", at = "bool")
    print "#### {:>7}: 'doNotDeleteRigAttr': created 'doNotDelete' attribute on '|asset|grp_rig'".format("Info")
    cmds.setAttr('|asset|grp_rig.doNotDelete',True)




def checkMeshNamingConvention(printInfo = True, inParent = "*"):
    """
    check all the meshes naming convention, '(geo|aux)_name_complement##' where 'name' and 'complement##' are strings of 24 alphanumeric characters
    only meshes of the main name space are taken into account, referenced meshes are therefore ignored.
        - printInfo (boolean) : print the 'multipleMesh' list 
        - return (list) : wrongMeshNamingConvention, all the meshes with a bad naming convetion
    """
    wrongMeshNamingConvention = []
    geoTransformList, instanceTransformL = miscUtils.getAllTransfomMeshes(inParent)
    if instanceTransformL:
        print "#### {:>7}: 'checkMeshNamingConvention': {} objects are actually instances: {}".format("Warning", len(instanceTransformL), instanceTransformL)
        geoTransformList = geoTransformList+ instanceTransformL

    if geoTransformList is None: geoTransformList = []
    
    for each in geoTransformList:
        eachShort = each.split("|")[-1]
        if not (re.match('^(geo|aux)_[a-zA-Z0-9]{1,24}$', eachShort) or re.match('^(geo|aux)_[a-zA-Z0-9]{1,24}_[a-zA-Z0-9]{1,24}$', eachShort)):
            wrongMeshNamingConvention.append(each)
    
    if printInfo == True:
        if wrongMeshNamingConvention:
            print "#### warning: 'checkMeshNamingConvention': the following MESH(ES) do not match the mesh naming convention:"
            print "#### warning: 'checkMeshNamingConvention': '(geo|aux)_name_complement##' where name and complement## are strings of 24 alphanumeric characters"
            for each in wrongMeshNamingConvention:
                print "#### warning: 'checkMeshNamingConvention': name not conform --> "+each
            cmds.select(wrongMeshNamingConvention, replace = True)
        else:
            print "#### info: 'checkMeshNamingConvention': MESH naming convention is correct"                
            
    return wrongMeshNamingConvention
    

def meshShapeNameConform(fixShapeName = True, myTransMesh = [], forceInfoOff = False, inParent = "*", GUI = True):
    """
    This function, makes sure every mesh shape name is consistant with its transform name: "transformName+Shape"
    Only shapes of the main name space are taken into account, referenced shapes are therefore ignored
        - fixShapeName (boolean): fix invalid shapes names if True, only log info otherwise
        - return (list): the meshes list that still have an invalid shape name
    """
    resultB = True
    logL = []

    if not myTransMesh:
        myTransMesh, instanceTransformL = miscUtils.getAllTransfomMeshes(inParent)

        if instanceTransformL:
            logMessage = "#### {:>7}: 'meshShapeNameConform': {} objects ignored since they are actually instances: {}".format("Warning", len(instanceTransformL), instanceTransformL)
            logL.append(logMessage)
            if GUI: print logMessage

        if myTransMesh is None: myTransMesh = []
        checkAllScene = True
    else:
        checkAllScene = False
    renamedNumber = 0
    shapesToFix = []
    for each in myTransMesh:  
        myShape = cmds.listRelatives (each, children = True, fullPath = True, type = "shape")
        if len(myShape)!= 1:
            print "#### error:'meshShapeNameConform' no or multiple shapes found for :"+each
            break
        myShape = myShape[0]
        myShapeCorrectName = each+"|"+each.split("|")[-1]+"Shape"
        if myShape != myShapeCorrectName and fixShapeName == True:
            logMessage = "#### {:>7}: 'meshShapeNameConform': rename '{}' --> as --> '{}'".format("Info",myShape.split("|")[-1],myShapeCorrectName.split("|")[-1])
            logL.append(logMessage)
            if GUI: print logMessage
            cmds.rename(myShape,each.split("|")[-1]+"Shape")
            renamedNumber = renamedNumber +1
        elif myShape != myShapeCorrectName and fixShapeName == False:
            logMessage = "#### warning: 'meshShapeNameConform': '"+each+"' has a wrong shape name: '"+myShape.split("|")[-1]+"' --> should be renamed as: --> '"+myShapeCorrectName.split("|")[-1]+"'"
            logL.append(logMessage)
            if GUI: print logMessage
            shapesToFix.append(each)
    if renamedNumber != 0:
        logMessage = "#### {:>7}: 'meshShapeNameConform': {} shape(s) fixed".format("Info",renamedNumber) 
        logL.append(logMessage)
        if GUI: print logMessage 
        return None
    elif shapesToFix: 
        logMessage = "#### {:>7}: 'meshShapeNameConform': {} shape(s) to be fixed".format("Info",shapesToFix)
        logL.append(logMessage)
        if GUI: print logMessage
        return shapesToFix
    elif checkAllScene == True:
        logMessage = "#### {:>7}: 'meshShapeNameConform': all meshes shapes names are correct".format("Info")
        logL.append(logMessage)
        if GUI: print logMessage
        return None
    else:
        return None



def makeAllMeshesUnique( inParent = "*", GUI = True):
    """
    make all the transform meshes shortName unique under de given 'inParent', 
    by default '*' means that any unreferenced mesh in the scene is taken into account
        - inParent (string) : long name of the parent 
    """
    resultB = True
    logL = []
    shortNameD = {}
   

    def renameAsUnique(longName="", reservedShortNameL = [], GUI = GUI):
        resultB = True
        logL = []
        shortName = longName.split("|")[-1]
        digit = re.findall('([0-9]+$)', longName)
        if digit:
            digit = digit[0]
            shortName = string.rstrip(shortName,digit)
            longNameNoDigit = string.rstrip(longName,digit)
        else:
            longNameNoDigit = longName
        digit = "1"    
        i = 0
        while shortName+digit in reservedShortNameL:
            digit = string.zfill(str(int(digit)+1), len(digit))
            i+=1
            if i>300:
                logMessage = "#### {:>7}: 'renameAsUnique' while loop has reached the security limit, program has been stopped".format("Error")
                if GUI == True: print logMessage
                logL.append(logMessage)
                resultB = False
                break
        newShortName = shortName+digit
        cmds.rename(longName,newShortName)
        newLongName = longNameNoDigit+digit
        logMessage = "#### {:>7}: 'renameAsUnique' Renamed '{}'   -->  '{}'".format("Info",longName,newShortName)
        if GUI == True: print logMessage
        logL.append(logMessage)
        return dict(resultB=resultB, logL=logL, newShortName = newShortName, newLongName=newLongName)


    allMeshL = cmds.ls(cmds.listRelatives(inParent, allDescendents = True, fullPath = True, type = "mesh"), noIntermediate = True, l=True)
    allTransL = cmds.listRelatives (allMeshL, parent = True, fullPath = True, type = "transform")
    allTransL = list(set(allTransL))

    transL = []
    instL =[]
    
    for each in allTransL:
        if len(cmds.listRelatives(each,allParents =True))>1:
            instL.append(each)
        else:
            transL.append(each)

    if instL:
        logMessage = "#### {:>7}: 'getSameShortNameMesh' Ignoring {} instance object : {}".format("Warning", len(instL), instL)
        logL.append(logMessage)
        if GUI == True: print logMessage

    multipleMesh = []
    for each in allTransL:
        eachShort = each.split("|")[-1]
        ## if the key exists, adds the value to the attached list
        if eachShort in shortNameD.keys():
            elemList = shortNameD.get(eachShort)
            elemList.append(each)
        else: ## else creates the list with a single value
            shortNameD[eachShort] = [each]


    reservedShortNameL = list(shortNameD.keys())
    renamedLongNameL = []
    for key in shortNameD.keys():
        if len(shortNameD[key])>1:
            toModifyL = list(set(shortNameD[key])&set(transL))
            for each in toModifyL[1:]:
                resultD = renameAsUnique(longName=each, reservedShortNameL = reservedShortNameL)
                reservedShortNameL.append(resultD['newShortName'])
                renamedLongNameL.append(resultD['newLongName'])
                logL.extend(resultD['logL'])
                if resultD['resultB']== False: resultB = False


    logMessage = "#### {:>7}: 'makeAllMeshesUnique' '{:>3}' object(s) renamed: '{}' ".format("Info", len(renamedLongNameL),renamedLongNameL)
    print logMessage
    logL.append(logMessage)

    return dict(resultB=resultB, logL=logL, shortNameD = shortNameD)


def geoGroupDeleteHistory(GUI=True, freezeVrtxPos = True):
    """
    gets all the mesh transformms under the '|asset|grp_geo', delete their history and delete any intermediate unconnected shape 
    """
    resultB = True
    logL = []
    geoTransformList,instanceTransformL = miscUtils.getAllTransfomMeshes(inParent = "|asset|grp_geo")


    if not cmds.listAttr( '|asset|grp_geo',string = "deleteHistoryDone") and cmds.ls("|asset|grp_geo"):
        cmds.addAttr("|asset|grp_geo",ln = "deleteHistoryDone", at = "bool")
        deleteHistoryDone = False
    else:
        deleteHistoryDone = cmds.getAttr('|asset|grp_geo.deleteHistoryDone')


    if  deleteHistoryDone:
        logMessage = "#### {:>7}: 'geoGroupDeleteHistory': 'geoGroupDeleteHistory': skipping operation, '|asset|grp_geo.deleteHistoryDone' attr is True".format("Info")
        logL.append(logMessage)
        if GUI == True: print logMessage
        return resultB, logL

    #now process vertex frezze position in a different loop for instances to avoid precessing the several time
    if freezeVrtxPos:
        for each in geoTransformList:
            cmds.polyMoveVertex (each, constructionHistory =True, random  = 0)
            

        processedInstTransL = []
        for each in instanceTransformL:
            eachShapeL = cmds.ls(cmds.listRelatives(each, noIntermediate = True, shapes = True, fullPath = True),l=True)
            parentTransL = cmds.listRelatives(eachShapeL,allParents =True, fullPath = True)
            if each not in processedInstTransL:
                cmds.polyMoveVertex (each, constructionHistory =True, random  = 0)
                processedInstTransL.extend(parentTransL)
       
        logMessage = "#### {:>7}: 'geoGroupDeleteHistory': vertex position freezed on {} geometries and {} instances".format("Info", len(geoTransformList),len(processedInstTransL))
        logL.append(logMessage)
        if GUI == True: print logMessage
        cmds.select(cl=True)


    if instanceTransformL:
        logMessage = "#### {:>7}: 'geoGroupDeleteHistory': {} objects are actually instances: {}".format("Warning", len(instanceTransformL), instanceTransformL)
        logL.append(logMessage)
        if GUI == True: print logMessage
        geoTransformList = list(geoTransformList+ instanceTransformL)

    cmds.delete(geoTransformList,ch =True)
    logMessage = "#### {:>7}: 'geoGroupDeleteHistory': deteted history on {} geometries".format("Info",len(geoTransformList))
    logL.append(logMessage)
    if GUI == True: print logMessage
    
    geoShapeList = cmds.ls(cmds.listRelatives("|asset|grp_geo", allDescendents = True, fullPath = True, type = "mesh"), noIntermediate = False, l=True)
    deletedShapeList = []
    for eachGeoShape in geoShapeList:
        if cmds.getAttr(eachGeoShape+".intermediateObject") == True:
            if  len(cmds.listHistory (eachGeoShape, lv=1)+ cmds.listHistory (eachGeoShape,future = True, lv=1))>2:
                logMessage = "#### warning : 'geoGroupDeleteHistory': this intermediate mesh shape still has an history and cannot be deleted : "+eachGeoShape
                logL.append(logMessage)
                if GUI == True: print logMessage
            else:
                cmds.delete(eachGeoShape)
                deletedShapeList.append(eachGeoShape)
            logMessage = "#### info : 'geoGroupDeleteHistory': deteted "+str(len(deletedShapeList))+" intermediate(s) mesh shape : "
            logL.append(logMessage)
            if GUI == True: print logMessage

    try:
        cmds.setAttr("|asset|grp_geo.deleteHistoryDone",1)
    except:
        pass

    return resultB, logL





def freezeResetTransforms(inParent = "*", inConform = False, GUI = True, selectUnfreezed = False, inGeoTransL=[]):
    """
    gets all the mesh transforms under de given inParent, an check that all the transforms values are set to 0 (1 for scales)
    freeze and reset the the transforms in case inConform is True.
    """
    log = miscUtils.LogBuilder(gui=GUI, funcName ="freezeResetTransforms")

    unFreezedTransfomList = []
    freezedTransfomList = []
    conformTransfomList = []
    if not inGeoTransL:
        geoTransformList,instanceTransformL = miscUtils.getAllTransfomMeshes(inParent)
        if instanceTransformL:
            logMessage = "{} objects ignored since they are actually instances: {}".format(len(instanceTransformL), instanceTransformL)
            log.printL("w", logMessage)
    else:
        geoTransformList = list(inGeoTransL)

    for each in geoTransformList:
        rotationL = cmds.xform( each, os=True, q=True,  ro=True)
        translationL=cmds.xform( each, os=True, q=True,  t=True)
        scaleL = cmds.xform( each, os=True, q=True,  s=True, r = True )
        rotatePivotL = cmds.xform( each, os=True, q=True, rp=True)
        scalePivotL = cmds.xform( each, os=True, q=True, sp=True)
        if (rotationL!=[0,0,0] or translationL!=[0,0,0] or scaleL!=[1,1,1] or rotatePivotL!=[0,0,0] or scalePivotL!=[0,0,0]):
            if inConform == False:
                unFreezedTransfomList.append(each)
                logMessage = "{} transform has unfreezed value(s):".format(each)
                if rotationL!=[0,0,0]:
                    logMessage = logMessage+" rotation = "+str(rotationL)
                if translationL!=[0,0,0]:
                    logMessage = logMessage+" translation = "+str(translationL)
                if scaleL!=[1,1,1]:
                    logMessage = logMessage+" scale = "+str(scaleL)
                if rotatePivotL!=[0,0,0]:
                    logMessage = logMessage+" rotate pivot = "+str(rotatePivotL)
                if scalePivotL!=[0,0,0]:
                    logMessage = logMessage+" scale pivot = "+str(scalePivotL)
                log.printL("e", logMessage)
            else:
                cmds.makeIdentity (each ,apply= True, n=0, pn=1)
                cmds.makeIdentity (each ,apply= False, n=0, pn=1)
                freezedTransfomList.append(each)
        else:
            conformTransfomList.append(each)

    if unFreezedTransfomList:
        if selectUnfreezed: cmds.select(unFreezedTransfomList)
        logMessage = "{} unfreezed transforms found: {}".format(len(unFreezedTransfomList),unFreezedTransfomList)
        log.printL("e", logMessage)
    if conformTransfomList:
        logMessage = "{} transforms checked successfully: {}".format(len(conformTransfomList),conformTransfomList)
        log.printL("i", logMessage)
    if freezedTransfomList != []:
        logMessage = "{} transforms have been freezed and reset: {}".format(len(freezedTransfomList),freezedTransfomList)
        log.printL("i", logMessage)

    return dict(resultB=log.resultB, logL=log.logL)


def compareHDToPreviz():
    """
    This script has been made at dreamwall, to compare previz and master modeling structure you must import the previz file as a reference, 
    the asset node should have this kind of name: "nameSpace:asset_previz". then select the previz asset transform and the master asst transform, 
    run the script and read the log
    """
    # compare asset_hi to asset_previz ( compare translate-rotate of group are the same and local pivot rotate-scale of hi must be 0).
    import maya.cmds as cmds
    import math

    DECIMAL_NB = 3
    EPSILON = 0.001 # if less than epsilon its zero !
    BOX_SCALE = 0.1 # 10%

    listWarning=[]
    dictWarning={}

    _DW = 0 # 1 if Dreamwall, 0 if 2Minutes


    def bboxPrintWarning(listWarning):
        print("\n*** Bbox warning if more than " + str(1./BOX_SCALE) + " % different between Hi and Previz ***")
        for warning in listWarning:
            print("\tWARNING: "+warning)

    # compare values 'hi' min-max to 'preview' min-max
    def compareMinMaxHiToPreviz(hiMin, hiMax, previzMin, previzMax, boxError):
        ##print("hiMin = " + str(hiMin) + " hiMax = " + str(hiMax) + " previzMin = " + str(previzMin) + " previzMax = " + str(previzMax) + " boxError = " + str(boxError))
        errCenter = False
        errDelta = False
        previzCenter = (previzMin + previzMax) / 2.
        hiCenter = (hiMin + hiMax) / 2
        centerDelta = math.fabs(previzCenter-hiCenter) # difference of two centers.
        previzDelta = math.fabs(previzMax-previzMin)
        if centerDelta > previzDelta*boxError: # if diff. center > bbox size * boxError, error in position of the box.
            errCenter = True

        hiDelta = math.fabs(hiMax-hiMin)

        if math.fabs(hiDelta-previzDelta) > previzDelta*boxError:
            errDelta = True

        return errCenter, errDelta

    def compareBboxHiToPreviz(groupHi, groupPreviz, boxScale, listWarning): # ex. boxScale = 0.1 (10%)
        hiBbox = cmds.exactWorldBoundingBox(groupHi)
        ##print("\tbbox hi = %f" % hiBbox[0], "%f" % hiBbox[1], "%f" % hiBbox[2], "%f" % hiBbox[3], "%f" % hiBbox[4], "%f" % hiBbox[5])
        previzBbox = cmds.exactWorldBoundingBox(groupPreviz)
        ##print("\tbbox previz = %f" % previzBbox[0], "%f" % previzBbox[1], "%f" % previzBbox[2], "%f" % previzBbox[3], "%f" % previzBbox[4], "%f" % previzBbox[5])

        errCenterX, errDeltaX = compareMinMaxHiToPreviz(hiBbox[0], hiBbox[3], previzBbox[0], previzBbox[3], boxScale)
        errCenterY, errDeltaY = compareMinMaxHiToPreviz(hiBbox[1], hiBbox[4], previzBbox[1], previzBbox[4], boxScale)       
        errCenterZ, errDeltaZ = compareMinMaxHiToPreviz(hiBbox[2], hiBbox[5], previzBbox[2], previzBbox[5], boxScale)

        if errCenterX or errCenterY or errCenterZ:
            warn = " has bbox position mismatch in "
            if errCenterX:
                warn += "X "
            if errCenterY:
                warn += "Y "
            if errCenterZ:
                warn += "Z "
            listWarning.append(str(groupHi) + warn)

        if errDeltaX or errDeltaY or errDeltaZ:
            warn = " has bbox size mismatch in "
            if errDeltaX:
                warn += "X "
            if errDeltaY:
                warn += "Y "
            if errDeltaZ:
                warn += "Z "
            listWarning.append(str(groupHi) + warn)
            

    #print(cmds.nodeType("grp_bureauArriere_grp_livre_to_ctrl_livre_prCns"))

    def is_group(node): # test if node is a group
        if cmds.nodeType(node) != 'transform': # test if node is a transform
            return False
        children = cmds.listRelatives(c=True, f=True)
        for child in children:
            if cmds.nodeType(child) == 'transform':
                return True
        return False

    def floatLimitDecimal(value, decimalNb):
        return float(format(value, "."+str(decimalNb)+"f"))
        
    def vectorLimitDecimal(vector, decimalNb):
        return [floatLimitDecimal(vector[0],decimalNb), floatLimitDecimal(vector[1],decimalNb), floatLimitDecimal(vector[2],decimalNb)]

    def cmp2zero(vec):
        return ((math.fabs(vec[0]) > EPSILON) or (math.fabs(vec[1]) > EPSILON) or (math.fabs(vec[2]) > EPSILON))

    def createSetForJulien(name, object):
        cmds.sets(object, n="previz:"+name)    

    def findGroupHiNotExistingInPreviz(assetHi, assetPreviz):
        groupsHi = cmds.listRelatives(assetHi, ad=True, f=True,type='transform') # get all transforms with ful path
        for groupHi in groupsHi:
            if is_group(groupHi) and "grp_" in groupHi.split("|")[-1] and not "grp_geo_" in groupHi.split("|")[-1]: # if the transform is a group
                #print("groupHi : " + groupHi)
                namespacePreviz = ""
                if "previz:" in assetPreviz:
                    namespacePreviz = assetPreviz.split(":")[0] + ":" # get namespace
                groupPreviz = (groupHi.replace(assetHi, assetPreviz)).replace("grp_", namespacePreviz+"grp_") # build groupPreviz name from groupHi
                #print("namespacePreviz = " + namespacePreviz)
                #print ("groupPreviz : " + groupPreviz)
                
                if not cmds.objExists(groupPreviz): # if groupPreviz doesnt exist, groupHi exist only in Hi !
                    #print ("groupPreviz : " + groupPreviz)
                    print ("\t\t" + groupHi)
                    createSetForJulien("Set_INFO_GroupOnlyExistingInHi_"+groupHi, groupHi)

    def computeBboxVolume(bbox):
        Xab = bbox[3]-bbox[0]
        if Xab == 0:
            Xab = 0.0001
        Yab = bbox[4]-bbox[1]
        if Yab == 0:
            Yab = 0.0001
        Zab = bbox[5]-bbox[2]
        if Zab == 0:
            Zab = 0.0001
        return (math.fabs(Xab)*math.fabs(Yab)*math.fabs(Zab)) 
                   
    def compareBboxVolumeHiToPreviz(groupHi, groupPreviz): # ex. boxScale = 0.1 (10%)
        ##print("groupHi = " + groupHi + " groupPreviz = " + groupPreviz)
        hiBbox = cmds.exactWorldBoundingBox(groupHi)
        ##print("\tbbox hi = %f" % hiBbox[0], "%f" % hiBbox[1], "%f" % hiBbox[2], "%f" % hiBbox[3], "%f" % hiBbox[4], "%f" % hiBbox[5])
        previzBbox = cmds.exactWorldBoundingBox(groupPreviz)
        ##print("\tbbox previz = %f" % previzBbox[0], "%f" % previzBbox[1], "%f" % previzBbox[2], "%f" % previzBbox[3], "%f" % previzBbox[4], "%f" % previzBbox[5])
        
        hiVol = computeBboxVolume(hiBbox)
        previzVol = computeBboxVolume(previzBbox)    
        ##print("hiVol = " + str(hiVol) + "  previzVol = " + str(previzVol))
        
        if (hiVol > 0.001) and (previzVol > 0.001): # some volume maybe zero because all vertex are on one plane ...
            diffBbox = math.fabs(hiVol - previzVol)
            percent = diffBbox / previzVol
            ##print("percent diff = " + str(percent*100))
            return percent
        else:
            return 99999

    if not _DW:
        result = cmds.promptDialog(title='Compare HD to Previz',message='Enter a % volume tolerance :',text= '20',button=['OK', 'Cancel'],defaultButton='OK',cancelButton='Cancel',dismissString='Cancel')
        if result == 'OK':
            text = cmds.promptDialog(query=True, text=True) 
            try:
                BOX_SCALE = float(text)/100
                if not 0<BOX_SCALE<1:
                    raise ValueError ("the entered value '"+text+"' must be an 0 < integer < 100")
            except:
                raise ValueError ("the entered text '"+text+"' must be an 0 < integer < 100")
        else:
            return

    ## previz is the ref, hi could have more group but not less, and check localspace pivot translate et scale MUST be 0 !
    namespacePreviz = ""
    errorCount = 0;
    sel = cmds.ls(sl=True, type='transform') # get the transform(s) selected
    ##print sel
    if len(sel) == 2: # test if current selection has 2 nodes
        assetPreviz = sel[1]
        assetHi = sel[0]
        
        print("\n***** checking group : " + assetHi + " to group : " + assetPreviz)
        
        if not _DW:
            print("\t*** INFO: Groups only existing in Hi")
            findGroupHiNotExistingInPreviz(assetHi, assetPreviz)
            print("\n")
        
        if "previz" in sel[0]:
            assetPreviz = sel[0]
            assetHi = sel[1]
             
        if "previz:" in assetPreviz:
            namespacePreviz = assetPreviz.split(":")[0] + ":" # get namespace

        print("\t*** comparing translations and rotations value from " + assetHi + " to reference " + assetPreviz)
        groupsPreviz = cmds.listRelatives(assetPreviz, ad=True, f=True,type='transform') # get all transforms with ful path
        #print ("* " + str(groupsPreviz))
        for groupPreviz in groupsPreviz:
            #print (groupPreviz + " " + groupPreviz.split("|")[-1])
             
            if is_group(groupPreviz) and "grp_" in groupPreviz.split("|")[-1] and not "grp_geo_" in groupPreviz.split("|")[-1]: # if the transform is a group
                ##print("\tgroupPreviz = " + str(groupPreviz))
                
                # get positions, rotations of locator
                rotPreviz = vectorLimitDecimal(cmds.xform(groupPreviz,q=True,r=1,ro=1), DECIMAL_NB) # get rotations
                posPreviz = vectorLimitDecimal(cmds.xform(groupPreviz,q=True,r=1,t=1), DECIMAL_NB) # get translations
                #print rotPreviz
                #print posPreviz
                groupHi=""
                if namespacePreviz != "": # if namespace, remove it to build groupHi
                    groupHi = groupPreviz.replace(assetPreviz, assetHi).replace(namespacePreviz, "") # build groupPreviz name 
                else:
                    groupHi = groupPreviz.replace(assetPreviz, assetHi) #build groupPreviz name
                #print("\tgroupHi = " + groupHi)
                if cmds.objExists(groupHi): # test if group exists ?
                    rotHi = vectorLimitDecimal(cmds.xform(groupHi,q=True,r=1,ro=1), DECIMAL_NB) # get rotations
                    posHi = vectorLimitDecimal(cmds.xform(groupHi,q=True,r=1,t=1), DECIMAL_NB) # get translations
                    error = False
                    if cmp(rotHi, rotPreviz):
                        print("\t\tERROR in group: " + groupHi + " has different rotate values: " + str(rotHi) + " instead of previz : " + str(rotPreviz))
                        error = True
                        errorCount += 1
                        if not _DW:
                            createSetForJulien("Set_ERROR_"+str(groupHi)+"_hasDifferentRotateValues", [groupHi,groupPreviz])
                    if cmp(posHi, posPreviz):
                        print("\t\tERROR in group: " + groupHi + " has different translation values: " + str(posHi) + " instead of previz : "+ str(posPreviz))
                        error = True
                        errorCount += 1
                        if not _DW:
                            createSetForJulien("Set_ERROR_"+str(groupHi)+"_hasDifferentTranslationValues", [groupHi,groupPreviz])
                    # test local pivot rotate and scale
                    localPivotRotateHi = vectorLimitDecimal(cmds.xform(groupHi,q=True,os=1,rp=1), DECIMAL_NB) # get local rotate pivot
                    localPivotScaleHi = vectorLimitDecimal(cmds.xform(groupHi,q=True,os=1,sp=1), DECIMAL_NB) # get local scale pivot
                    if cmp2zero(localPivotRotateHi): # compare to zero with epsilon precision.
                        print("\t\tERROR in group: " + groupHi + " has local pivot rotate values: " + str(localPivotRotateHi))
                        error = True
                        errorCount += 1
                        if not _DW:
                            createSetForJulien("Set_ERROR_"+str(groupHi)+"_hasLocalPivotRotateNotZero", groupHi)
                    if cmp2zero(localPivotScaleHi):
                        print("\t\tERROR in group: " + groupHi + " has local pivot scale values: " +  str(localPivotScaleHi))
                        error = True
                        errorCount += 1
                        if not _DW:
                            createSetForJulien("Set_ERROR_"+str(groupHi)+"_hasLocalPivotScaleNotZero", groupHi)

                    if _DW:
                        compareBboxHiToPreviz(groupHi, groupPreviz, BOX_SCALE, listWarning)
                    else:
                        percent = compareBboxVolumeHiToPreviz(groupHi, groupPreviz)
                        if percent > BOX_SCALE: 
                            if (percent == 99999):
                                dictWarning["ERROR: " + groupHi] = -1
                                createSetForJulien("Set_ERROR_Bbox_"+str(groupHi)+"_hasVolumeEqualZero", groupHi)
                                error = True
                                errorCount += 1
                            else:
                                dictWarning["WARNING: " + groupHi + " volume is different than previz"] = percent
                                createSetForJulien("Set_WARNING_Bbox"+str(groupHi)+"_hasVolueGretaerThanPrvizBy_" + str(floatLimitDecimal(percent*100,DECIMAL_NB)) + "_percent", [groupHi,groupPreviz])
                     
                else:
                    print("\t\tERROR: group: " + groupHi + " is missing")
                    error = True
                    errorCount += 1
                    ##if not _DW:
                    ##    createSetForJulien("Set_ERROR_"+str(groupHi)+"_isMissing", groupHi)
                        

        if _DW:
            bboxPrintWarning(listWarning) # print list warning for bbox.
        else:
            listEllipseWarning = sorted(dictWarning.items(), key=lambda t: t[1], reverse=True) # sort by value greatest to smallest.
            print("\n\t*** Bbox warning if more than " + str(1./BOX_SCALE) + " % different between Hi and Previz ***")
            for warn in listEllipseWarning:
                if warn[1] == -1: # volume is zero
                    print("\t\t" + warn[0] + " can't compare volume because object are flat")
                else:
                    print ("\t\t" + warn[0] + " by " + str(floatLimitDecimal(warn[1]*100,DECIMAL_NB)) + " %")

        print("\n")
        if (errorCount != 0):
            if (errorCount == 1):
                print("**** " + str(errorCount) + " error found ")
            else:
                print("**** " + str(errorCount) + " errors found ")
                  
        warningCount = len(listWarning)
        if (warningCount != 0):
            if (warningCount == 1):
                print("**** " + str(warningCount) + " warning found ")
            else:
                print("**** " + str(warningCount) + " warnings found ")

        print("**** checking done")
    else:
        print ("\n***** please select both asset hi-def and asset previz and try again")



def combineGeoGroup(toCombineTransfL = [], combineByMaterialB = False, GUI = True, autoRenameI = 0, verbose = True):
    """
    this script merge selected objects only if they are under the same group.
    It ensure that the resulting object is under the intial group.
    Warning: if GUI is False a part of the tests are skipped to speed up the process in larges scenes.
    the tests mus be done in the callin script, see combineAllGroups for instance
    instances will be skipped
        toCombineTransfL: a list of transform objects to combine, groups are not accepeted. if nothing in input try with the selection
        combineByMaterialB: if True il merge only objects that share the same material
        GUI: if True wil log messages and select merged object when combined 
        autoRenameI:    0: do not rename the combined objects, name is the first selected object or first of the list
                        1: rename combined object as the group he's under, '_mergedxx' extention is added at the extend

    """
    resultB = True
    logL = []
    resultObjL = []
    combinedObjL = []
    soloMeshToCombine = []
    shaderAssignationD = {'multiMaterial':[]}

    if not toCombineTransfL:
        toCombineTransfL = cmds.ls(selection = True,l = True)
    else:
        toCombineTransfL= cmds.ls(toCombineTransfL, l = True)

    if GUI == True: 
        #exclude instances from the input
        transMeshL, instanceTransformL = miscUtils.getAllTransfomMeshes("*")
        instanceTransformL= cmds.ls(instanceTransformL, l = True)
        InstanceToCombineL = list(set(toCombineTransfL) & set(instanceTransformL))
        if InstanceToCombineL:
            logMessage = "#### {:>7}: 'combineGeo' {} elements cannot be combined since they are instances, they will be skipped: {}".format("Warning", len(InstanceToCombineL), InstanceToCombineL)
            if GUI == True: print logMessage
            logL.append(logMessage)
            toCombineTransfL = list(set(toCombineTransfL) - set(InstanceToCombineL))


        #fail if one input is not a transform
        toCombineTransfFilteredL = cmds.ls(toCombineTransfL, type= 'transform', l=True)
        if toCombineTransfFilteredL!= toCombineTransfL:
            notTransformObjL = list(set(toCombineTransfL)-set(toCombineTransfFilteredL))
            logMessage = "#### {:>7}: 'combineGeo' Cannot merge elements that are not transforms: {}".format("Error", notTransformObjL)
            if GUI == True : raise ValueError (logMessage)
            resultB = False
            logL.append(logMessage)
            return [resultB, logL, toCombineTransfL, resultObjL] 


    toCombineShapesL = cmds.ls(toCombineTransfL,l = True, shapes = True)+ cmds.ls(cmds.listRelatives(toCombineTransfL, children = True, fullPath = True, type = "mesh"), noIntermediate = True, l=True)
    if len(toCombineShapesL)<2:
        print "combineGeoGroup: toCombineTransfL",toCombineTransfL
        soloMeshToCombine= list(toCombineTransfL)
        print "soloMeshToCombine",soloMeshToCombine
        return [resultB, logL, toCombineTransfL, resultObjL] 

    path = cmds.listRelatives(cmds.listRelatives(toCombineShapesL[-1], parent = True, fullPath = True, type = "transform"), parent = True, fullPath = True, type = "transform")[0]
    mtx = cmds.xform( path, q = True, ws = True, matrix = True )
    finalObjectName = toCombineShapesL[-1].split("|")[-1]

    if GUI == True:
    # check that all the meshes belong to the same group
        for each in toCombineShapesL:
            eachPath = cmds.listRelatives(cmds.listRelatives(each, parent = True, fullPath = True, type = "transform"), parent = True, fullPath = True, type = "transform")[0]
            if path != eachPath:
                logMessage = "#### {:>7}: 'combineGeo' Cannot merge 2 elements of a different group: {} is not under '{}'".format("Error", each, path)
                if GUI == True : raise ValueError (logMessage)
                resultB = False
                logL.append(logMessage)
                return [resultB, logL, toCombineTransfL, resultObjL] 

    # create a dictionnary to gather all the shapes that share the same material. 
    # every key correspond to a shading engine and reference the objects this SE is connected to:
    if combineByMaterialB:
        shadingEngineL = []
        for each in toCombineShapesL:
            shadEngEachL = cmds.listConnections(each, destination = True, source = False, type = "shadingEngine")
            if not shadEngEachL or len(shadEngEachL)>1:
                continue
            else:
                if shadEngEachL[0] not in shadingEngineL:
                    shadingEngineL.append(shadEngEachL[0])

        for eachSE in shadingEngineL:
            shapeShareMatL = cmds.ls(cmds.listConnections(eachSE, source = True, destination = False, shapes = True ),l=True)
            shapeToCombineL = list(set(shapeShareMatL).intersection(set(toCombineShapesL)))
            for eachShareMat in shapeToCombineL:
                if len(cmds.listConnections(eachShareMat, destination = True, source = False, type = "shadingEngine"))>1:
                    shaderAssignationD['multiMaterial'].append(eachShareMat)
                else:
                    if not eachSE in shaderAssignationD:
                        shaderAssignationD[eachSE]=[eachShareMat]
                    else:
                        shaderAssignationD[eachSE].append(eachShareMat)
    else:
        if not 'miscSE' in shaderAssignationD:
            shaderAssignationD['miscSE']=toCombineShapesL
        else:
            shaderAssignationD['miscSE'].append(toCombineShapesL)

    #combine objects depending on the dictionary key they are referenced under
    for each in shaderAssignationD:
        if each == 'multiMaterial' :
            if shaderAssignationD['multiMaterial']:
                logMessage = "#### {:>7}: 'combineGeoGroup' {} objects have several materials assigned hence cannot be combined".format("Warning",len(shaderAssignationD['multiMaterial']))
                logL.append(logMessage)
                if GUI == True: print logMessage
        else:
            if len(shaderAssignationD[each])>1:
                combinedObjL.extend(shaderAssignationD[each]) 
                mergedObjectName = cmds.polyUnite(shaderAssignationD[each], ch=False, mergeUVSets = True, name = finalObjectName )[0]
                groupName = path.split("|")[-1]
                parentName = path.split(groupName)[0].rstrip("|")
                #parent back the merged object under the initial group 
                if not cmds.ls(path):
                    if parentName =='':
                        newGroupName = cmds.group( name= groupName, empty=True)
                        cmds.xform( path,  ws = True, matrix = mtx )
                        mergedObjectName = cmds.parent(mergedObjectName, path )[0]
                    else:
                        newGroupName = cmds.group(empty=True, name= groupName, parent = parentName)
                        cmds.xform( path,  ws = True, matrix = mtx )
                        mergedObjectName = cmds.parent(mergedObjectName, path )[0]
                else:
                    mergedObjectName = cmds.parent(mergedObjectName, path )[0]
                if autoRenameI ==0 : mergedObjectName = cmds.rename(mergedObjectName,mergedObjectName.split("Shape")[0])
                elif autoRenameI == 1 : mergedObjectName = cmds.rename(mergedObjectName,groupName.replace("grp_","geo_")+"_merged00" )
                resultObjL.append(mergedObjectName)

    logMessage = "#### {:>7}: 'combineGeoGroup' {} objects combined in : {} objects".format("Info",len(combinedObjL),len(resultObjL))
    logL.append(logMessage)

       
    if GUI == True: 
        cmds.select(resultObjL)
        if verbose == True: print logMessage

    return [resultB, logL, toCombineTransfL, resultObjL] 



def combineAllGroups(inParent = "asset|grp_geo", GUI = True, autoRenameI= 1, combineByMaterialB = True):
    resultB = True
    logL = []
    skippedInstanceL =[]
    soloMeshToCombine=[]
    resultL = []
    CombineNbPerformedI = 0

    #exclude instances from the input
    transMeshL, instanceTransformL = miscUtils.getAllTransfomMeshes(inParent)
    instanceTransformL= cmds.ls(instanceTransformL, l = True)



    meshNbBeforeConbineI = len(cmds.listRelatives(cmds.listRelatives(inParent, allDescendents = True, fullPath = True, type = "mesh"), allParents = True, fullPath = True, type = "transform"))
    transformL = cmds.ls(cmds.listRelatives(inParent, allDescendents = True, fullPath = True, type = "transform"), l=True, exactType="transform")
    for each in transformL:
        if re.match('^grp_', each.split("|")[-1]):
            meshL = cmds.listRelatives(cmds.listRelatives(each, children = True, fullPath = True), children = True, fullPath = True, type = "mesh")
            toCombineTransfL = cmds.listRelatives(meshL, parent = True, fullPath = True, type = "transform")
            if toCombineTransfL: skippedInstanceL.extend(list(set(toCombineTransfL)&set(instanceTransformL)))
            if toCombineTransfL and len(toCombineTransfL)>1:
                toCombineTransfL = list(set(toCombineTransfL)-set(instanceTransformL))
                if len(toCombineTransfL)>1: 
                    combineGeoGroup(toCombineTransfL = toCombineTransfL, GUI = False,verbose = False, autoRenameI= autoRenameI, combineByMaterialB = combineByMaterialB)
                    CombineNbPerformedI += 1
            elif toCombineTransfL:
                soloMeshToCombine.extend(toCombineTransfL)


    meshNbAfterConbineI = len(cmds.listRelatives(cmds.listRelatives("asset|grp_geo", allDescendents = True, fullPath = True,type = "mesh"), allParents = True))


    logMessage = "#### {:>7}: 'combineAllGroups' {} meshes in the scene : {} meshes after conbine operation, {} combine performed".format("Info",meshNbBeforeConbineI,meshNbAfterConbineI,CombineNbPerformedI)
    if GUI == True: print logMessage
    logL.append(logMessage)

    logMessage = "#### {:>7}: 'combineAllGroups' --> {} could not be combined --> unique under their group".format("Info", len(soloMeshToCombine))
    logL.append(logMessage)
    if GUI == True: print logMessage
    if skippedInstanceL:
        skippedInstanceL = cmds.ls(skippedInstanceL)
        logMessage = "#### {:>7}: 'combineAllGroups' --> {} could not be combined --> instances".format("Info", len(skippedInstanceL))
        logL.append(logMessage)
        if GUI == True: print logMessage

    # make sure alle the geometry is in the geometry layer
    geoTransformList = []
    allTransMesh, instanceTransformL = miscUtils.getAllTransfomMeshes(inParent="|asset|grp_geo", inType = "mesh")
    geoTransformList = allTransMesh+ instanceTransformL
    if cmds.ls("geometry", type = "displayLayer"):
        cmds.editDisplayLayerMembers( "geometry", geoTransformList, noRecurse=True)

    return resultB, logL


def convertObjToInstance(transformL=[], GUI = True, checkTopo = True, updateSetLayInstance = True, legacy = False):
    #exemple of transform naming selection
    #cmds.listRelatives(cmds.ls("geo_femmeFatyVisiteurA*",type='mesh'),parent =True, fullPath = True, type = "transform")
    logL = []
    resultB = True

    shapesL = cmds.listRelatives(cmds.ls(transformL,l = True, type = "mesh"), parent =True, fullPath = True, type = "transform")
    if not shapesL:
        shapesL=[]
    transformL = list(set(cmds.ls(transformL,l = True, type = "transform"))|set(shapesL))

    if checkTopo: 
        result =  compareMeshTopologie(transformL, GUI = False, vrtxCnt = True, worldArea = True)
        if not result["resultB"]:
            logMessage = "#### {:>7}: 'convertObjToInstance' geometry missmach".format("Error")
            if GUI ==True: 
                print logMessage
                for each in result["logL"]:
                    print each
            resultB = False
            logL.append(logMessage)
            logL.extend(result["logL"])
            return dict(resultB=resultB, logL=logL, resultL= transformL)

    #check if input, is a transform list 
    noTransformL = list(set(transformL)-set(cmds.ls(transformL,type = "transform",l = True)))
    if noTransformL:
            logMessage = "#### {:>7}: 'convertObjToInstance' {} objects are not transform type : '{}'".format("Error", len(noTransformL), noTransformL)
            if GUI == True : raise ValueError (logMessage)
            resultB = False
            logL.append(logMessage)
    #exclude instances from the objects to process
    transMeshL, instanceTransformL = miscUtils.getAllTransfomMeshes("*",inType = "shape")
    alreadyInstanceL = list(set(transformL)&set(instanceTransformL))
    if alreadyInstanceL:
        allAlreadyInstanceL = cmds.listRelatives(cmds.listRelatives(alreadyInstanceL, children = True, fullPath = True, type = "mesh"), allParents = True, fullPath = True, type = "transform")
        logMessage = "#### {:>7}: 'convertObjToInstance' {} Inputs are instances already, appending other objects to them : {}".format("Info",len(allAlreadyInstanceL),allAlreadyInstanceL)
        if GUI == True : print logMessage
        logL.append(logMessage)
        transformL = list(set(transformL) | set(allAlreadyInstanceL))

    if len(transformL)<2:
        logMessage = "#### {:>7}: 'convertObjToInstance' nothing  to instanciate, at least 2 inputs needed".format("Info")
        if GUI == True : print logMessage
        logL.append(logMessage)
        return dict(resultB=resultB, logL=logL, resultL= transformL)


    masterS = transformL[0]
    masterShapeL = cmds.ls(cmds.listRelatives(masterS, noIntermediate = True, shapes = True, fullPath = True),l=True)
    if not masterShapeL:
        logMessage = "#### {:>7}: 'convertObjToInstance' No shape could be found under the master  : '{}'".format("Error", masterS)
        if GUI == True : raise ValueError (logMessage)
        resultB = False
        logL.append(logMessage)
        return dict(resultB=resultB, logL=logL, resultL= transformL)
    elif len(masterShapeL)>1:
        logMessage = "#### {:>7}: 'convertObjToInstance' {} shapes were found under the master  : '{}'".format("Error",len(masterShapeL), masterS)
        if GUI == True : raise ValueError (logMessage)
        resultB = False
        logL.append(logMessage)
        return dict(resultB=resultB, logL=logL, resultL= transformL)
    else:
        masterShapeS = masterShapeL[0]  

    transformL.remove(masterS)
    if legacy == True:
        for each in transformL:
            mtx = cmds.xform( each, q = True, ws = True, matrix = True )
            eachParent = each.split(each.split("|")[-1])[0].rstrip("|")
            resultInstance = cmds.instance( masterS , leaf=True)[0]
            cmds.delete(each)
            resultParentedInstance= cmds.parent(resultInstance, eachParent )[0]
            renamedInstance = cmds.rename(resultParentedInstance,each.split("|")[-1])
            cmds.xform( renamedInstance,  ws = True, matrix = mtx )
    else:
        for each in transformL:
            eachShapeL = cmds.ls(cmds.listRelatives(each, noIntermediate = True, shapes = True, fullPath = True),l=True)
            if len(eachShapeL)>1 or not eachShapeL:
                logMessage = "#### {:>7}: 'convertObjToInstance' {} shapes were found under the geometry  : '{}'".format("Error",len(eachShapeL), each)
                if GUI == True : raise ValueError (logMessage)
                resultB = False
                logL.append(logMessage)
                return dict(resultB=resultB, logL=logL, resultL= transformL)
            else:
                eachShapeS = eachShapeL[0]
            if len(cmds.listRelatives(eachShapeS,allParents =True))>1: #object is an instance already
                continue
            cmds.parent(masterShapeS, each, addObject = True, shape = True)
            cmds.delete(eachShapeS)



    logMessage = "#### {:>7}: 'convertObjToInstance' {} objects have been instanced. Master:'{}' <----> '{}'".format("Info",len(transformL)+1,masterS,transformL)
    if GUI == True : print logMessage
    logL.append(logMessage)
    if updateSetLayInstance: 
        setInstanceUpdate()
        layerUpdate()

    return dict(resultB=resultB, logL=logL, resultL= transformL+[masterS])


def convertInstanceToObj(transformL=[],GUI = True, updateSetLayInstance = True,inParent = "asset|grp_geo"):
    logL = []
    resultB = True
    initSelectionL = cmds.ls(selection=True)
    geoTransformL, instanceTransformL = miscUtils.getAllTransfomMeshes(inParent)

    shapesL = cmds.listRelatives(cmds.ls(transformL,l = True, type = "mesh"), parent =True, fullPath = True, type = "transform")
    if not shapesL:
        shapesL=[]
    transformL = list(set(cmds.ls(transformL,l = True, type = "transform"))|set(shapesL))

    transformL = list(set(transformL) & set(instanceTransformL))

    if transformL:
        cmds.select(transformL)
        pmr.ConvertInstanceToObject()

        if updateSetLayInstance: 
            setInstanceUpdate()
            layerUpdate()
        cmds.select(initSelectionL)
        logMessage = "#### {:>7}: 'convertInstanceToObj' {} instances converted to objects: '{}'".format("Info",len(transformL),transformL)
        if GUI == True : print logMessage
        logL.append(logMessage)
    else:
        logMessage = "#### {:>7}: 'convertInstanceToObj' no instances to convert".format("Info")
        if GUI == True : print logMessage
        logL.append(logMessage)

    return dict(resultB=resultB, logL=logL)


def convertBranchToLeafInstance(inParent ="asset|grp_geo", GUI = True, mode = "listOnly"):
    """
    mode = listOnly   : list the branch instances parents
    mode = instToObj  : branch instances are converted to object but the shapes are not re-instanced
    mode = convToLeaf : branch instances are converted to object, leaf are reinciated 
    """
    resultB = True
    logL=[]
    printedBranchL = []
    initSelection = cmds.ls(selection=True)
    allTransformL = cmds.listRelatives(inParent, allDescendents = True, fullPath = True, type = "transform")
    if mode == "instToObj" :
        logMessage = "#### {:>7}: 'convertBranchToLeafInstance' converting branches instances to objects".format("Info")
        logL.append(logMessage)
        if GUI == True: print logMessage
    elif mode == "listOnly":
        logMessage = "#### {:>7}: 'convertBranchToLeafInstance' listing the branches of instances (every dag is instance, not only leaf):".format("Info")
        logL.append(logMessage)
        if GUI == True: print logMessage

    #for each transform under de given "inParent"
    for each in allTransformL:
        parentL = cmds.listRelatives (each, allParents = True, fullPath = True, type = "transform")
        if len(parentL)>1:
            if len(cmds.listRelatives (parentL[0], allParents = True, fullPath = True, type = "transform"))>1:
                continue
            else:# parentL list a bunch of transform that are not instances but has children whitch are instances
                for eachBranch in parentL:  # convert each branch to objects
                    trans, inst = miscUtils.getAllTransfomMeshes(eachBranch)
                    if inst:
                        if mode == "instToObj" :
                            if parentL[0] not in printedBranchL:
                                printedBranchL.extend(parentL)
                                logMessage = "#### {:>7}: ----> {}".format("Info",parentL)
                                logL.append(logMessage)
                                if GUI == True: print logMessage
                            cmds.select(eachBranch, r= True)
                            pmr.ConvertInstanceToObject()

                        elif mode == "convToLeaf":
                            cmds.select(eachBranch, r= True)
                            pmr.ConvertInstanceToObject()

                        elif mode == "listOnly":
                            if parentL[0] not in printedBranchL:
                                printedBranchL.extend(parentL)
                                logMessage = "#### {:>7}: ----> {}".format("Info",parentL)
                                logL.append(logMessage)
                                if GUI == True: print logMessage

                if mode == "convToLeaf":
                    logMessage = "#### {:>7}: 'convertBranchToLeafInstance' converting branch instances to leaf instances {}".format("Info",parentL)
                    logL.append(logMessage)
                    if GUI == True: print logMessage
                    allTransMeshParent0, instanceTransformL = miscUtils.getAllTransfomMeshes(parentL[0])
                    allTransfAllParent = cmds.listRelatives (parentL, allDescendents = True, fullPath = True, type = "transform")
                    #for each of all the transform (above a mesh) of the main branch
                    for eachTMP in allTransMeshParent0: # ex: eachTMP  = |grp_geo|misterB|group4|pSphere1, parentL[0]= |grp_geo|misterB
                        #cmds.listRelatives(cmds.ls(eachTransMesh,type='mesh'),parent =True, fullPath = True, type = "transform")
                        toInstanciateL = []
                        patern =  eachTMP.replace(parentL[0]+"|","") #group4|pSphere1
                        for eachTransf in allTransfAllParent: 
                            if patern in eachTransf:
                                toInstanciateL.append(eachTransf)
                        result = convertObjToInstance(transformL=toInstanciateL, GUI = False, updateSetLayInstance = False)
                        if result["resultB"] == False:
                            logMessage = "#### {:>7}: 'convertBranchToLeafInstance' sub function 'convertObjToInstance() failed to instanciate: {}'".format("Error",toInstanciateL)
                            logL.append(logMessage)
                            if GUI == True : raise ValueError (logMessage)
                            resultB = False
    setInstanceUpdate()
    layerUpdate()
    cmds.select(initSelection, r= True)
    return dict(resultB=resultB, logL=logL)



def getRelatedInstance(transformL=[]):
    logL = []
    resultB = True
    resultL = []

    shapesL = cmds.listRelatives(cmds.ls(transformL,l = True, type = "mesh"), parent =True, fullPath = True, type = "transform")
    if not shapesL: shapesL=[]
    transformL = cmds.ls(transformL,l = True, type = "transform")+shapesL
    if not transformL: transformL=[]

    for each in transformL:
        relatedInstanceL = cmds.listRelatives(cmds.listRelatives(each,children = True, fullPath = True, type = "mesh"),allParents = True, fullPath = True, type = "transform")
        if len(relatedInstanceL)>1:
            resultL.extend(relatedInstanceL)

    return dict(resultB=resultB, logL=logL, resultL= resultL)


def layerUpdate(inParent="asset|grp_geo", GUI = True, displayMode = 0):
    """
    display mode:   '0' --> default values
                    '1' --> anim   mode, crtl: visib 'on'  select 'on' , geo: visib 'on' select 'off' 
                    '2' --> render mode, crtl: visib 'off' select 'off', geo: visib 'on' select 'on' 
    """

    resultB = True
    logL = []

    geoTransformL, instanceTransformL = miscUtils.getAllTransfomMeshes(inParent)
    setCtrl = cmds.ls('set_control')
    if setCtrl:
        crtlL = cmds.sets( setCtrl[0], q=True )
    else:
        crtlL=[]

    try:
        myInstanceLayerL = cmds.ls("instance")
        if myInstanceLayerL:
            cmds.delete(myInstanceLayerL)
        if instanceTransformL:
            myInstanceLayerS = cmds.createDisplayLayer(instanceTransformL, number=3, empty=False, noRecurse=False, name="instance")
            cmds.setAttr(myInstanceLayerS+".displayType",0)
            cmds.setAttr(myInstanceLayerS+".color",23)
            cmds.setAttr(myInstanceLayerS+".overrideColorRGB",0,0,0)
            cmds.setAttr(myInstanceLayerS+".overrideRGBColors",0)
            if displayMode == 1:
                cmds.setAttr("instance.displayType", 2)
                cmds.setAttr("instance.visibility", 1)
            elif displayMode == 2:
                cmds.setAttr("instance.displayType", 0)
                cmds.setAttr("instance.visibility", 1)

        myGeometryLayerL = cmds.ls("geometry")
        if myGeometryLayerL:
            cmds.delete(myGeometryLayerL)
        if geoTransformL:
            myGeometryLayerS = cmds.createDisplayLayer(geoTransformL,number=1, empty=False, noRecurse=False, name="geometry")
            if displayMode == 1:
                cmds.setAttr("geometry.displayType", 2)
                cmds.setAttr("geometry.visibility", 1)
            elif displayMode == 2:
                cmds.setAttr("geometry.displayType", 0)
                cmds.setAttr("geometry.visibility", 1)

        myControlLayerL = cmds.ls("control")
        if myControlLayerL:
            cmds.delete(myControlLayerL)
        if crtlL:
            myControlLayerS = cmds.createDisplayLayer(crtlL, number=2, empty=False, noRecurse=True, name="control")
            #cmds.setAttr("control.hideOnPlayback", 0)
            if displayMode == 1:
                cmds.setAttr("control.displayType", 0)
                cmds.setAttr("control.visibility", 1)
            elif displayMode == 2:
                cmds.setAttr("control.displayType", 0)
                cmds.setAttr("control.visibility", 0)

        logMessage = "#### {:>7}: 'layerUpdate' display layers updated ".format("Info")

    except Exception,err:
        resultB = False
        logMessage = "#### {:>7}: 'layerUpdate'  --> '{}'".format("Error", err)

    logL.append(logMessage)
    if GUI == True : print logMessage
    return dict(resultB=resultB, logL=logL)




def setInstanceUpdate(inParent="asset|grp_geo", delSetOnly = False, GUI = True):
    resultB = True
    logL = []
    deletedSetL = []

    setL = cmds.ls("set_instance*", type = "objectSet")
    for eachSet in setL:
        subsetL = cmds.ls(cmds.sets(eachSet, query = True), type = "objectSet")
        cmds.delete(subsetL)
        deletedSetL.extend(subsetL)
        if cmds.ls(eachSet):
            cmds.delete(eachSet)
            deletedSetL.append(eachSet)
    if deletedSetL and delSetOnly:
        logMessage = "#### {:>7}: 'setInstanceUpdate' {} 'set_instances' and sub sets deleted ".format("Info",len(deletedSetL))
        logL.append(logMessage)
        if GUI == True : print logMessage

    if delSetOnly == False:
        transMeshL, instanceTransformL = miscUtils.getAllTransfomMeshes(inParent)
        if not instanceTransformL:
            logMessage = "#### {:>7}: 'setInstanceUpdate' no instances found".format("Info")
            logL.append(logMessage)
            if GUI == True : print logMessage
            return dict(resultB=resultB, logL=logL)

        allInstancedShapeL = cmds.listRelatives(instanceTransformL, children = True, fullPath = True, type = "mesh")
        processedShapes = []
        subSetL = []
        for each in allInstancedShapeL:
            relatedInstanciedTransfL = cmds.listRelatives(each , allParents = True, fullPath = True, type = "transform")
            if relatedInstanciedTransfL[0] not in processedShapes:
                setNameS = "set_"+relatedInstanciedTransfL[0].split("|")[-1]
                setNameS = setNameS.replace('geo_','')
                subSetL.append(cmds.sets(relatedInstanciedTransfL, name=setNameS))
                processedShapes.extend(relatedInstanciedTransfL)
        setInstanceS = cmds.sets(subSetL, name="set_instance")
        logMessage = "#### {:>7}: 'setInstanceUpdate'  'set_instance' re-generated with {} sub sets".format("Info",len(subSetL))
        logL.append(logMessage)
        if GUI == True : print logMessage

    return dict(resultB=resultB, logL=logL)






def compareMeshTopologie(transformL = [], GUI = True, vrtxCnt = True, worldArea = True, verbose = False):
    resultB = True
    logL=[]
    vrtxCntMismatchL = []
    worldAreaMismatchL = []
    transformL = cmds.ls(transformL,l = True)

    if len(transformL)>1:
        masterMeshS = cmds.listRelatives(transformL[0], children = True, fullPath = True, type = "mesh")[0]
        if not masterMeshS:
            logMessage = "#### {:>7}: 'compareMeshTopologie' can't compare topology, no mesh shape found under {}'".format("Info",transformL[0])
            logL.append(logMessage)
            if GUI == True : print logMessage
            return dict(resultB=resultB, logL=logL)
    else:
        logMessage = "#### {:>7}: 'compareMeshTopologie' no transform to compare topology'".format("Info")
        logL.append(logMessage)
        if GUI == True : print logMessage
        return dict(resultB=resultB, logL=logL)

    masterMeshVrtxCnt = len(cmds.getAttr(masterMeshS+".vrts[:]"))
    masterWorldArea =  cmds.polyEvaluate(masterMeshS, worldArea= True)
    transformL.remove(transformL[0])

    for eachTransf in transformL:
        vrtxCntMatch = True
        eachMesh = cmds.listRelatives(eachTransf, children = True, fullPath = True, type = "mesh")[0]
        if not eachMesh:
            logMessage = "#### {:>7}: 'compareMeshTopologie' can't compare topology, no mesh shape found under {}'".format("Error",eachTransf)
            logL.append(logMessage)
            resultB = False
            if GUI == True : print logMessage
            return dict(resultB=resultB, logL=logL)
        if vrtxCnt == True:
            eachMeshVrtxCnt = len(cmds.getAttr(eachMesh+".vrts[:]"))
            if masterMeshVrtxCnt != eachMeshVrtxCnt:
                vrtxCntMismatchL.append(eachMesh)
                resultB = False
                vrtxCntMatch = False
                if verbose == True:
                    logMessage = "#### {:>7}: 'compareMeshTopologie' Vertex number mismatch: '{}' vertex nb = {} -- '{}' vertex nb = {}".format("Error",masterMeshS,masterMeshVrtxCnt, eachMesh,eachMeshVrtxCnt)
                    logL.append(logMessage)
                    if GUI == True : print logMessage
        if worldArea == True and vrtxCntMatch:
            areaTolF = 0.01 #percentage world area tolerance
            eachWorldArea =  cmds.polyEvaluate(eachMesh, worldArea= True)
            areaDifF = abs(float(masterWorldArea - eachWorldArea)/masterWorldArea *100)
            if areaDifF > areaTolF:
                worldAreaMismatchL.append(eachMesh)
                resultB = False
            if verbose == True:
                logMessage = "#### {:>7}: 'compareMeshTopologie' World area is {:.3f} percent different: '{}' -- '{}'".format("Error",areaDifF, masterWorldArea, eachWorldArea)
                logL.append(logMessage)
                if GUI == True : print logMessage

    mismatchL = list(set(worldAreaMismatchL) | set(vrtxCntMismatchL))
    if not mismatchL:
        logMessage = "#### {:>7}: 'compareMeshTopologie' meshes tolopogies match".format("Info")
        logL.append(logMessage)
        if GUI == True : print logMessage
    else:
        logMessage = "#### {:>7}: 'compareMeshTopologie' meshes tolopogies mismatch: {} != {}".format("Error",cmds.ls(masterMeshS),cmds.ls(mismatchL))
        logL.append(logMessage)


    return dict(resultB=resultB, logL=logL)


def groupEachMesh():

    selL = cmds.ls(selection= True, l=1)
    if not selL: return
    newSelL = []

    geoL, insL = miscUtils.getAllTransfomMeshes(inParent = selL, inType = "mesh", recursive = True)
    geoL.extend(insL)
    geoL = cmds.ls(geoL, l=1)

    trsL = list(set(selL)&set(geoL))

    for each in trsL:
        stripedNameS = each.split("|")[-1].replace("geo_","")
        grpNameS = each.replace(each.split("|")[-1],"grp_"+stripedNameS)
        grpShortNameS = grpNameS.split("|")[-1]
        grpParentNameS = each.replace("|"+each.split("|")[-1],"")
        print "---"
        print "grpNameS: ", grpNameS
        print "grpShortNameS: ",grpShortNameS
        print "grpParentNameS: ",grpParentNameS
       
        mtx = cmds.xform( each, q = True, ws = True, matrix = True )
        cmds.makeIdentity (each ,apply= False, n=0, pn=1)

        createdGrp = cmds.group( each, name = grpShortNameS, parent = grpParentNameS)

        newEachNameS = createdGrp+"|"+each.split("|")[-1]
        print "newEachNameS: ",newEachNameS
        cmds.makeIdentity ( newEachNameS,apply= False, n=0, pn=1)
        cmds.makeIdentity ( newEachNameS,apply= True, n=0, pn=1)
        newSelL.append(newEachNameS)
        cmds.xform( createdGrp,  ws = True, matrix = mtx )
        print "#### {:>7}: 'groupEachMesh' '{}' transforms grouped under their own group".format("Info",len(newSelL))

    if newSelL: cmds.select(newSelL)

def assGeoExport(objectL=[], gui=True):
    log = miscUtils.LogBuilder(gui=gui, funcName ="assGeoExport")
    initSelL=cmds.ls(selection=True, l=True)
    mainFilePath = cmds.file(q=True, list = True)[0]
    mainFile = mainFilePath.split("/")[-1]
    geometryDir = miscUtils.pathJoin(mainFilePath.replace("/"+mainFile,""),"geometry")
    if not os.path.isdir(geometryDir):
        txt= "directory doesn't exist: "+geometryDir
        log.printL("e", txt, guiPopUp = True)
        raise valueError (txt)             

    
    for each in objectL:
        standInRad = each.split("|")[-1].replace("geo_","").replace("aux_","")
        fileName = miscUtils.pathJoin(geometryDir,standInRad+".ass")
        txt= "exporting: "+fileName
        log.printL("i", txt)
        cmds.select(each)                        
        #cmds.file( fileName, exportSelected = True, type= "ASS Export",force=True, options= "-mask 249;-lightLinks 0;-shadowLinks 0")

        eachParent = each.replace("|"+each.split("|")[-1],"")
        print eachParent
        eachStandIn = eachParent+"|std_"+standInRad
        if not(cmds.ls(eachStandIn)):
            print "non"



# -------------------------- RIG SUPPLEMENT -------------------------------------------------------------------
def createPropsControlRecur(inGrp, inRoot, b_inRecursive=True):
    # print"createPropsControlRecur()"
    createdObjs = ([], [],[])
    
    ctrlName = inGrp.name().replace("grp_", "ctrl_")
    icon = None

    isRootControl = False
    
    if inGrp.name() in SPECNAMES:
        if inGrp.name() == 'grp_geo':
            isRootControl = True

        ctrlName = SPECNAMES[inGrp.name()]
        icon = tkc.createCubeIcon(ctrlName, size=CTRLS_SIZE, scale=(3, 0.001, 3))
        tkc.setObjectColor(icon, [255, 255, 0, 0])
    else:
        icon = tkc.createRingsIcon(ctrlName, size=CTRLS_SIZE)
        tkc.setObjectColor(icon, [255, 128, 255, 0])
    
    pc.parent(icon, inRoot)
    tkc.matchTRS(icon, inGrp)
    tkc.setNeutralPose(icon)

    # create DEF child of ctr
    cmds.select(d=True)
    defo = cmds.joint(n="DEF_"+inGrp,)
    cmds.setAttr(defo + ".radius", 1)

    #connect vis
    if not cmds.objExists( "grp_rig.SHOW_DEF"): 
        cmds.addAttr("grp_rig", longName="SHOW_DEF", attributeType = "long",keyable=1,
                                     min = 0,max=1) 
        cmds.setAttr("grp_rig.SHOW_DEF",0)
    cmds.connectAttr("grp_rig.SHOW_DEF",defo+".v",f=1)
    # parent
    print inGrp,">",defo
    cmds.parent(defo,icon.name())
    # match position
    jpm.matchByXformMatrix(cursel=[icon.name(),defo], mode=0)



    if isRootControl:
        global_srt = tkc.createCubeIcon(SPECNAMES['global_srt'], size=CTRLS_SIZE, scale=(4, 0.001, 4))
        tkc.setObjectColor(global_srt, [255, 255, 0, 0])
        pc.parent(global_srt, inRoot)
        tkc.matchTRS(global_srt, inGrp)
        tkc.setNeutralPose(global_srt)
        tkc.parent(icon, global_srt)
        createdObjs[0].append(global_srt)

        big_daddy = tkc.createCubeIcon(SPECNAMES['big_daddy'], size=CTRLS_SIZE, scale=(5, 0.001, 5))
        tkc.setObjectColor(big_daddy, [255, 255, 0, 0])
        #connect vis
        if not cmds.objExists( "grp_rig.SHOW_BIGDADDY"): 
            cmds.addAttr("grp_rig", longName="SHOW_BIGDADDY", attributeType = "long",keyable=1,
                                         min = 0,max=1) 
            cmds.setAttr("grp_rig.SHOW_BIGDADDY",0)
        big_daddyShape = big_daddy.getShape()
        cmds.connectAttr("grp_rig.SHOW_BIGDADDY",big_daddyShape+".v",f=1)

        # pc.setAttr('{0}.visibility'.format(big_daddy.getShape().name()), False)
        pc.parent(big_daddy, inRoot)
        tkc.matchTRS(big_daddy, inGrp)
        tkc.setNeutralPose(big_daddy)
        tkc.parent(global_srt, big_daddy)
        createdObjs[0].append(big_daddy)

    createdObjs[0].append(icon)
    
    if b_inRecursive:
        children = tkc.getChildren(inGrp, False)
        grpsChildren = []
        for child in children:
            shape = child.getShape()
            if child.name()[:4] == "grp_" and shape == None:
                grpsChildren.append(child) 
            elif shape !=None and shape.type() == "mesh":
                createdObjs[1].append(child)
                # Skin the children geos
                print "skin",child.name()
                cmds.skinCluster( defo,child.name(), bindMethod=1, maximumInfluences=1, )
            else:
                pc.warning('Unmanaged object {}'.format(child.name()))

        for grpChild in grpsChildren:
            subCreatedObjs = createPropsControlRecur(grpChild, icon)
            createdObjs[0].extend(subCreatedObjs[0])
            createdObjs[1].extend(subCreatedObjs[1])
            createdObjs[2].extend(subCreatedObjs[2])



    return createdObjs


def rigProps(inRoot):
    children = tkc.getChildren(inRoot, False)
    
    valid = True
    
    if not "grp_geo" in [a.name() for a in children]:
        pc.warning("Root is supposed to have at least one 'grp_geo' child !")
        valid=False

    for child in children:
        if child.name() != "grp_geo" and child.name() != "grp_placeHolders" and child.name() != "grp_rig":
            pc.warning("Unexpected asset root child {0} (expected 'grp_geo', and eventually 'grp_placeHolders' or 'grp_rig')".format( child.name() ) )
            valid=False

    if not valid:
        return None
    
    cleanSet(inRoot)
    
    grp_rig = pc.group(name="grp_rig", empty=True, parent=inRoot)
    
    # -----------------------------------------------------------------
    ctrls, geos,cstL = createPropsControlRecur(children[0], grp_rig)  # ////////////////////////////////////// convert to jipe_control_skined here it's csts
    print "ctrls=", len(ctrls),ctrls
    print "geos=", len(geos),geos
    print "cstL=", len(cstL),  cstL
    #-------------------------------------------------------------------------------

    #-------------------------------------------------------------------------------
    #We can try to reApply displays if saved
    if pc.attributeQuery(DISPLAYS_CACHE_ATTRNAME, node=inRoot, exists=True):
        try:
            displaysDict = eval(pc.getAttr(inRoot.name() + "." + DISPLAYS_CACHE_ATTRNAME))
            for ctrl in ctrls:
                if ctrl.name() in displaysDict:
                    display, color = displaysDict[ctrl.name()]
                    tkc.setDisplay(ctrl, trs=display[0], size=display[1], select=False, displayName=display[2])
                    realColor = tkc.getColorFromMayaColor(color)
                    tkc.setObjectColor(ctrl, realColor)
        except:
            pc.warning('Cannot reapply displays !')

    #Put all controls in a set
    if pc.objExists(CTRL_SETNAME):
        pc.delete(CTRL_SETNAME)

    pc.sets(ctrls, name=CTRL_SETNAME)

    #Put all geo in a set for caching /////////////////////// change to geometry only finding
    if pc.objExists(CACHE_SETNAME):
        pc.delete(CACHE_SETNAME)

    pc.sets(geos, name=CACHE_SETNAME)

    #Clean old layers ////////////////////////////////////////// mauvais moyen de cleaner les layer
    oldLayers = pc.ls("layer_*", type="displayLayer")
    if len(oldLayers) > 0:
        pc.delete(oldLayers)

    #Put all geometries in a layer, and set it to "reference"
    if pc.objExists(GEOMETRIES_LAYERNAME):
        pc.delete(GEOMETRIES_LAYERNAME)

    pc.select(geos)
    newLayer = pc.createDisplayLayer(name=GEOMETRIES_LAYERNAME) #///////// crado use of pc.select()
    pc.setAttr(newLayer + ".displayType", 2)

    #Put all controls in a layer
    if pc.objExists(CTRLS_LAYERNAME):
        pc.delete(CTRLS_LAYERNAME)

    pc.select(ctrls)
    newLayer = pc.createDisplayLayer(name=CTRLS_LAYERNAME, noRecurse=True) #///////// crado use of pc.select()

    pc.select(clear=True)



