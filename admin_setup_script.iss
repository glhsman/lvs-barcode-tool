; Drinkport-Barcode Admin - Inno Setup Skript
; Erstellt eine Installations-Datei für das Admin-Programm.

[Setup]
; Eigene AppId für das Admin-Tool
AppId={{E2CC993C-80DF-511D-BBEE-29866CC25364}}
AppName=Drinkport-Barcode Admin
AppVersion=1.6
AppPublisher=Drinkport KG
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DefaultDirName={autopf}\Drinkport\Drinkport-Admin
DefaultGroupName=Drinkport
OutputDir=dist
OutputBaseFilename=Drinkport-Admin_Setup
PrivilegesRequired=admin
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\Drinkport-Admin.exe

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Alle Dateien aus dem dist\Drinkport-Admin-Ordner rekursiv einbeziehen
Source: "dist\Drinkport-Admin\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Erzeuge bei Erstinstallation eine config.ini aus der Vorlage, ohne bestehende Datei zu ueberschreiben
Source: "example_config.ini"; DestDir: "{app}"; DestName: "config.ini"; Flags: onlyifdoesntexist

[Icons]
Name: "{group}\Drinkport-Barcode Admin"; Filename: "{app}\Drinkport-Admin.exe"
Name: "{autodesktop}\Drinkport-Barcode Admin"; Filename: "{app}\Drinkport-Admin.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Drinkport-Admin.exe"; Description: "{cm:LaunchProgram,Drinkport-Barcode Admin}"; Flags: nowait postinstall skipifsilent
