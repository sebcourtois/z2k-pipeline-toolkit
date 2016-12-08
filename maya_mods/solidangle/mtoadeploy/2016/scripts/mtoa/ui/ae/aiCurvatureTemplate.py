import pymel.core as pm
import mtoa.utils as utils
import mtoa.ui.ae.utils as aeUtils
from mtoa.ui.ae.shaderTemplate import ShaderAETemplate


class AEaiCurvatureTemplate(ShaderAETemplate):

   
    def setup(self):
        self.addSwatch()
       
        self.beginScrollLayout()
        
        self.addCustom('message', 'AEshaderTypeNew', 'AEshaderTypeReplace')


        self.beginLayout('Curvature', collapse=False)
        self.addControl('output', label='Output')

        self.addControl('samples', label='Samples')
        self.addControl('radius', label='Radius')        
        self.addControl('spread', label='Spread')
        self.addControl('threshold', label='Threshold')
        self.addControl('bias', label='Bias')
        self.addControl('multiply', label='multiply')
        self.addControl('trace_set', label='Trace Set')
        self.addControl('inclusive', label='Inclusive')
        self.addControl('self_only', label='Self Only')
        
        self.endLayout()
  
        # include/call base class/node attributes
        pm.mel.AEdependNodeTemplate(self.nodeName)
        
        self.addExtraControls()
        
        self.endScrollLayout()
