

import os
#import os.path as osp
from os.path import expandvars as expand
from os.path import join

s = os.getenv("DEV_MODE_ENV", "0")
DEV_MODE = eval(s) if s else False

all_expect_pipangai_sites = ["online", "dmn_paris", "dream_wall", "dmn_angouleme"]

class project(object):

    maya_version = 2016
    dir_name = "zomb"
    aliases = ("proj",)

    private_path = join(expand("$ZOMB_PRIVATE_LOC"), "private", "{$DAVOS_USER@user_name}", "{proj.dir_name@project_dir}")
    template_path = expand('$ZOMB_TOOL_PATH/template/').replace("\\", "/")

    damas_root_path = "/{}/".format(dir_name)

    private_path_envars = ("ZOMB_PRIVATE_LOC",)

    libraries = (
        "asset_lib",
        "shot_lib",
        "output_lib",
        "misc_lib",
        )

    child_sections = libraries

    shotgun_class = "zomblib.shotgunengine.ShotgunEngine"
    authenticator_class = ".authtypes.DualAuth"

    sPort = os.getenv("DAMAS_DEV_PORT", "8443") if DEV_MODE else "8443"
    damas_server_addr = "https://62.210.104.42:{}/api".format(sPort)

    editable_file_patterns = ("*.ma", "*.mb", "*.nk", "*.py")#, "*.psd"
    allowed_texture_formats = (".tga", ".jpg", ".exr")
    sg_versions_mandatory = True

    all_sync_sites = ("online", "dmn_paris", "dmn_angouleme", "dream_wall", "pipangai")

    sg_publish_statuses = ("ip", "rev", "omt", "wfa", "fin")

    sg_tasks_settings = {"model_hd":{"upd_status_art":True},
                         "texture":{"upd_status_art":True},
                         "shading":{"upd_status_art":True},
                        }

class damas(object):

    public_path = project.damas_root_path
    private_path = join(project.damas_root_path, "private", "$DAVOS_USER", "{proj.dir_name@project_dir}")

