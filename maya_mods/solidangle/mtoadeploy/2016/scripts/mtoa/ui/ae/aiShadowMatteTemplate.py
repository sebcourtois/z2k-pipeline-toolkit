import pymel.core as pm
from mtoa.ui.ae.shaderTemplate import ShaderAETemplate

class AEaiShadowMatteTemplate(ShaderAETemplate):
    
    def setup(self):
        self.beginScrollLayout()

        self.addCustom('message', 'AEshaderTypeNew', 'AEshaderTypeReplace')

        self.beginLayout("Shadows", collapse=False)
        self.addControl("background", label="Background Color")
        self.addControl("shadowColor", label="Shadow Color")
        self.addControl("shadowOpacity", label="Shadow Opacity")
        self.addControl("backlighting", label="Backlighting")
        
        
        self.endLayout()

        self.beginLayout("Diffuse", collapse=False)
        self.addControl("catchDiffuse", label="Catch Diffuse")
        self.addControl("diffuseColor", label="Diffuse Color")
        self.endLayout()

        pm.mel.AEdependNodeTemplate(self.nodeName)

        self.addExtraControls()
        self.endScrollLayout()

