from django.conf import settings
from django.utils.translation import get_language


LANGUAGE_META = {
    "en": {
        "code": "en",
        "name": "English",
        "native_name": "English",
        "flag": "🇬🇧",
    },
    "fr": {
        "code": "fr",
        "name": "French",
        "native_name": "Français",
        "flag": "🇫🇷",
    },
    "sw": {
        "code": "sw",
        "name": "Swahili",
        "native_name": "Kiswahili",
        "flag": "🇹🇿",
    },
    "pt": {
        "code": "pt",
        "name": "Portuguese",
        "native_name": "Português",
        "flag": "🇵🇹",
    },
}


def language_switcher_context(request):
    current_language = get_language() or settings.LANGUAGE_CODE

    languages = []
    for code, _name in settings.LANGUAGES:
        meta = LANGUAGE_META.get(code, {
            "code": code,
            "name": code.upper(),
            "native_name": code.upper(),
            "flag": "🌍",
        })
        languages.append(meta)

    current_language_meta = LANGUAGE_META.get(current_language, {
        "code": current_language,
        "name": current_language.upper(),
        "native_name": current_language.upper(),
        "flag": "🌍",
    })

    return {
        "language_switcher_languages": languages,
        "current_language_meta": current_language_meta,
    }