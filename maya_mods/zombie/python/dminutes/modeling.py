import pymel.core as pc
import tkMayaCore as tkc

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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def getObj(in_sName):
    obj = None
    try:
        obj = pc.PyNode(inName)
    except:
        pass
    return obj
 

def showErrors(in_errorsList, in_stoppedDef=None):
    if in_stoppedDef != None:
        pc.error(stoppedDef + " has stopped with errors:\n" + "\n".join(in_errorsList))
    else:
        pc.warning("\n".join(errorsList))

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
    assetType, characterName, step = (chunk for chunk in splitName)
    
    if len(splitName) > 3:
        variation = splitName[2]
        step = splitName[3]
    
    if assetType != "chr":
        errors.append("Detected type is unknown" % assetType)
        showErrors(errors)
    
    #Make sure that "Geometries" exists.
    objname = "%s:%s" % (ns, "Geometries")
    geoRoot = getObj(objname)
    if geoRoot == None:
        errors.append("Geometries root cannot be found ('%s')" % objname)
        showErrors(errors, "createBS")
    
    #Make sure that "BS" exists...
    objname = "%s:%s" % (ns, "BS")
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
            pc.delete(child)
            return

    return

def createSetControlRecur(inGrp, inRoot):
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
    
    children = tkc.getChildren(inGrp, False)
    
    for child in children:
        if child.name()[:4] == "grp_" and child.getShape() == None:
            createSetControlRecur(child, icon)

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
    
    createSetControlRecur(children[0], grp_rig)