from pyrogram import Client, filters
from pyrogram.types import Message

from alisu.config import prefix
from alisu.utils.consts import http
from alisu.utils.localization import use_chat_lang
from alisu.utils.bot_error_log import logging_errors

from io import BytesIO


class QuotlyException(Exception):
    pass


def get_user_full_name_pyro(msg):
    if msg.from_user:
        return f"{msg.from_user.first_name or 'unknown'} {msg.from_user.last_name or ''}".rstrip()
    else:
        return "unknown"


# based on https://github.com/TheHamkerCat/Python_ARQ/blob/master/Python_ARQ/arq.py
async def pyrogram_to_quotly(messages):
    if not isinstance(messages, list):
        messages = [messages]

    payload = {
        "type": "quote",
        "format": "png",
        "backgroundColor": "#1b1429",
        "messages": [
            {
                "entities": [
                    {
                        "type": entity.type,
                        "offset": entity.offset,
                        "length": entity.length,
                    }
                    for entity in message.entities
                ]
                if message.entities
                else [],
                "chatId": message.forward_from.id
                if message.forward_from
                else message.from_user.id,
                "avatar": True,
                "from": {
                    "id": message.from_user.id,
                    "username": message.from_user.username
                    if message.from_user.username
                    else "",
                    "photo": {
                        "small_file_id": message.from_user.photo.small_file_id,
                        "small_photo_unique_id": message.from_user.photo.small_photo_unique_id,
                        "big_file_id": message.from_user.photo.big_file_id,
                        "big_photo_unique_id": message.from_user.photo.big_photo_unique_id,
                    }
                    if message.from_user.photo
                    else "",
                    "type": message.chat.type,
                    "name": get_user_full_name_pyro(message),
                }
                if not message.forward_from
                else {
                    "id": message.forward_from.id,
                    "username": message.forward_from.username
                    if message.forward_from.username
                    else "",
                    "photo": {
                        "small_file_id": message.forward_from.photo.small_file_id,
                        "small_photo_unique_id": message.forward_from.photo.small_photo_unique_id,
                        "big_file_id": message.forward_from.photo.big_file_id,
                        "big_photo_unique_id": message.forward_from.photo.big_photo_unique_id,
                    }
                    if message.forward_from.photo
                    else "",
                    "type": message.chat.type,
                    "name": f"{message.forward_from.first_name or 'unknown'} {message.forward_from.last_name or ''}".rstrip(),
                },
                "text": message.text if message.text else "",
                "replyMessage": (
                    {
                        "name": get_user_full_name_pyro(message.reply_to_message),
                        "text": message.reply_to_message.text,
                        "chatId": message.reply_to_message.from_user.id,
                    }
                    if message.reply_to_message
                    else {}
                )
                if len(messages) == 1
                else {},
            }
            for message in messages
        ],
    }
    r = await http.post(f"https://bot.lyo.su/quote/generate.png", json=payload)
    if not r.is_error:
        return r.read()
    else:
        raise QuotlyException(r.json())


def isArgInt(txt) -> list:
    count = txt
    try:
        count = int(count)
        return [True, count]
    except ValueError:
        return [False, 0]


@Client.on_message(filters.command("q", prefix) & filters.reply)
@use_chat_lang()
@logging_errors
async def msg_quotly_cmd(c: Client, m: Message, strings):
    if len(m.text.split()) > 1:
        check_arg = isArgInt(m.command[1])
        if check_arg[0]:
            if check_arg[1] < 2 or check_arg[1] > 10:
                return await m.reply_text(strings("quotly_range_inavlid_string"))
            else:
                try:
                    messages = [
                        i
                        for i in await c.get_messages(
                            chat_id=m.chat.id,
                            message_ids=range(
                                m.reply_to_message.message_id,
                                m.reply_to_message.message_id + (check_arg[1] + 5),
                            ),
                            replies=-1,
                        )
                        if not i.empty and not i.media
                    ]
                except:
                    return await m.reply_text("¯\\_(ツ)_/¯")
                try:
                    make_quotly = await pyrogram_to_quotly(messages)
                    bio_sticker = BytesIO(make_quotly)
                    bio_sticker.name = "biosticker.webp"
                    return await m.reply_sticker(bio_sticker)
                except:
                    return await m.reply_text("¯\\_(ツ)_/¯")
        else:
            pass
    try:
        messages_one = await c.get_messages(
            chat_id=m.chat.id, message_ids=m.reply_to_message.message_id, replies=-1
        )
        messages = [messages_one]
    except:
        return await m.reply_text("¯\\_(ツ)_/¯")
    try:
        make_quotly = await pyrogram_to_quotly(messages)
        bio_sticker = BytesIO(make_quotly)
        bio_sticker.name = "biosticker.webp"
        return await m.reply_sticker(bio_sticker)
    except:
        return await m.reply_text("¯\\_(ツ)_/¯")
