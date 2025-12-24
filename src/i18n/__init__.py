"""다국어 지원 모듈."""
from .translator import Translator, tr, set_language, get_current_language, get_available_languages

__all__ = ['Translator', 'tr', 'set_language', 'get_current_language', 'get_available_languages']
