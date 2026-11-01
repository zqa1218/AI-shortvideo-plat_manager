; 猫后台助手 安装包脚本（Inno Setup 6）
; 构建：先运行 build-release.ps1 生成 release\payload，再用 ISCC.exe 编译本文件。

#define MyAppName "猫后台助手"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "zqa1218"
#define MyAppURL "https://github.com/zqa1218/AI-shortvideo-plat_manager"
#define MyAppExeName "猫后台助手.exe"

[Setup]
AppId={{09FDB230-EC9B-48CA-9F86-BAA001A75891}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\release
OutputBaseFilename=猫后台助手_Setup_{#MyAppVersion}
SetupIconFile=..\assets\cat.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
DisableWelcomePage=no

[Languages]
Name: "zh"; MessagesFile: "ChineseSimplified.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; release\payload 由 build-release.ps1 生成：应用本体（不含 data 用户数据）
Source: "..\release\payload\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\tools\setup-vendor.ps1"; DestDir: "{app}\tools"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "..\CHANGELOG.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\安装自动发布依赖（需 Python 3.12）"; Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -NoExit -File ""{app}\tools\setup-vendor.ps1"""; WorkingDir: "{app}"
Name: "{group}\使用说明"; Filename: "{app}\README.md"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 只清理程序自身产生的缓存缩略图，不动 data\social.db（用户数据）
Type: filesandordirs; Name: "{app}\data\thumbs"
Type: filesandordirs; Name: "{app}\data\collector_debug"
