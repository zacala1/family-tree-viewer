# Family Tree API Documentation

## 목차
- [Core Models](#core-models)
- [Family Tree Manager](#family-tree-manager)
- [Validators](#validators)
- [File Handlers](#file-handlers)
- [Utilities](#utilities)
- [Duplicate Detector](#duplicate-detector)
- [PDF Exporter](#pdf-exporter)
- [Lineage Report Dialog](#lineage-report-dialog)
- [Performance Monitoring](#performance-monitoring)

---

## Core Models

### Person

사람 정보를 나타내는 데이터 클래스입니다.

#### 속성

```python
@dataclass
class Person:
    # 기본 정보
    id: str                          # UUID (자동 생성)
    name: str                        # 이름 (필수)
    gender: Literal["M", "F"]        # 성별

    # 출생 정보
    birth_year: Optional[int]        # 출생년도
    birth_month: Optional[int]       # 출생월 (1-12, 0=미상)
    birth_day: Optional[int]         # 출생일 (1-31, 0=미상)
    is_lunar_birth: bool             # 음력 여부

    # 사망 정보
    death_year: Optional[int]
    death_month: Optional[int]
    death_day: Optional[int]
    is_lunar_death: bool

    # 추가 정보
    birth_place: str                 # 출생지
    current_address: str             # 현주소
    nationality: str                 # 국적 (기본값: "한국")
    occupation: str                  # 직업
    education: str                   # 학력
    phone: str                       # 연락처
    email: str                       # 이메일
    notes: str                       # 메모

    # 사진
    photo_path: Optional[str]        # 사진 경로

    # 이벤트
    events: List[Event]              # 생애 주요 사건

    # 관계 (ID 참조)
    father_id: Optional[str]
    mother_id: Optional[str]
    spouse_ids: List[str]
    children_ids: List[str]

    # 세대 정보
    generation: int                  # 세대 번호 (0부터 시작)
```

#### 주요 메서드

```python
def to_dict(self) -> Dict[str, Any]:
    """Person 객체를 딕셔너리로 변환 (직렬화)."""

@classmethod
def from_dict(cls, data: Dict[str, Any]) -> "Person":
    """딕셔너리에서 Person 객체 생성 (역직렬화)."""
```

#### 속성 (Properties)

```python
@property
def birth_date_str(self) -> str:
    """출생일을 문자열로 반환 (예: "1990년 5월 15일")."""

@property
def death_date_str(self) -> str:
    """사망일을 문자열로 반환."""

@property
def lifespan_str(self) -> str:
    """생애 기간 문자열 (예: "1990.05.15 - 2020.12.31")."""

@property
def is_alive(self) -> bool:
    """생존 여부."""
```

---

### Event

개인의 생애 주요 사건을 나타냅니다.

```python
@dataclass
class Event:
    id: str                          # UUID (자동 생성)
    title: str                       # 제목
    description: str                 # 설명
    event_type: EventType            # 이벤트 유형
    year: Optional[int]
    month: Optional[int]
    day: Optional[int]
    is_lunar: bool
    location: str                    # 장소
    person_id: Optional[str]         # 소속 인물 ID
```

#### EventType

```python
EventType = Literal[
    "birth",        # 출생
    "death",        # 사망
    "marriage",     # 결혼
    "divorce",      # 이혼
    "graduation",   # 졸업
    "employment",   # 취업
    "retirement",   # 퇴직
    "relocation",   # 이사
    "achievement",  # 성취
    "other"         # 기타
]
```

---

### Relationship

두 사람 간의 관계를 나타냅니다.

```python
class Relationship:
    id: str
    person1_id: str
    person2_id: str
    rel_type: RelationType           # 관계 유형

    # 결혼 정보 (배우자 관계의 경우)
    marriage_year: Optional[int]
    marriage_month: Optional[int]
    marriage_day: Optional[int]
    is_lunar_marriage: bool

    # 이혼 정보
    divorce_year: Optional[int]
    divorce_month: Optional[int]
    divorce_day: Optional[int]
```

#### RelationType

```python
class RelationType(Enum):
    PARENT_CHILD = "parent_child"    # 부모-자녀
    SPOUSE = "spouse"                # 배우자
```

#### RelationshipRequestType

관계 추가 요청 타입 상수 (매직 스트링 방지).

```python
class RelationshipRequestType:
    PARENT = "parent"    # 부모 추가 요청
    SPOUSE = "spouse"    # 배우자 추가 요청
    CHILD = "child"      # 자녀 추가 요청
```

---

## Family Tree Manager

### FamilyTree

가계도 전체를 관리하는 중앙 클래스입니다. **스레드 안전**합니다.

#### 인원 관리

```python
def add_person(self, person: Person) -> None:
    """사람 추가.

    Raises:
        ValueError: ID 중복 또는 최대 인원 초과 (50,000명)
    """

def get_person(self, person_id: str) -> Optional[Person]:
    """ID로 사람 조회."""

def get_all_persons(self) -> List[Person]:
    """모든 사람 목록 반환."""

def remove_person(self, person_id: str) -> None:
    """사람 삭제 (관련 관계도 함께 삭제)."""

def update_person(self, person: Person) -> None:
    """사람 정보 업데이트."""
```

#### 관계 관리

```python
def set_parent_child(self, parent_id: str, child_id: str) -> Optional[Relationship]:
    """부모-자녀 관계 설정.

    Returns:
        생성된 Relationship 또는 None (순환 참조 등으로 실패한 경우)
    """

def set_spouse(
    self,
    person1_id: str,
    person2_id: str,
    marriage_year: Optional[int] = None,
    marriage_month: Optional[int] = None,
    marriage_day: Optional[int] = None,
    is_lunar: bool = False,
) -> Optional[Relationship]:
    """배우자 관계 설정."""
```

#### 관계 조회

```python
def get_parents(self, person_id: str) -> List[Person]:
    """부모 목록 반환."""

def get_children(self, person_id: str) -> List[Person]:
    """자녀 목록 반환."""

def get_spouses(self, person_id: str) -> List[Person]:
    """배우자 목록 반환."""

def get_spouse_relationship(self, person1_id: str, person2_id: str) -> Optional[Relationship]:
    """두 사람 간의 배우자 관계 객체 반환."""

def get_spouse_relationships(self, person_id: str) -> List[Relationship]:
    """특정 사람의 모든 배우자 관계 객체 반환."""

def get_current_spouse(self, person_id: str) -> Optional[Person]:
    """현재 배우자(이혼하지 않은) 반환. 여러 명이면 가장 최근 결혼."""

def get_current_spouse_id(self, person_id: str) -> Optional[str]:
    """현재 배우자(이혼하지 않은)의 ID 반환."""

def get_siblings(self, person_id: str) -> List[Person]:
    """형제자매 목록 반환."""

def get_direct_family(self, person_id: str) -> List[Person]:
    """직계 가족 목록 반환 (부모, 배우자, 자녀)."""

def get_direct_family_ids(self, person_id: str) -> Set[str]:
    """직계 가족 ID 집합 반환."""
```

#### 세대 계산

```python
@profile("family_tree.calculate_generations")
def calculate_generations(self, force: bool = False) -> None:
    """세대 정보 계산 (BFS 알고리즘).

    Args:
        force: True면 캐시 무시하고 재계산

    Performance:
        - Time: O(V + E) where V=persons, E=relationships
        - 캐싱으로 불필요한 재계산 방지
    """

def get_persons_by_generation(self) -> Dict[int, List[Person]]:
    """세대별 사람 목록 반환."""
```

#### 직렬화

```python
def to_dict(self) -> dict:
    """딕셔너리로 변환 (JSON 저장용)."""

@classmethod
def from_dict(cls, data: dict) -> "FamilyTree":
    """딕셔너리에서 FamilyTree 객체 생성."""

def clear(self) -> None:
    """모든 데이터 삭제."""
```

#### 수정 상태 관리

```python
@property
def is_modified(self) -> bool:
    """수정 여부."""

def mark_modified(self) -> None:
    """수정됨으로 표시."""

def mark_saved(self) -> None:
    """저장됨으로 표시."""
```

---

## Validators

### PersonValidator

비즈니스 로직 검증 클래스입니다.

```python
class PersonValidator:
    @staticmethod
    def validate_name(name: str) -> Tuple[bool, str]:
        """이름 검증.

        Returns:
            (is_valid, error_message)
        """

    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """이메일 형식 검증 (RFC 5322 간소화)."""

    @staticmethod
    def validate_phone(phone: str) -> Tuple[bool, str]:
        """전화번호 형식 검증."""

    @staticmethod
    def validate_date(
        year: Optional[int],
        month: Optional[int],
        day: Optional[int]
    ) -> Tuple[bool, str]:
        """날짜 검증."""

    @staticmethod
    def validate_lifespan(
        birth_year: Optional[int],
        birth_month: Optional[int],
        birth_day: Optional[int],
        death_year: Optional[int],
        death_month: Optional[int],
        death_day: Optional[int]
    ) -> Tuple[bool, str]:
        """출생일-사망일 관계 검증."""

    @staticmethod
    def validate_all(...) -> Tuple[bool, str]:
        """모든 Person 데이터 검증."""
```

---

## File Handlers

### FileHandler

파일 입출력 담당 클래스입니다.

```python
class FileHandler:
    @staticmethod
    def load_file(file_path: str) -> Optional[FamilyTree]:
        """파일 로드 (자동 형식 감지: JSON, Excel, GEDCOM).

        Returns:
            FamilyTree 객체 또는 None (실패 시)
        """

    @staticmethod
    def save_file(family_tree: FamilyTree, file_path: str) -> bool:
        """파일 저장 (확장자 기반: .json, .xlsx).

        Returns:
            성공 여부
        """

    @staticmethod
    def get_open_filters() -> str:
        """파일 열기 다이얼로그용 필터 문자열."""

    @staticmethod
    def get_save_filters() -> str:
        """파일 저장 다이얼로그용 필터 문자열."""
```

#### 지원 형식

- **JSON** (`.json`): 모든 데이터 완벽 보존
- **Excel** (`.xlsx`): 표 형식 export (관계 정보 일부 제한)
- **GEDCOM** (`.ged`): 표준 가계도 형식 (import only)

---

## Utilities

### Logger

구조화된 로깅 시스템입니다.

```python
# 기본 로깅 함수
def debug(msg: str) -> None:
    """디버그 로그."""

def info(msg: str) -> None:
    """정보 로그."""

def warning(msg: str) -> None:
    """경고 로그."""

def error(msg: str) -> None:
    """오류 로그."""

def critical(msg: str) -> None:
    """치명적 오류 로그."""

# 구조화된 로깅
def log_action(action: str, person_id: Optional[str] = None, **kwargs: Any) -> None:
    """구조화된 액션 로그 (JSON 형식).

    Example:
        log_action("person_added", person_id="123", name="홍길동")

    Output (JSON 파일):
        {
            "timestamp": "2026-01-01T12:34:56.789",
            "level": "INFO",
            "action": "person_added",
            "person_id": "123",
            "name": "홍길동"
        }
    """

# 로그 레벨 설정
def set_log_level(level_name: str) -> None:
    """로그 레벨 설정.

    Args:
        level_name: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
    """
```

#### 로그 파일 위치

- **콘솔**: INFO 레벨 이상 (사람이 읽기 쉬운 형식)
- **파일**: `~/.familytree/logs/familytree.log` (JSON 형식, DEBUG 레벨 포함)

---

## Duplicate Detector

`src/utils/duplicate_detector.py` — 유사한 이름의 인물을 찾아 중복 입력을 방지합니다.

### 함수

```python
def normalize_name(name: str) -> str
```
이름을 정규화합니다 (공백 제거 + 소문자 변환).

```python
def levenshtein_distance(s1: str, s2: str) -> int
```
두 문자열 간 레벤슈타인 편집 거리를 반환합니다. 삽입/삭제/치환 각 1.

```python
def find_similar_persons(
    name: str,
    persons: List[Person],
    threshold: int = 2,
    exclude_id: str = "",
) -> List[Tuple[Person, int]]
```

**파라미터:**
- `name`: 검색할 이름
- `persons`: 검색 대상 인물 목록
- `threshold`: 최대 편집 거리 (이하면 유사로 간주, 기본 2)
- `exclude_id`: 결과에서 제외할 인물 ID (편집 시 자기 자신 제외용)

**반환:** `(Person, distance)` 튜플 리스트, 거리 오름차순 정렬.

### 사용 예제

```python
from src.utils.duplicate_detector import find_similar_persons

persons = family_tree.get_all_persons()
similar = find_similar_persons("김서준", persons, threshold=2)
for person, dist in similar:
    print(f"{person.name} (편집거리 {dist})")
```

`MainWindow._check_duplicate_name()`에서 호출되어 `_on_person_updated()`가
이름 변경을 감지했을 때 경고 다이얼로그를 띄웁니다.

---

## PDF Exporter

`src/utils/pdf_exporter.py` — 가계도 캔버스를 PDF 파일로 내보냅니다.

PyQt6의 `QtPrintSupport` 모듈을 사용하므로 추가 의존성이 필요하지 않습니다.

### PdfExporter

```python
class PdfExporter:
    @staticmethod
    def is_available() -> bool
```
PDF 내보내기가 가능한지 여부 (`QtPrintSupport` import 성공 여부).

```python
    @staticmethod
    def export(
        canvas: TreeCanvas,
        file_path: str,
        landscape: bool = True,
    ) -> bool
```

**파라미터:**
- `canvas`: 그릴 `TreeCanvas` 인스턴스
- `file_path`: 저장할 PDF 경로
- `landscape`: 가로 방향 여부 (기본 True)

**반환:** 성공 여부 (bool).

**동작:**
- `QPrinter` (HighResolution, PdfFormat) 생성
- 15 mm 여백, 랜드스케이프 기본
- 캔버스의 모든 노드를 포함하는 바운딩 박스 계산 → 페이지에 자동 맞춤 (최대 3배 스케일)
- `canvas._draw_connections()` / `canvas._draw_nodes()`를 직접 호출하여 벡터 렌더링
- 실패 시 로그 기록 후 `False` 반환

### 사용 예제

```python
from src.utils.pdf_exporter import PdfExporter

if PdfExporter.is_available():
    success = PdfExporter.export(tree_canvas, "/path/to/tree.pdf")
```

메인 윈도우의 **File → Export PDF** (`Ctrl+P`)에서 호출됩니다.

---

## Lineage Report Dialog

`src/views/lineage_report_dialog.py` — 특정 인물의 후손/조상 계보를 텍스트
트리로 표시하는 다이얼로그입니다.

### LineageReportDialog

```python
class LineageReportDialog(QDialog):
    def __init__(
        self,
        family_tree: FamilyTree,
        person_id: str,
        mode: str = "descendants",  # "descendants" | "ancestors"
        parent: QWidget | None = None,
    )
```

**파라미터:**
- `family_tree`: 가계도 모델
- `person_id`: 리포트 대상 인물 ID
- `mode`: `"descendants"`(후손) 또는 `"ancestors"`(조상)

**특징:**
- 재귀 트리 구축, `visited: Set[str]`로 순환 방지
- 들여쓰기된 텍스트 출력 (`├─ 이름 (생몰)`)
- 읽기 전용 `QTextEdit`에 표시

### 사용 예제

```python
from src.views.lineage_report_dialog import LineageReportDialog

dlg = LineageReportDialog(family_tree, person_id, "descendants", parent=self)
dlg.exec()
```

트리 뷰에서 인물을 우클릭 → **후손 보기 / 조상 보기**로 호출됩니다.

---

## Performance Monitoring

### PerformanceMonitor

성능 메트릭 수집 클래스입니다.

```python
def get_performance_monitor() -> PerformanceMonitor:
    """전역 성능 모니터 인스턴스 반환."""

class PerformanceMonitor:
    def record(self, operation: str, duration: float) -> None:
        """작업 수행 시간 기록."""

    def get_stats(self, operation: str) -> Optional[Dict[str, float]]:
        """작업의 통계 반환 (count, total, average, min, max)."""

    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """모든 작업의 통계 반환."""

    def log_stats(self) -> None:
        """수집된 통계를 로그로 출력."""

    def clear(self) -> None:
        """메트릭 초기화."""
```

### 사용 예제

#### 컨텍스트 매니저

```python
from src.utils.performance import measure_time

with measure_time("load_file"):
    tree = FileHandler.load_file(path)
```

#### 데코레이터

```python
from src.utils.performance import profile

@profile("my_operation")
def my_function():
    # 자동으로 실행 시간 측정
    ...
```

#### 통계 확인

```python
from src.utils.performance import log_performance_stats

# 프로그램 종료 전
log_performance_stats()

# 출력 예:
# === Performance Statistics ===
# family_tree.calculate_generations: avg=0.005s, min=0.002s, max=0.015s, count=10
# load_file: avg=0.120s, min=0.100s, max=0.200s, count=3
```

---

## Configuration

### config.py

모든 상수는 `src/config.py`에 중앙 관리됩니다.

```python
# 데이터 모델 제한
MAX_PERSONS = 50000              # 최대 인원
MAX_CYCLE_DEPTH = 50             # 순환 감지 최대 깊이

# 레이아웃
CARD_WIDTH = 120
CARD_HEIGHT = 80
CARD_SPACING_X = 40
CARD_SPACING_Y = 100

# 날짜 검증
YEAR_MIN = 1800
YEAR_MAX = 2100

# 텍스트 길이 제한
MAX_NAME_LENGTH = 100
MAX_TEXT_LENGTH = 500
MAX_EMAIL_LENGTH = 100
MAX_PHONE_LENGTH = 50
MAX_NOTES_LENGTH = 5000

# 파일 제한
MAX_FILE_SIZE = 100 * 1024 * 1024    # 100 MB
MAX_PHOTO_SIZE = 5 * 1024 * 1024     # 5 MB

# 기본값
DEFAULT_NATIONALITY = "한국"

# 검증 패턴
EMAIL_PATTERN = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
PHONE_PATTERN = r"^[\+\d][\d\-\s\(\)]{7,}$"
```

---

## Command Pattern (Undo/Redo)

### UndoRedoManager

실행 취소/다시 실행 관리자입니다.

```python
class UndoRedoManager:
    def __init__(self, max_history: int = 50):
        """최대 50개 히스토리 유지."""

    def execute(self, command: Command) -> None:
        """명령 실행 및 undo 스택에 추가."""

    def can_undo(self) -> bool:
        """실행 취소 가능 여부."""

    def can_redo(self) -> bool:
        """다시 실행 가능 여부."""

    def undo(self) -> Optional[str]:
        """실행 취소. 취소된 작업 설명 반환."""

    def redo(self) -> Optional[str]:
        """다시 실행. 재실행된 작업 설명 반환."""
```

### 사용 가능한 Command

- `AddPersonCommand(family_tree, person)`
- `DeletePersonCommand(family_tree, person_id)`
- `UpdatePersonCommand(family_tree, person_id, new_data)`
- `AddRelationshipCommand(family_tree, parent_id, child_id)`

---

## 국제화 (i18n)

### Translator

```python
def tr(key: str, **kwargs) -> str:
    """번역 문자열 반환.

    Args:
        key: 번역 키 (예: "button.save")
        **kwargs: 포맷 파라미터 (예: count=5)

    Returns:
        번역된 문자열

    Example:
        tr("status.member_count", count=10)  # "Members: 10"
    """

def set_language(lang_code: str) -> None:
    """언어 설정 ("en", "ko")."""

def get_current_language() -> str:
    """현재 언어 코드 반환."""

def get_available_languages() -> Dict[str, str]:
    """사용 가능한 언어 목록."""
```

---

## 스레드 안전성

### 스레드 안전 클래스

- ✅ **FamilyTree**: 모든 메서드가 RLock으로 보호
  - `is_modified`, `mark_modified()`, `mark_saved()`
  - `add_person()`, `get_person()`, `get_all_persons()`, `remove_person()`, `update_person()`
  - `add_relationship()`, `get_relationship()`, `get_all_relationships()`, `remove_relationship()`
  - `set_parent_child()`, `set_spouse()`
  - `get_spouse_relationship()`, `get_spouse_relationships()`
  - `_would_create_cycle()` (내부 메서드)
- ✅ **AppLogger**: 싱글톤, Double-check locking
- ✅ **PerformanceMonitor**: 싱글톤

### RLock (Reentrant Lock)

FamilyTree는 RLock을 사용하므로 같은 스레드에서 재진입이 가능합니다.

```python
# 예: set_parent_child는 내부적으로 add_relationship를 호출
# 둘 다 락을 획득하지만, RLock이므로 데드락 없음
def set_parent_child(self, parent_id: str, child_id: str):
    with self._lock:  # 첫 번째 락 획득
        # ...
        self.add_relationship(rel)  # 내부에서 다시 락 획득 (재진입 성공)
```

### 주의사항

- UI 조작은 반드시 메인 스레드에서 수행
- PyQt6 Signal/Slot 사용 권장

---

## 예제 코드

### 기본 사용법

```python
from src.models.family_tree import FamilyTree
from src.models.person import Person

# 가계도 생성
tree = FamilyTree()

# 사람 추가
father = Person(name="홍길동", gender="M", birth_year=1950)
mother = Person(name="김영희", gender="F", birth_year=1955)
son = Person(name="홍철수", gender="M", birth_year=1980)

tree.add_person(father)
tree.add_person(mother)
tree.add_person(son)

# 관계 설정
tree.set_parent_child(father.id, son.id)
tree.set_parent_child(mother.id, son.id)
tree.set_spouse(father.id, mother.id, marriage_year=1975)

# 세대 계산
tree.calculate_generations()

# 조회
parents = tree.get_parents(son.id)  # [father, mother]
children = tree.get_children(father.id)  # [son]

# 저장
from src.utils.file_handler import FileHandler
FileHandler.save_file(tree, "my_family.json")

# 로드
tree = FileHandler.load_file("my_family.json")
```

### Undo/Redo 예제

```python
from src.models.command import UndoRedoManager, AddPersonCommand

manager = UndoRedoManager()

# 사람 추가 (undo 가능)
person = Person(name="테스트")
command = AddPersonCommand(tree, person)
manager.execute(command)

# 실행 취소
manager.undo()  # person 삭제됨

# 다시 실행
manager.redo()  # person 다시 추가됨
```

### 성능 모니터링 예제

```python
from src.utils.performance import measure_time, log_performance_stats

# 측정
with measure_time("big_operation"):
    for i in range(1000):
        person = Person(name=f"Person {i}")
        tree.add_person(person)

# 통계 출력
log_performance_stats()
```

---

## 보안 고려사항

### 입력 검증

- ✅ **Path Traversal 방지**: `os.path.basename()` 사용
- ✅ **파일 크기 제한**: 100MB (GEDCOM), 5MB (사진)
- ✅ **이메일/전화번호 정규식 검증**: `EMAIL_PATTERN`, `PHONE_PATTERN`
- ✅ **HTML Sanitization**: XSS 방지 (최대 200자)
- ✅ **순환 참조 방지**: BFS 기반 사이클 감지
- ✅ **매직 스트링 제거**: `RelationshipRequestType` 상수 클래스 사용

### 제한 사항

- **최대 인원**: 50,000명 (`MAX_PERSONS`)
- **최대 검색 쿼리 길이**: 100자 (`MAX_SEARCH_QUERY_LENGTH`)
- **이름 길이**: 100자 (`MAX_NAME_LENGTH`)
- **노트 길이**: 5,000자 (`MAX_NOTES_LENGTH`)
- **순환 감지 깊이**: 50세대 (`MAX_CYCLE_DEPTH`) - 경고만 발생, 계속 검사

---

## 라이선스

이 프로젝트는 내부 사용을 위한 것입니다.
