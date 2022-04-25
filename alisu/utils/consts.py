from typing import List

from pyrogram import enums

import httpx

group_types: List[str] = (
    enums.ChatType.GROUP,
    enums.ChatType.SUPERGROUP,
)

admin_status: List[str] = [
    enums.ChatMemberStatus.OWNER,
    enums.ChatMemberStatus.ADMINISTRATOR,
]

timeout = httpx.Timeout(
    40,
    pool=None,
)

http = httpx.AsyncClient(
    http2=True,
    timeout=timeout,
)


class Permissions:
    can_be_edited: str = "can_be_edited"
    delete_messages: str = "can_delete_messages"
    restrict_members: str = "can_restrict_members"
    promote_members: str = "can_promote_members"
    change_info: str = "can_change_info"
    invite_users: str = "can_invite_users"
    pin_messages: str = "can_pin_messages"
