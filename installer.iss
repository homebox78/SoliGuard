; installer.iss - Inno Setup으로 설치형 패키지(SoliGuard_Setup.exe) 생성
; 빌드 순서: pyinstaller build_exe.spec → ISCC installer.iss
[Setup]
AppName=SoliGuard
AppVersion=0.4.0
AppPublisher=Solideo
DefaultDirName={autopf}\SoliGuard
DefaultGroupName=SoliGuard
OutputBaseFilename=SoliGuard_Setup
SetupIconFile=assets\soliguard.ico
Compression=lzma2
PrivilegesRequired=admin
; 브랜드 배너(크림슨 + 방패) — 정본 설치 디자인
WizardStyle=modern
WizardImageFile=assets\installer_banner.bmp
WizardSmallImageFile=assets\installer_small.bmp
WizardImageStretch=yes
AppPublisherURL=https://github.com/homebox78/SoliGuard

[Files]
Source: "dist\SoliGuard\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\SoliGuard"; Filename: "{app}\SoliGuard.exe"
Name: "{commondesktop}\SoliGuard"; Filename: "{app}\SoliGuard.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "바탕화면 아이콘 생성"; GroupDescription: "추가 작업:"
Name: "autoscan"; Description: "주 1회 자동 점검 사용 (작업 스케줄러 등록)"; \
  GroupDescription: "자동 점검 설정:"

[Run]
; 설치 직후 GUI 1회 실행(초기 설정 유도)
Filename: "{app}\SoliGuard.exe"; Description: "SoliGuard 실행"; \
  Flags: nowait postinstall skipifsilent
; 자동 점검을 선택하면 매주 월요일 09시 작업 등록(에이전트는 --once 로 1회 스캔)
Filename: "schtasks"; \
  Parameters: "/Create /TN SoliGuard_PeriodicScan /TR ""'{app}\SoliGuardAgent.exe' --once"" /SC WEEKLY /D MON /ST 09:00 /F"; \
  Tasks: autoscan; Flags: runhidden

[UninstallRun]
; 제거 시 등록된 작업도 함께 삭제
Filename: "schtasks"; Parameters: "/Delete /TN SoliGuard_PeriodicScan /F"; \
  Flags: runhidden; RunOnceId: "DelTask"
