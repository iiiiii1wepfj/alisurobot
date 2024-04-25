from hydrogram import Client
from hydrogram.types import Message

from alisu.utils import add_chat, chat_exists
from alisu.utils.localization import set_db_lang, default_language

# This is the first plugin run to guarantee
# that the actual chat is initialized in the DB.


@Client.on_message(group=-1)
async def check_chat(c: Client, m: Message):
    chat_id = m.chat.id
    chat_type = m.chat.type
    check_the_chat = await chat_exists(chat_id, chat_type)

    if not check_the_chat:
        await add_chat(chat_id, chat_type)
        await set_db_lang(m.chat.id, m.chat.type, default_language)
