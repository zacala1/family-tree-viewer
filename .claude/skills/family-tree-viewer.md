# Family Tree Viewer 프로젝트 작업 가이드

**스택:** Python 3.9+ · PyQt6 6.6+ · pytest · PyInstaller
**저장소:** `C:/Users/zacal/source/repos/family-tree-viewer`
**참고 문서:** `README.md` · `ARCHITECTURE.md` · `CONTRIBUTING.md` · `USER_GUIDE.md` · `CHANGELOG.md` · `docs/API.md`

---

## ⚠️ 절대 규칙

1. **`src/models/` 에는 PyQt6 import 금지** — 100% 순수 Python. GUI 의존성은 `src/views/`에서만.
2. **검증 로직은 `src/models/validators.py`에 집중** — `views/`에서 정규식·길이 체크 직접 작성 금지. `PersonValidator.validate_all(...)` 호출만.
3. **Magic string 금지** — 관계 타입 등은 `RelationshipRequestType` 같은 상수 클래스 사용 (`PARENT`/`SPOUSE`/`CHILD`).
4. **`FamilyTree` 데이터 접근은 RLock 보호 필수** — `with self._lock:` 패턴 유지.
5. **타입 힌트 필수**, **줄길이 ≤ 100자**, **PEP 8**.
6. **i18n 키는 `en.json`·`ko.json` 동기화** — 두 파일 키 수 동일 (현재 221개).
7. **하드코딩 상수 금지** — 모두 `src/config.py`에 집중. 신규 상수도 거기에 추가.

---

## 5-Layer 아키텍처

| 레이어 | 위치 | 책임 | 의존 |
|--------|------|------|------|
| Presentation | `src/views/` | PyQt6 위젯, Signal-Slot | Service, models, validators |
| Service | `src/services/` | 비즈니스 로직 조율 | Repositories |
| Repository | `src/repositories/` | CRUD 추상화 | Models |
| Data | `src/models/` | 도메인 모델 + validators | 없음 (순수 Python) |
| Utility | `src/utils/` | 파일I/O, 로깅, 검색 인덱스, PDF, 사진 등 | 도메인별 최소 |

데이터 흐름 (추가 예): `View → PersonValidator.validate_all → Person.from_dict → FamilyTree.add_person (locked) → person_updated signal → View refresh`

---

## 디자인 패턴

- **Observer** (Signal-Slot): 컴포넌트 간 통신
- **Singleton**: `ThemeManager`, `Translator`, `Logger`, `PerformanceMonitor`
- **Command** (Undo/Redo): `AddPersonCommand`, `DeletePersonCommand`, `UpdatePersonCommand`, `AddRelationshipCommand` — 50-level history. **새 가역 동작은 반드시 `Command` 서브클래스로** (`src/models/command.py`).
- **Strategy**: `FileHandler.load_file` 확장자별 분기 — 새 포맷 추가 시 분기 추가
- **Factory**: `Person.from_dict`, `FamilyTree.from_dict`
- **Validator**: `PersonValidator` 전 함수 정적 메서드
- **Decorator**: `@profile("namespace.fn")` 성능 측정, `measure_time("…")` 컨텍스트 매니저

---

## 자주 쓰는 명령

```bash
python main.py                              # 앱 실행
python -m pytest tests/ -v                  # 전체 테스트
python -m pytest tests/test_<name>.py -v    # 단일 파일
python -m pytest tests/ -v -k <keyword>     # 키워드 매칭
python build.py                             # PyInstaller 빌드 → dist/FamilyTree.exe
pip install -r requirements.txt             # 의존성 설치
```

---

## 데이터/보안 제한 (`src/config.py`)

