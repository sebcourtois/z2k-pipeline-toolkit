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
        
        self.beginLayout('Ambient', collapse=False)
        self.addControl('ambient_color', label='Color')
        self.addControl('ambient_intensity', label='Intensity')
        self.addControl('ambient_tint', label='Tint')
        self.endLayout()


        self.beginLayout('Diffuse', collapse=False)
        self.addControl('diffuse_color', label='Color')
        self.addControl('diffuse_intensity', label='Intensity')
        self.addControl('diffuse_tint', label='Tint')
        self.endLayout()


        self.beginLayout('Shadow Mask', collapse=False)
        self.addControl('shadow_mask_weight', label='Weight')
        self.addControl('shadow_mask', label='Mask')
        self.addControl('shadow_mask_weight_01', label='Weight 1')
        self.addControl('shadow_mask_01', label='Mask')
        self.addControl('shadow_mask_weight_02', label='Weight 2')
        self.addControl('shadow_mask_02', label='Mask')
        self.addControl('shadow_mask_weight_03', label='Weight 3')
        self.addControl('shadow_mask_03', label='Mask')
        self.endLayout()

        self.beginLayout('Specular', collapse=True)
        self.addControl('specular_weight', label='Weight')
        self.addControl('specular_color', label='Color')
        self.addControl('specular_roughness', label='Roughness')
        self.endLayout()

        self.beginLayout('Reflection', collapse=True)
        self.addControl('reflection_weight', label='Weight')
        self.addControl('reflection_additive', label='Additive')
        self.addControl('reflection_color', label='Color')
        self.addControl('reflection_roughness', label='Roughness')
        self.addControl('reflection_look_at_fast', label='Look at Fast Shader')
        self.endLayout()

        self.beginLayout('Fresnel', collapse=True)
        self.addControl('fresnel_reflection', label='Reflections')
        self.addControl('fresnel_specular', label='Specular')
        self.addControl('fresnel_refraction', label='Refraction')
        self.addControl('fresnel_front_reflectivity', label='Front Reflectivity')
        self.addControl('fresnel_falloff', label='Falloff')
        self.endLayout()

        self.beginLayout('Transparency', collapse=True)
        self.addControl('opacity', label='Opacity')
        self.addControl('refraction', label='Refraction')
        self.addControl('ior', label='IOR')
        self.addControl('shadow_opacity', label='Shadow Opacity Mult.')
        self.endLayout()

        self.beginLayout('Masks', collapse=True)
        self.addControl('dmn_mask00', label='dmn_mask00')
        self.addControl('dmn_mask01', label='dmn_mask01')
        self.addControl('dmn_mask02', label='dmn_mask02')
        self.addControl('dmn_mask03', label='dmn_mask03')
        self.addControl('dmn_mask04', label='dmn_mask04')
        self.addControl('dmn_mask05', label='dmn_mask05')
        self.addControl('dmn_mask06', label='dmn_mask06')
        self.addControl('dmn_mask07', label='dmn_mask07')
        self.addControl('dmn_mask08', label='dmn_mask08')
        self.addControl('dmn_mask09', label='dmn_mask09')
        self.addControl('use_light_groups', label='use_light_groups')

        self.endLayout()

        self.beginLayout('Advanced', collapse=True)


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
        self.addControl('toon_as_float', label='As Float')
        self.addControl('self_shadows', label='Self-Shadows')
		
        self.beginLayout('Mid-tone', collapse=True)
        self.addControl('toon_midtone', label='Enable Mid-tone')
        self.addControl('toon_midtone_color', label='Color')
        self.addControl('toon_midtone_coverage', label='Coverage')
        self.addControl('toon_midtone_softness', label='Softness')
        self.endLayout()
		
		
        self.beginLayout('Rim Toon', collapse=True)
        self.addControl('rim_toon_weight', label='Rim Weight')
        self.addControl('rim_toon_bright', label='Bright Color')
        self.addControl('rim_toon_dark', label='Dark Color')
        self.addControl('rim_toon_coverage', label='Coverage')
        self.addControl('rim_toon_softness', label='Softness')
        self.addControl('rim_incidence_falloff', label='Incidence Falloff')
        self.addControl('rim_toon_as_float', label='As Float')
        self.addControl('rim_toon_premult_diffuse', label='Premult Diffuse in Beauty')
        self.endLayout()
		
        self.beginLayout('Beauty Adjustments (for lighting dep)', collapse=True)
        self.addControl('lgt_ambient_color', label='Ambient Color Mult.')
        self.addControl('lgt_ambient_intensity', label='Ambient Mult.')
        self.addControl('lgt_diffuse_color', label='Diffuse Color Mult.')
        self.addControl('lgt_diffuse_intensity', label='Diffuse Mult.')
        self.endLayout()


        self.endLayout()

        self.beginLayout('Lambert', collapse=True)
        self.addControl('lambert_weight', label='Weight')
        self.addControl('lambert_color', label='Color')
        self.addControl('lambert_as_float', label='As Float')
        self.endLayout()

        self.beginLayout('Incidence', collapse=True)
        self.addControl('incidence_weight', label='Weight')
        self.addControl('incidence_color', label='Color')
        self.addControl('incidence_falloff', label='Falloff')
        self.endLayout()

        self.beginLayout('Occlusion', collapse=True)
        self.addControl('occlusion_weight', label='Weight')
        self.addControl('ambient_beauty_mix', label='Ambient Beauty Mix')
        self.addControl('occlusion_black', label='Dark Color')
        self.addControl('occlusion_samples', label='Samples')
        self.addControl('occlusion_spread', label='Spread')
        self.addControl('occlusion_min_dist', label='Min. Dist')
        self.addControl('occlusion_max_dist', label='Max. Dist')
        self.addControl('occlusion_falloff', label='Falloff')
        self.addControl('occlusion_saturate', label='Saturation Factor')		        

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

        self.endLayout()

		
        self.beginLayout('Fast Shader', collapse=True)
        self.addControl('diffuse_fast_bounces', label='Diffuse Fast Bounces')
        self.addControl('diffuse_fast_color', label='Diffuse Fast Color')
        self.addControl('glossy_fast_bounces', label='Glossy Fast Bounces')
        self.addControl('glossy_fast_color', label='Glossy Fast Color')
        self.endLayout()
		
        self.addControl('contour_id', label='ID')
        self.addControl('id_transparency', label='ID Transparency')
        self.endLayout()



        # include/call base class/node attributes
        pm.mel.AEdependNodeTemplate(self.nodeName)

        self.addExtraControls()

        self.endScrollLayout()
