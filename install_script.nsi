; GetWindowsVersion 3.0 (2013-02-07)
;
; Based on Yazno's function, http://yazno.tripod.com/powerpimpit/
; Update by Joost Verburg
; Update (Macro, Define, Windows 7 detection) - John T. Haller of PortableApps.com - 2008-01-07
; Update (Windows 8 detection) - Marek Mizanin (Zanir) - 2013-02-07
;
; Usage: ${GetWindowsVersion} $R0
;
; $R0 contains: 95, 98, ME, NT x.x, 2000, XP, 2003, Vista, 7, 8 or '' (for unknown)
 
Function GetWindowsVersion
 
  Push $R0
  Push $R1
 
  ClearErrors
 
  ReadRegStr $R0 HKLM \
  "SOFTWARE\Microsoft\Windows NT\CurrentVersion" CurrentVersion
 
  IfErrors 0 lbl_winnt
 
  ; we are not NT
  ReadRegStr $R0 HKLM \
  "SOFTWARE\Microsoft\Windows\CurrentVersion" VersionNumber
 
  StrCpy $R1 $R0 1
  StrCmp $R1 '4' 0 lbl_error
 
  StrCpy $R1 $R0 3
 
  StrCmp $R1 '4.0' lbl_win32_95
  StrCmp $R1 '4.9' lbl_win32_ME lbl_win32_98
 
  lbl_win32_95:
    StrCpy $R0 '95'
  Goto lbl_done
 
  lbl_win32_98:
    StrCpy $R0 '98'
  Goto lbl_done
 
  lbl_win32_ME:
    StrCpy $R0 'ME'
  Goto lbl_done
 
  lbl_winnt:
 
  StrCpy $R1 $R0 1
 
  StrCmp $R1 '3' lbl_winnt_x
  StrCmp $R1 '4' lbl_winnt_x
 
  StrCpy $R1 $R0 3
 
  StrCmp $R1 '5.0' lbl_winnt_2000
  StrCmp $R1 '5.1' lbl_winnt_XP
  StrCmp $R1 '5.2' lbl_winnt_2003
  StrCmp $R1 '6.0' lbl_winnt_vista
  StrCmp $R1 '6.1' lbl_winnt_7
  StrCmp $R1 '6.2' lbl_winnt_8 lbl_error
 
  lbl_winnt_x:
    StrCpy $R0 "NT $R0" 6
  Goto lbl_done
 
  lbl_winnt_2000:
    Strcpy $R0 '2000'
  Goto lbl_done
 
  lbl_winnt_XP:
    Strcpy $R0 'XP'
  Goto lbl_done
 
  lbl_winnt_2003:
    Strcpy $R0 '2003'
  Goto lbl_done
 
  lbl_winnt_vista:
    Strcpy $R0 'Vista'
  Goto lbl_done
 
  lbl_winnt_7:
    Strcpy $R0 '7'
  Goto lbl_done
 
  lbl_winnt_8:
    Strcpy $R0 '8'
  Goto lbl_done
 
  lbl_error:
    Strcpy $R0 ''
  lbl_done:
 
  Pop $R1
  Exch $R0
 
FunctionEnd
 
!macro GetWindowsVersion OUTPUT_VALUE
	Call GetWindowsVersion
	Pop `${OUTPUT_VALUE}`
!macroend


!define GetWindowsVersion '!insertmacro "GetWindowsVersion"'

# define installer name
outFile "installer.exe"
 
# set install directory
InstallDir "$PROGRAMFILES\codebender"
 
# default section start
section
 
# define output path
setOutPath $INSTDIR
 
# specify file to go in output path
File /r dist\*


${GetWindowsVersion} $R0

StrCmp $R0 "XP" isxp isnotxp
isxp:
; Install Windows Visual Studio 2008 Runtime (includes the .dlls py2exe needs)
;MessageBox MB_OK "Windows XP detected"
ExecWait '"$INSTDIR\vcredist_x86.exe" /q'
isnotxp:

!include x64.nsh

${if} ${RunningX64}
; 64 bits go here
ExecWait '"$INSTDIR\drivers\Windows\dpinst-amd64.exe" /sw'
${Else}
; 32 bits go here
ExecWait '"$INSTDIR\drivers\Windows\dpinst-x86.exe" /sw'
${EndIf}

# define uninstaller name
writeUninstaller $INSTDIR\uninstaller.exe

SimpleSC::InstallService "codebender" "codebender daemon" "16" "2" "$PROGRAMFILES\codebender\mywinserver.exe" "" "" ""
Pop $0 ; returns an errorcode (<>0) otherwise success (0)
SimpleSC::StartService "codebender" "" 30
Pop $0 ; returns an errorcode (<>0) otherwise success (0)
 
 
#-------
# default section end
sectionEnd
 
# create a section to define what the uninstaller does.
# the section will always be named "Uninstall"
section "Uninstall"
 
; Stop a service and waits for file release
SimpleSC::StopService "codebender" 1 30
Pop $0 ; returns an errorcode (<>0) otherwise success (0)

SimpleSC::RemoveService "codebender"
Pop $0 ; returns an errorcode (<>0) otherwise success (0)


# Always delete uninstaller first
delete $INSTDIR\uninstaller.exe
 
# now delete installed file
RMDir /r $INSTDIR
 
sectionEnd