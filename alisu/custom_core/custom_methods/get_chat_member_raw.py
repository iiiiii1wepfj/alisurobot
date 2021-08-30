from typing import Union
from pyrogram.raw.functions.channels import GetParticipant
from pyrogram.scaffold import Scaffold


class GetChatMemberRaw(Scaffold):
    async def get_chat_member_raw(
        self,
        chat_id: Union[int, str],
        user_id: Union[int, str],
    ):
        chat = await self.resolve_peer(chat_id)
        user = await self.resolve_peer(user_id)

        r = await self.send(
            GetParticipant(
                channel=chat,
                participant=user,
            )
        )
        return r
