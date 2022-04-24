from pyrogram.scaffold import Scaffold
from pyrogram.types import Message
from pyrogram.raw import functions
from pyrogram.raw.types import InputMessageID
from alisu.utils.bot_custom_exceptions import invalid_chat_type_custom_exception


class GetRawMessageFromPyrogram(Scaffold):
    async def get_raw_message_from_pyrogram(
        self,
        message: Message,
    ):
        messageid = message.message_id
        if message.chat.type in ["supergroup", "channel"]:
            the_peer = await self.resolve_peer(message.chat.id)
            r = await self.invoke(
                functions.channels.GetMessages(
                    channel=the_peer,
                    id=[InputMessageID(id=messageid)],
                )
            )
        elif message.chat.type in ["private", "bot", "group"]:
            r = await self.invoke(
                functions.messages.GetMessages(id=[InputMessageID(id=messageid)])
            )
        else:
            raise invalid_chat_type_custom_exception(
                f"Invalid Chat Type: {message.chat.type}"
            )

        return r
