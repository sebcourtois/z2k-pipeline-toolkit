import pymel.core as pc
import tkMayaCore as tkc
import pymel.core.datatypes as dt

import maya.cmds as mc
import re
import string
import miscUtils


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
GEOMETRIES_LAYERNAME = "layer_geometry"

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
    createdObjs = ([], [])

    ctrlName = inGrp.name().replace("grp_", "ctrl_")
    icon = None

    isRootControl = False
    
    if inGrp.name() in SPECNAMES:
        if inGrp.name() == 'grp_geo':
            isRootControl = True

        ctrlName = SPECNAMES[inGrp.name()]
        icon = tkc.createCubeIcon(ctrlName, size=CTRLS_SIZE, scale=(3, 0.001, 3))
        tkc.setObjectColor(icon, [255, 128, 0, 0])
    else:
        icon = tkc.createRingsIcon(ctrlName, size=CTRLS_SIZE)
        tkc.setObjectColor(icon, [255, 255, 255, 0])
    
    pc.parent(icon, inRoot)
    tkc.matchTRS(icon, inGrp)
    tkc.setNeutralPose(icon)
    tkc.constrain(inGrp, icon, "Pose", inAdditionnalArg=True)

    if isRootControl:
        global_srt = tkc.createCubeIcon(SPECNAMES['global_srt'], size=CTRLS_SIZE, scale=(2, 0.001, 2))
        tkc.setObjectColor(global_srt, [255, 255, 0, 0])
        pc.parent(global_srt, inRoot)
        tkc.matchTRS(global_srt, inGrp)
        tkc.setNeutralPose(global_srt)
        tkc.parent(icon, global_srt)
        createdObjs[0].append(global_srt)

        big_daddy = tkc.createCubeIcon(SPECNAMES['big_daddy'], size=CTRLS_SIZE, scale=(4, 0.001, 4))

        pc.setAttr('{0}.visibility'.format(big_daddy.getShape().name()), False)
        tkc.setObjectColor(big_daddy, [255, 255, 0, 0])
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
            subCreatedObjs = createSetControlRecur(grpChild, icon)
            createdObjs[0].extend(subCreatedObjs[0])
            createdObjs[1].extend(subCreatedObjs[1])

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
    
    ctrls, geos = createSetControlRecur(children[0], grp_rig)

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

    #Put all groups in a set for caching
    groups=[]

    for geo in geos:
        group = geo.getParent()
        if not group in groups:
            groups.append(group)

    if pc.objExists(CACHE_SETNAME):
        pc.delete(CACHE_SETNAME)

    pc.sets(groups, name=CACHE_SETNAME)

    #Put all geometries in a layer, and set it to "reference"
    if pc.objExists(GEOMETRIES_LAYERNAME):
        pc.delete(GEOMETRIES_LAYERNAME)

    pc.select(geos)
    newLayer = pc.createDisplayLayer(name=GEOMETRIES_LAYERNAME)
    pc.setAttr(newLayer + ".displayType", 2)

    pc.select(clear=True)


    

def checkMeshNamingConvention(printInfo = True):
    """
    check all the meshes naming convention, '(geo|aux)_name_complement##' where 'name' and 'complement##' are strings of 24 alphanumeric characters
    only meshes of the main name space are taken into account, referenced meshes are therefore ignored.
        - printInfo (boolean) : print the 'multipleMesh' list 
        - return (list) : wrongMeshNamingConvention, all the meshes with a bad naming convetion
    """
    wrongMeshNamingConvention = []
    allTransMesh =  mc.listRelatives (mc.ls("*:",type = "mesh"), parent = True, fullPath = True, type = "transform")
    if allTransMesh is None: allTransMesh = []
    
    for each in allTransMesh:
        eachShort = each.split("|")[-1]
        if not (re.match('^(geo|aux)_[a-zA-Z0-9]{1,24}$', eachShort) or re.match('^(geo|aux)_[a-zA-Z0-9]{1,24}_[a-zA-Z0-9]{1,24}$', eachShort)):
            wrongMeshNamingConvention.append(each)
    
    if printInfo == True:
        if wrongMeshNamingConvention:
            print "#### warning: 'checkMeshNamingConvention': the following MESH(ES) do not match the mesh naming convention:"
            print "#### warning: 'checkMeshNamingConvention': '(geo|aux)_name_complement##' where name and complement## are strings of 24 alphanumeric characters"
            for each in wrongMeshNamingConvention:
                print "#### warning: 'checkMeshNamingConvention': name not conform --> "+each
            mc.select(wrongMeshNamingConvention, replace = True)
        else:
            print "#### info: 'checkMeshNamingConvention': MESH naming convention is correct"                
            
    return wrongMeshNamingConvention
    

