SET "ENGINE=%~dp0..\..\python\zombie\shotgunengine.py"
call :resolve "%ENGINE%"

"C:\Python27\python.exe" "%~dp0setup_env_tools.py" True False "C:\Python27\python.exe" %_RETURN% %*
pause
:resolve
	set "_RETURN=%~f1"
	goto :EOF