import asyncio
import logging
import platform
import sys
import time

import pyrogram
from pyrogram import Client, idle
from pyrogram.errors import BadRequest

import alisu
from alisu.config import (
    API_HASH,
    API_ID,
    TOKEN,
    disabled_plugins,
    log_chat,
)
from alisu.custom_core.conv_handler import Conversation
from alisu.utils import shell_exec
from alisu.utils.consts import http
from alisu.database.database_handler import init_database


client = Client(
    session_name="bot",
    app_version=f"v{alisu.__version__}",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=TOKEN,
    workers=24,
    parse_mode="html",
    plugins=dict(root="alisu.plugins", exclude=disabled_plugins),
)
Conversation(client)


async def main() -> None:
    await init_database()
    await client.start()

    # Saving commit number
    client.version_code = int((await shell_exec("git rev-list --count HEAD"))[0])

    client.me = await client.get_me()

    client.start_time = time.time()
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


loop = asyncio.get_event_loop()

loop.run_until_complete(main())
