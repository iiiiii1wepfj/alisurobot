from pyrogram import Client, filters
from pyrogram.types import Message
from telegraph import upload_file

from alisu.config import prefix
from alisu.utils.localization import use_chat_lang
from alisu.utils.bot_error_log import logging_errors


@Client.on_message(filters.command("telegraph", prefix))
@use_chat_lang()
@logging_errors
async def telegraph(c: Client, m: Message, strings):
    if m.reply_to_message:
        if (
            m.reply_to_message.photo
            or m.reply_to_message.video
            or m.reply_to_message.animation
        ):
            d_file = await m.reply_to_message.download()
            media_urls = upload_file(d_file)
            tele_link = "https://telegra.ph" + media_urls[0]
            await m.reply_text(tele_link)
    else:
        await m.reply_text(strings("telegraph_err_no_reply"))
