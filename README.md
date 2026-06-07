# SoliGuard (솔리가드)

> SI 실무자용 **개인정보 자가점검 데스크톱 앱**. 내 PC의 산출물(문서·소스·이미지)에서
> 개인정보·기밀을 찾아 **검출 → 마스킹/격리/삭제 → 진단서**까지 처리한다.
> **모든 처리는 100% 로컬**에서 이루어진다(외부 전송 없음). 검출 엔진·조치 계층은
> 표준 라이브러리만으로 동작하며, 포맷 확장(xls/pdf/hwp/OCR/PSD)만 선택 의존성으로 활성화한다.

PySide6 GUI(대시보드·스캔·결과·격리함·이력·설정), 트레이 상주 + 정기 자동 점검,
직무별 스캔 프로파일, PDF 진단서까지 포함한 완성형 구조다.

## 무엇을 하는가

기획서가 명시한 **2단계 검출**(① 정규식으로 후보를 빠르게 찾고 → ② 검증 알고리즘으로
진위를 가림)에 더해, **확장자별 구조 인식 검증**(표/JSON의 컬럼·키 라벨을 이용한 문맥 검증)을
구현했다. 이 검증 단계가 일반 무료 도구 대비 핵심 차별점이다.

| 정보 유형 | 1차 탐지 | 2차 검증 | 직무 |
|---|---|---|---|
| 주민등록번호 | 정규식 | 생년월일·성별코드·체크섬 | 전체 |
| 외국인등록번호 | 정규식 | 성별코드(5~8)·체크섬 | 전체 |
| 신용카드번호 | 13~19자리 | Luhn 알고리즘 | 전체 |
| 사업자등록번호 | 정규식 | 국세청 체크섬 공식 | 전체 |
| 여권번호 | 정규식 | 발급기호 + 형식 | 전체 |
| 운전면허번호 | 정규식 | 지역코드 + 형식 | 전체 |
| 전화번호 | 정규식 | 형식·자릿수 | 전체 |
| 이메일 | 정규식 | 형식 검증 | 전체 |
| 계좌번호 | 정규식 | 길이·구분자(느슨) | 전체 |
| 한국 주소 | 정규식 | 시·도+시군구+도로/동+번지 | 전체 |
| IP 주소 | 정규식 | 옥텟 범위(0~255) | 개발자 |
| API 키·시크릿·DB접속정보·하드코딩 비밀번호 | 키워드+패턴 | **Shannon 엔트로피** | 개발자 |

부가 기능:
- **확장자별 구조 인식 검증**: CSV/XLSX/JSON에서 컬럼 헤더·키를 **필드 라벨**로 추출해 각 값에
  부착한다. "주민등록번호" 열에 있으나 체크섬이 안 맞는 값(2020년 이후 신규/마스킹 데이터)도
  **필드 라벨로 구제**해 검출하고, 자유 텍스트의 오탐은 그대로 차단한다.
- **직무별 프로파일**: 직무에 따라 활성 검출기를 다르게 구성(합집합-가산 방식 — 공통 PII는 전
  직무 항상 활성, 개발자만 시크릿/IP 추가). 디자이너는 이미지·PSD **OCR**로 차별화.
- **신뢰도 등급**: 2차 검증 통과 시 `검증됨(VERIFIED)`, 패턴만 일치하면 `패턴일치(PATTERN_ONLY)`.
  약한 하드코딩 비밀번호처럼 검증은 약해도 위험한 항목을 놓치지 않는다.