def meshShapeNameConform(fixShapeName = True, myTransMesh = [], forceInfoOff = False):
    """
    This function, makes sure every mesh shape name is concistant with its transform name: "transformName+Shape"
    Only shapes of the main name space are taken into account, referenced shapes are therefore ignored
        - fixShapeName (boolean): fix invalid shapes names if True, only log info otherwise
        - return (list): the meshes list that still have an invalid shape name
    """
    if not myTransMesh:
        myTransMesh =  mc.listRelatives (mc.ls("*:", type = "mesh"), parent = True, fullPath = True, type = "transform")
        if myTransMesh is None: myTransMesh = []
        checkAllScene = True
    else:
        checkAllScene = False
    renamedNumber = 0
    shapesToFix = []
    for each in myTransMesh:  
        myShape = mc.listRelatives (each, children = True, fullPath = True, type = "shape")
        if len(myShape)!= 1:
            print "#### error:'meshShapeNameConform' no or multiple shapes found for :"+each
            break
        myShape = myShape[0]
        myShapeCorrectName = each+"|"+each.split("|")[-1]+"Shape"
        if myShape != myShapeCorrectName and fixShapeName == True:
            if forceInfoOff is False: print "#### info: 'meshShapeNameConform': rename '"+myShape.split("|")[-1]+"' --> as --> '"+myShapeCorrectName.split("|")[-1]+"'"
            mc.rename(myShape,each.split("|")[-1]+"Shape")
            renamedNumber = renamedNumber +1
        elif myShape != myShapeCorrectName and fixShapeName == False:
            print "#### warning: 'meshShapeNameConform': '"+each+"' has a wrong shape name: '"+myShape.split("|")[-1]+"' --> should be renamed as: --> '"+myShapeCorrectName.split("|")[-1]+"'"
            shapesToFix.append(each)
    if renamedNumber != 0:
        if forceInfoOff is False: print "#### info: 'meshShapeNameConform': "+str(renamedNumber)+" shape(s) fixed"
        return None
    elif shapesToFix:
        if forceInfoOff is False: print "#### info: 'meshShapeNameConform': "+str(len(shapesToFix))+" shape(s) to be fixed"
        return shapesToFix
    elif checkAllScene == True:
        if forceInfoOff is False: print "#### info: 'meshShapeNameConform': all meshes shapes names are correct"
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

    allTransMesh = miscUtils.getAllTransfomMeshes(inParent)
    multipleMesh = []

    for eachTrasnMesh in allTransMesh:
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
    allTransMesh = miscUtils.getAllTransfomMeshes(inParent)
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
        mc.rename(myMesh,newShortName+newDigit)
        print "#### info: 'renameMeshAsUnique' rename "+myMesh+"  -->  "+string.rstrip(myMesh,digit)+newDigit
        meshShapeNameConform(fixShapeName = True, myTransMesh = [string.rstrip(myMesh,digit)+newDigit], forceInfoOff = True )
        
    else:
        digit = "1"
        i = 1
        while str(allTransMesh).count(shortName+digit) > 0:
            digit = str(int(digit)+1)
            i = i+1
        myMeshNew = [mc.rename(myMesh,shortName+digit)]
        print "#### info: 'renameMeshAsUnique' rename "+myMesh+"  -->  "+myMesh+digit
        meshShapeNameConform(fixShapeName = True, myTransMesh = myMeshNew, forceInfoOff = True)

                        
