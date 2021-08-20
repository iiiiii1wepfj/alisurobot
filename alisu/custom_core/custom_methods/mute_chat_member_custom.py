# based on https://github.com/pyrogram/pyrogram/blob/master/pyrogram/methods/chats/restrict_chat_member.py

from typing import Union
from pyrogram import Client
from pyrogram.raw.types import ChatBannedRights
from pyrogram.raw.functions.channels import EditBanned
from pyrogram.types import ChatPermissions


async def mute_chat_member_custom(
    client: Client,
    chat_id: Union[int, str],
    user_id: Union[int, str],
    perms: ChatPermissions,
    mute_time: int = 0,
):
    return await client.send(
        EditBanned(
            channel=await client.resolve_peer(chat_id),
            participant=await client.resolve_peer(user_id),
            banned_rights=ChatBannedRights(
                until_date=mute_time,
                send_messages=True if not perms.can_send_messages else None,
                send_media=True if not perms.can_send_media_messages else None,
                send_stickers=True if not perms.can_send_other_messages else None,
                send_gifs=True if not perms.can_send_other_messages else None,
                send_games=True if not perms.can_send_other_messages else None,
                send_inline=True if not perms.can_send_other_messages else None,
                embed_links=True if not perms.can_add_web_page_previews else None,
                send_polls=True if not perms.can_send_polls else None,
                change_info=True if not perms.can_change_info else None,
                invite_users=True if not perms.can_invite_users else None,
                pin_messages=True if not perms.can_pin_messages else None,
            ),
        )
    )
