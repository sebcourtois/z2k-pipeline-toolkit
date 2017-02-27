import nuke
def nodePresetsStartup():
  nuke.setUserPreset("Expression", "normalize_depth", {'expr0': 'depth.Z==0?1000:1/depth.Z'})
  nuke.setUserPreset("Expression", "override_inf_depth_val", {'expr0': 'r==0?.000001:r'})
  nuke.setUserPreset("Expression", "bad_pixel_fix", {'expr2': 'g>.99 ? (b(x,y+1) + b(x,y-1) + b(x-1,y) + b(x+1,y) )/4 : b', 'expr0': 'g>.99 ? (r(x,y+1) + r(x,y-1) + r(x-1,y) + r(x+1,y) )/4 : r', 'expr1': 'g>.99 ? (g(x,y+1) + g(x,y-1) + g(x-1,y) + g(x+1,y) )/4 : g', 'selected': 'true'})
  nuke.setUserPreset("Expression", "uv_map", {'expr2': '0', 'expr0': '(x+.5) / w', 'expr1': '(y+.5) / h', 'selected': 'true'})
  nuke.setUserPreset("Expression", "convert_depth_to_point", {'expr0': '(x/w-.5)*blue', 'expr1': '(y/h-.5)*blue', 'selected': 'true'})
