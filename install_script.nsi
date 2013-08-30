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