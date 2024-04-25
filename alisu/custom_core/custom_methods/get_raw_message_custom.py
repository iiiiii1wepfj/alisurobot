from typing import Union
from hydrogram.raw import functions
from hydrogram.raw.types import InputMessageID
from alisu.utils.bot_custom_exceptions import invalid_chat_type_custom_exception


class GetRawMessageCustom:
    async def get_raw_message_custom(
        self,
        chat_id: Union[int, str],
        message_id: Union[int, str],
        chat_type: str,
    ):
        if chat_type in ["supergroup", "channel"]:
            the_peer = await self.resolve_peer(chat_id)
            r = await self.invoke(
                functions.channels.GetMessages(
                    channel=the_peer,
                    id=[InputMessageID(id=message_id)],
                )
            )
        elif chat_type in ["private", "bot", "group"]:
            r = await self.invoke(
                functions.messages.GetMessages(id=[InputMessageID(id=message_id)])
            )
        else:
            raise invalid_chat_type_custom_exception(f"Invalid Chat Type: {chat_type}")

        return r
