from hydrogram import Client, filters
from hydrogram.types import Message

from alisu.config import prefix
from alisu.utils import commands
from alisu.utils.consts import http
from alisu.utils.localization import use_chat_lang
from alisu.utils.bot_error_log import logging_errors


@Client.on_message(filters.command("paste", prefix))
@use_chat_lang(context="pastes")
@logging_errors
async def nekobin(c: Client, m: Message, strings):
    if m.reply_to_message:
        if m.reply_to_message.document:
            tfile = m.reply_to_message
            to_file = await tfile.download()
            with open(to_file, "rb") as fd:
                mean = fd.read().decode("UTF-8")
        if m.reply_to_message.text:
            mean = m.reply_to_message.text

        url: str = "https://nekobin.com/api/documents"
        r = await http.post(url, json={"content": mean})
        url: str = f"https://nekobin.com/{r.json()['result']['key']}"
        await m.reply_text(url, disable_web_page_preview=True)
    else:
        await m.reply_text(strings("reply_to_document_or_text"))


commands.add_command("paste", "tools", "nekobin_description", context_location="pastes")
