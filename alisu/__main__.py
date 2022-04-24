import asyncio
import logging
import platform
import sys
import time

import pyrogram
from pyrogram import Client, idle, enums
from pyrogram.errors import BadRequest
from pyrogram.raw.functions.help import (
    GetConfig as pyrogetclientconfraw,
)

import alisu
from alisu.config import (
    API_HASH,
    API_ID,
    TOKEN,
    disabled_plugins,
    log_chat,
)
from alisu.custom_core.conv_handler import Conversation
from alisu.custom_core.custom_methods import custom_methods
from alisu.utils import shell_exec
from alisu.utils.consts import http
from alisu.database.database_handler import init_database


class botclient(custom_methods, Client):
    def __init__(self):
        super().__init__(
            name="bot",
            app_version=f"v{alisu.__version__}",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=TOKEN,
            workers=24,
            parse_mode=enums.ParseMode.HTML,
            plugins=dict(
                root="alisu.plugins",
                exclude=disabled_plugins,
            ),
        )

    async def start(self):
        await super().start()

    async def stop(self, *args):
        await super().stop()


async def main() -> None:
    await init_database()
    client = botclient()
    Conversation(client)
    await client.start()

    # Saving commit number
    client.version_code = int((await shell_exec("git rev-list --count HEAD"))[0])

    client.me = await client.get_me()

    client.start_time = time.time()
    try:
        getpyroclientconfraw = await client.invoke(pyrogetclientconfraw())
        client.tg_max_text_msg_len = int(getpyroclientconfraw.message_length_max)
        client.tg_max_caption_msg_len = int(getpyroclientconfraw.caption_length_max)
    except:
        client.tg_max_text_msg_len = 4096
        client.tg_max_caption_msg_len = 1024
    client.log_chat_errors: bool = True
    if "test" not in sys.argv:

        start_message = (
            "<b>The bot was started!</b>\n\n"
            f"<b>Version:</b> <code>v{alisu.__version__} ({client.version_code})</code>\n"
            f"<b>Pyrogram:</b> <code>v{pyrogram.__version__}</code>"
        )

        try:
            await client.send_message(chat_id=log_chat, text=start_message)
        except BadRequest:
            logging.warning("Unable to send message to log_chat.")
            client.log_chat_errors: bool = False

        await idle()

    await http.aclose()
    await client.stop()


event_policy = asyncio.get_event_loop_policy()
event_loop = event_policy.new_event_loop()
event_loop.run_until_complete(main())
