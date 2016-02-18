import pymel.core as pc
import tkMayaCore as tkc
import pymel.core.datatypes as dt
import pymel.core.runtime as pmr

import maya.cmds as cmds

import re
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
        if child.name() != "grp_geo" and child.name() != "grp_placeHolders" and child.name() != "grp_rig":
            pc.warning("Unexpected asset root child {0} (expected 'grp_geo', and eventually 'grp_placeHolders' or 'grp_rig')".format(child.name()))
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




def getMeshesWithSameName(inVerbose = True, inParent = "*"):
    """
    list all the meshes that share the same short name, under de given 'inParent', 
    by default '*' means that any unreferenced mesh in the scene is taken into account
        - inVerbose (boolean) : print the 'multipleMesh' list
        - inParent (string) : long name of the parent 
        - return (list) : multipleMesh
    """

    allTransMesh, instanceTransformL = miscUtils.getAllTransfomMeshes(inParent)
    allTransMesh.extend(instanceTransformL)
    multipleMesh = []

    for eachTrasnMesh in allTransMesh:
        if len(cmds.ls(cmds.listRelatives(eachTrasnMesh, allDescendents = True, fullPath = True, type = "mesh"), noIntermediate = True)) > 1:
            raise ValueError("#### {:>7}:'getMeshesWithSameName': {} has multiple shapes, please clean this mesh and run the script again".format("Error",eachTrasnMesh))
        shortName = eachTrasnMesh.split("|")[-1]
        if str(allTransMesh).count(shortName+"'") > 1:
            multipleMesh.append(eachTrasnMesh)
    if multipleMesh:
        if inVerbose is True:
            print "#### warning: 'getMeshesWithSameName': somes meshes have the same short name: "
            for each in multipleMesh:
                    print "#### warning: 'getMeshesWithSameName': "+each
        return multipleMesh
    else:
        if inVerbose is True:
            print "#### info: 'getMeshesWithSameName': no multiple short names found in '"+str(inParent)+"'"
        return None 


def renameMeshAsUnique(myMesh, inParent = "*", GUI = True):
    """
    Makes the given mesh name unique by adding a digit and/or incrementing it till the short name is unique in the scene. 
    Only meshes of the main name space are taken into account, referenced meshes are therefore ignored.
    myMesh  (string) : the long name of a mesh (a transform parent of a mesh shape) that has to be renamed to have a unique short name in the scene

    """
    allTransMesh, instanceTransformL = miscUtils.getAllTransfomMeshes(inParent)

    shortName = myMesh.split("|")[-1]
    digit = re.findall('([0-9]+$)', myMesh)
    if digit:
        digit = digit[0]
        newShortName = string.rstrip(shortName,digit)
        newDigit = string.zfill(str(int(digit)+1), len(digit))
        i = 1
        while str(allTransMesh).count(newShortName+newDigit) > 0:
            newDigit = string.zfill(str(int(digit)+i), len(digit))
            i = i+1
            if i>300:
                print "#### {:>7}: 'renameMeshAsUnique' while loop has reached the security limit, program has been stopped".format("Error")
                break
        cmds.rename(myMesh,newShortName+newDigit)
        if GUI == True: print "#### info: 'renameMeshAsUnique' rename "+myMesh+"  -->  "+string.rstrip(myMesh,digit)+newDigit
        if myMesh in allTransMesh: meshShapeNameConform(fixShapeName = True, myTransMesh = [string.rstrip(myMesh,digit)+newDigit], forceInfoOff = True )
        
    else:
        digit = "1"
        i = 1
        while str(allTransMesh).count(shortName+digit) > 0:
            digit = str(int(digit)+1)
            i = i+1
            if i>300:
                print "#### {:>7}: 'renameMeshAsUnique' while loop has reached the security limit, program has been stopped".format("Error")
                break
        myMeshNew = [cmds.rename(myMesh,shortName+digit)]
        if GUI == True: print "#### info: 'renameMeshAsUnique' rename "+myMesh+"  -->  "+myMesh+digit
        if myMesh in allTransMesh: meshShapeNameConform(fixShapeName = True, myTransMesh = myMeshNew, forceInfoOff = True)

                        
