ECHO off

SET "PYDIR=%~dp0..\..\python"
call :resolve "%PYDIR%"

SET PYTHONPATH=%PYTHONPATH%;%_RETURN%

SET ZOMBI_TOOL_PATH=\\Diskstation\z2k\05_3D\zombillenium\tool
SET ZOMBI_ASSET_DIR=\\Diskstation\z2k\05_3D\zombillenium\asset
SET ZOMBI_SHOT_DIR=\\Diskstation\z2k\05_3D\zombillenium\shot
SET ZOMBI_OUTPUT_DIR=\\Diskstation\z2k\05_3D\zombillenium\output

:resolve
    set "_RETURN=%~f1"
    goto :EOF