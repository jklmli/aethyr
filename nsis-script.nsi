;--------------------------------
;Constants

!define NAME "Aethyr"
!define VERSION "1.5.0"
!define PUBLISHER "598074"
!define DESCRIPTION "the itunes jb"

;--------------------------------
;Include Modern UI

  !include "MUI2.nsh"
  !define MUI_ICON "icon.ico"
  !define MUI_UNICON "icon.ico"

;--------------------------------
;General

  ;Name and file
  Name "Aethyr"
  OutFile "aethyr-1.5.0-win3264-installer.exe"
  Icon "icon.ico"
  BrandingText "Aethyr v1.5.0 Setup"

  ;Default installation folder
  InstallDir $PROGRAMFILES\Aethyr
  
  ;Get installation folder from registry if available
  InstallDirRegKey HKLM "Software\Aethyr" "Install_Dir"

  ;Request application privileges for Windows Vista
  RequestExecutionLevel admin

;--------------------------------
;Variables

  Var StartMenuFolder

;--------------------------------
;Interface Settings

  !define MUI_ABORTWARNING

;--------------------------------
;Pages

  !insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
  !insertmacro MUI_PAGE_COMPONENTS
  !insertmacro MUI_PAGE_DIRECTORY
  
  ;Start Menu Folder Page Configuration
  !define MUI_STARTMENUPAGE_REGISTRY_ROOT "HKLM" 
  !define MUI_STARTMENUPAGE_REGISTRY_KEY "Software\Aethyr" 
  !define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "Start Menu Folder"

  !insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder
  
  !insertmacro MUI_PAGE_INSTFILES
  
  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
;Languages
 
  !insertmacro MUI_LANGUAGE "English"

;--------------------------------
;Installer Sections

Section "Adobe AIR" AdobeAIR
  SectionIn RO

  ReadRegStr $2 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\com.598074.Aethyr" "UninstallString"
  IfErrors done_deleting_old_AIR +1
  ExecWait $2

  done_deleting_old_AIR:
  
  ReadRegStr $3 HKLM "Software\Aethyr" "Install_Dir"
  IfErrors done_checkOld +1
  Delete "$3\icon.ico"
  RMDir /r "$3\aethyrBin"
  Delete "$3\Uninstall.exe"
  RMDir $3

  ReadRegStr $3 HKLM "Software\Aethyr" "StartMenu"
  Delete "$3\Uninstall.lnk"
  Delete "$3\Aethyr.lnk"
  RMDir $3

  done_checkOld:
  SetOutPath "$INSTDIR"
  
  ;Put file there
  File "Flash\Aethyr.air"
  File "icon.ico"

  ;Launch AIR Installer silently
  Call DetectAIR
SectionEnd

Section "Aethyr" Aethyr
  SectionIn RO
  ReadRegStr $2 HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Adobe AIR" "InstallLocation"
  ExecWait '"$2\Versions\1.0\Adobe AIR Application Installer.exe" -silent -location "$INSTDIR" "Aethyr.air"'
  Delete "$INSTDIR\Aethyr.air"

  ;Store installation folder
  WriteRegStr HKLM "Software\Aethyr" "Install_Dir" $INSTDIR
  WriteRegStr HKLM "Software\Aethyr" "StartMenu" "$SMPROGRAMS\$StartMenuFolder"
  
  ;Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Aethyr" "DisplayName" "Aethyr"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Aethyr" "DisplayVersion" "1.5.0"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Aethyr" "DisplayIcon" "$INSTDIR\icon.ico"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Aethyr" "Publisher" "598074"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Aethyr" "UninstallString" "$INSTDIR\uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Aethyr" "URLInfoAbout" "http://www.aethyrjb.com"
  WriteRegDWord HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Aethyr" "EstimatedSize" "0x00001f54"

SectionEnd

Section "Start Menu Shortcuts" StartMenu

    !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
    
    ;Create shortcuts
    SetOutPath "$INSTDIR\aethyrBin"
    
    CreateDirectory "$SMPROGRAMS\$StartMenuFolder"
    CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
    CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Aethyr.lnk" "$INSTDIR\aethyrBin\Aethyr.exe" "" "$INSTDIR\icon.ico" "" SW_SHOWMINIMIZED

    !insertmacro MUI_STARTMENU_WRITE_END

