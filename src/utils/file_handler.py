"""파일 Import/Export 핸들러."""
import json
import os
from typing import Optional
from datetime import datetime

try:
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

from ..models.family_tree import FamilyTree
from ..models.person import Person


class FileHandler:
    """파일 Import/Export를 처리하는 클래스."""

    # 지원 파일 형식
    SUPPORTED_FORMATS = {
        'json': 'Family Tree JSON (*.json)',
        'xlsx': 'Excel Workbook (*.xlsx)',
        'gedcom': 'GEDCOM (*.ged)',
    }

    @staticmethod
    def get_save_filters() -> str:
        """저장 다이얼로그용 필터 문자열."""
        return ";;".join([
            "Family Tree JSON (*.json)",
            "Excel Workbook (*.xlsx)",
        ])

    @staticmethod
    def get_open_filters() -> str:
        """열기 다이얼로그용 필터 문자열."""
        return ";;".join([
            "All Supported Files (*.json *.xlsx *.ged)",
            "Family Tree JSON (*.json)",
            "Excel Workbook (*.xlsx)",
            "GEDCOM (*.ged)",
        ])

    # === JSON ===

    @staticmethod
    def save_json(tree: FamilyTree, file_path: str) -> bool:
        """JSON 형식으로 저장."""
        try:
            data = tree.to_dict()
            data['_meta'] = {
                'version': '1.0',
                'created': datetime.now().isoformat(),
                'app': 'FamilyTree'
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"JSON 저장 오류: {e}")
            return False

    @staticmethod
    def load_json(file_path: str) -> Optional[FamilyTree]:
        """JSON 파일 로드."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return FamilyTree.from_dict(data)
        except Exception as e:
            print(f"JSON 로드 오류: {e}")
            return None

    # === Excel ===

    @staticmethod
    def save_excel(tree: FamilyTree, file_path: str) -> bool:
        """Excel 형식으로 저장."""
        if not HAS_OPENPYXL:
            print("openpyxl 라이브러리가 설치되지 않았습니다.")
            return False

        try:
            wb = Workbook()
            ws = wb.active
            ws.title = "가족 구성원"

            # 헤더 스타일
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="4A4A4A", end_color="4A4A4A", fill_type="solid")
            header_align = Alignment(horizontal="center", vertical="center")

            # 헤더
            headers = [
                "ID", "이름", "성별", "출생연도", "출생월", "출생일", "음력여부",
                "사망연도", "사망월", "사망일", "출생지", "현주소", "직업",
                "학력", "연락처", "이메일", "메모", "아버지ID", "어머니ID",
                "배우자ID", "세대"
            ]

            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_align

            # 데이터
            for row, person in enumerate(tree.get_all_persons(), 2):
                ws.cell(row=row, column=1, value=person.id)
                ws.cell(row=row, column=2, value=person.name)
                ws.cell(row=row, column=3, value="남" if person.gender == 'M' else "여")
                ws.cell(row=row, column=4, value=person.birth_year)
                ws.cell(row=row, column=5, value=person.birth_month)
                ws.cell(row=row, column=6, value=person.birth_day)
                ws.cell(row=row, column=7, value="예" if person.is_lunar_birth else "아니오")
                ws.cell(row=row, column=8, value=person.death_year)
                ws.cell(row=row, column=9, value=person.death_month)
                ws.cell(row=row, column=10, value=person.death_day)
                ws.cell(row=row, column=11, value=person.birth_place)
                ws.cell(row=row, column=12, value=person.current_address)
                ws.cell(row=row, column=13, value=person.occupation)
                ws.cell(row=row, column=14, value=person.education)
                ws.cell(row=row, column=15, value=person.phone)
                ws.cell(row=row, column=16, value=person.email)
                ws.cell(row=row, column=17, value=person.notes)
                ws.cell(row=row, column=18, value=person.father_id)
                ws.cell(row=row, column=19, value=person.mother_id)
                ws.cell(row=row, column=20, value=",".join(person.spouse_ids))
                ws.cell(row=row, column=21, value=person.generation)

            # 열 너비 자동 조정
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        cell_value = str(cell.value) if cell.value is not None else ""
                        if len(cell_value) > max_length:
                            max_length = len(cell_value)
                    except (TypeError, ValueError):
                        pass
                ws.column_dimensions[column].width = min(max_length + 2, 50)

            wb.save(file_path)
            return True

        except Exception as e:
            print(f"Excel 저장 오류: {e}")
            return False

    @staticmethod
    def load_excel(file_path: str) -> Optional[FamilyTree]:
        """Excel 파일 로드."""
        if not HAS_OPENPYXL:
            print("openpyxl 라이브러리가 설치되지 않았습니다.")
            return None

        try:
            wb = load_workbook(file_path)
            ws = wb.active

            tree = FamilyTree()

            # 헤더 건너뛰고 데이터 읽기
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row[0]:  # ID가 없으면 건너뛰기
                    continue

                gender_str = row[2] if row[2] else "남"
                gender = 'M' if gender_str == "남" else 'F'

                lunar_str = row[6] if row[6] else "아니오"
                is_lunar = lunar_str == "예"

                spouse_ids = []
                if row[19]:
                    spouse_ids = [s.strip() for s in str(row[19]).split(",") if s.strip()]

                person = Person(
                    id=str(row[0]),
                    name=str(row[1]) if row[1] else "",
                    gender=gender,
                    birth_year=int(row[3]) if row[3] else None,
                    birth_month=int(row[4]) if row[4] else None,
                    birth_day=int(row[5]) if row[5] else None,
                    is_lunar_birth=is_lunar,
                    death_year=int(row[7]) if row[7] else None,
                    death_month=int(row[8]) if row[8] else None,
                    death_day=int(row[9]) if row[9] else None,
                    birth_place=str(row[10]) if row[10] else "",
                    current_address=str(row[11]) if row[11] else "",
                    occupation=str(row[12]) if row[12] else "",
                    education=str(row[13]) if row[13] else "",
                    phone=str(row[14]) if row[14] else "",
                    email=str(row[15]) if row[15] else "",
                    notes=str(row[16]) if row[16] else "",
                    father_id=str(row[17]) if row[17] else None,
                    mother_id=str(row[18]) if row[18] else None,
                    spouse_ids=spouse_ids,
                    generation=int(row[20]) if row[20] else 0,
                )

                tree.add_person(person)

            # 부모 참조에서 children_ids 복구
            FileHandler._rebuild_children_ids(tree)

            tree.mark_saved()
            return tree

        except Exception as e:
            print(f"Excel 로드 오류: {e}")
            return None

    @staticmethod
    def _rebuild_children_ids(tree: FamilyTree) -> None:
        """부모 참조로부터 children_ids를 복구."""
        for person in tree.get_all_persons():
            if person.father_id:
                father = tree.get_person(person.father_id)
                if father and person.id not in father.children_ids:
                    father.children_ids.append(person.id)
            if person.mother_id:
                mother = tree.get_person(person.mother_id)
                if mother and person.id not in mother.children_ids:
                    mother.children_ids.append(person.id)

    # === GEDCOM ===

    @staticmethod
    def load_gedcom(file_path: str) -> Optional[FamilyTree]:
        """GEDCOM 파일 로드 (기본 파싱)."""
        try:
            tree = FamilyTree()
            persons = {}  # GEDCOM ID -> Person
            families = {}  # GEDCOM FAM ID -> {husb, wife, children}

            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()

            current_record = None
            current_id = None
            current_data = {}

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                parts = line.split(' ', 2)
                level = int(parts[0])
                tag = parts[1] if len(parts) > 1 else ""
                value = parts[2] if len(parts) > 2 else ""

                # 새 레코드 시작
                if level == 0:
                    # 이전 레코드 저장
                    if current_record == 'INDI' and current_id:
                        persons[current_id] = current_data.copy()
                    elif current_record == 'FAM' and current_id:
                        families[current_id] = current_data.copy()

                    current_data = {}

                    if tag.startswith('@') and value in ('INDI', 'FAM'):
                        current_id = tag
                        current_record = value
                    else:
                        current_record = None
                        current_id = None

                elif current_record == 'INDI':
                    if tag == 'NAME':
                        # 이름에서 /성/ 제거
                        name = value.replace('/', '').strip()
                        current_data['name'] = name
                    elif tag == 'SEX':
                        current_data['gender'] = value
                    elif tag == 'BIRT':
                        current_data['_in_birth'] = True
                    elif tag == 'DEAT':
                        current_data['_in_death'] = True
                    elif tag == 'DATE' and current_data.get('_in_birth'):
                        current_data['birth_date'] = value
                        current_data['_in_birth'] = False
                    elif tag == 'DATE' and current_data.get('_in_death'):
                        current_data['death_date'] = value
                        current_data['_in_death'] = False

                elif current_record == 'FAM':
                    if tag == 'HUSB':
                        current_data['husb'] = value
                    elif tag == 'WIFE':
                        current_data['wife'] = value
                    elif tag == 'CHIL':
                        if 'children' not in current_data:
                            current_data['children'] = []
                        current_data['children'].append(value)

            # 마지막 레코드 저장
            if current_record == 'INDI' and current_id:
                persons[current_id] = current_data
            elif current_record == 'FAM' and current_id:
                families[current_id] = current_data

            # Person 객체 생성
            id_map = {}  # GEDCOM ID -> UUID
            for ged_id, data in persons.items():
                person = Person(
                    name=data.get('name', ''),
                    gender=data.get('gender', 'M'),
                )

                # 날짜 파싱 시도
                if 'birth_date' in data:
                    year = FileHandler._parse_gedcom_year(data['birth_date'])
                    if year:
                        person.birth_year = year

                if 'death_date' in data:
                    year = FileHandler._parse_gedcom_year(data['death_date'])
                    if year:
                        person.death_year = year

                tree.add_person(person)
                id_map[ged_id] = person.id

            # 관계 설정
            for fam_data in families.values():
                husb_id = id_map.get(fam_data.get('husb'))
                wife_id = id_map.get(fam_data.get('wife'))
                children = [id_map.get(c) for c in fam_data.get('children', []) if id_map.get(c)]

                # 배우자 관계
                if husb_id and wife_id:
                    tree.set_spouse(husb_id, wife_id)

                # 부모-자녀 관계
                for child_id in children:
                    if husb_id:
                        tree.set_parent_child(husb_id, child_id)
                    if wife_id:
                        tree.set_parent_child(wife_id, child_id)

            tree.mark_saved()
            return tree

        except Exception as e:
            print(f"GEDCOM 로드 오류: {e}")
            return None

    @staticmethod
    def _parse_gedcom_year(date_str: str) -> Optional[int]:
        """GEDCOM 날짜에서 연도 추출."""
        import re
        match = re.search(r'\b(\d{4})\b', date_str)
        if match:
            return int(match.group(1))
        return None

    # === 자동 감지 로드 ===

    @staticmethod
    def load_file(file_path: str) -> Optional[FamilyTree]:
        """파일 확장자에 따라 자동으로 적절한 로더 사용."""
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.json':
            return FileHandler.load_json(file_path)
        elif ext == '.xlsx':
            return FileHandler.load_excel(file_path)
        elif ext == '.ged':
            return FileHandler.load_gedcom(file_path)
        else:
            print(f"지원하지 않는 파일 형식: {ext}")
            return None

    @staticmethod
    def save_file(tree: FamilyTree, file_path: str) -> bool:
        """파일 확장자에 따라 자동으로 적절한 저장 방식 사용."""
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.json':
            return FileHandler.save_json(tree, file_path)
        elif ext == '.xlsx':
            return FileHandler.save_excel(tree, file_path)
        else:
            # 기본은 JSON
            if not file_path.endswith('.json'):
                file_path += '.json'
            return FileHandler.save_json(tree, file_path)
