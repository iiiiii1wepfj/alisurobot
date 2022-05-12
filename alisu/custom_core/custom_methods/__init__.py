from typing import List
from .get_admin_permissions_raw import GetAdminPermissionsRaw
from .get_chat_member_raw import GetChatMemberRaw
from .get_raw_message_from_pyrogram import GetRawMessageFromPyrogram
from .get_raw_message_custom import GetRawMessageCustom


class custom_methods(
    GetAdminPermissionsRaw,
    GetChatMemberRaw,
    GetRawMessageFromPyrogram,
    GetRawMessageCustom,
):
    pass
