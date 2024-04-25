from hydrogram import Client, filters
from hydrogram.types import Message

from alisu.config import prefix
from alisu.utils import commands
from alisu.utils.localization import use_chat_lang
from alisu.utils.bot_error_log import logging_errors


@Client.on_message(
    filters.command(
        [
            "dice",
            "dados",
        ],
        prefix,
    )
)
@use_chat_lang()
@logging_errors
async def dice(c: Client, m: Message, strings):
    dicen = await c.send_dice(
        m.chat.id,
        reply_to_message_id=m.id,
    )
    await dicen.reply_text(
        strings("result").format(
            number=dicen.dice.value,
        ),
        quote=True,
    )


commands.add_command("dice", "general")
