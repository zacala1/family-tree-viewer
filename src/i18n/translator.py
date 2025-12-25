"""다국어 번역 시스템."""
import json
import os
from typing import Dict, Optional

# 전역 번역기 인스턴스
_translator: Optional['Translator'] = None


class Translator:
    """다국어 번역을 관리하는 클래스."""

    def __init__(self, lang: str = 'en'):
        self._current_lang = lang
        self._translations: Dict[str, Dict[str, str]] = {}
        self._load_translations()

    def _load_translations(self):
        """번역 파일들을 로드."""
        i18n_dir = os.path.dirname(__file__)

        for lang_file in ['ko.json', 'en.json']:
            file_path = os.path.join(i18n_dir, lang_file)
            lang_code = lang_file.replace('.json', '')

            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self._translations[lang_code] = json.load(f)
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    from ..utils.logger import error
                    error(f"Translation file load error ({lang_file}): {e}")
                    self._translations[lang_code] = {}
                except Exception as e:
                    from ..utils.logger import error
                    error(f"Unexpected error loading translation ({lang_file}): {e}")
                    self._translations[lang_code] = {}

    def set_language(self, lang: str):
        """언어 설정."""
        if lang in self._translations:
            self._current_lang = lang
        else:
            from ..utils.logger import warning
            warning(f"Unsupported language: {lang}")

    def get_language(self) -> str:
        """현재 언어 반환."""
        return self._current_lang

    def get_available_languages(self) -> Dict[str, str]:
        """사용 가능한 언어 목록 반환."""
        return {
            'ko': '한국어',
            'en': 'English'
        }

    def translate(self, key: str, **kwargs) -> str:
        """
        키를 현재 언어로 번역.

        Args:
            key: 번역 키 (예: 'menu.file', 'button.save')
            **kwargs: 문자열 포맷팅 인자

        Returns:
            번역된 문자열, 키가 없으면 키 자체 반환
        """
        translations = self._translations.get(self._current_lang, {})

        # 중첩 키 지원 (예: 'menu.file')
        keys = key.split('.')
        value = translations

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                value = None
                break

        if value is None:
            # 폴백: 영어 시도
            if self._current_lang != 'en':
                en_translations = self._translations.get('en', {})
                value = en_translations
                for k in keys:
                    if isinstance(value, dict):
                        value = value.get(k)
                    else:
                        value = None
                        break

        if value is None:
            return key

        # 문자열 포맷팅
        if kwargs:
            try:
                value = value.format(**kwargs)
            except KeyError:
                pass

        return value


def get_translator() -> Translator:
    """전역 번역기 인스턴스 반환."""
    global _translator
    if _translator is None:
        _translator = Translator()
    return _translator


def tr(key: str, **kwargs) -> str:
    """
    번역 단축 함수.

    사용예:
        tr('menu.file')  # '파일' 또는 'File'
        tr('message.count', count=5)  # '5개 항목'
    """
    return get_translator().translate(key, **kwargs)


def set_language(lang: str):
    """언어 설정 단축 함수."""
    get_translator().set_language(lang)


def get_current_language() -> str:
    """현재 언어 반환."""
    return get_translator().get_language()


def get_available_languages() -> Dict[str, str]:
    """사용 가능한 언어 목록 반환."""
    return get_translator().get_available_languages()
