import inspect
import json
import os.path
from functools import partial, wraps
from glob import glob
from typing import Dict, List
from pathlib import Path as pypathlibpath

from pyrogram import enums
from pyrogram.types import CallbackQuery, InlineQuery, Message

from alisu.database import groups, users, channels
from alisu.utils.consts import group_types

enabled_locales: List[str] = [
    "ckb-IR",  # Sorani (Kurdish)
    "de-DE",  # German
    "en-GB",  # English
    "en-US",  # English (United States)
    "fr-FR",  # French
    "he-IL",  # Hebrew
    "it-IT",  # Italian
]

default_language: str = "en-GB"


async def set_db_lang(
    chat_id: int,
    chat_type: str,
    lang_code: str,
):
    if chat_type == enums.ChatType.PRIVATE:
        await users.filter(user_id=chat_id).update(chat_lang=lang_code)
    elif chat_type in group_types:  # groups and supergroups share the same table
        await groups.filter(chat_id=chat_id).update(chat_lang=lang_code)
    elif chat_type == enums.ChatType.CHANNEL:
        await channels.filter(chat_id=chat_id).update(chat_lang=lang_code)
    else:
        raise TypeError("Unknown chat type '%s'." % chat_type)


async def get_db_lang(chat_id: int, chat_type: str) -> str:
    if chat_type == enums.ChatType.PRIVATE:
        ul = (await users.get(user_id=chat_id)).chat_lang
    elif chat_type in group_types:  # groups and supergroups share the same table
        ul = (await groups.get(chat_id=chat_id)).chat_lang
    elif chat_type == enums.ChatType.CHANNEL:
        ul = (await channels.get(chat_id=chat_id)).chat_lang
    else:
        raise TypeError("Unknown chat type '%s'." % chat_type)
    return ul if ul else None


def cache_localizations(files: List[str]) -> Dict[str, Dict[str, Dict[str, str]]]:
    ldict = {lang: {} for lang in enabled_locales}
    for file in files:
        _, lname, pname = file.split(os.path.sep)
        pname = pname.split(".")[0]
        dic = json.load(open(file, encoding="utf-8"))
        dic.update(ldict[lname].get(pname, {}))
        ldict[lname][pname] = dic
    return ldict


jsons: List[str] = []

for locale in enabled_locales:
    jsons += glob(os.path.join("locales", locale, "*.json"))

langdict = cache_localizations(jsons)


bot_locales_categories_names_list: List[str] = [
    pypathlibpath(x).stem
    for x in glob(os.path.join("locales", default_language, "*.json"))
]


def get_locale_string(
    dic: dict,
    language: str,
    default_context: str,
    key: str,
    context: str = None,
) -> str:
    if context:
        default_context = context
        dic = langdict[language].get(context, langdict[default_language][context])
    res: str = (
        dic.get(key) or langdict[default_language][default_context].get(key) or key
    )
    return res


async def get_lang(message) -> str:
    if isinstance(message, CallbackQuery):
        chat = message.message.chat
    elif isinstance(message, Message):
        chat = message.chat
    elif isinstance(message, InlineQuery):
        chat, chat.type = message.from_user, enums.ChatType.PRIVATE
    else:
        raise TypeError(f"Update type '{message.__name__}' is not supported.")

    lang = await get_db_lang(chat.id, chat.type)

    if chat.type == enums.ChatType.PRIVATE:
        lang = lang or message.from_user.language_code or default_language
    else:
        lang = lang or default_language
    # User has a language_code without hyphen
    if len(lang.split("-")) == 1:
        # Try to find a language that starts with the provided language_code
        for locale_ in enabled_locales:
            if locale_.startswith(lang):
                lang = locale_
    elif lang.split("-")[1].islower():
        lang = lang.split("-")
        lang[1] = lang[1].upper()
        lang = "-".join(lang)
    return lang if lang in enabled_locales else default_language


def use_chat_lang(context=None):
    if not context:
        frame = inspect.stack()[1]
        context = frame[0].f_code.co_filename.split(os.path.sep)[-1].split(".")[0]

    def decorator(func):
        @wraps(func)
        async def wrapper(client, message):
            lang = await get_lang(message)

            dic = langdict.get(lang, langdict[default_language])

            lfunc = partial(get_locale_string, dic.get(context, {}), lang, context)
            return await func(client, message, lfunc)

        return wrapper

    return decorator
