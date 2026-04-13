; Drinkport-Barcode - Inno Setup Skript
; Erstellt eine Installations-Datei fuer das gesamte Programm.

[Setup]
AppId={{D1BB882B-79CE-420C-AADE-18755BB14253}}
AppName=Drinkport-Barcode
AppVersion=1.6
AppPublisher=Drinkport KG
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DefaultDirName={autopf}\Drinkport\Drinkport-Barcode
DefaultGroupName=Drinkport
OutputDir=dist
OutputBaseFilename=Drinkport-Barcode_Setup
PrivilegesRequired=admin
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\Drinkport-Barcode.exe

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Alle Dateien aus dem dist-Ordner rekursiv einbeziehen
Source: "dist\Drinkport-Barcode\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Erzeuge bei Erstinstallation eine config.ini aus der Vorlage, ohne bestehende Datei zu ueberschreiben
Source: "example_config.ini"; DestDir: "{app}"; DestName: "config.ini"; Flags: onlyifdoesntexist

[Icons]
Name: "{group}\Drinkport-Barcode"; Filename: "{app}\Drinkport-Barcode.exe"
Name: "{autodesktop}\Drinkport-Barcode"; Filename: "{app}\Drinkport-Barcode.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Drinkport-Barcode.exe"; Description: "{cm:LaunchProgram,Drinkport-Barcode}"; Flags: nowait postinstall skipifsilent
