# SoliGuard 백엔드 파이프라인 (M1 검출 엔진 + 추출·조치 계층)

> SI 실무자용 경량 개인정보 검출·조치 데스크톱 도구의 **백엔드** 부분.
> M1 마일스톤(검출 엔진 PoC) + MVP 백엔드 파이프라인(스캔 → 검출 → 조치 → 기록)에 해당한다.
> **모든 처리는 100% 로컬**에서 이루어진다. 핵심 엔진·조치는 표준 라이브러리만으로 동작하며,
> 포맷 확장(xls/pdf/hwp/OCR)만 선택 의존성으로 활성화한다.

## 무엇을 하는가

기획서가 명시한 **2단계 검출**(① 정규식으로 후보를 빠르게 찾고 → ② 검증 알고리즘으로 진위를 가림)을 구현했다. 이 2단계 검증이 일반 무료 도구 대비 핵심 차별점이다.

| 정보 유형 | 1차 탐지 | 2차 검증 | 직무 |
|---|---|---|---|
| 주민등록번호 | 정규식 | 생년월일·성별코드·체크섬 | 전체 |
| 외국인등록번호 | 정규식 | 성별코드(5~8)·체크섬 | 전체 |
| 신용카드번호 | 13~19자리 | Luhn 알고리즘 | 전체 |
| 사업자등록번호 | 정규식 | 국세청 체크섬 공식 | 전체 |
| 전화번호 | 정규식 | 형식·자릿수 | 전체 |
| 이메일 | 정규식 | 형식 검증 | 전체 |
| 계좌번호 | 정규식 | 길이·구분자(느슨) | 전체 |
| API 키·시크릿·DB접속정보·하드코딩 비밀번호 | 키워드+패턴 | **Shannon 엔트로피** | 개발자 |

부가 기능:
- **직무별 프로파일**: 직무에 따라 활성 검출기를 다르게 구성(예: 시크릿 검출은 개발자만 기본 활성).
- **신뢰도 등급**: 2차 검증 통과 시 `검증됨(VERIFIED)`, 패턴만 일치하면 `패턴일치(PATTERN_ONLY)`. 약한 하드코딩 비밀번호처럼 검증은 약해도 위험한 항목을 놓치지 않는다.
- **화이트리스트**: 카드사 공개 테스트번호 등 알려진 더미 값을 제외해 오탐을 줄인다.
- **중복 스팬 정리**: 같은 위치가 여러 검출기에 걸리면 검증된/우선순위 높은 것만 남긴다.
- **마스킹**: 모든 미리보기는 마스킹된 형태로만 노출(화면설계서 원칙 #3). 원문은 조치 단계에서만 사용.

## 구조

```
soliguard/
  detection/          # ── 검출 엔진(M1) ──
    base.py           # Finding, Severity, Confidence, Detector 추상 클래스, 2단계 스캔 루프
    validators.py     # 체크섬·Luhn·BRN·엔트로피 (순수 함수, 단위 테스트 대상)
    detectors.py      # 구체 검출기 7종 + 시크릿 다중규칙 검출기(정규식 내장)
    whitelist.py      # 더미/테스트 값 제외
    engine.py         # 오케스트레이터: 등록·스캔·중복정리·집계
  extractors.py       # ── 추출 계층 ── 포맷별 텍스트 추출(txt/csv/xlsx/docx/hwp(x)/pdf/이미지)
  actions.py          # ── 조치 계층 ── 마스킹 / AES-256-GCM 격리·복원 / 안전 삭제 + 감사 로그
  report.py           # ── 리포트 계층 ── PDF 진단서 생성(마스킹 값만 기재, reportlab)
  scanner.py          # 스캔 오케스트레이션: 추출→검출, '검사불가' 격리
  cli.py              # 데모 CLI(전체 파이프라인, --report 로 PDF 발급)
tests/                # unittest 41케이스 (핵심은 외부 의존성 0)
examples/             # 데모용 더미 데이터(.py/.xlsx/.hwpx/.pdf)
```

정규식(1차)과 검증 함수(2차)를 독립 모듈로 분리해, 추후 **문맥 기반 AI 판단**으로 2차 검증만 교체·고도화할 수 있다(기획서 6장).

### 파이프라인 (스캔 → 검출 → 조치 → 기록)

```
파일/폴더 ─▶ extractors.extract_text() ─▶ DetectionEngine.scan_text() ─▶ Finding[]
   │              (포맷별, 실패 시 ExtractionError)         │
   │                                                        ▼
   └────────── scanner.scan_paths() (검사불가 격리) ─▶ actions(마스킹/격리/삭제) ─▶ audit.log
```

추출 계층은 한 파일의 파싱 실패가 전체 스캔을 멈추지 않도록 `ExtractionError`로 격리해
`검사불가`로 분리 기록한다(기획서 9장 리스크 #3). `.hwpx`와 `.xlsx`는 표준 라이브러리만으로
동작하고(국내 SI 차별점인 한글 파싱 포함), 나머지 포맷은 선택 의존성이 있을 때 활성화된다.

## 실행

요구사항: Python 3.10+ (개발 환경 3.14 확인). 핵심 기능은 추가 설치 불필요.
포맷 확장은 `pip install -r requirements.txt` 로 선택 활성화.

```powershell
# 테스트 (41케이스)
py -m unittest discover -s tests -t .

# 데모 스캔(폴더: txt/xlsx/hwpx/pdf 혼재, pdf는 라이브러리 없으면 검사불가)
py -m soliguard.cli examples --role developer
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

- **주민번호 체크섬**: 2020-10 이후 신규 발급분은 뒤 6자리가 임의 부여되어 체크섬이 맞지 않을 수 있다. 현재는 검증 실패 시 제외하므로 일부 미탐 가능 → 문맥 신호로 보완 예정.
- **계좌번호**: 은행별 포맷이 다양해 오탐 여지가 있어 느슨하게 검증(`PATTERN_ONLY` 다수). 은행별 규칙 테이블 필요.
- **격리 키 보관**: 데모는 복호화 키를 격리 메타(.meta.json)에 함께 둔다. 실제 제품에선 Windows DPAPI 등 OS 보안 저장소로 분리해야 한다(`actions.quarantine_file` 주석 참조).
- **비텍스트 마스킹**: `mask_in_text_file`은 텍스트 파일만 in-place 사본 마스킹을 지원한다. xlsx/hwp 등 바이너리 포맷은 격리/삭제를 권장(원문 구조 보존 마스킹은 후속 과제).
- **OCR 엔진**: 이미지/스캔 PDF는 `pytesseract` + Tesseract 바이너리(+한국어 데이터)가 있어야 활성화. 기본은 로컬 처리이며 외부 OCR API는 명시적 동의 시에만 연동(기획서 6장).

## 다음 단계

기획서 2~3단계: 직무별 스캔 프로파일 전체(스캔 범위 자동 구성), 프로젝트 클로징 점검, PDF 진단 리포트 발급, SQLite 감사 로그 영구화, 그리고 GUI(PySide/Qt) — 화면설계서·목업스펙을 1:1로 구현. 백엔드 파이프라인(스캔→검출→조치→기록)은 본 코드로 완성되어 GUI가 그 위에 얹히는 구조다.
