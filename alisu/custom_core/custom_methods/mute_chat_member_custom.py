#  Pyrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-2021 Dan <https://github.com/delivrance>
#
#  This file is part of Pyrogram.
#
#  Pyrogram is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Pyrogram is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Pyrogram.  If not, see <http://www.gnu.org/licenses/>.

from typing import Union

from pyrogram import Client
from pyrogram.raw.types import ChatBannedRights
from pyrogram.raw.functions.channels import EditBanned
from pyrogram.types import ChatPermissions


async def mute_chat_member_custom(
    client: Client,
    chat_id: Union[int, str],
    user_id: Union[int, str],
    permissions: ChatPermissions,
    until_date: int = 0,
):
    return await client.send(
        EditBanned(
            channel=await client.resolve_peer(chat_id),
            participant=await client.resolve_peer(user_id),
            banned_rights=ChatBannedRights(
                until_date=until_date,
                send_messages=True if not permissions.can_send_messages else None,
                send_media=True if not permissions.can_send_media_messages else None,
                send_stickers=True if not permissions.can_send_other_messages else None,
                send_gifs=True if not permissions.can_send_other_messages else None,
                send_games=True if not permissions.can_send_other_messages else None,
                send_inline=True if not permissions.can_send_other_messages else None,
                embed_links=True if not permissions.can_add_web_page_previews else None,
                send_polls=True if not permissions.can_send_polls else None,
                change_info=True if not permissions.can_change_info else None,
                invite_users=True if not permissions.can_invite_users else None,
                pin_messages=True if not permissions.can_pin_messages else None,
            ),
        )
    )
