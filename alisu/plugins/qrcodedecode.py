from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.file_id import FileId

from alisu.config import prefix
from alisu.utils import commands
from alisu.utils.localization import use_chat_lang

from pyzbar.pyzbar import (
    decode as pyzbar_decode,
)

import cv2


@Client.on_message(
    filters.command(
        [
            "decode_qr",
            "qr_decode",
        ],
        prefix,
    )
    & filters.reply
    & ~filters.edited
)
@use_chat_lang()
async def get_qr_code(
    c: Client,
    m: Message,
    strings,
):
    msg = m.reply_to_message
    if msg.photo or msg.document:
        if msg.document:
            msg_media_type = "document"
            if not msg.document.mime_type:
                return
            else:
                if "image" in msg.document.mime_type:
                    pass
                else:
                    return
        else:
            msg_media_type = "photo"
        media_type_get_attr = getattr(msg, msg_media_type, None)
        pyro_file_id_str = media_type_get_attr.file_id
        pyro_file_id_obj = FileId.decode(pyro_file_id_str)
        pyro_get_file = await c.get_file(
            file_id=pyro_file_id_obj,
            file_size=getattr(media_type_get_attr, "file_size", 0),
            progress=None,
        )
        qr_img = cv2.imread(pyro_get_file)
        detector = pyzbar_decode(qr_img)
        qr_data = detector[0].data.decode()
        await msg.reply_text(strings("qr_decoder_string").format(qr_data=qr_data))


commands.add_command("decode_qr", "general")
