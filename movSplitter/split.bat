ECHO Off
REM "Arg1 : Source_video_path path, Arg2 : StartTC, Arg3 : EndTC[, Arg4 : out_filename][, Arg5 : dest_folder]"

SET FFMPEG="%~dp0ffmpeg\bin\ffmpeg.exe"

REM "Set variables"
if [%1]==[] GOTO ARGSERRORLBL

SET OUT=%1
For %%A in ("%1") do (
	SET INFOLDER=%%~dpA
    Set INNAME=%%~nxA
)

if [%2]==[] (SET STARTTC="00:00:00") else (SET STARTTC=%2)
if [%3]==[] (SET ENDTC="00:00:08.208") else (SET ENDTC=%3)
if [%4]==[] (SET OUTNAME=%INNAME:.mov=_split.mov%) else (SET OUTNAME=%4)
if [%5]==[] (SET OUTFOLDER=%INFOLDER%) else SET (OUTFOLDER=%5)

SET OUTPATH=%OUTFOLDER%%OUTNAME%

ECHO "-------- VIDEO EXTRACTION ---------"
call %FFMPEG% -i %1 -vcodec libx264 -acodec copy -ss %STARTTC% -to %ENDTC% -y %OUTPATH%

ECHO "-------- AUDIO EXTRACTION ---------"
SET AUDIOOUT=%OUTPATH:animatic.mov=sound.wav%
REM AUDIO EXTRACTION
call %FFMPEG% -i %OUTPATH% -vn -ar 48000 -ac 2 -y %AUDIOOUT%

GOTO :EOF

:ARGSERRORLBL
ECHO "-------- ERROR ---------"
ECHO "Three arguments (at least) must be given (Source_video_path, StartTC, EndTC) !"
pause