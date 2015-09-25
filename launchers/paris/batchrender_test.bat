set MAYA_RENDER_DESC_PATH=\\ZOMBIWALK\Projects\zomb\tool\z2k-pipeline-toolkit\maya_mods\solidangle\mtoadeploy\2016
set DAVOS_USER=jeanmarcl

set render="C:\Program Files\Autodesk\Maya2016\bin\Render.exe"
set scene=\\ZOMBIWALK\Projects\private\jeanmarcl\zomb\asset\chr\chr_aurelien_polo\chr_aurelien_polo_render-v001-temp.0007_aube_01.mb
"C:\Python27\python.exe" "%~dp0\setup_env_tools.py" launch %render% -r arnold %scene%
pause