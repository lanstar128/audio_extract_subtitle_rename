[Setup]
AppName=Audio Subtitle Tools
AppVersion=2.1.1
AppPublisher=智剪大师
AppPublisherURL=https://https://https://https://videosage.lanstar.top/
AppSupportURL=https://https://https://https://videosage.lanstar.top/
AppUpdatesURL=https://https://https://https://videosage.lanstar.top/
AppId={{A5B3C2D1-E4F5-6789-ABCD-EF0123456789}
DefaultDirName={autopf}\audio_subtitle_tools
DefaultGroupName=音频字幕工具
AllowNoIcons=yes
LicenseFile=
InfoAfterFile=
OutputDir=..\installer
OutputBaseFilename=视频处理工具集_v2.1.1-beta-01_安装包
SetupIconFile=..\resources\images\logo.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
DisableReadyPage=yes
ShowLanguageDialog=no
LanguageDetectionMethod=uilanguage
UninstallDisplayIcon={app}\audio_subtitle_tools.exe
; 版本控制设置
VersionInfoVersion=2.1.1
; 卸载旧版本设置
UninstallRestartComputer=no
CloseApplications=yes
RestartApplications=no

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
// 检测并卸载旧版本
function GetUninstallString(): String;
var
  sUnInstPath: String;
  sUnInstallString: String;
begin
  sUnInstPath := ExpandConstant('Software\Microsoft\Windows\CurrentVersion\Uninstall\{#SetupSetting("AppId")}_is1');
  sUnInstallString := '';
  if not RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', sUnInstallString) then
    RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', sUnInstallString);
  Result := sUnInstallString;
end;

function IsUpgrade(): Boolean;
begin
  Result := (GetUninstallString() <> '');
end;

function UnInstallOldVersion(): Integer;
var
  sUnInstallString: String;
  iResultCode: Integer;
begin
  Result := 0;
  sUnInstallString := GetUninstallString();
  if sUnInstallString <> '' then begin
    sUnInstallString := RemoveQuotes(sUnInstallString);
    if Exec(sUnInstallString, '/SILENT /NORESTART /SUPPRESSMSGBOXES','', SW_HIDE, ewWaitUntilTerminated, iResultCode) then
      Result := 3
    else
      Result := 2;
  end else
    Result := 1;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep=ssInstall) then
  begin
    if (IsUpgrade()) then
    begin
      UnInstallOldVersion();
    end;
  end;
end;

function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
  OldVersion: String;
begin
  Result := True;
  
  // 检测是否已安装旧版本
  if IsUpgrade() then
  begin
    if MsgBox('检测到系统中已安装旧版本的程序。' #13#13 '安装程序将自动卸载旧版本后继续安装新版本。' #13#13 '是否继续？', mbConfirmation, MB_YESNO) = IDYES then
    begin
      Result := True;
    end
    else
    begin
      Result := False;
    end;
  end;
end;
