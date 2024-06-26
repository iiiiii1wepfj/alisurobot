import random

from hydrogram import Client, filters
from hydrogram.types import Message

from alisu.config import prefix
from alisu.utils import commands
from alisu.utils.consts import http
from alisu.utils.localization import use_chat_lang
from alisu.utils.bot_error_log import logging_errors


@Client.on_message(filters.command("coub", prefix))
@use_chat_lang()
@logging_errors
async def coub(c: Client, m: Message, strings):
    text = m.text[6:]
    r = await http.get("https://coub.com/api/v2/search/coubs", params=dict(q=text))
    rjson = r.json()
    try:
        content = random.choice(rjson["coubs"])
        links = content["permalink"]
        title = content["title"]
    except IndexError:
        await m.reply_text(strings("no_results", context="general"))
    else:
        await m.reply_text(f'<b><a href="https://coub.com/v/{links}">{title}</a></b>')


commands.add_command("coub", "general")
