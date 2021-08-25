from alisu.utils.localization import get_locale_string, langdict, default_language
from functools import partial
from typing import Optional


def get_bot_locale_string_simple(
    category: str,
    string_name: str,
    language: Optional[str] = default_language,
):
    strings = partial(
        get_locale_string,
        langdict[language].get(category, langdict[default_language][category]),
        language,
        category,
    )
    res = strings(string_name)
    return res
