from typing import List
from .get_admin_permissions_raw import GetAdminPermissionsRaw
from .get_chat_member_raw import GetChatMemberRaw


class custom_methods(
    GetAdminPermissionsRaw,
    GetChatMemberRaw,
):
    pass