class shot_lib(object):

    entity_class = "davos.core.damtypes.DamShot"

    dir_name = "{shot@library_dir}"
    public_path = join(expand('$ZOMB_SHOT_LOC'), "{proj.dir_name@project_dir}", dir_name)
    private_path = join(project.private_path, dir_name)

    public_path_envars = ('ZOMB_SHOT_PATH',)
    private_path_envars = tuple(("PRIV_" + v) for v in public_path_envars)

    template_path = project.template_path
    template_dir = "shot_template"

    mayaProj_alembic_dir = "$ZOMB_MAYA_PROJECT_PATH/cache/alembic/{sequence}/{name}"

    resource_tree = {
        "{sequence} -> sequence_dir":
            {
            "{name} -> entity_dir":
                {
                 "00_data -> data_dir":
                    {
                     "{name}_sound.wav -> animatic_sound":None,
                     "{name}_animatic.mov -> animatic_capture":None,
                     "{name}_camera.ma -> camera_scene":None,
                     "{name}_camera.atom -> camera_atom":None,
                     "{name}_camera.abc -> camera_abc":None,
                     "{name}_infoSet.txt -> infoSet_file":None,
                    },
                 "{01_previz@step} -> previz_dir":
                    {
                     "export -> previz_export_dir":{},
                     "{name}_previz.ma -> previz_scene":None,
                     "{name}_previz.mov -> previz_capture":None,
                    },
                 "{01_stereo@step} -> stereo_dir":
                    {
                     "{name}_stereo.ma -> stereo_scene":None,
                     "{name}_left.mov -> left_capture":None,
                     "{name}_right.mov -> right_capture":None,
                     "{name}_stereoCam.atom -> stereoCam_anim":None,
                     "{name}_stereoInfo.json -> stereoCam_info":None,
                    },
                "{02_layout@step} -> layout_dir":
                   {
                    "{name}_layout.ma -> layout_scene":None,
                    "{name}_layout.mov -> layout_capture":None,
                    "{name}_layoutInfo.json -> layoutInfo_file":None,
                   },
                "{04_anim@step} -> anim_dir":
                   {
                    "geoCache -> animCache_dir":{},
                    "{name}_anim.ma -> anim_scene":None,
                    "{name}_anim.mov -> anim_capture":None,
                    "{name}_ref.mov -> animRef_movie":None,

                    "{name}_animSplitA.ma -> animSplitA_scene":None,
                    "{name}_animSplitA.mov -> animSplitA_capture":None,

                    "{name}_animSplitB.ma -> animSplitB_scene":None,
                    "{name}_animSplitB.mov -> animSplitB_capture":None,

                    "{name}_animSplitC.ma -> animSplitC_scene":None,
                    "{name}_animSplitC.mov -> animSplitC_capture":None,
                   },
                "{05_charFx@step} -> charFx_dir":
                   {
                    "geoCache -> charFx_cache_dir":{},
                    "{name}_charFx.ma -> charFx_scene":None,
                    "{name}_charFx.mov -> charFx_capture":None,
                   },
                "{06_finalLayout@step} -> finalLayout_dir":
                   {
                    "geoCache -> finalLayout_cache_dir":{},
                    "{name}_finalLayout.ma -> finalLayout_scene":None,
                    "{name}_finalLayout.mov -> finalLayout_movie":None,
                    "{name}_arlequin.mov -> arlequin_movie":None,
                   },
                "{07_fx3d@step} -> fx3d_dir":
                   {
                    "geoCache -> fx3d_geoCache_dir":{},
                    "fxCache -> fx3d_fxCache_dir":{},
                    "texture -> fx3d_texture_dir":{},
                    "{name}_fx3d.ma -> fx3d_scene":None,
                    "{name}_fx3d.mov -> fx3d_capture":None,
                    "{name}_fxPrecomp.mov -> fx3d_precomp_movie":None,
                   },
                "{08_render@step} -> rendering_dir":
                   {
                    "{name}_render.ma -> rendering_scene":None,
                    "{name}_render.mov -> rendering_movie":None,
                    "{name}_precomp.nk -> rendering_comp":None,
                   },
                "{10_compo@step} -> compo_dir":
                   {
                    "{name}_compo.mov -> compo_movie":None,
                    "{name}_left.mov -> compo_left_movie":None,
                    "{name}_right.mov -> compo_right_movie":None,
                    "{name}_compo.nk -> compo_comp":None,
                    "{name}_stereo.nk -> stereo_comp":None,
                    #"lyr_{name} -> compo_frames":None,
                   },
                },
            },
        }

    sg_step_map = {"01_previz":"Previz 3D",
                   "01_stereo":"Stereo",
                   "02_layout":"Layout",
                   "04_anim":"Animation",
                   "05_charFx":"CharFX",
                   "06_finalLayout":"Final Layout",
                   "07_fx3d":"Fx3D",
                   "08_render":"Rendering",
                   "10_compo":"Compositing",
                   }

    resource_settings = {

    "animatic_capture":{"create_sg_version":True,
                        "sg_tasks":("animatic",),
                        "sg_status":"rev",
                        },

    "data_dir":{"default_sync_rules":["all_sites"], },

    #===========================================================================
    # PREVIZ RESOURCES
    #===========================================================================

    "previz_scene":{"outcomes":("previz_capture",),
                    "create_sg_version":True,
                    "sg_uploaded_movie":"previz_capture",
                    "sg_path_to_movie":"previz_capture",
                    "sg_tasks":("previz 3D",),
                    "sg_status":"rev",
                    },
    "previz_dir":{"default_sync_rules":["all_sites"], },

    #===========================================================================
    # STEREO RESOURCES
    #===========================================================================

    "stereo_scene":{"outcomes":("right_capture", "left_capture"),
                    "create_sg_version":True,
                    "sg_uploaded_movie":"right_capture",
                    "sg_path_to_movie":"left_capture",
                    "sg_tasks":("stereo",),
                    "sg_status":"rev",
                    },
    "stereo_dir":{"default_sync_rules":["online", "dmn_paris", "dmn_angouleme"], },

    #===========================================================================
    # LAYOUT RESOURCES
    #===========================================================================

    "layout_scene":{"outcomes":("layout_capture",),
                    "create_sg_version":True,
                    "sg_uploaded_movie":"layout_capture",
                    "sg_path_to_movie":"layout_capture",
                    "sg_tasks":("layout",),
                    "sg_status":"rev",
                    },
    "layout_dir":{"default_sync_rules":["all_sites"], },

    #===========================================================================
    # ANIMATION RESOURCES
    #===========================================================================

    "anim_scene":{"outcomes":("anim_capture",),
                  "create_sg_version":True,
                  "sg_uploaded_movie":"anim_capture",
                  "sg_path_to_movie":"anim_capture",
                  "sg_tasks":("Animation|animation",),
                  },
    "animSplitA_scene":{"outcomes":("animSplitA_capture",),
                        "create_sg_version":True,
                        "sg_uploaded_movie":"animSplitA_capture",
                        "sg_path_to_movie":"animSplitA_capture",
                        "sg_tasks":("Animation|split_A",),
                        "sg_status":"rev",
                        },
    "animSplitB_scene":{"outcomes":("animSplitB_capture",),
                        "create_sg_version":True,
                        "sg_uploaded_movie":"animSplitB_capture",
                        "sg_path_to_movie":"animSplitB_capture",
                        "sg_tasks":("Animation|split_B",),
                        "sg_status":"rev",
                        },
    "animSplitC_scene":{"outcomes":("animSplitC_capture",),
                        "create_sg_version":True,
                        "sg_uploaded_movie":"animSplitC_capture",
                        "sg_path_to_movie":"animSplitC_capture",
                        "sg_tasks":("Animation|split_C",),
                        "sg_status":"rev",
                        },
    "anim_capture":{"default_sync_priority":1, },
    "animSplitA_capture":{"auto_create":True, "default_sync_priority":1},
    "animSplitB_capture":{"auto_create":True, "default_sync_priority":1},
    "animSplitC_capture":{"auto_create":True, "default_sync_priority":1},

    "animRef_movie":{"create_sg_version":True,
                     "sg_uploaded_movie":True,
                     "sg_path_to_movie":True,
                     "sg_tasks":("Animation|reference",),
                     "sg_status":"rev",
                     },
    "anim_dir":{"default_sync_rules":["all_sites"], },

    #===========================================================================
    # CHARFX RESOURCES
    #===========================================================================

    "charFx_scene":{"outcomes":("charFx_capture",),
                    "create_sg_version":True,
                    "sg_uploaded_movie":"charFx_capture",
                    "sg_path_to_movie":"charFx_capture",
                    "sg_tasks":("charfx",),
                    },
    "charFx_capture":{"default_sync_priority":1, },

    "charFx_dir":{"default_sync_rules":["all_sites"], },
    "charFx_cache_dir":{"free_to_publish":True, },

    #===========================================================================
    # FINAL LAYOUT RESOURCES
    #===========================================================================

    "finalLayout_scene":{"create_sg_version":True,
                         "sg_tasks":("Final Layout|final layout",),
                         "dependency_types":
                            {"geoCache_dep":
                                {"dep_public_loc":"finalLayout_cache_dir",
                                 "dep_source_loc":"|mayaProj_alembic_dir",
                                 "checksum":True},
                            }
                         },
    "finalLayout_movie":{"create_sg_version":True,
                         "sg_uploaded_movie":True,
                         "sg_path_to_movie":True,
                         "sg_tasks":("Final Layout|FL_Art",),
                         #"sg_status":"rev",
                         },
    "arlequin_movie":{"create_sg_version":True,
                      "sg_uploaded_movie":True,
                      "sg_path_to_movie":True,
                      "sg_tasks":("Final Layout|Anim_MeshCache",),
                      #"sg_status":"rev",
                      },
    "finalLayout_dir":{"default_sync_rules":["all_sites"], },
    "finalLayout_cache_dir":{"default_sync_rules":["online", "dmn_paris",
                                                   "dream_wall", "dmn_angouleme"], },

    #===========================================================================
    # FX3D RESOURCES
    #===========================================================================

    "fx3d_dir":{"default_sync_rules":["all_sites"], },

    "fx3d_scene":{"outcomes":("fx3d_capture",),
                  "create_sg_version":True,
                  "sg_uploaded_movie":"fx3d_capture",
                  "sg_path_to_movie":"fx3d_capture",
                  "sg_tasks":("Fx3D|fx3D",),
                  "dependency_types":
                        {"geoCache_dep":
                            {"dep_public_loc":"fx3d_geoCache_dir",
                             "dep_source_loc":"|mayaProj_alembic_dir",
                             "checksum":True},
                         "fxCache_dep":
                            {"dep_public_loc":"fx3d_fxCache_dir",
                             "checksum":True},
                         "texture_dep":
                            {"dep_public_loc":"fx3d_texture_dir",
                            "checksum":True},
                            }
                  },
    "fx3d_precomp_movie":{"create_sg_version":True,
                          "sg_uploaded_movie":True,
                          "sg_path_to_movie":True,
                          "sg_tasks":("Fx3D|fx_precomp",),
                          #"sg_status":"rev",
                          },

    "fx3d_geoCache_dir":{"free_to_publish":False,
                         "default_sync_rules":["no_sync"], },
    "fx3d_fxCache_dir":{"free_to_publish":True,
                      "default_sync_rules":["online", "dmn_paris", "dmn_angouleme"], },
    "fx3d_texture_dir":{"free_to_publish":True,
                        "default_sync_rules":["online", "dmn_paris", "dmn_angouleme"], },

    #===========================================================================
    # RENDERING RESOURCES
    #===========================================================================

    "rendering_dir":{"default_sync_rules":["online", "dmn_paris", "dmn_angouleme"],
                     "free_to_publish":True, },

    "rendering_scene":{"create_sg_version":True,
                       "sg_tasks":("Rendering|rendering",),
                       },
    "rendering_comp":{"outcomes":("rendering_movie",),
                      "create_sg_version":True,
                      "sg_uploaded_movie":"rendering_movie",
                      "sg_path_to_movie":"rendering_movie",
                      "sg_tasks":("Rendering|rendering",),
                      },
#    "rendering_movie":{"create_sg_version":True,
#                       "sg_uploaded_movie":True,
#                       "sg_path_to_movie":True,
#                       "sg_tasks":("Rendering|rendering",),
#                       #"sg_status":"rev",
#                       },

    #===========================================================================
    # COMPOSITING RESOURCES
    #===========================================================================

    "compo_dir":{"default_sync_rules":["online", "dmn_paris", "dmn_angouleme"],
                 "free_to_publish":True, },

    "compo_comp":{"outcomes":("compo_movie",),
                  "create_sg_version":True,
                  "sg_uploaded_movie":"compo_movie",
                  "sg_path_to_movie":"compo_movie",
                  "sg_tasks":("Compositing|compositing", "Compositing|compoDEF"),
                  },

    "stereo_comp":{"outcomes":("compo_right_movie", "compo_left_movie"),
                  "create_sg_version":True,
                  "sg_uploaded_movie":"compo_right_movie",
                  "sg_path_to_movie":"compo_left_movie",
                  "sg_tasks":("Compositing|compo_stereo",),
                  },

    #"compo_frames":{"default_sync_priority":1, },
    "compo_movie":{"default_sync_priority":1, },
    "compo_left_movie":{"default_sync_priority":1, },
    "compo_right_movie":{"default_sync_priority":1, },
    }

