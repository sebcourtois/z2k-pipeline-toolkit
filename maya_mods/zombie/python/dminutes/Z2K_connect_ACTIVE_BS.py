# Z2K connect ACTIVE BLEND SHAPES

############### Importing other LIBS ####################
import maya.cmds as cmds

#########################################################

targetBS_Obj = "geo_head"
targetBS_Node = "geo_head_BSOp"
tableD = {
    "mouth_stretch_vertical": ["Jaw_Bone_Ctrl","stretch_vertical","double", -5, 0, 5 ,True],
    "mouth_stretch_horizontal": ["Jaw_Bone_Ctrl","stretch_horizontal","double", -5, 0, 5,True ],


    "mouth_center_planar_up": ["UpperLip_Center","curvature_planar","double", -2, 0, 2,True ],
    "mouth_center_planar_dn": ["LowerLip_Center","curvature_planar","double", -2, 0, 2,True ],

    "mouth_center_pinch_up_local": ["UpperLip_Center","pinch","double", -2, 0, 2,True ],
    "mouth_center_pinch_dn_local": ["LowerLip_Center","pinch","double", -2, 0, 2,True ],
    "mouth_center_pinch_up_larger": ["UpperLip_Center","pinch_larger","double", -2, 0, 2,True ],
    "mouth_center_pinch_dn_larger": ["LowerLip_Center","pinch_larger","double", -2, 0, 2,True ],

    "mouth_midCenter_pinch_dn_L" : ["Left_LowerLip_1_Ctrl","pinch","double", -3, 0, 3,True ],
    "mouth_midCenter_pinch_dn_R" : ["Right_LowerLip_1_Ctrl","pinch","double", -3, 0, 3,True ],

    "mouth_midCenter_pinch_up_L": ["Left_UpperLip_1_Ctrl","pinch","double", -3, 0, 3,True ],
    "mouth_midCenter_pinch_up_R": ["Right_UpperLip_1_Ctrl","pinch","double", -3, 0, 3,True ],

    "mouth_corner_pinch_L": ["Left_MouthCorner","pinch","double", -2, 0, 2,True ],
    "mouth_corner_pinch_R": ["Right_MouthCorner","pinch","double", -2, 0, 2,True ],
    

    "eyeLid_center_pinch_dn_R": ["Right_Eye_Bulge","cheek_squeeze","double", -2, 0, 2,True ],
    "eyeLid_center_pinch_dn_L": ["Left_Eye_Bulge","cheek_squeeze","double", -2, 0, 2,True ],

    "eyeLid_center_pinch_up_R": ["Right_Eye_Bulge","upperLid_up","double", -2, 0, 2,True ],
    "eyeLid_center_pinch_up_L": ["Left_Eye_Bulge","upperLid_up","double", -2, 0, 2,True ],


}

# delete old BS -------------------------

# construct current BS attr Dict
bsAttrL = cmds.aliasAttr( targetBS_Node, query=True )
bsAttrD = {}
enu = enumerate(bsAttrL)
for i,a in enu:
   bsAttrD[a]=i+1
   next(enu)

# delete BSattr  
for a,i in bsAttrD.iteritems():
    print a,i
    try:
        cmds.blendShape (targetBS_Node, e=1, remove=True, t= (targetBS_Obj,i,a,0)  )
    except:
        pass

    

# add BS and connect
for sourceBS_Obj,paramL in tableD.iteritems():
    print sourceBS_Obj
    ctrObj = paramL[0]
    attrN = paramL[1]
    attrT =  paramL[2]
    attrMin = paramL[3]
    attrDv = paramL[4]
    attrMax = paramL[5]
    attrK = paramL[6]

    oldN = sourceBS_Obj
    
    # add to BSNode
    
    index = len( cmds.getAttr(targetBS_Node+"."+"w")[0] )
    print "index=", index
    cmds.blendShape (targetBS_Node, e=1, t = [targetBS_Obj, index, sourceBS_Obj, 1 ] )
    
    # delete old attrib
    try:
        print ctrObj
        cmds.deleteAttr(ctrObj, at=attrN, )
    except Exception,err:
        print err
        pass
    # add attr to control object
    print ctrObj,attrN
    cmds.addAttr(ctrObj, longName=attrN, attributeType= attrT, min=attrMin,dv= attrDv, max= attrMax,
                            keyable=attrK,) 
    # connect
    cmds.connectAttr(ctrObj + "."+attrN, targetBS_Node + "."+ sourceBS_Obj, f=True)


print "BS link and applied, ho yeah, rock the cashbah!"