def makeAllMeshesUnique(inParent = "*", GUI = True):
    """
    makes all the meshes short names unique by adding a digit and/or incrementing it till the short name is unique in the scene
    then makes sure the shapes names are corrects
    """
    resultB = True
    logL = []

    allTransMesh, instanceTransformL = miscUtils.getAllTransfomMeshes(inParent)
    if instanceTransformL:
        logMessage = "#### {:>7}: 'makeAllMeshesUnique' {} objects are actually instances: {}".format("Warning", len(instanceTransformL), instanceTransformL)
        logL.append(logMessage)
        if GUI == True: print logMessage

    multipleMesh = getMeshesWithSameName(inVerbose = False,inParent = inParent)
    if multipleMesh :
        i=0
        while multipleMesh:
            renameMeshAsUnique(multipleMesh[0], inParent, GUI= False)
            multipleMesh = getMeshesWithSameName(inVerbose = False,inParent = inParent)
            i = i+1
            if i>300:
                print "#### {:>7}: 'makeAllMeshesUnique' while loop has reached the security limit, program has been stopped: {}".format("Error", multipleMesh)
                break
    else:
        if inParent == "*":
            logMessage =  "#### {:>7}: 'makeAllMeshesUnique' no multiple mesh found, all meshes have unique short name".format("Info")
            logL.append(logMessage)
            if GUI == True: print logMessage
        else :
            logMessage = "#### {:>7}: 'makeAllMeshesUnique' no multiple mesh found under '{}' all meshes have unique short name ".format("Info",inParent)
            logL.append(logMessage)
            if GUI == True: print logMessage

    return resultB, logL





def geoGroupDeleteHistory(GUI=True, freezeVrtxPos = True):
    """
    gets all the mesh transformms under the '|asset|grp_geo', delete their history and delete any intermediate unconnected shape 
    """
    resultB = True
    logL = []
    geoTransformList,instanceTransformL = miscUtils.getAllTransfomMeshes(inParent = "|asset|grp_geo")
    if instanceTransformL:
        logMessage = "#### {:>7}: 'geoGroupDeleteHistory': {} objects are actually instances: {}".format("Warning", len(instanceTransformL), instanceTransformL)
        logL.append(logMessage)
        if GUI == True: print logMessage
        geoTransformList = geoTransformList+ instanceTransformL

    if freezeVrtxPos:
        for each in geoTransformList:
            cmds.polyMoveVertex (each,constructionHistory =True, random  = 0)
        logMessage = "#### {:>7}: 'geoGroupDeleteHistory': vertex position freezed on {} geometries".format("Info", len(geoTransformList))
        logL.append(logMessage)
        if GUI == True: print logMessage
        cmds.select(cl=True)

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
    return resultB, logL





def freezeResetTransforms(inParent = "*", inVerbose = True, inConform = False, GUI = True):
    """
    gets all the mesh transforms under de given inParent, an check that all the transforms values are set to 0 (1 for scales)
    logs infos in case inVerbose is true, freeze and reset the the transforms in case inConform is True.
    """
    resultB = True
    logL = []
    if GUI == True: print "#### {:>7}: modeling.freezeResetTransforms(inParent = {}, inVerbose = {}, inConform = {})".format("Info",inParent, inVerbose, inConform)
    unFreezedTransfomList = []
    freezedTransfomList = []
    geoTransformList,instanceTransformL = miscUtils.getAllTransfomMeshes(inParent)
    if instanceTransformL:
        logMessage = "#### {:>7}: 'freezeResetTransforms': {} objects ignored since they are actually instances: {}".format("Warning", len(instanceTransformL), instanceTransformL)
        logL.append(logMessage)
        if GUI == True: print logMessage

    for each in geoTransformList:
        if (cmds.xform( each, os=True, q=True,  ro=True)!=[0,0,0] or cmds.xform( each, os=True, q=True,  t=True)!=[0,0,0] or cmds.xform( each, os=True, q=True,  s=True, r = True )!=[1,1,1] or 
            cmds.xform( each, os=True, q=True, rp=True)!=[0,0,0] or cmds.xform( each, os=True, q=True, sp=True)!=[0,0,0]):
            if inVerbose == True and inConform == False:
                unFreezedTransfomList.append(each)
                if GUI == True: print "#### {:>7}: {:^28} --> has unfreezed tranform values".format("Info", each)
            if inConform == True:
                cmds.makeIdentity (each ,apply= True, n=0, pn=1)
                cmds.makeIdentity (each ,apply= False, n=0, pn=1)
                freezedTransfomList.append(each)
                if inVerbose == True: print "#### {:>7}: {:^28} --> has been freezed and reset".format("Info", each)

    if unFreezedTransfomList !=[] and inVerbose == True:
        cmds.select(unFreezedTransfomList)
        logMessage = "#### {:>7}: {} unfreezed transforms have been selected".format("Info", str(len(unFreezedTransfomList)))
        logL.append(logMessage)
        if GUI == True: print logMessage

    if freezedTransfomList != []:
        logMessage = "#### {:>7}: {} transforms have been freezed and reset".format("Info", len(freezedTransfomList))
        logL.append(logMessage)
        if GUI == True: print logMessage

    if unFreezedTransfomList ==[] and inVerbose == True:
        logMessage = "#### {:>7}: {} transforms checked successfully".format("Info", str(len(geoTransformList)))
        logL.append(logMessage)
        if GUI == True: print logMessage

    return resultB, logL

