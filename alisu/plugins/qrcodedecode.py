from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.file_id import FileId

from alisu.config import prefix
from alisu.utils import commands

import cv2


@Client.on_message(filters.command("decode_qr", prefix) & filters.reply)
async def get_qr_code(c: Client, m: Message):
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
        detector = cv2.QRCodeDetector()
        qr_data, vertices_array, bun_qr = detector.detectAndDecode(qr_img)
        await msg.reply_text(
            f"<b>the text from the qr code</b>\n\n<code>{qr_data}</code>"
        )


commands.add_command("decode_qr", "general")