- 최대 인원: **50,000명**
- 최대 파일: **100MB**
- 최대 사진: **5MB**
- 이름 길이: `MIN_NAME_LENGTH` ~ `MAX_NAME_LENGTH_UNICODE`
- 사망 시 나이: 0~150세
- 이메일: RFC 5322 (`EMAIL_PATTERN`)
- **Path traversal 보호 필수** — 파일 경로는 항상 검증
- 로그: `~/.familytree/logs/familytree.log` (JSON, DEBUG+) / 콘솔 (INFO+)

---

## 파일 형식

| 형식 | I/O | 모듈 |
|------|-----|------|
| JSON (`.json`) | 양방향 (native, 완전 보존) | `utils/file_handler.py` |
| Excel (`.xlsx`) | 양방향 | `utils/file_handler.py` (openpyxl) |
| GEDCOM (`.ged`) | import only | `utils/file_handler.py` |
| PDF (`.pdf`) | export only (Ctrl+P) | `utils/pdf_exporter.py` (QtPrintSupport) |

---

## 신규 기능 추가 체크리스트

1. **상수 → Model → Validator → Service → Repository → View** 순서로 작성
2. `tests/test_<feature>.py` 추가 — 모델은 100% 커버리지 유지
3. i18n 키 추가 시 `en.json` + `ko.json` **둘 다** (개수 일치 유지)
4. 가역 동작이면 `Command` 서브클래스 추가 (`models/command.py`)
5. 무거운 동작은 `@profile("module.fn")` 데코레이터로 감싸 성능 추적
6. 하드코딩 상수는 `src/config.py`에 등록 후 import
7. **`CHANGELOG.md [Unreleased]`** 섹션에 항목 추가 (Keep a Changelog 포맷)
8. 사용자 노출 변경은 `USER_GUIDE.md` 갱신, 필요 시 `README.md`도

---

## 커밋 메시지 (Conventional Commits)

```
type(scope): brief description

본문 (선택): 상세 설명

- 변경 1
- 변경 2
```

**type**: `feat` · `fix` · `docs` · `style` · `refactor` · `test` · `chore`

예시:
- `feat(ui): add export to PDF feature`
- `fix(validation): prevent negative birth years`
- `refactor(models): extract validators to separate module`
- `test(family_tree): add cycle detection edge cases`

---

## 핵심 진입점

| 파일 | 역할 |
|------|------|
| `main.py` | 앱 부트스트랩 |
| `src/config.py` | 모든 상수·제한값·정규식 |
| `src/views/main_window.py` | MainWindow — 전역 단축키·메뉴, `SearchIndex` 사용 |
| `src/views/tree_canvas.py` | 트리 시각화 커스텀 위젯 |
| `src/views/detail_panel.py` | 인물 상세 편집기 |
| `src/models/family_tree.py` | `FamilyTree` — BFS 세대 계산, RLock |
| `src/models/command.py` | Undo/Redo Command 패턴 |
| `src/models/validators.py` | 전 검증 로직 (`PersonValidator`) |
| `src/services/family_tree_service.py` | 비즈니스 로직 조율 (Trie 검색 포함) |
| `src/utils/file_handler.py` | JSON/Excel/GEDCOM 양방향 |
| `src/utils/search_index.py` | Trie 기반 O(m) 검색 |
| `src/utils/duplicate_detector.py` | Levenshtein 유사명 감지 (임계 2) |
| `src/utils/pdf_exporter.py` | Canvas → PDF |
| `tests/` | 100+ unit tests (모델 100% / UI smoke) |
| `data/sample.json` | 샘플 가족 트리 |

---

## 빠른 진단

- **앱이 안 뜨면**: `~/.familytree/logs/familytree.log` 확인
- **테스트 실패 분석**: `python -m pytest tests/ -v --tb=short`
- **빌드 실패**: `build/`·`dist/` 삭제 후 재시도, `pip install pyinstaller` 확인
- **i18n 키 누락 감지**: `en.json` ↔ `ko.json` 키 수 비교
- **느린 동작 추적**: `PerformanceMonitor`가 0.5s 초과 시 자동 경고 로그