- **화이트리스트**: 카드사 공개 테스트번호 등 알려진 더미 값을 제외해 오탐을 줄인다.
- **중복 스팬 정리**: 같은 위치가 여러 검출기에 걸리면 검증된/우선순위 높은 것만 남긴다.
- **마스킹**: 모든 미리보기는 마스킹된 형태로만 노출(화면설계서 원칙 #3). 원문은 조치 단계에서만 사용.

## 폴더 구조 & 모듈 설명

```
soliguard/                  # 메인 패키지
  detection/                # ── 검출 엔진 (순수 로직, 외부 의존성 0) ──
    base.py                 #   Finding/Severity/Confidence, Detector 추상 + 2단계 스캔 루프
                            #   (필드 라벨·약후보 yield 포함)
    validators.py           #   체크섬·Luhn·BRN·여권·운전면허·IPv4·Shannon 엔트로피 (순수 함수)
    detectors.py            #   구체 검출기 11종 + 시크릿 다중규칙 검출기(개발자)
    whitelist.py            #   더미/테스트 값 제외
    engine.py               #   오케스트레이터: 등록·스캔·필드 컨텍스트 구제·중복정리·집계
  extractors.py             # ── 추출 계층 ── 포맷별 텍스트 + 구조(ExtractedDoc: 표/JSON 컬럼 라벨)
                            #   txt/csv/xlsx/docx/hwp(x)/pdf/이미지. .hwpx·.xlsx는 표준 라이브러리
  design_extractors.py      #   디자인 파일(PSD/XD) 텍스트 추출(디자이너 직무)
  figma_scan.py             #   Figma 클라우드 검사(옵트인: 동의+토큰, 검출 후 즉시 폐기)
  profiles.py               #   직무별 스캔 프로파일 기본값(확장자·폴더·OCR)
  scanner.py                # ── 스캔 오케스트레이션 ── extract_doc→검출, '검사불가' 격리
  engine.py                 # ── 파사드 ── run_scan(folders,...) → ScanSummary (CLI·GUI 공용 진입점)
  actions.py                # ── 조치 계층 ── 마스킹 / AES-256-GCM 격리·복원 / 안전 삭제 + 감사 로그
  report.py                 # ── 리포트 계층 ── PDF 진단서 생성(마스킹 값만 기재, reportlab)
  theme.py                  # ── UI 토큰 ── 디자인 토큰→QSS, 등급/위험도 색(Qt 불필요·순수)
  icons.py                  #   라인 아이콘·브랜드 로고·앱 아이콘(QPainter/SVG)
  fonts.py                  #   번들 Pretendard 폰트 로딩
  gui.py                    # ── GUI ── PySide6 메인 윈도우(대시보드→스캔→결과→조치/리포트)
                            #   사이드바 접기, 결과 3뷰(테이블/그룹/카드), 앱 디자인 모달
  onboarding.py             #   최초 실행 온보딩 마법사(직무·자동점검·OCR)
  installer.py              #   인앱 설치 마법사 화면(시안 구현)
  app.py                    # ── 앱 진입점 ── 트레이 상주 + 온보딩 분기 + 테마 (soliguard-gui)
  config.py                 #   설정 저장/로드(platformdirs 또는 ~/.soliguard)
  scheduler.py              #   정기 자동 스캔 + Windows 작업 등록(--once) (soliguard-agent)
  cli.py / __main__.py      #   CLI 진입점(전체 파이프라인, --report 로 PDF 발급) (soliguard)
  ui/settings_figma.py      #   Figma 옵트인 설정 섹션(동의+토큰 이중 가드)
  docs/                     #   설계 스펙 문서(.md) + 화면 스크린샷(참고용)
assets/                     # 앱 아이콘·번들 폰트·브랜드 로고·QSS용 SVG
pyproject.toml              # 패키지 메타·optional 의존성·콘솔 스크립트
requirements.txt            # 포맷 확장(선택) 의존성
build_exe.spec              # PyInstaller(GUI exe + 에이전트 exe)
installer.iss               # Inno Setup 설치 스크립트(작업 스케줄러 등록 포함)
```

정규식(1차)·검증 함수(2차)·구조 컨텍스트(엔진)를 독립 계층으로 분리해, 추후 **문맥 기반 AI
판단**으로 2차 검증만 교체·고도화할 수 있다(기획서 6장).

### 파이프라인 (스캔 → 검출 → 조치 → 기록)

```
파일/폴더 ─▶ extractors.extract_doc() ─▶ DetectionEngine.scan_text(text, fields) ─▶ Finding[]
   │           (포맷별 텍스트 + 구조 필드,        │  (필드 라벨로 문맥 검증·구제)
   │            실패 시 ExtractionError)          ▼
   └────────── scanner.scan_paths() (검사불가 격리) ─▶ actions(마스킹/격리/삭제) ─▶ audit.log
```

추출 계층은 한 파일의 파싱 실패가 전체 스캔을 멈추지 않도록 `ExtractionError`로 격리해
`검사불가`로 분리 기록한다(기획서 9장 리스크 #3). `.hwpx`와 `.xlsx`는 표준 라이브러리만으로
동작하고(국내 SI 차별점인 한글 파싱 포함), 나머지 포맷은 선택 의존성이 있을 때 활성화된다.
표(csv/xlsx)·JSON은 `extract_doc()`이 컬럼/키 라벨까지 함께 추출해 엔진의 구조 검증에 쓰인다.

상위 진입점은 `engine.run_scan(folders, role/profile, progress_cb, should_stop) → ScanSummary`
이며 CLI·GUI 모두 이 파사드를 공유한다.

## 빌드 & 배포 (설치형 exe)

```powershell
pip install -e ".[all,build]"          # 전체 의존성 + PyInstaller
pyinstaller build_exe.spec             # dist/SoliGuard/{SoliGuard,SoliGuardAgent}.exe
ISCC installer.iss                     # SoliGuard_Setup.exe (Inno Setup)
```

> 빌드 산출물(`dist/`, `build/`, `*.egg-info`)은 저장소에 포함하지 않는다(`.gitignore` 처리).

생애주기: 설치(작업 스케줄러 등록 옵션) → 최초 실행 온보딩 → 메인 앱(트레이 상주) →
주기적으로 OS가 `SoliGuardAgent.exe --once` 를 깨워 무인 스캔·리포트·토스트 알림.
자동 완전삭제는 제공하지 않으며, 자동 격리는 설정 시에만 동작한다.

## 실행

요구사항: Python 3.10+. 핵심 검출/조치 기능은 추가 설치 불필요.
포맷 확장(xls/pdf/docx/OCR/PSD)은 `pip install -r requirements.txt` 로 선택 활성화.

```powershell
# GUI 실행(PySide6 필요)
py -m soliguard.app

# 폴더 스캔(CLI, --report 로 PDF 진단서 발급)
py -m soliguard.cli C:\스캔할폴더 --role developer
py -m soliguard.cli C:\스캔할폴더 --role planner --no-ocr
```

라이브러리로 사용:

```python
from soliguard.detection import DetectionEngine
from soliguard.scanner import scan_paths
from soliguard import actions

engine = DetectionEngine(role="developer")

for result in scan_paths(["C:/Projects/고객사A"], engine):
    if result.status == "검사불가":
        print("검사불가:", result.path, result.error)
        continue
    for f in result.findings:
        print(f.severity.value, f.info_type, f.masked)   # 원문(f.raw)은 화면 노출 금지

    # 조치 예: 텍스트 파일 마스킹 사본 생성(원본 보존)
    if result.findings:
        actions.mask_in_text_file(result.path, result.findings)
```

## 알려진 한계 (다음 단계 입력값)

- **주민번호 체크섬**: 2020-10 이후 신규 발급분은 뒤 6자리가 임의 부여되어 체크섬이 맞지 않을
  수 있다. 표/JSON에서는 컬럼 라벨로 구제하지만, 자유 텍스트에서는 미탐 가능 → 문맥 신호로 보완 중.
- **계좌번호**: 은행별 포맷이 다양해 오탐 여지가 있어 느슨하게 검증(`PATTERN_ONLY` 다수). 은행별 규칙 테이블 필요.
- **주소/IP**: 체크섬이 없어 형식 검증에 의존(단독 노출 위험이 낮아 `낮음` 등급). 컬럼 라벨이 있으면 신뢰도가 올라간다.
- **격리 키 보관**: 데모는 복호화 키를 격리 메타(.meta.json)에 함께 둔다. 실제 제품에선 Windows DPAPI 등 OS 보안 저장소로 분리해야 한다(`actions.quarantine_file` 주석 참조).
- **비텍스트 마스킹**: `mask_in_text_file`은 텍스트 파일만 in-place 사본 마스킹을 지원한다. xlsx/hwp 등 바이너리 포맷은 격리/삭제를 권장(원문 구조 보존 마스킹은 후속 과제).
- **OCR 엔진**: 이미지/스캔 PDF는 `pytesseract` + Tesseract 바이너리(+한국어 데이터)가 있어야 활성화. 기본은 로컬 처리이며 외부 OCR API는 명시적 동의 시에만 연동(기획서 6장).
