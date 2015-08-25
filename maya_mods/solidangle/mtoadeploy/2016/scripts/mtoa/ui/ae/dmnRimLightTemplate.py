import pymel.core as pm
from mtoa.ui.ae.shaderTemplate import ShaderAETemplate

class AEdmnRimLightTemplate(ShaderAETemplate):
    def setup(self):
        self.beginScrollLayout()

        pm.mel.AEdependNodeTemplate(self.nodeName)
        self.addExtraControls()
        self.endScrollLayout()
