
#import os.path as osp

from . import zombillenium as zomb
reload(zomb)

class project(zomb.project):
    damas_root_path = "/zombtest/"

class asset_lib(zomb.asset_lib):
    pass

class camera(zomb.camera):
    pass

class character3d(zomb.character3d):
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

class shot_lib(zomb.shot_lib):
    pass

class output_lib(zomb.output_lib):
    pass




