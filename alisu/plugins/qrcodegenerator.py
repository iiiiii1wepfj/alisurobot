from pyrogram import Client, filters
from pyrogram.types import Message

from alisu.config import prefix
from alisu.utils import commands

from io import BytesIO

import qrcode


@Client.on_message(filters.command("gen_qr", prefix) & ~filters.edited)
async def genqrcodecmd(c: Client, m: Message):
    if m.reply_to_message:
        if m.reply_to_message.caption:
            qrcodetext = m.reply_to_message.caption
        elif m.reply_to_message.text:
            qrcodetext = m.reply_to_message.text
        elif len(m.text.split()) > 1:
            qrcodetext = m.text.split(None, 1)[1]
        else:
            return
    else:
        if len(m.text.split()) > 1:
            qrcodetext = m.text.split(None, 1)[1]
        else:
            return
    make_qr_code = qrcode.make(qrcodetext)
    bytes_qr_code = BytesIO()
    make_qr_code.save(bytes_qr_code)
    qr_code_result = BytesIO(bytes_qr_code.getvalue())
    await m.reply_photo(qr_code_result)


commands.add_command("gen_qr", "general")
