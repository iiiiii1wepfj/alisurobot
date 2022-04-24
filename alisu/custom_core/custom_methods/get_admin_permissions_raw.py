from typing import Union
from pyrogram.raw.functions.channels import GetParticipant
from pyrogram.scaffold import Scaffold


class GetAdminPermissionsRaw(Scaffold):
    async def get_admin_permissions_raw(
        self,
        chat_id: Union[int, str],
        user_id: Union[int, str],
    ):
        chat = await self.resolve_peer(chat_id)
        user = await self.resolve_peer(user_id)

        r = (
            await self.invoke(
                GetParticipant(
                    channel=chat,
                    participant=user,
                )
            )
        ).participant.admin_rights
        return r
