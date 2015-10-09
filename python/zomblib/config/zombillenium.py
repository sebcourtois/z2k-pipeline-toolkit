

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
        )

    child_sections = libraries

    shotgun_class = "zomblib.shotgunengine.ShotgunEngine"
    authenticator_class = ".authtypes.DualAuth"

    if DEV_MODE:
        damas_server_addr = "https://62.210.104.42:8444/api"
    else:
        damas_server_addr = "https://62.210.104.42:8443/api"

    editable_files = ("*.ma", "*.mb", "*.psd", "*.nk", "*.py")


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
                    },
                 "{step=01_previz} -> previz_dir":
                    {
                     "export -> previz_export_dir":{},
                     "{name}_previz.ma -> previz_scene":None,
                     "{name}_previz.mov -> previz_capture":None,
                    },
                 "{step=02_layout} -> layout_dir":
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
#    "previz_capture":{"editable":False,
#                      },
    }


class output_lib(object):

    dir_name = "output"
    public_path = join(expand('$ZOMB_OUTPUT_LOC'), "{proj.dir_name}", dir_name)
    private_path = join(project.private_path, dir_name)

    public_path_envars = ('ZOMB_OUTPUT_PATH',)
    private_path_envars = tuple(("PRIV_" + v) for v in public_path_envars)


class asset_lib(object):

    dir_name = "asset"
    public_path = join(expand('$ZOMB_ASSET_LOC'), "{proj.dir_name}", dir_name)
    private_path = join(project.private_path, dir_name)

    public_path_envars = ('ZOMB_ASSET_PATH', 'ZOMB_TEXTURE_PATH')
    private_path_envars = tuple(("PRIV_" + v) for v in public_path_envars)

    asset_types = (
        "camera",
        "character3d",
        "prop3d",
        "vehicle3d",
        "set3d",
        "environment3d",
        "fx_previz",
        )

    child_sections = asset_types

    entity_dir = "{assetType}/{name}"

class camera(object):

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
            "{name}_animRef.mb -> anim_ref":None,
            "{name}_modelingRef.mb-> modeling_ref":None,
            "{name}_previzRef.mb-> previz_ref":None,
            "{name}_renderRef.mb-> render_ref":None,
            },
        "review -> review_dir":{},
        "script -> script_dir":{},
        "texture -> texture_dir":{},
        "{name}_anim.ma -> anim_scene":None,
        "{name}_modeling.ma -> modeling_scene":None,
        "{name}_previz.ma -> previz_scene":None,
        "{name}_render.ma -> render_scene":None,

        #"{name}_preview.jpg -> preview_image":None,
        },
    }

    resources_settings = {
    "previz_scene":{
                    "create_sg_version":True,
                    "sg_step":"Model Previz",
                    #"upload_to_sg":"preview_image"
                    },
    }

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
            "{name}_animRef.mb -> anim_ref":None,
            "{name}_modelingRef.mb -> modeling_ref":None,
            "{name}_previzRef.mb -> previz_ref":None,
            "{name}_renderRef.mb -> render_ref":None,
            },
        "review -> review_dir":{},
        #"script -> script_dir":{},
        "texture -> texture_dir":{},
        "{name}_anim.ma -> anim_scene":None,
        "{name}_modeling.ma -> modeling_scene":None,
        "{name}_previz.ma -> previz_scene":None,
        "{name}_render.ma -> render_scene":None,
        },
    }

class vehicle3d(prop3d):

    entity_class = "davos.core.damtypes.DamAsset"

    prefix = "vhl"
    aliases = (prefix, "Vehicle 3D",)
    assetType = prefix

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
            "{name}_previzRef.mb-> previz_ref":None,
            "{name}_masterRef.mb-> master_ref":None,
            },
        "review -> review_dir":{},
        #"script -> script_dir":{},
        "texture -> texture_dir":{},
        "{name}_previz.ma -> previz_scene":None,
        "{name}_master.ma -> master_scene":None,
        },
    }

class environment3d(set3d):

    entity_class = "davos.core.damtypes.DamAsset"

    prefix = "env"
    aliases = (prefix, "Env 3D",)
    assetType = prefix

class fx_previz(object):

    entity_class = "davos.core.damtypes.DamAsset"

    prefix = "fxp"
    aliases = (prefix,)
    assetType = prefix

    public_path = join(asset_lib.public_path, "{assetType}")
    private_path = join(asset_lib.private_path, "{assetType}")