class output_lib(object):

    dir_name = "{output@library_dir}"
    public_path = join(expand('$ZOMB_OUTPUT_LOC'), "{proj.dir_name@project_dir}", dir_name)
    private_path = join(project.private_path, dir_name)

    public_path_envars = ('ZOMB_OUTPUT_PATH',)
    private_path_envars = tuple(("PRIV_" + v) for v in public_path_envars)

    resource_tree = {
    "{sequence} -> sequence_dir":
        {
        "{name} -> entity_dir":{}
         }
    }

    free_to_publish = True

class misc_lib(object):

    dir_name = "{misc@library_dir}"
    public_path = join(expand('$ZOMB_MISC_LOC'), "{proj.dir_name@project_dir}", dir_name)
    private_path = join(project.private_path, dir_name)

    public_path_envars = ('ZOMB_MISC_PATH',)
    private_path_envars = tuple(("PRIV_" + v) for v in public_path_envars)

    free_to_publish = True

class asset_lib(object):

    dir_name = "{asset@library_dir}"
    public_path = join(expand('$ZOMB_ASSET_LOC'), "{proj.dir_name@project_dir}", dir_name)
    private_path = join(project.private_path, dir_name)

    public_path_envars = ('ZOMB_ASSET_PATH', 'ZOMB_TEXTURE_PATH', 'ZOMB_GEOMETRY_PATH')
    private_path_envars = tuple(("PRIV_" + v) for v in public_path_envars)

    asset_types = ("camera",
                   "character3d",
                   "character2d",
                   "prop3d",
                   "vehicle3d",
                   "set3d",
                   "environment3d",
                   "fx_previz",
                   "crowd_previz",
                   "vegetation3d",
                   )

    child_sections = asset_types

    entity_dir = "{assetType}/{name}"

    resource_settings = {
    "modeling_scene":{"create_sg_version":True,
                      "sg_steps":("Model HD", "Surfacing"),
                      },

    "master_scene":{"create_sg_version":True,
                    "sg_steps":("Model HD", "Rigging", "Surfacing"),
                    },

    "previz_scene":{"create_sg_version":True,
                    "sg_steps":("Model Previz",),
                    },
    "previz_ref":{"create_sg_version":True,
                  "sg_tasks":("Rig_Previz",),
                  "sg_status":"rev",
                  },

    "anim_scene":{"create_sg_version":True,
                  "sg_steps":("Rigging",),
                  },
    "animMaster_scene":{"create_sg_version":True,
                        "sg_steps":("Rigging",),
                        },
    "anim_ref":{"create_sg_version":True,
                "sg_tasks":("Rig_Anim",),
                "sg_status":"rev",
                },

    "render_scene":{"create_sg_version":True,
                    "sg_steps":("Surfacing",),
                    },
    "render_ref":{"create_sg_version":True,
                  "sg_tasks":("Rig_Render",),
                  "sg_status":"rev",
                  },
    }

    dependency_types = {
    "texture_dep":{"dep_public_loc":"texture_dir",
                   "dep_source_loc":"private|texture_dir",
                   "checksum":True, "env_var":"ZOMB_TEXTURE_PATH"},
    #"geometry_dep":{"dep_public_loc":"geometry_dir", "checksum":True, "env_var":"ZOMB_GEOMETRY_PATH"},
    }

