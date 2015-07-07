call "%~dp0\common_env.bat"

SET "ENGINE=%~dp0..\..\python\shotgun_zombie_engine\shotgun_engine.py"
call :resolve "%ENGINE%"

REM call "C:\Python27\python.exe %_RETURN% %*"
call "C:\Python27\python.exe" %_RETURN% %*

pause

:resolve
	set "_RETURN=%~f1"
	goto :EOF