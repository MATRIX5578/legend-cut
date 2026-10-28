; Legend Cut — ملف التنصيب (Inno Setup)
#define AppVer GetEnv("APP_VERSION")

[Setup]
AppId={{6B1F2C4E-9A7D-4C2B-8E31-LEGENDCUT001}
AppName=Legend Cut
AppVersion={#AppVer}
AppPublisher=MATRIX5578
AppPublisherURL=https://github.com/MATRIX5578/legend-cut
DefaultDirName={localappdata}\Programs\Legend Cut
DefaultGroupName=Legend Cut
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=LegendCut-Setup
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\LegendCut.exe
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"

[Files]
Source: "dist\LegendCut\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\Legend Cut"; Filename: "{app}\LegendCut.exe"
Name: "{autodesktop}\Legend Cut"; Filename: "{app}\LegendCut.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\LegendCut.exe"; Description: "Launch Legend Cut"; Flags: nowait postinstall skipifsilent
Filename: "{app}\LegendCut.exe"; Flags: nowait; Check: WizardSilent
