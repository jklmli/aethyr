@ECHO OFF
TASKKILL /F /IM "AethyrBin.exe"
TASKKILL /F /IM "AethyrHelper.exe"

for /f "tokens=2,*" %%a in ('REG QUERY "HKLM\Software\Aethyr" /v "Install_Dir" ^| find "Install_Dir"') do cd "%%b\AethyrBin"
start /min AethyrHelper.exe
