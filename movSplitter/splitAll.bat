ECHO Off
REM "Arg1 : Source_video_path path[, Arg2 : out_filename][, Arg3 : edl_path][, Arg4 : dest_folder]"

SET FFMPEG="%~dp0ffmpeg\bin\ffmpeg.exe"

For %%A in ("%~dp0") do (
	SET CURFOLDER=%%~dpA
)

REM "Set variables"
if [%1]==[] GOTO ARGSERRORLBL

SET OUT=%1
For %%A in ("%1") do (
	SET INFOLDER=%%~dpA
    Set INNAME=%%~nxA
)

if [%2]==[] (SET OUTNAME=%INNAME:.mov=_split.mov%) else (SET OUTNAME=%2)
if [%3]==[] (SET EDL=%OUT:.mov=.edl%) else (SET EDL=%3)
if [%4]==[] (SET OUTFOLDER=%INFOLDER%) else (SET OUTFOLDER=%4)

SET OUTPATH=%OUTFOLDER%%OUTNAME%

ECHO "-------- PYTHON CALL ---------"
SET "CMDLINE=%CURFOLDER%splitter.py %1"
SET "CMDLINE=%CMDLINE% %EDL%"

set /p FILTER=Sequence Filter:
if NOT [%FILTER%]==[] (SET "CMDLINE=%CMDLINE% %FILTER%")

call C:\Python27\python.exe %CMDLINE%
pause