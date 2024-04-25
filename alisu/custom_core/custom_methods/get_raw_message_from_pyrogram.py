from hydrogram.types import Message
from hydrogram.raw import functions
from hydrogram.raw.types import InputMessageID
from hydrogram import enums
from alisu.utils.bot_custom_exceptions import invalid_chat_type_custom_exception


class GetRawMessageFromPyrogram:
    async def get_raw_message_from_pyrogram(
        self,
        message: Message,
    ):
        messageid = message.id
        if message.chat.type in [enums.ChatType.SUPERGROUP, enums.ChatType.CHANNEL]:
            the_peer = await self.resolve_peer(message.chat.id)
            r = await self.invoke(
                functions.channels.GetMessages(
                    channel=the_peer,
                    id=[InputMessageID(id=messageid)],
                )
            )
        elif message.chat.type in [enums.ChatType.PRIVATE, enums.ChatType.BOT, enums.ChatType.GROUP]:
            r = await self.invoke(
                functions.messages.GetMessages(id=[InputMessageID(id=messageid)])
            )
        else:
            raise invalid_chat_type_custom_exception(
                f"Invalid Chat Type: {message.chat.type}"
            )

        return r
