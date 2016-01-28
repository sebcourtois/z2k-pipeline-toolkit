
#import os.path as osp

from zomblib.config import zombillenium as zomb

class project(zomb.project):
    dir_name = "zombtest"
    damas_root_path = "/{}/".format(dir_name)
    sg_versions_mandatory = False

class asset_lib(zomb.asset_lib):
    pass

class camera(zomb.camera):
    pass

class character3d(zomb.character3d):
    pass

class character2d(zomb.character2d):
    pass

class prop3d(zomb.prop3d):
    pass

class vehicle3d(zomb.vehicle3d):
    pass

class set3d(zomb.set3d):
    pass

class environment3d(zomb.environment3d):
    pass

class fx_previz(zomb.fx_previz):
    pass

class crowd_previz(zomb.crowd_previz):
    pass

class shot_lib(zomb.shot_lib):
    pass

class output_lib(zomb.output_lib):
    pass

class misc_lib(zomb.misc_lib):
    pass

