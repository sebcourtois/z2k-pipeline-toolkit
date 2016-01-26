import pymel.core as pc
import tkMayaCore as tkc
import pymel.core.datatypes as dt

import maya.cmds as cmds

import re
import string
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
    

def meshShapeNameConform(fixShapeName = True, myTransMesh = [], forceInfoOff = False, inParent = "*"):
    """
    This function, makes sure every mesh shape name is concistant with its transform name: "transformName+Shape"
    Only shapes of the main name space are taken into account, referenced shapes are therefore ignored
        - fixShapeName (boolean): fix invalid shapes names if True, only log info otherwise
        - return (list): the meshes list that still have an invalid shape name
    """

    if not myTransMesh:
        myTransMesh, instanceTransformL = miscUtils.getAllTransfomMeshes(inParent)

        if instanceTransformL:
            print "#### {:>7}: 'meshShapeNameConform': {} objects ignored since they are actually instances: {}".format("Warning", len(instanceTransformL), instanceTransformL)

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
            if forceInfoOff is False: print "#### info: 'meshShapeNameConform': rename '"+myShape.split("|")[-1]+"' --> as --> '"+myShapeCorrectName.split("|")[-1]+"'"
            cmds.rename(myShape,each.split("|")[-1]+"Shape")
            renamedNumber = renamedNumber +1
        elif myShape != myShapeCorrectName and fixShapeName == False:
            print "#### warning: 'meshShapeNameConform': '"+each+"' has a wrong shape name: '"+myShape.split("|")[-1]+"' --> should be renamed as: --> '"+myShapeCorrectName.split("|")[-1]+"'"
            shapesToFix.append(each)
    if renamedNumber != 0:
        if forceInfoOff is False: print "#### {:>7}:'meshShapeNameConform': {} shape(s) fixed".format("Info",renamedNumber)    
        return None
    elif shapesToFix: 
        if forceInfoOff is False: print "#### {:>7}:'meshShapeNameConform': {} shape(s) to be fixed".format("Info",shapesToFix)
        return shapesToFix
    elif checkAllScene == True:
        if forceInfoOff is False: print "#### {:>7}:'meshShapeNameConform': all meshes shapes names are correct".format("Info",shapesToFix)
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


def renameMeshAsUnique(myMesh, inParent = "*"):
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
            if i>20:
                print "#### {:>7}:'renameMeshAsUnique' while loop has reached the security limit, program has been stopped".format("Error")
                break
        cmds.rename(myMesh,newShortName+newDigit)
        print "#### info: 'renameMeshAsUnique' rename "+myMesh+"  -->  "+string.rstrip(myMesh,digit)+newDigit
        if myMesh in allTransMesh: meshShapeNameConform(fixShapeName = True, myTransMesh = [string.rstrip(myMesh,digit)+newDigit], forceInfoOff = True )
        
    else:
        digit = "1"
        i = 1
        while str(allTransMesh).count(shortName+digit) > 0:
            digit = str(int(digit)+1)
            i = i+1
            if i>20:
                print "#### {:>7}:'renameMeshAsUnique' while loop has reached the security limit, program has been stopped".format("Error")
                break
        myMeshNew = [cmds.rename(myMesh,shortName+digit)]
        print "#### info: 'renameMeshAsUnique' rename "+myMesh+"  -->  "+myMesh+digit
        if myMesh in allTransMesh: meshShapeNameConform(fixShapeName = True, myTransMesh = myMeshNew, forceInfoOff = True)

                        
def makeAllMeshesUnique(inParent = "*"):
    """
    makes all the meshes short names unique by adding a digit and/or incrementing it till the short name is unique in the scene
    then makes sure the shapes names are corrects
    """

    allTransMesh, instanceTransformL = miscUtils.getAllTransfomMeshes(inParent)
    if instanceTransformL:
        print "#### {:>7}:'makeAllMeshesUnique' {} objects are actually instances: {}".format("Warning", len(instanceTransformL), instanceTransformL)


    multipleMesh = getMeshesWithSameName(inVerbose = False,inParent = inParent)
    if multipleMesh :
        i=0
        while multipleMesh:
            renameMeshAsUnique(multipleMesh[0], inParent)
            multipleMesh = getMeshesWithSameName(inVerbose = False,inParent = inParent)
            i = i+1
            if i>20:
                print "#### {:>7}:'makeAllMeshesUnique' while loop has reached the security limit, program has been stopped".format("Error")
                break
    else:
        if inParent == "*":
            print "#### {:>7}:'makeAllMeshesUnique' no multiple mesh found, all meshes have unique short name".format("Info")
        else :
            print "#### {:>7}:'makeAllMeshesUnique' no multiple mesh found under '{}' all meshes have unique short name ".format("Info",inParent)