def compareHDToPreviz():
    """
    This script has been made at dreamwall, to compare previz and master modeling structure you must import the previz file as a reference, 
    the asset node should have this kind of name: "nameSpace:asset_previz". then select the previz asset transform and the master asst transform, 
    run the script and read the log
    """

    DECIMAL_NB = 3
    BOX_SCALE = 0.1 # 10%
    listWarning=[]

    def bboxPrintWarning(listWarning):
        print("\n*** Bbox warning if more than " + str(1./BOX_SCALE) + " % different between Hi and Previz ***")
        for warning in listWarning:
            print("\tWARNING: "+warning)

    def compareMinMaxHiToPreviz(hiMin, hiMax, previzMin, previzMax, boxScale):
        ##print("hiMin = " + str(hiMin) + " hiMax = " + str(hiMax) + " previzMin = " + str(previzMin) + " previzMax = " + str(previzMax) + " boxScale = " + str(boxScale))
        errMin = False
        errMax = False
        center = (previzMin + previzMax) / 2.
        delta = math.fabs(previzMax-previzMin)
        deltaHalf = delta / 2.
        if math.fabs(hiMin-previzMin) > delta*boxScale:
            errMin = True
        if math.fabs(hiMax-previzMax) > delta*boxScale:
            errMax = True
        return errMin, errMax

    def compareBboxHiToPreviz(groupHi, groupPreviz, boxScale, listWarning): # ex. boxScale = 0.1 (10%)
        hiBbox = cmds.exactWorldBoundingBox(groupHi)
        ##print("\tbbox hi = %f" % hiBbox[0], "%f" % hiBbox[1], "%f" % hiBbox[2], "%f" % hiBbox[3], "%f" % hiBbox[4], "%f" % hiBbox[5])
        previzBbox = cmds.exactWorldBoundingBox(groupPreviz)
        ##print("\tbbox previz = %f" % previzBbox[0], "%f" % previzBbox[1], "%f" % previzBbox[2], "%f" % previzBbox[3], "%f" % previzBbox[4], "%f" % previzBbox[5])

        errMin, errMax = compareMinMaxHiToPreviz(hiBbox[0], hiBbox[3], previzBbox[0], previzBbox[3], boxScale)
        if errMin:
            listWarning.append(str(groupHi) + " bbox xmin = " + str(floatLimitDecimal(hiBbox[0],2)) + " instead previz = " + str(floatLimitDecimal(previzBbox[0],2)))
        if errMax:
            listWarning.append(str(groupHi) + " bbox xmin = " + str(floatLimitDecimal(hiBbox[3],2)) + " instead previz = " + str(floatLimitDecimal(previzBbox[3],2)))

        errMin, errMax = compareMinMaxHiToPreviz(hiBbox[1], hiBbox[4], previzBbox[1], previzBbox[4], boxScale)
        if errMin:
            listWarning.append(str(groupHi) + " bbox xmin = " + str(floatLimitDecimal(hiBbox[1],2)) + " instead previz = " + str(floatLimitDecimal(previzBbox[1],2)))
        if errMax:
            listWarning.append(str(groupHi) + " bbox xmin = " + str(floatLimitDecimal(hiBbox[4],2)) + " instead previz = " + str(floatLimitDecimal(previzBbox[4],2)))
            
        errMin, errMax = compareMinMaxHiToPreviz(hiBbox[2], hiBbox[5], previzBbox[2], previzBbox[5], boxScale)
        if errMin:
            listWarning.append(str(groupHi) + " bbox xmin = " + str(floatLimitDecimal(hiBbox[2],2)) + " instead previz = " + str(floatLimitDecimal(previzBbox[2],2)))
        if errMax:
            listWarning.append(str(groupHi) + " bbox xmin = " + str(floatLimitDecimal(hiBbox[5],2)) + " instead previz = " + str(floatLimitDecimal(previzBbox[5],2)))
            

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

    ## previz is the ref, hi could have more group but not less, and check localspace pivot translate et scale MUST be 0 !

    namespacePreviz = ""
    errorCount = 0;
    sel = cmds.ls(sl=True, type='transform') # get the transform(s) selecte
    print sel
    if len(sel) == 2: # test if current selection has 2 nodes
        assetPreviz = sel[1]
        assetHi = sel[0]
        if "previz" in sel[0]:
            assetPreviz = sel[0]
            assetHi = sel[1]
             
        if "previz:" in assetPreviz:
            namespacePreviz = assetPreviz.split(":")[0] + ":" # get namespace

        print("\n***** comparing translations and rotations value from " + assetHi + " to reference " + assetPreviz)
        groupsPreviz = cmds.listRelatives(assetPreviz, ad=True, f=True,type='transform') # get all transforms with ful path
        #print ("* " + str(groupsPreviz))
        for groupPreviz in groupsPreviz:
            #print (groupPreviz + " " + groupPreviz.split("|")[-1])
             
            if is_group(groupPreviz) and "grp_" in groupPreviz.split("|")[-1] and not "grp_geo_" in groupPreviz.split("|")[-1]: # if the transform is a group
                ##print("\tgroupPreviz = " + str(groupPreviz))
                # get positions, rotations of locator
                rotPreviz = vectorLimitDecimal(cmds.xform(groupPreviz,q=True,ws=1,ro=1), DECIMAL_NB) #get rotations
                posPreviz = vectorLimitDecimal(cmds.xform(groupPreviz,q=True,ws=1,t=1), DECIMAL_NB) # gettranslations
                #print rotPreviz
                #print posPreviz
                groupHi=""
                if namespacePreviz != "": # if namespace, remove it to build groupHi
                    groupHi = groupPreviz.replace(assetPreviz, assetHi).replace(namespacePreviz, "") #build groupPreviz name 
                else:
                    groupHi = groupPreviz.replace(assetPreviz, assetHi) #build groupPreviz name
                #print("\tgroupHi = " + groupHi)
                if cmds.objExists(groupHi): # test if group exists ?
                    rotHi = vectorLimitDecimal(cmds.xform(groupHi,q=True,ws=1,ro=1), DECIMAL_NB) # get rotations
                    posHi = vectorLimitDecimal(cmds.xform(groupHi,q=True,ws=1,t=1), DECIMAL_NB) # get translations
                    error = False
                    if cmp(rotHi, rotPreviz):
                        print("\tERROR in group: " + groupHi + " has different rotate values: " + str(rotHi) + " instead of previz : " +str(rotPreviz))
                        error = True
                        errorCount += 1
                    if cmp(posHi, posPreviz):
                        print("\tERROR in group: " + groupHi + " has different translation values: " + str(posHi) + " instead of previz : "+ str(posPreviz))
                        error = True
                        errorCount += 1
                    # test local pivot rotate and scale
                    localPivotRotateHi =cmds.xform(groupHi,q=True,os=1,rp=1) # get local rotate pivot
                    localPivotScaleHi =cmds.xform(groupHi,q=True,os=1,sp=1) # get local scale pivot
                    if cmp(localPivotRotateHi, [0,0,0]):
                        print("\tERROR in group: " + groupHi + " has local pivot rotate values: " + str(localPivotRotateHi))
                        error = True
                        errorCount += 1
                    if cmp(localPivotScaleHi, [0,0,0]):
                        print("\tERROR in group: " + groupHi + " has local pivot scale values: " + str(localPivotScaleHi))
                        error = True
                        errorCount += 1

                    compareBboxHiToPreviz(groupHi, groupPreviz, BOX_SCALE, listWarning)
                     
                else:
                    print("\tERROR: group: " + groupHi + " is missing")

        bboxPrintWarning(listWarning) # print list warning for bbox.

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
                        newGroupName = cmds.group(mergedObjectName, name= groupName)
                    else:
                        newGroupName = cmds.group(mergedObjectName, name= groupName, parent = parentName)
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
    #mc.listRelatives(mc.ls("geo_femmeFatyVisiteurA*",type='mesh'),parent =True, fullPath = True, type = "transform")
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
        layInstanceUpdate()

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
            layInstanceUpdate()
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
    layInstanceUpdate()
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


def layInstanceUpdate(inParent="asset|grp_geo", GUI = True):
    resultB = True
    logL = []

    geoTransformL, instanceTransformL = miscUtils.getAllTransfomMeshes(inParent)

    myInstanceLayerL = cmds.ls("instance")
    if myInstanceLayerL:
        cmds.delete(myInstanceLayerL)
    if instanceTransformL:
        myInstanceLayerS = cmds.createDisplayLayer(instanceTransformL, empty=False, noRecurse=False, name="instance")
        cmds.setAttr(myInstanceLayerS+".displayType",0)
        cmds.setAttr(myInstanceLayerS+".color",23)
        cmds.setAttr(myInstanceLayerS+".overrideColorRGB",0,0,0)
        cmds.setAttr(myInstanceLayerS+".overrideRGBColors",0)

    myGeometryLayerL = cmds.ls("geometry")
    if myGeometryLayerL:
        cmds.delete(myGeometryLayerL)
    if geoTransformL:
        myGeometryLayerS = cmds.createDisplayLayer(geoTransformL, empty=False, noRecurse=False, name="geometry")

    logMessage = "#### {:>7}: 'layInstanceUpdate' 'geometry' and 'instance' display layers updated ".format("Info")
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