def makeAllMeshesUnique(inParent = "*"):
    """
    makes all the meshes short names unique by adding a digit and/or incrementing it till the short name is unique in the scene
    then makes sure the shapes names are corrects
    """           
    multipleMesh = getMeshesWithSameName(inVerbose = False,inParent = inParent)
    if multipleMesh :
        while multipleMesh:
            renameMeshAsUnique(multipleMesh[0], inParent)
            multipleMesh = getMeshesWithSameName(inVerbose = False,inParent = inParent)
    else:
        if inParent == "*":
            print "#### info: 'makeAllMeshesUnique' no multiple mesh found, all meshes have unique short name "
        else :
            print "#### info: 'makeAllMeshesUnique' no multiple mesh found under '"+inParent+"' all meshes have unique short name "


def geoGroupDeleteHistory():
    """
    gets all the mesh transformms under the '|asset|grp_geo', delete their history and delete any intermediate unconnected shape 
    """
    geoTransformList = miscUtils.getAllTransfomMeshes(parent = "|asset|grp_geo")
    mc.delete(geoTransformList,ch =True)
    print "#### info :'geoGroupDeleteHistory': deteted history on "+str(len(geoTransformList))+" geometries : "
    
    geoShapeList = mc.ls(mc.listRelatives(grpGeo, allDescendents = True, fullPath = True, type = "mesh"), noIntermediate = False, l=True)
    deletedShapeList = []
    for eachGeoShape in geoShapeList:
        if mc.getAttr(eachGeoShape+".intermediateObject") == True:
            if  len(mc.listHistory (eachGeoShape, lv=1)+ mc.listHistory (eachGeoShape,future = True, lv=1))>2:
                print "#### warning :'geoGroupDeleteHistory': this intermediate mesh shape still has an history and cannot be deleted : "+eachGeoShape
            else:
                mc.delete(eachGeoShape)
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
    geoTransformList = miscUtils.getAllTransfomMeshes(inParent)
    for each in geoTransformList:
        if (mc.xform( each, os=True, q=True,  ro=True)!=[0,0,0] or mc.xform( each, os=True, q=True,  t=True)!=[0,0,0] or mc.xform( each, os=True, q=True,  s=True, r = True )!=[1,1,1] or 
            mc.xform( each, os=True, q=True, rp=True)!=[0,0,0] or mc.xform( each, os=True, q=True, sp=True)!=[0,0,0]):
            if inVerbose == True and inConform == False:
                unFreezedTransfomList.append(each)
                print "#### {:>7}: {:^28} has unfreezed tranform values".format("Info", each)
            if inConform == True:
                mc.makeIdentity (each ,apply= True, n=0, pn=1)
                mc.makeIdentity (each ,apply= False, n=0, pn=1)
                freezedTransfomList.append(each)
                if inVerbose == True: print "#### {:>7}: {:^28} has been freezed and reset".format("Info", each)

    if unFreezedTransfomList !=[] and inVerbose == True:
        mc.select(unFreezedTransfomList)
        print "#### {:>7}: {} unfreezed transforms have been selected".format("Info", str(len(unFreezedTransfomList)))

    if freezedTransfomList != []:
        print "#### {:>7}: {} transforms have been freezed and reset".format("Info", len(freezedTransfomList))

    if unFreezedTransfomList ==[] and inVerbose == True:
        print "#### {:>7}: {} transforms checked successfully".format("Info", str(len(geoTransformList)))

    return unFreezedTransfomList if unFreezedTransfomList != [] else  None