class camera(object):

    entity_class = "davos.core.damtypes.DamAsset"

    prefix = "cam"
    aliases = (prefix, "Camera",)
    assetType = prefix
    template_dir = "asset_cam"

    public_path = join(asset_lib.public_path, "{assetType}")
    private_path = join(asset_lib.private_path, "{assetType}")
    template_path = project.template_path

    resource_tree = {
    "{name} -> entity_dir":
        {
        "{name}.ma -> scene":None,
        },
    }

class character3d(object):

    entity_class = "davos.core.damtypes.DamAsset"

    prefix = "chr"
    sg_type = "Character 3D"
    aliases = (prefix, sg_type,)
    assetType = prefix
    template_dir = "asset_chr"

    public_path = join(asset_lib.public_path, "{assetType}")
    private_path = join(asset_lib.private_path, "{assetType}")
    template_path = project.template_path

    resource_tree = {
    "{name} -> entity_dir":
        {
        "ref -> ref_dir":
            {
            "{name}_previzRef.mb -> previz_ref":None,
            "{name}_animRef.mb -> anim_ref":None,
            "{name}_renderRef.mb -> render_ref":None,
            },
        "review -> review_dir":
            {
            "{name}_anim.mov -> anim_review":None,
            "{name}_modeling.mov -> modeling_review":None,
            "{name}_previz.mov -> previz_review":None,
            "{name}_render.mov -> render_review":None,
            },
        "script -> script_dir":
            {
             "{name}_blendShape.bsd -> blendShape_bsd":None
             },
        "texture -> texture_dir":{},

        "{name}_anim.ma -> anim_scene":None,
        "{name}_modeling.ma -> modeling_scene":None,
        "{name}_previz.ma -> previz_scene":None,
        "{name}_render.ma -> render_scene":None,
        "{name}_blendShape.ma -> blendShape_scene":None,
        "{name}_animMaster.ma -> animMaster_scene":None,

        #"{name}_preview.jpg -> preview_image":None,
        },
    }

    resource_settings = {
    "texture_dir":{"per_ext_sync_rules":{".jpg":["all_sites"],
                                         ".psd":["online", "dmn_paris", "dmn_angouleme"]},
                   },
    }
    resource_settings.update(asset_lib.resource_settings)

    dependency_types = asset_lib.dependency_types

