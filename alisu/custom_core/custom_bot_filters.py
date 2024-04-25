from hydrogram import filters
from hydrogram.types import Message, Update
from typing import Union, Pattern
import re

viewsfilter = filters.create(lambda _, __, Message: Message.views)

non_anonymous_poll = filters.create(
    lambda *_: _[2].poll is not None and not _[2].poll.is_anonymous
)

anon_channel_filter = filters.create(
    lambda _, __, Message: Message.sender_chat
    and not (Message.forward_from_chat and not Message.from_user)
    and (Message.sender_chat.id != Message.chat.id)
)


def biofilter(pattern: Union[str, Pattern], flags: int = 0):
    async def func(flt, client, message):
        if not message.from_user:
            return False
        _ = await client.get_chat(message.from_user.id)
        value = _.bio
        if value:
            Update.matches = list(flt.p.finditer(value)) or None
            return bool(Update.matches)

    return filters.create(
        func,
        "biofilter",
        p=pattern if isinstance(pattern, Pattern) else re.compile(pattern, flags),
    )