SectionEnd

Section "Desktop Shortcut" DesktopShortcut

  CreateShortCut "$DESKTOP\Aethyr.lnk" "$INSTDIR\aethyrBin\Aethyr.exe" "" "$INSTDIR\icon.ico" "" SW_SHOWMINIMIZED
  
SectionEnd

  


;--------------------------------
;Descriptions

  ;Language strings
  LangString DESC_AdobeAIR ${LANG_ENGLISH} "Adobe AIR is required to use Aethyr."
  LangString DESC_Aethyr ${LANG_ENGLISH} "The core utilities for Aethyr."
  LangString DESC_StartMenu ${LANG_ENGLISH} "Toggle start menu shortcuts"
  LangString DESC_DesktopShortcut ${LANG_ENGLISH} "Toggle desktop shortcut."

  ;Assign language strings to sections
  !insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${AdobeAIR} $(DESC_AdobeAIR)
    !insertmacro MUI_DESCRIPTION_TEXT ${Aethyr} $(DESC_Aethyr)
    !insertmacro MUI_DESCRIPTION_TEXT ${StartMenu} $(DESC_StartMenu)
    !insertmacro MUI_DESCRIPTION_TEXT ${DesktopShortcut} $(DESC_DesktopShortcut)
  !insertmacro MUI_FUNCTION_DESCRIPTION_END
 
;--------------------------------
;Uninstaller Section

Section "Uninstall"

  ClearErrors
  ReadRegStr $2 HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\com.598074.Aethyr" "UninstallString"
  IfErrors done_deleting_AIR +1
  ExecWait $2

  done_deleting_AIR:
  ClearErrors
  ReadRegStr $2 HKLM "SOFTWARE\Aethyr" "Install_Dir"

  IfErrors done_old +1
  Delete "$DESKTOP\Aethyr.lnk"
  
  Delete "$2\icon.ico"
  RMDir /r "$2\aethyrBin"

  done_old:
  !insertmacro MUI_STARTMENU_GETFOLDER Application $StartMenuFolder
    
; Delete "$SMPROGRAMS\$StartMenuFolder\Uninstall.lnk"
  RMDir /r "$SMPROGRAMS\$StartMenuFolder"
  
  DeleteRegKey HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Aethyr"
  DeleteRegKey HKLM SOFTWARE\Aethyr

  Delete "$2\Uninstall.exe"
  RMDir $2

SectionEnd

;--------------------------------

;Download Adobe AIR
 
Function DetectAIR
  ClearErrors
  ReadRegDWORD $2 HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Adobe AIR" "VersionMajor"
  
  IfErrors download_AIR +1
  StrCmp $2 "2" done_AIR

  download_AIR:
  MessageBox MB_OK "Aethyr uses Adobe AIR, it will now be downloaded and installed.  By clicking 'Ok,' you agree to the terms set forth in the Software Licensing Agreement at http://get.adobe.com/air/."

  StrCpy $2 "$TEMP\AdobeAIRInstaller.exe"
  nsisdl::download /TIMEOUT=30000 "http://airdownload.adobe.com/air/win/download/latest/AdobeAIRInstaller.exe" $2
  Pop $R0 ;Get the return value
	StrCmp $R0 "success" +4
	MessageBox MB_OK "Download failed.  Please check your internet connection and run the installer again."
	RMDir /r "$INSTDIR"
	Quit
  ExecWait $2
  
  ClearErrors
  ReadRegDWORD $3 HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Adobe AIR" "VersionMajor"
  StrCmp $3 "2" success_AIR
  MessageBox MB_OK "Adobe AIR installation was aborted, but it is a required component of Aethyr.  Aethyr will now abort installation."
  RMDir /r "$INSTDIR"
  Quit
  success_AIR:
  Delete $2
  
  done_AIR:
FunctionEnd