class character2d(object):

    entity_class = "davos.core.damtypes.DamAsset"

    prefix = "c2d"
    sg_type = "Character 2D"
    aliases = (prefix, sg_type,)
    assetType = prefix
    template_dir = "asset_c2d"

    public_path = join(asset_lib.public_path, "{assetType}")
    private_path = join(asset_lib.private_path, "{assetType}")
    template_path = project.template_path

    resource_tree = {
    "{name} -> entity_dir":
        {
        "ref -> ref_dir":
            {
            "{name}_previzRef.mb -> previz_ref":None,
            "{name}_animRef.mb -> anim_ref":None,
            "{name}_renderRef.mb -> render_ref":None,
            },
        "review -> review_dir":
            {
            "{name}_anim.mov -> anim_review":None,
            "{name}_modeling.mov -> modeling_review":None,
            "{name}_previz.mov -> previz_review":None,
            "{name}_render.mov -> render_review":None,
            },
        "texture -> texture_dir":{},

        "{name}_anim.ma -> anim_scene":None,
        "{name}_modeling.ma -> modeling_scene":None,
        "{name}_previz.ma -> previz_scene":None,
        "{name}_render.ma -> render_scene":None,
        },
    }

    resource_settings = asset_lib.resource_settings
    dependency_types = asset_lib.dependency_types

