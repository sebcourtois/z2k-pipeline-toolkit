import pymel.core as pm
import mtoa.utils as utils
import mtoa.ui.ae.utils as aeUtils
from mtoa.ui.ae.shaderTemplate import ShaderAETemplate


class AEdmnToonTemplate(ShaderAETemplate):

    def setup(self):
        self.addSwatch()
        self.beginScrollLayout()
        self.addCustom('message', 'AEshaderTypeNew', 'AEshaderTypeReplace')


        self.addControl('output', label='Output')

        self.beginLayout('Toon', collapse=True)
        self.addControl('toon_weight', label='Weight')
        self.addControl('toon_bright', label='Bright Color')
        self.addControl('toon_dark', label='Dark Color')
        self.addControl('toon_coverage', label='Coverage')
        self.addControl('toon_softness', label='Softness')
        self.addControl('toon_illum_multiplier', label='Illum Multiplier')
        self.addControl('toon_sphere_normals', label='Sphere Normals')
        self.addControl('toon_normal_map', label='Normal Map')
        self.addControl('toon_normal_map_weight', label='Normal Map Weight')
		
        self.beginLayout('Rim Toon', collapse=True)
        self.addControl('rim_toon_weight', label='Rim Weight')
        self.addControl('rim_toon_bright', label='Bright Color')
        self.addControl('rim_toon_dark', label='Dark Color')
        self.addControl('rim_toon_coverage', label='Coverage')
        self.addControl('rim_toon_softness', label='Softness')
        self.endLayout()
		
        self.endLayout()

        self.beginLayout('Diffuse', collapse=True)
        self.addControl('diffuse_color', label='Color')
        self.addControl('diffuse_intensity', label='Intensity')
        self.addControl('diffuse_tint', label='Tint')
        self.endLayout()

        self.beginLayout('Ambient', collapse=True)
        self.addControl('ambient_color', label='Color')
        self.addControl('ambient_intensity', label='Intensity')
        self.addControl('ambient_tint', label='Tint')
        self.endLayout()

        self.beginLayout('Incandescence', collapse=True)
        self.addControl('incandescent_color', label='Color')
        self.addControl('incandescent_intensity', label='Intensity')
        self.endLayout()

        self.beginLayout('Shadow Mask', collapse=True)
        self.addControl('shadow_mask_weight', label='Weight')
        self.addControl('shadow_mask', label='Mask')
        self.endLayout()

        self.beginLayout('Lambert', collapse=True)
        self.addControl('lambert_weight', label='Weight')
        self.addControl('lambert_color', label='Color')
        self.endLayout()

        self.beginLayout('Incidence', collapse=True)
        self.addControl('incidence_weight', label='Weight')
        self.addControl('incidence_color', label='Color')
        self.addControl('incidence_falloff', label='Falloff')
        self.endLayout()

        self.beginLayout('Occlusion', collapse=True)
        self.addControl('occlusion_weight', label='Weight')
        self.addControl('ambient_occlusion', label='Ambient Occlusion')
        self.addControl('occlusion_black', label='Dark Color')
        self.addControl('occlusion_samples', label='Samples')
        self.addControl('occlusion_spread', label='Spread')
        self.addControl('occlusion_min_dist', label='Min. Dist')
        self.addControl('occlusion_max_dist', label='Max. Dist')
        self.addControl('occlusion_falloff', label='Falloff')
		        

        self.endLayout()

        self.beginLayout('Contour', collapse=True)
        self.addControl('contour_weight', label='Weight')
        self.addControl('contourSize', label='Contour Size')
        self.addControl('contour_samples', label='Samples')

        self.addControl('rasterOrient', label='Raster Orient')
        self.addControl('contourColor', label='Contour Color')
        self.addControl('contourOther', label='Inter-Objects Contour')
        self.addControl('baseColor', label='Base Color')
        
        self.beginLayout('Self Contours', collapse=False)
        self.addControl('contourSelf', label='Enable Self-Contours')
        self.addControl('selfCompareShader', label='Compare Shader')
        self.addControl('selfNormalThreshold', label='Normal Threshold')
        self.addControl('selfDepthThreshold', label='Depth Threshold')
        self.endLayout()

        self.beginLayout('Anisotropy', collapse=False)
        self.addControl('anisotropy', label='Enable Anisotropy')
        self.addControl('anisotropy_angle', label='Angle')
        self.addControl('anisotropy_factor', label='Size Factor')
        self.endLayout()

        self.beginLayout('Remap Incidence', collapse=True)
        self.addControl('remapIncidence', label='Remap Incidence')
        self.addControl('remapIncidenceFactor', label='Size Factor')
        self.addControl('remapIncidenceFalloff', label='Falloff')
        self.endLayout()

        self.beginLayout('Remap Depth', collapse=True)
        self.addControl('remapDepth', label='Remap Depth')
        self.addControl('remapDepth_distance', label='Distance')
        self.addControl('remapDepth_factor', label='Size Factor')
        self.addControl('remapDepth_falloff', label='Falloff')
        self.endLayout()

        self.beginLayout('Remap Curvature', collapse=True)
        self.addControl('remapCurvature', label='Remap Curvature')
        self.addControl('remapCurvature_factor', label='Size Factor')
        self.endLayout()

        self.addControl('contour_id', label='ID')
        self.endLayout()


        self.beginLayout('AOVs', collapse=True)
        self.addControl('toon_AOV', label='Toon')
        self.addControl('shadow_mask_AOV', label='Shadow Mask')
        self.addControl('lambert_AOV', label='Lambert')
        self.addControl('diffuse_AOV', label='Diffuse')
        self.addControl('ambient_AOV', label='Ambient')
        self.addControl('incandescence_AOV', label='Incandescence')
        self.addControl('incidence_AOV', label='Incidence')
        self.addControl('occlusion_AOV', label='Occlusion')
        self.addControl('contour_AOV', label='Contour')
        self.endLayout()

        self.beginLayout('Masks', collapse=True)
        self.addControl('dmn_mask00', label='dmn_mask00')
        self.addControl('dmn_mask01', label='dmn_mask01')
        self.addControl('dmn_mask02', label='dmn_mask02')
        self.addControl('dmn_mask03', label='dmn_mask03')
        self.addControl('dmn_mask04', label='dmn_mask04')
        self.endLayout()

        # include/call base class/node attributes
        pm.mel.AEdependNodeTemplate(self.nodeName)

        self.addExtraControls()

        self.endScrollLayout()
