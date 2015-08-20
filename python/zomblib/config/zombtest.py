
import os.path as osp

from . import zombillenium as zombase

class project(zombase.project):

    dir_name = "zombtest"

    public_path = '//Diskstation/Projects/{}/'.format(dir_name)
    private_path = '//Diskstation/Projects/private/${{DAVOS_USER}}/{}/'.format(dir_name)
    damas_root_path = "{}/".format(dir_name)


class asset_lib(zombase.asset_lib):

    dir_name = "asset"

    public_path = project.public_path + dir_name
    private_path = project.private_path + dir_name

class camera(zombase.camera):

    public_path = osp.join(asset_lib.public_path, "{assetType}")
    private_path = osp.join(asset_lib.private_path, "{assetType}")

class character3d(zombase.character3d):

    public_path = osp.join(asset_lib.public_path, "{assetType}")
    private_path = osp.join(asset_lib.private_path, "{assetType}")

class prop3d(zombase.prop3d):

    public_path = osp.join(asset_lib.public_path, "{assetType}")
    private_path = osp.join(asset_lib.private_path, "{assetType}")

class vehicle3d(zombase.vehicle3d):
    pass

class set3d(zombase.set3d):

    public_path = osp.join(asset_lib.public_path, "{assetType}")
    private_path = osp.join(asset_lib.private_path, "{assetType}")

class environment3d(zombase.environment3d):
    pass

class fx_previz(zombase.fx_previz):

    public_path = osp.join(asset_lib.public_path, "{assetType}")
    private_path = osp.join(asset_lib.private_path, "{assetType}")


class shot_lib(zombase.shot_lib):

    dir_name = "shot"

    public_path = project.public_path + dir_name
    private_path = project.private_path + dir_name


class output_lib(zombase.output_lib):

    dir_name = "output"

    public_path = project.public_path + dir_name
    private_path = project.private_path + dir_name




