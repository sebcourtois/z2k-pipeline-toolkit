+ zombie any ./zombie
PYTHONPATH+:=python


+ MAYAVERSION:2016 PLATFORM:win64 Oscar	any ./Toonkit_module/Maya2016
PATH+:=bin
MAYA_CUSTOM_TEMPLATE_PATH+:=AETemplates


+ mtoa any ./solidangle/mtoadeploy/2016
PATH +:= bin 
MAYA_RENDER_DESC_PATH+:= .

+ MAYAVERSION:2016 PLATFORM:win64 third_party any ./third_party
PYTHONPATH+:=python
plug-ins: plug-ins/2016_win

+ openVdb any ./openVdbForMaya

+ MAYAVERSION:2016 PLATFORM:win64 soup any ./soup
plug-ins: plug-ins/maya2016_win
MAYA_PLUG_IN_PATH +:= plug-ins/pyExpression

+ MAYAVERSION:2016 PLATFORM:win64 wobble 0.9.6 ./wobble/2016