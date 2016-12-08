import maya.cmds as cmds
import pymel.core as pm
import mtoa.ui.ae.lightTemplate as lightTemplate
import mtoa.ui.ae.aiSwatchDisplay as aiSwatchDisplay
import mtoa.ui.ae.templates as templates
import mtoa.utils as utils

def inMeshReplace(plugName):
    nodeAndAttrs = plugName.split(".")
    node = nodeAndAttrs[0]
    cmds.attrNavigationControlGrp("aiMeshLightInMeshCtrl", edit=True, attribute=("%s.inMesh" % node))

def inMeshNew(plugName):
    cmds.attrNavigationControlGrp("aiMeshLightInMeshCtrl", label="In Mesh")
    inMeshReplace(plugName)

class AEaiMeshLightTemplate(lightTemplate.LightTemplate):

    def addSwatch(self):
        self.addCustom("message", aiSwatchDisplay.aiSwatchDisplayNew, aiSwatchDisplay.aiSwatchDisplayReplace)

    def setup(self):
        self.addSwatch()
        self.beginScrollLayout()

        self.beginLayout("Mesh Attributes", collapse=False)
        self.addCustom("inMesh", inMeshNew, inMeshReplace)
        self.addControl("showOriginalMesh")
        self.endLayout()

        self.beginLayout("Light Attributes", collapse=False)
        self.addControl("color")
        self.addControl("intensity")
        self.addControl("aiExposure", label = "Exposure")
        self.addSeparator()
        self.setupColorTemperature("ArnoldMesh")
        self.addSeparator()
        self.addControl("emitDiffuse")
        self.addControl("emitSpecular")
        self.addControl("aiDecayType")
        self.addSeparator()
        self.addControl("lightVisible")
        self.addSeparator()
        self.addControl("aiSamples")
        self.addControl("aiNormalize")
        self.addSeparator()
        self.addControl("aiCastShadows")
        self.addControl("aiShadowDensity")
        self.addControl("aiShadowColor")
        self.addSeparator()
        self.commonLightAttributes()
        self.endLayout()

        # Do not show extra attributes
        extras = ["visibility",
                  "intermediateObject",
                  "template",
                  "ghosting",
                  "instObjGroups",
                  "useObjectColor",
                  "objectColor",
                  "drawOverride",
                  "lodVisibility",
                  "renderInfo",
                  "renderLayerInfo",
                  "ghostingControl",
                  "ghostCustomSteps",
                  "ghostFrames",
                  "ghostRangeStart",
                  "ghostRangeEnd",
                  "ghostDriver",
                  "ghostColorPreA",
                  "ghostColorPre",
                  "ghostColorPostA",
                  "ghostColorPost",
                  "motionBlur",
                  "visibleInReflections",
                  "visibleInRefractions",
                  "castsShadows",
                  "receiveShadows",
                  "maxVisibilitySamplesOverride",
                  "maxVisibilitySamples",
                  "geometryAntialiasingOverride",
                  "antialiasingLevel",
                  "shadingSamplesOverride",
                  "shadingSamples",
                  "maxShadingSamples",
                  "volumeSamplesOverride",
                  "volumeSamples",
                  "depthJitter",
                  "ignoreSelfShadowing",
                  "primaryVisibility",
                  "compInstObjGroups",
                  "localPosition",
                  "localScale"]

        for extra in extras:
            self.suppress(extra)
        
        pm.mel.AEdependNodeTemplate(self.nodeName)

        self.addExtraControls()
        self.endScrollLayout()