class prop3d(object):

    entity_class = "davos.core.damtypes.DamAsset"

    prefix = "prp"
    sg_type = "Prop 3D"
    aliases = (prefix, sg_type,)
    assetType = prefix
    template_dir = "asset_vhlPrp"

    public_path = join(asset_lib.public_path, "{assetType}")
    private_path = join(asset_lib.private_path, "{assetType}")
    template_path = project.template_path

    resource_tree = {
    "{name} -> entity_dir":
        {
        "ref -> ref_dir":
            {
            "{name}_previzRef.mb -> previz_ref":None,
            "{name}_animRef.mb -> anim_ref":None,
            "{name}_renderRef.mb -> render_ref":None,
            },
        "review -> review_dir":
            {
            "{name}_anim.mov -> anim_review":None,
            "{name}_modeling.mov -> modeling_review":None,
            "{name}_previz.mov -> previz_review":None,
            "{name}_render.mov -> render_review":None,
            },
        "texture -> texture_dir":{},

        "{name}_anim.ma -> anim_scene":None,
        "{name}_modeling.ma -> modeling_scene":None,
        "{name}_previz.ma -> previz_scene":None,
        "{name}_render.ma -> render_scene":None,
        },
    }

    resource_settings = {
    "texture_dir":{"per_ext_sync_rules":{".jpg":["all_sites"],
                                         ".psd":["online", "dmn_paris", "dream_wall"]},
                   },
    }
    resource_settings.update(asset_lib.resource_settings)

    dependency_types = asset_lib.dependency_types

