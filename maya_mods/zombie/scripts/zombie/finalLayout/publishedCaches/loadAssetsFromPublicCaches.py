
from dminutes.maya_scene_operations import loadRenderRefsFromCaches
from davos_maya.tool.general import infosFromScene

loadRenderRefsFromCaches(infosFromScene().get("dam_entity"), "public")