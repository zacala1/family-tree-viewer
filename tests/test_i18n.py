"""다국어 지원 유닛 테스트."""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.i18n.translator import Translator, tr, set_language, get_current_language, get_available_languages


class TestTranslator(unittest.TestCase):
    """Translator 클래스 테스트."""

    def setUp(self):
        """테스트 전 언어 초기화."""
        set_language('ko')

    def test_korean_translation(self):
        """한국어 번역 테스트."""
        set_language('ko')

        self.assertEqual(tr('app.name'), '가족관계도')
        self.assertEqual(tr('menu.file'), '파일(&F)')
        self.assertEqual(tr('button.save'), '저장')

    def test_english_translation(self):
        """영어 번역 테스트."""
        set_language('en')

        self.assertEqual(tr('app.name'), 'Family Tree')
        self.assertEqual(tr('menu.file'), '&File')
        self.assertEqual(tr('button.save'), 'Save')

    def test_language_switch(self):
        """언어 전환 테스트."""
        set_language('ko')
        self.assertEqual(tr('button.edit'), '편집')

        set_language('en')
        self.assertEqual(tr('button.edit'), 'Edit')

        set_language('ko')
        self.assertEqual(tr('button.edit'), '편집')

    def test_nested_keys(self):
        """중첩 키 테스트."""
        set_language('ko')

        self.assertEqual(tr('label.name'), '이름')
        self.assertEqual(tr('dialog.save_confirm_title'), '저장')

    def test_missing_key_returns_key(self):
        """누락된 키는 키 자체 반환 테스트."""
        result = tr('nonexistent.key.path')
        self.assertEqual(result, 'nonexistent.key.path')

    def test_format_string(self):
        """문자열 포맷팅 테스트."""
        set_language('ko')

        result = tr('status.member_count', count=5)
        self.assertEqual(result, '구성원: 5명')

        result = tr('status.selected', name='홍길동')
        self.assertEqual(result, '선택됨: 홍길동')

    def test_format_string_english(self):
        """영어 문자열 포맷팅 테스트."""
        set_language('en')

        result = tr('status.member_count', count=10)
        self.assertEqual(result, 'Members: 10')

    def test_get_current_language(self):
        """현재 언어 조회 테스트."""
        set_language('ko')
        self.assertEqual(get_current_language(), 'ko')

        set_language('en')
        self.assertEqual(get_current_language(), 'en')

    def test_get_available_languages(self):
        """사용 가능한 언어 목록 테스트."""
        languages = get_available_languages()

        self.assertIn('ko', languages)
        self.assertIn('en', languages)
        self.assertEqual(languages['ko'], '한국어')
        self.assertEqual(languages['en'], 'English')

    def test_unsupported_language(self):
        """지원하지 않는 언어 설정 테스트."""
        set_language('ko')
        set_language('unsupported_lang')

        # 지원하지 않는 언어는 무시되고 이전 언어 유지
        self.assertEqual(get_current_language(), 'ko')


class TestTranslatorInstance(unittest.TestCase):
    """Translator 인스턴스 직접 테스트."""

    def test_create_translator(self):
        """Translator 인스턴스 생성 테스트."""
        translator = Translator(lang='en')
        self.assertEqual(translator.get_language(), 'en')

    def test_translate_method(self):
        """translate 메서드 테스트."""
        translator = Translator(lang='ko')
        result = translator.translate('app.name')
        self.assertEqual(result, '가족관계도')

    def test_set_language_method(self):
        """set_language 메서드 테스트."""
        translator = Translator(lang='ko')
        translator.set_language('en')
        self.assertEqual(translator.get_language(), 'en')


class TestTranslationCompleteness(unittest.TestCase):
    """번역 완전성 테스트."""

    def test_all_korean_keys_exist_in_english(self):
        """한국어의 모든 키가 영어에도 존재하는지 테스트."""
        import json

        i18n_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'src', 'i18n'
        )

        ko_path = os.path.join(i18n_dir, 'ko.json')
        en_path = os.path.join(i18n_dir, 'en.json')

        with open(ko_path, 'r', encoding='utf-8') as f:
            ko_data = json.load(f)

        with open(en_path, 'r', encoding='utf-8') as f:
            en_data = json.load(f)

        def get_all_keys(data, prefix=''):
            """재귀적으로 모든 키 수집."""
            keys = []
            for k, v in data.items():
                full_key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    keys.extend(get_all_keys(v, full_key))
                else:
                    keys.append(full_key)
            return keys

        ko_keys = set(get_all_keys(ko_data))
        en_keys = set(get_all_keys(en_data))

        missing_in_en = ko_keys - en_keys
        missing_in_ko = en_keys - ko_keys

        self.assertEqual(
            len(missing_in_en), 0,
            f"영어에 누락된 키: {missing_in_en}"
        )
        self.assertEqual(
            len(missing_in_ko), 0,
            f"한국어에 누락된 키: {missing_in_ko}"
        )


if __name__ == '__main__':
    unittest.main()
