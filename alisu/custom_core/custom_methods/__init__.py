from typing import List
from .get_admin_permissions_raw import GetAdminPermissionsRaw
from .get_chat_member_raw import GetChatMemberRaw
from .get_raw_message_from_pyrogram import GetRawMessageFromPyrogram


class custom_methods(
    GetAdminPermissionsRaw,
    GetChatMemberRaw,
    GetRawMessageFromPyrogram,
):
    pass
