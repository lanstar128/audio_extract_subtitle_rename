[Setup]
AppName=Audio Subtitle Tools
AppVersion=2.0.0
AppPublisher=Development Team
AppPublisherURL=
AppSupportURL=
AppUpdatesURL=
DefaultDirName={autopf}\audio_subtitle_tools
DefaultGroupName=音频字幕工具
AllowNoIcons=yes
LicenseFile=
InfoAfterFile=
OutputDir=..\installer
OutputBaseFilename=视频处理工具集_v2.0.0_安装包
SetupIconFile=..\resources\images\logo.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
DisableReadyPage=yes
ShowLanguageDialog=no
LanguageDetectionMethod=uilanguage
UninstallDisplayIcon={app}\audio_subtitle_tools.exe

[Languages]
Name: "chinesesimp"; MessagesFile: "ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
Source: "..\dist\audio_subtitle_tools\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\音频字幕工具"; Filename: "{app}\audio_subtitle_tools.exe"
Name: "{group}\{cm:UninstallProgram,音频字幕工具}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\音频字幕工具"; Filename: "{app}\audio_subtitle_tools.exe"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\音频字幕工具"; Filename: "{app}\audio_subtitle_tools.exe"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\audio_subtitle_tools.exe"; Description: "{cm:LaunchProgram,Audio Subtitle Tools}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // 安装完成后的操作
  end;
end;
