
cd %~dp0
echo off
set PATH=C:\Program Files (x86)\Git\cmd;C:\Program Files\Git\cmd;%PATH%
echo on
git submodule foreach git pull && git pull
pause