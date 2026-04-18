; Inno Setup script for ACB Large Print Tool
; Accessible installer -- uses standard Windows controls (screen reader compatible)
; All text descriptions are clear and descriptive for non-visual users

#define MyAppName "ACB Large Print Tool"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "BITS - Blind Information Technology Solutions"
#define MyAppURL "https://www.bitsonline.org"
#define MyAppExeName "acb-large-print-win-x64.exe"
#define MyCliExeName "acb-large-print-cli-win-x64.exe"

[Setup]
AppId={{E7F2A4B1-3C5D-4E6F-8A9B-0C1D2E3F4A5B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\ACB Large Print Tool
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Output settings
OutputDir=..\dist\installer
OutputBaseFilename=ACB-Large-Print-Setup-{#MyAppVersion}
; Compression
Compression=lzma2/ultra64
SolidCompression=yes
; UI
WizardStyle=modern
; Privileges -- per-user install by default (no admin needed)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; Accessibility: ensure all wizard pages have descriptive text
DisableWelcomePage=no
; License
LicenseFile=..\LICENSE.txt
; Uninstall
UninstallDisplayIcon={app}\{#MyAppExeName}
; Version info shown in Add/Remove Programs
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=ACB Large Print compliance tool for Word documents
VersionInfoProductName={#MyAppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
english.WelcomeLabel2=This will install {#MyAppName} version {#MyAppVersion} on your computer.%n%nThe ACB Large Print Tool helps you audit, fix, and create Microsoft Word documents that comply with the American Council of the Blind Large Print Guidelines.%n%nIt is recommended that you close Microsoft Word before continuing.
english.FinishedLabel=Setup has finished installing {#MyAppName} on your computer. You can launch the application from the Start menu, or run it from the command line for batch processing.
english.SelectComponentsLabel2=Select the components you want to install. Each component is described below. Press Space to toggle a component on or off.

[Types]
Name: "full"; Description: "Full installation (application, template, and documentation)"
Name: "compact"; Description: "Compact installation (application only)"
Name: "custom"; Description: "Custom installation (choose components)"; Flags: iscustom

[Components]
Name: "main"; Description: "ACB Large Print Tool (command-line and graphical interface)"; Types: full compact custom; Flags: fixed
Name: "template"; Description: "Install ACB Large Print Word template to Microsoft Word's Templates folder for use in File, New"; Types: full
Name: "docs"; Description: "Documentation and ACB Guidelines quick reference"; Types: full

[Files]
; Main application (--onedir output: exe + supporting DLLs/pyds)
Source: "..\dist\acb-large-print-win-x64\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: main
; CLI application (--onedir output: needs its own _internal folder)
Source: "..\dist\acb-large-print-cli-win-x64\*"; DestDir: "{app}\cli"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: main

; Template file -- installed to both app folder and Word Templates
Source: "..\dist\ACB-Large-Print.dotx"; DestDir: "{app}"; Flags: ignoreversion; Components: template
Source: "..\dist\ACB-Large-Print.dotx"; DestDir: "{userappdata}\Microsoft\Templates"; Flags: ignoreversion; Components: template

; Documentation
Source: "..\README.md"; DestDir: "{app}\docs"; Flags: ignoreversion; Components: docs
Source: "..\LICENSE.txt"; DestDir: "{app}\docs"; Flags: ignoreversion; Components: docs

[Icons]
; Start menu shortcuts
Name: "{group}\ACB Large Print Tool"; Filename: "{app}\{#MyAppExeName}"; Comment: "Launch ACB Large Print Tool graphical interface"
Name: "{group}\ACB Large Print Tool (Command Line)"; Filename: "{cmd}"; Parameters: "/k ""{app}\cli\{#MyCliExeName}"" --help"; Comment: "Open a command prompt with ACB Large Print Tool help"
Name: "{group}\Uninstall ACB Large Print Tool"; Filename: "{uninstallexe}"; Comment: "Remove ACB Large Print Tool from your computer"

; Desktop shortcut (optional)
Name: "{autodesktop}\ACB Large Print Tool"; Filename: "{app}\{#MyAppExeName}"; Comment: "Launch ACB Large Print Tool"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"
Name: "addtopath"; Description: "Add to system PATH for command-line use from any directory"; GroupDescription: "Command-line integration:"; Flags: unchecked

[Registry]
; Add to PATH if requested
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}\cli"; Tasks: addtopath; Check: NeedsAddPath(ExpandConstant('{app}\cli'))

[Run]
; Option to launch after install
Filename: "{app}\{#MyAppExeName}"; Description: "Launch ACB Large Print Tool now"; Flags: nowait postinstall skipifsilent

[Code]
// Check if the app directory is already in PATH
function NeedsAddPath(Param: string): Boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', OrigPath) then
  begin
    Result := True;
    exit;
  end;
  // Look for the path with and without trailing backslash
  Result := (Pos(';' + Param + ';', ';' + OrigPath + ';') = 0);
end;

// Clean up PATH on uninstall
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  Path: string;
  AppDir: string;
  P: Integer;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    AppDir := ExpandConstant('{app}\cli');
    if RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', Path) then
    begin
      P := Pos(';' + AppDir, Path);
      if P > 0 then
      begin
        Delete(Path, P, Length(';' + AppDir));
        RegWriteStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', Path);
      end;
    end;
  end;
end;
