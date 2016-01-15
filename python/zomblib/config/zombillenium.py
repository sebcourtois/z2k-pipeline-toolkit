

import os
#import os.path as osp
from os.path import expandvars as expand
from os.path import join

s = os.getenv("DEV_MODE_ENV", "0")
DEV_MODE = eval(s) if s else False

class project(object):

    maya_version = 2016
    dir_name = "zomb"
    aliases = ("proj",)

    #public_path = '//ZOMBIWALK/z2k/05_3D/{}/'.format(dir_name)
    private_path = join(expand('$ZOMB_PRIVATE_LOC'), "private", "$DAVOS_USER", "{proj.dir_name}")
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

    if DEV_MODE:
        damas_server_addr = "https://62.210.104.42:8444/api"
    else:
        damas_server_addr = "https://62.210.104.42:8443/api"

    editable_file_patterns = ("*.ma", "*.mb", "*.nk", "*.py")#, "*.psd"
    allowed_texture_formats = (".tga", ".jpg", ".exr")
    sg_versions_mandatory = True

    all_sync_sites = ("dmn_paris", "dmn_angouleme", "online", "dream_wall", "pipangai")

class shot_lib(object):

    entity_class = "davos.core.damtypes.DamShot"

    dir_name = "shot"
    public_path = join(expand('$ZOMB_SHOT_LOC'), "{proj.dir_name}", dir_name)
    private_path = join(project.private_path, dir_name)

    public_path_envars = ('ZOMB_SHOT_PATH',)
    private_path_envars = tuple(("PRIV_" + v) for v in public_path_envars)

    template_path = project.template_path
    template_dir = "shot_template"

    resource_tree = {
        "{sequence}":
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
                 "{step:01_previz} -> previz_dir":
                    {
                     "export -> previz_export_dir":{},
                     "{name}_previz.ma -> previz_scene":None,
                     "{name}_previz.mov -> previz_capture":None,
                    },
                "{step:02_layout} -> layout_dir":
                   {
                    "{name}_layout.ma -> layout_scene":None,
                    "{name}_layout.mov -> layout_capture":None,
                   },
                },
            },
        }

    resources_settings = {
    "previz_scene":{"outcomes":("previz_capture",),
                    "create_sg_version":True,
                    "sg_tasks":("previz 3D",),
                    "upload_to_sg":"previz_capture"
                    },
    "layout_scene":{"outcomes":("layout_capture",),
                    "create_sg_version":True,
                    "sg_tasks":("layout",),
                    "upload_to_sg":"layout_capture"
                    },
    "animatic_capture":{"create_sg_version":True,
                        "sg_tasks":("animatic",),
                        },
    "data_dir":{"default_sync_rules":"all_sites",
                },
    "previz_dir":{"default_sync_rules":"all_sites",
                  },
    "layout_dir":{"default_sync_rules":"all_sites",
                  },
    }


class output_lib(object):

    dir_name = "output"
    public_path = join(expand('$ZOMB_OUTPUT_LOC'), "{proj.dir_name}", dir_name)
    private_path = join(project.private_path, dir_name)

    public_path_envars = ('ZOMB_OUTPUT_PATH',)
    private_path_envars = tuple(("PRIV_" + v) for v in public_path_envars)


class misc_lib(object):

    dir_name = "misc"
    public_path = join(expand('$ZOMB_MISC_LOC'), "{proj.dir_name}", dir_name)
    private_path = join(project.private_path, dir_name)

    public_path_envars = ('ZOMB_MISC_PATH',)
    private_path_envars = tuple(("PRIV_" + v) for v in public_path_envars)

    free_publish = True

class asset_lib(object):

    dir_name = "asset"
    public_path = join(expand('$ZOMB_ASSET_LOC'), "{proj.dir_name}", dir_name)
    private_path = join(project.private_path, dir_name)

    public_path_envars = ('ZOMB_ASSET_PATH', 'ZOMB_TEXTURE_PATH')
    private_path_envars = tuple(("PRIV_" + v) for v in public_path_envars)

    asset_types = (
        "camera",
        "character3d",
        "character2d",
        "prop3d",
        "vehicle3d",
        "set3d",
        "environment3d",
        "fx_previz",
        )

    child_sections = asset_types

    entity_dir = "{assetType}/{name}"

    resources_settings = {
    "modeling_scene":{"create_sg_version":True,
                      "sg_steps":("Model HD", "Surfacing"), },

    "master_scene":{"create_sg_version":True,
                    "sg_steps":("Model HD", "Rigging", "Surfacing"), },

    "previz_scene":{"create_sg_version":True,
                    "sg_steps":("Model Previz",), },
    "previz_ref":{"create_sg_version":True,
                  "sg_tasks":("Rig_Previz",), },

    "anim_scene":{"create_sg_version":True,
                  "sg_steps":("Rigging",), },
    "anim_ref":{"create_sg_version":True,
                "sg_tasks":("Rig_Anim",), },

    "render_scene":{"create_sg_version":True,
                    "sg_steps":("Surfacing",), },
    "render_ref":{"create_sg_version":True,
                  "sg_tasks":("Rig_Render",), },
    }

    dependency_types = {
    "texture_dep":{"location":"texture_dir", "checksum":True, "env_var":"ZOMB_TEXTURE_PATH"}
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

class charbase(object):

    entity_class = "davos.core.damtypes.DamAsset"

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
        "{name}_blendShape.ma -> blendShape_scene":None

        #"{name}_preview.jpg -> preview_image":None,
        },
    }

    resources_settings = asset_lib.resources_settings
    dependency_types = asset_lib.dependency_types

class character3d(charbase):

    prefix = "chr"
    aliases = (prefix, "Character 3D",)
    assetType = prefix

class character2d(charbase):

    prefix = "c2d"
    aliases = (prefix, "Character 2D",)
    assetType = prefix

class prop3d(object):

    entity_class = "davos.core.damtypes.DamAsset"

    prefix = "prp"
    aliases = (prefix, "Prop 3D",)
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

    resources_settings = asset_lib.resources_settings
    dependency_types = asset_lib.dependency_types

class vehicle3d(prop3d):

    entity_class = "davos.core.damtypes.DamAsset"

    prefix = "vhl"
    aliases = (prefix, "Vehicle 3D",)
    assetType = prefix

    dependency_types = asset_lib.dependency_types

class fx_previz(prop3d):

    entity_class = "davos.core.damtypes.DamAsset"

    prefix = "fxp"
    aliases = (prefix, "FX")
    assetType = prefix

    dependency_types = asset_lib.dependency_types

class set3d(object):

    entity_class = "davos.core.damtypes.DamAsset"

    prefix = "set"
    aliases = (prefix, "Set 3D",)
    assetType = prefix
    template_dir = "asset_envSet"

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
            #"{name}_masterRef.mb -> master_ref":None,
            },
        "review -> review_dir":
            {
            "{name}_previz.mov -> previz_review":None,
            "{name}_master.mov -> master_review":None,
            },
        "texture -> texture_dir":{},

        "{name}_previz.ma -> previz_scene":None,
        "{name}_master.ma -> master_scene":None,
        },
    }

    resources_settings = asset_lib.resources_settings
    dependency_types = asset_lib.dependency_types

class environment3d(set3d):

    entity_class = "davos.core.damtypes.DamAsset"

    prefix = "env"
    aliases = (prefix, "Environment",)
    assetType = prefix

    dependency_types = asset_lib.dependency_types