def geoGroupDeleteHistory():
    """
    gets all the mesh transformms under the '|asset|grp_geo', delete their history and delete any intermediate unconnected shape 
    """
    geoTransformList,instanceTransformL = miscUtils.getAllTransfomMeshes(inParent = "|asset|grp_geo")
    if instanceTransformL:
        print "#### {:>7}: 'geoGroupDeleteHistory': {} objects are actually instances: {}".format("Warning", len(instanceTransformL), instanceTransformL)
        geoTransformList = geoTransformList+ instanceTransformL

    cmds.delete(geoTransformList,ch =True)
    print "#### {:>7}:'geoGroupDeleteHistory': deteted history on {} geometries".format("Info",len(geoTransformList))
    
    geoShapeList = cmds.ls(cmds.listRelatives("|asset|grp_geo", allDescendents = True, fullPath = True, type = "mesh"), noIntermediate = False, l=True)
    deletedShapeList = []
    for eachGeoShape in geoShapeList:
        if cmds.getAttr(eachGeoShape+".intermediateObject") == True:
            if  len(cmds.listHistory (eachGeoShape, lv=1)+ cmds.listHistory (eachGeoShape,future = True, lv=1))>2:
                print "#### warning :'geoGroupDeleteHistory': this intermediate mesh shape still has an history and cannot be deleted : "+eachGeoShape
            else:
                cmds.delete(eachGeoShape)
                deletedShapeList.append(eachGeoShape)
            print "#### info :'geoGroupDeleteHistory': deteted "+str(len(deletedShapeList))+" intermediate(s) mesh shape : "


def freezeResetTransforms(inParent = "*", inVerbose = True, inConform = False):
    """
    gets all the mesh transforms under de given inParent, an check that all the transforms values are set to 0 (1 for scales)
    logs infos in case inVerbose is true, freeze and reset the the transforms in case inConform is True.
    """
    print ""
    print "#### {:>7}: modeling.freezeResetTransforms(inParent = {}, inVerbose = {}, inConform = {})".format("Info",inParent, inVerbose, inConform)
    unFreezedTransfomList = []
    freezedTransfomList = []
    geoTransformList,instanceTransformL = miscUtils.getAllTransfomMeshes(inParent)
    if instanceTransformL:
        print "#### {:>7}: 'freezeResetTransforms': {} objects ignored since they are actually instances: {}".format("Warning", len(instanceTransformL), instanceTransformL)

    for each in geoTransformList:
        if (cmds.xform( each, os=True, q=True,  ro=True)!=[0,0,0] or cmds.xform( each, os=True, q=True,  t=True)!=[0,0,0] or cmds.xform( each, os=True, q=True,  s=True, r = True )!=[1,1,1] or 
            cmds.xform( each, os=True, q=True, rp=True)!=[0,0,0] or cmds.xform( each, os=True, q=True, sp=True)!=[0,0,0]):
            if inVerbose == True and inConform == False:
                unFreezedTransfomList.append(each)
                print "#### {:>7}: {:^28} --> has unfreezed tranform values".format("Info", each)
            if inConform == True:
                cmds.makeIdentity (each ,apply= True, n=0, pn=1)
                cmds.makeIdentity (each ,apply= False, n=0, pn=1)
                freezedTransfomList.append(each)
                if inVerbose == True: print "#### {:>7}: {:^28} --> has been freezed and reset".format("Info", each)

    if unFreezedTransfomList !=[] and inVerbose == True:
        cmds.select(unFreezedTransfomList)
        print "#### {:>7}: {} unfreezed transforms have been selected".format("Info", str(len(unFreezedTransfomList)))

    if freezedTransfomList != []:
        print "#### {:>7}: {} transforms have been freezed and reset".format("Info", len(freezedTransfomList))

    if unFreezedTransfomList ==[] and inVerbose == True:
        print "#### {:>7}: {} transforms checked successfully".format("Info", str(len(geoTransformList)))

    return unFreezedTransfomList if unFreezedTransfomList != [] else  None

