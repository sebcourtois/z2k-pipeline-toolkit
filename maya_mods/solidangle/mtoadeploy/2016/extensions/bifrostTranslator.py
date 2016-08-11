import mtoa.ui.ae.templates as templates
from mtoa.ui.ae.templates import AttributeTemplate

class BifrostTemplate(AttributeTemplate):
    def setup(self):
        self.addControl("aiStepSize", label="Step Size")
        self.addControl("aiMaxSteps", label="Max Steps")
        self.addControl("aiShadowing", label="Shadowing")
        self.addControl("aiShadowingStepSize", label="Shadowing Step Size")
        self.addControl("aiShadowingMaxSteps", label="Shadowing Max Steps")

        
templates.registerAETemplate(BifrostTemplate, 'bifrostAeroMaterial')