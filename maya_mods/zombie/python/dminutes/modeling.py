import pymel.core as pc
import tkMayaCore as tkc
import pymel.core.datatypes as dt

'''
Temporary module to manage modeling


identified checks
-namespace|shortname
-names equality
-name structure : type_characterName_variation[eventually]_step
-hierarchy

'''

SPECNAMES = {"grp_geo":"ctrl_global"}
CTRLS_SIZE = 1.0

CTRL_SETNAME = "set_ctrls"
GEOMETRIES_LAYERNAME = "layer_geometries"

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

            #Finally delete the rig Root 
            pc.delete(child)
            return

    return

def createSetControlRecur(inGrp, inRoot):
    createdObjs = ([], [])

    ctrlName = inGrp.name().replace("grp_", "ctrl_")
    icon = None
    
    if inGrp.name() in SPECNAMES:
        ctrlName = SPECNAMES[inGrp.name()]
        icon = tkc.createCubeIcon(ctrlName, size=CTRLS_SIZE, scale=(1, 0.001, 1))
        tkc.setObjectColor(pc.ls(sl=True)[0], [255, 255, 0, 0])
    else:
        icon = tkc.createRingsIcon(ctrlName, size=CTRLS_SIZE)
        tkc.setObjectColor(pc.ls(sl=True)[0], [255, 255, 255, 0])
    
    pc.parent(icon, inRoot)
    tkc.matchTRS(icon, inGrp)
    tkc.setNeutralPose(icon)
    tkc.constrain(inGrp, icon, "Pose")

    createdObjs[0].append(icon)
    
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

    #Put all geometries in a layer, and set it to "reference"
    if pc.objExists(GEOMETRIES_LAYERNAME):
        pc.delete(GEOMETRIES_LAYERNAME)

    pc.select(geos)
    newLayer = pc.createDisplayLayer(name=GEOMETRIES_LAYERNAME)
    pc.setAttr(newLayer + ".displayType", 2)

    pc.select(clear=True)