class vehicle3d(prop3d):

    entity_class = "davos.core.damtypes.DamAsset"

    prefix = "vhl"
    sg_type = "Vehicle 3D"
    aliases = (prefix, sg_type,)
    assetType = prefix

    dependency_types = asset_lib.dependency_types

class crowd_previz(object):

    entity_class = "davos.core.damtypes.DamAsset"

    prefix = "cwp"
    sg_type = "Crowd Previz"
    aliases = (prefix, sg_type,)
    assetType = prefix
    template_dir = "asset_fxpCwp"

    public_path = join(asset_lib.public_path, "{assetType}")
    private_path = join(asset_lib.private_path, "{assetType}")
    template_path = project.template_path

    resource_tree = {
    "{name} -> entity_dir":
        {
        "ref -> ref_dir":
            {
            "{name}_previzRef.mb -> previz_ref":None,
            "{name}_animRef.mb -> anim_ref":None,
            "{name}_renderRef.mb -> render_ref":None,
            },
        "texture -> texture_dir":{},

        "{name}_anim.ma -> anim_scene":None,
        "{name}_previz.ma -> previz_scene":None,
        "{name}_render.ma -> render_scene":None,
        },
    }

    resource_settings = asset_lib.resource_settings
    resource_settings.update({
    "texture_dir":{"per_ext_sync_rules":{".jpg":["all_sites"],
                                         ".psd":["online", "dmn_paris", "dmn_angouleme"]},
                   }, })

    dependency_types = asset_lib.dependency_types

class fx_previz(crowd_previz):

    entity_class = "davos.core.damtypes.DamAsset"

    prefix = "fxp"
    sg_type = "FX"
    aliases = (prefix, sg_type,)
    assetType = prefix

    dependency_types = asset_lib.dependency_types

class set3d(object):

    entity_class = "davos.core.damtypes.DamAsset"

    prefix = "set"
    sg_type = "Set 3D"
    aliases = (prefix, sg_type,)
    assetType = prefix
    template_dir = "asset_envSetVeg"

    public_path = join(asset_lib.public_path, "{assetType}")
    private_path = join(asset_lib.private_path, "{assetType}")
    template_path = project.template_path

    resource_tree = {
    "{name} -> entity_dir":
        {
        "ref -> ref_dir":
            {
            "{name}_previzRef.mb -> previz_ref":None,
            "{name}_animRef.mb -> anim_ref":None,
            "{name}_renderRef.mb -> render_ref":None,
            "{name}_animRef.json -> animRef_json":None,
            },
        "review -> review_dir":
            {
            "{name}_previz.mov -> previz_review":None,
            "{name}_master.mov -> master_review":None,
            },
        "texture -> texture_dir":{},
        "geometry -> geometry_dir":{},

        "{name}_previz.ma -> previz_scene":None,
        "{name}_master.ma -> master_scene":None,
        },
    }

    resource_settings = {
    "texture_dir":{"per_ext_sync_rules":{".jpg":["all_sites"], ".tga":["all_sites"],
                                         ".psd":["online", "dmn_paris", "dream_wall"]},
                   "default_sync_rules":["online", "dmn_paris", "dream_wall", "dmn_angouleme"],
                   },
    "geometry_dir":{"free_to_publish":True, },
    }
    resource_settings.update(asset_lib.resource_settings)

    dependency_types = asset_lib.dependency_types

class environment3d(set3d):

    entity_class = "davos.core.damtypes.DamAsset"

    prefix = "env"
    sg_type = "Environment"
    aliases = (prefix, sg_type,)
    assetType = prefix

    dependency_types = asset_lib.dependency_types

class vegetation3d(set3d):

    entity_class = "davos.core.damtypes.DamAsset"

    prefix = "veg"
    sg_type = "Veg 3D"
    aliases = (prefix, sg_type,)
    assetType = prefix

    dependency_types = asset_lib.dependency_types

