
cd %~dp0
set PATH=C:\Program Files (x86)\Git\cmd;%PATH%

git submodule foreach git pull && git pull
pause