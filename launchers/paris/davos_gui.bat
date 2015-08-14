SET "ENGINE=%~dp0..\..\scripts\davos_gui.py"
call :resolve "%ENGINE%"

"C:\Python27\python.exe" "%~dp0setup_env_tools.py" True True "C:\Python27\python.exe" -i %_RETURN%
pause

:resolve
	set "_RETURN=%~f1"
	goto :EOF