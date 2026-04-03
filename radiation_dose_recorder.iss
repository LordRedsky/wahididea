; Inno Setup Script untuk Radiation Dose Recorder
; Download Inno Setup: https://jrsoftware.org/isdl.php
; Install Inno Setup, lalu compile script ini

#define MyAppName "Radiation Dose Recorder"
#define MyAppVersion "1.0"
#define MyAppPublisher "Abdurrahman Wahid, ST"
#define MyAppURL "https://github.com/wahid-idea"
#define MyAppExeName "RadiationDoseRecorder.exe"
#define MyAppAssocName "Radiation Dose Recorder"
#define MyAppAssocExt ".rdr"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=
OutputDir=installer_output
OutputBaseFilename=RadiationDoseRecorder_Setup
SetupIconFile=
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "indonesian"; MessagesFile: "compiler:Languages\Indonesian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Main executable and all dependencies from PyInstaller build
Source: "dist\RadiationDoseRecorder\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\RadiationDoseRecorder\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\RadiationDoseRecorder\app.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\RadiationDoseRecorder\ocr_extractor.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\RadiationDoseRecorder\excel_handler.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\RadiationDoseRecorder\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  
  // Check if Tesseract is installed
  if not RegKeyExists(HKLM, 'SOFTWARE\Tesseract-OCR') then
  begin
    if not FileExists('C:\Program Files\Tesseract-OCR\tesseract.exe') then
    begin
      if MsgBox('Tesseract OCR tidak terdeteksi di sistem Anda.' + #13#10 +
                'Aplikasi ini memerlukan Tesseract OCR untuk berfungsi.' + #13#10 +
                'Apakah Anda ingin menginstall Tesseract OCR sekarang?',
                mbConfirmation, MB_YESNO) = IDYES then
      begin
        // Open Tesseract download page
        ShellExec('open', 'https://github.com/UB-Mannheim/tesseract/wiki', '', '', SW_SHOWNORMAL, ewNoWait, ResultCode);
      end;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Create data directory for Excel files
    if not DirExists(ExpandConstant('{userdocs}\RadiationDoseRecorder')) then
      CreateDir(ExpandConstant('{userdocs}\RadiationDoseRecorder'));
  end;
end;
