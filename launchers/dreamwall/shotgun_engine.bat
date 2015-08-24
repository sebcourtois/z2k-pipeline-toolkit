SET "ENGINE=%~dp0\..\..\python\zomblib\shotgunengine.py"
call :resolve "%ENGINE%"

"C:\Python27\python.exe" "%~dp0\setup_env_tools.py" launch "C:\Python27\python.exe" %_RETURN% %*
pause

:resolve
    set "_RETURN=%~f1"
    goto :EOF