@ECHO OFF
TASKKILL /F /IM "aethyrBin.exe"
TASKKILL /F /IM "aethyrHelper.exe"

for /f "tokens=2,*" %%a in ('REG QUERY "HKLM\Software\Aethyr" /v "Install_Dir" ^| find "Install_Dir"') do cd "%%b\aethyrBin"
start /min aethyrHelper.exe
