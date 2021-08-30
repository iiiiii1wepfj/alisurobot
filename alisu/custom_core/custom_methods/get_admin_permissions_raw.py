from typing import Union
from pyrogram import Client
from pyrogram.raw.functions.channels import GetParticipant


async def get_admin_permissions_raw(
    client: Client,
    chat_id: Union[int, str],
    user_id: Union[int, str],
):
    chat = await client.resolve_peer(chat_id)
    user = await client.resolve_peer(user_id)

    r = (
        await client.send(
            GetParticipant(
                channel=chat,
                user_id=user,
            )
        )
    ).participant.admin_rights
    return r
