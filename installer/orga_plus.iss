; Inno Setup Script for orga+ Desktop Application
; Generates an installable Windows setup installer (not a portable exe)
; Allows user to select Desktop shortcut, Taskbar shortcut, or both.

#define MyAppName "orga+"
#define MyAppVersion "2.2.0"
#define MyAppPublisher "OrgaPlus"
#define MyAppURL "https://bilnov.com"
#define MyAppExeName "orga+.exe"

[Setup]
; App Identity
AppId={{5E4790E5-46D7-48DF-9CB8-E07C6B7B49F3}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Installation directories
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Architecture & Privileges
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequiredOverridesAllowed=dialog
PrivilegesRequired=lowest

; Output Configuration
OutputDir=..\dist
OutputBaseFilename=orga+_Setup
SetupIconFile=..\desktop\assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

; Compression & UI styling
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked
Name: "taskbaricon"; Description: "Create a &taskbar shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
; Packaging files from dist directory
Source: "..\dist\orga+-Portable\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\desktop\assets\icon.ico"; DestDir: "{app}\assets"; Flags: ignoreversion

[Icons]
; Start menu shortcut (always created)
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"

; Desktop shortcut (user selectable via checkbox)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; Taskbar shortcut (user selectable via checkbox)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: taskbaricon

[Run]
; PowerShell script to ensure desktop shortcut is created and pinned properly if selected
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([System.IO.Path]::Combine([System.Environment]::GetFolderPath('Desktop'), '{#MyAppName}.lnk')); $s.TargetPath = '{app}\{#MyAppExeName}'; $s.WorkingDirectory = '{app}'; $s.IconLocation = '{app}\{#MyAppExeName},0'; $s.Save()"""; Flags: runhidden; Tasks: desktopicon

; PowerShell script to ensure taskbar shortcut is created and pinned properly if selected
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""$ws = New-Object -ComObject WScript.Shell; $tbDir = [System.IO.Path]::Combine($env:APPDATA, 'Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar'); if (-not (Test-Path $tbDir)) { New-Item -ItemType Directory -Path $tbDir -Force | Out-Null }; $s = $ws.CreateShortcut([System.IO.Path]::Combine($tbDir, '{#MyAppName}.lnk')); $s.TargetPath = '{app}\{#MyAppExeName}'; $s.WorkingDirectory = '{app}'; $s.IconLocation = '{app}\{#MyAppExeName},0'; $s.Save()"""; Flags: runhidden; Tasks: taskbaricon

; Option to launch orga+ after setup completes
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar\{#MyAppName}.lnk"
Type: files; Name: "{autodesktop}\{#MyAppName}.lnk"