def compareHDToPreviz():
    """
    This script has been made at dreamwall, to compare previz and master modeling structure you must import the previz file as a reference, 
    the asset node should have this kind of name: "nameSpace:asset_previz". then select the previz asset transform and the master asst transform, 
    run the script and read the log
    """

    # compare asset_hi to asset_previz ( compare translate-rotate of group are the same and local pivot rotate-scale of hi must be 0).
    #import maya.cmds as cmds

    DECIMAL_NB = 3

    #print(cmds.nodeType("grp_bureauArriere_grp_livre_to_ctrl_livre_prCns"))

    def is_group(node): # test if node is a group
        if cmds.nodeType(node) != 'transform': # test if node is a transform
            return False
        children = cmds.listRelatives(c=True, f=True)
        for child in children:
            if cmds.nodeType(child) != 'transform':
                return False
        return True

    def floatLimitDecimal(value, decimalNb):
        return float(format(value, "."+str(decimalNb)+"f"))
        
    def vectorLimitDecimal(vector, decimalNb):
        return [floatLimitDecimal(vector[0],decimalNb), floatLimitDecimal(vector[1],decimalNb), floatLimitDecimal(vector[2],decimalNb)]

    ## previz is the ref, hi could have more group but not less, and check localspace pivot translate et scale MUST be 0 !

    namespacePreviz = ""
    errorCount = 0;
    sel = cmds.ls(sl=True, type='transform') # get the transform(s) selected
    #print sel
    if len(sel) == 2: # test if current selection has 2 nodes
         assetPreviz = sel[1]
         assetHi = sel[0]
         if "previz" in sel[0]:
             assetPreviz = sel[0]
             assetHi = sel[1]
             
         if "previz:" in assetPreviz:
             namespacePreviz = assetPreviz.split(":")[0] # get namespace

         print("\n***** comparing translations and rotations value from " + assetHi + " to reference " + assetPreviz)
         groupsPreviz = cmds.listRelatives(assetPreviz, ad=True, f=True,type='transform') # get all transforms with ful path
         #print ("* " + str(groupsPreviz))
         for groupPreviz in groupsPreviz:
             #print (groupPreviz + " " + groupPreviz.split("|")[-1])
             
             if is_group(groupPreviz) and "grp_" in groupPreviz.split("|")[-1] and not "grp_geo_" in groupPreviz.split("|")[-1]: # if the transform is a group
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
                 #print("groupHi = " + groupHi)
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

                 else:
                     print("\tERROR: group: " + groupHi + " is missing")


         if (errorCount != 0):
             if (errorCount == 1):
                 print("**** " + str(errorCount) + " error found ")
             else:
                 print("**** " + str(errorCount) + " errors found ")
         else:
             print("**** checking done, no error")

    else:
         print ("\n***** please select both asset hi-def and asset previz and try again")



def combineGeoGroup(toCombineObjL = [], combineByMaterialB = False, GUI = True, autoRenameI = 0):
    """
    this script merge selected objects only if they are under the same group.
    It ensure that the resulting object is under the intial group.
        toCombineObjL: a list of shapes ot transform objects to combine, groups are not accepeted. if nothing in input try with the selection
        combineByMaterialB: if True il merge only objects that share the same material
        GUI: if True wil log messages and select merged object when combined 
        autoRenameI:    0: do not rename the combined objects, name is the first selected object or first of the list
                        1: rename combined object as the group he's under, '_mergedxx' extention is added at the extend

    """
    resultB = True
    logL = []
    resultObjL = []
    combinedObjL = []
    shaderAssignationD = {'multiMaterial':[]}


    if not toCombineObjL:
        toCombineObjL = cmds.ls(selection = True,l = True)

    toCombineShapesL = cmds.ls(toCombineObjL,l = True, shapes = True)+ cmds.ls(cmds.listRelatives(toCombineObjL, children = True, fullPath = True, type = "mesh"), noIntermediate = True, l=True)

    if len(toCombineShapesL)<2:
        return [resultB, logL, toCombineObjL, resultObjL] 

    #path = toCombineShapesL[-1].split(toCombineShapesL[-1].split("|")[-1])[0].rstrip("|")
    path = cmds.listRelatives(cmds.listRelatives(toCombineShapesL[-1], parent = True, fullPath = True, type = "transform"), parent = True, fullPath = True, type = "transform")[0]
    finalObjectName = toCombineShapesL[-1].split("|")[-1]

    # check that all the meshes belong to the same group
    for each in toCombineShapesL:
        eachPath = cmds.listRelatives(cmds.listRelatives(each, parent = True, fullPath = True, type = "transform"), parent = True, fullPath = True, type = "transform")[0]
        if path != eachPath:
            logMessage = "#### {:>7}: 'combineGeo' Cannot merge 2 elements of a different group: {} is not under '{}'".format("Error", each, path)
            if GUI == True : raise ValueError (logMessage)
            resultB = False
            logL.append(logMessage)

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

    #combine objects depending on the key they are referenced under
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
                    newGroupName = cmds.group(mergedObjectName, name= groupName, parent = parentName)
                    mergedObjectName = newGroupName+"|"+mergedObjectShortName
                else:
                    mergedObjectName = cmds.parent(mergedObjectName, path )[0]
                if autoRenameI ==0 : mergedObjectName = cmds.rename(mergedObjectName,mergedObjectName.rstrip("Shape"))
                elif autoRenameI == 1 : mergedObjectName = cmds.rename(mergedObjectName,groupName.replace("grp_","geo_")+"_merged00" )
                resultObjL.append(mergedObjectName)

    logMessage = "#### {:>7}: 'combineGeoGroup' {} objects combined in : {} objects".format("Info",len(combinedObjL),len(resultObjL))
    logL.append(logMessage)
        
    if GUI == True: 
        cmds.select(resultObjL)
        print logMessage

    return [resultB, logL, toCombineObjL, resultObjL] 



def combineAllGroups():
 
    transformL = mc.ls(mc.listRelatives("asset|grp_geo", allDescendents = True, fullPath = True, type = "transform"), l=True, exactType="transform")
    for each in transformL:
        if re.match('^grp_', each.split("|")[-1]):
            meshL = mc.listRelatives(each, allDescendents = True, fullPath = True, type = "mesh")
            modeling.combineGeoGroup(toCombineObjL = meshL, GUI = False, autoRenameI= 1, combineByMaterialB = True)



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


