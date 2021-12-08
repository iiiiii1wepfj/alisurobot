import asyncio
from typing import Optional

from pyrogram import Client, filters
from pyrogram.types import ChatPermissions, Message, User

from alisu.config import prefix
from alisu.database import groups
from alisu.utils import (
    commands,
    require_admin,
    bot_require_admin,
    time_extract,
    check_if_ban_time_range,
)
from alisu.utils.utils import InvalidTimeUnitStringSpecifiedError
from alisu.utils.consts import admin_status
from alisu.utils.localization import use_chat_lang
from alisu.utils.bot_error_log import logging_errors
from alisu.utils.bot_custom_exceptions import target_user_not_found_custom_exception


async def get_reason_text(
    c: Client,
    m: Message,
) -> Message:
    reply = m.reply_to_message
    spilt_text = m.text.split
    if not reply and len(spilt_text()) >= 3:
        reason = spilt_text(None, 2)[2]
    elif reply and len(spilt_text()) >= 2:
        reason = spilt_text(None, 1)[1]
    else:
        reason = None
    return reason


async def mention_or_unknowen(m: Message):
    if m.from_user:
        return m.from_user.mention
    else:
        return "¯\_(ツ)_/¯"


async def check_if_antichannelpin(chat_id: int):
    return (await groups.get(chat_id=chat_id)).antichannelpin


async def toggle_antichannelpin(
    chat_id: int,
    mode: Optional[bool],
):
    await groups.filter(chat_id=chat_id).update(antichannelpin=mode)


async def check_if_del_service(chat_id: int):
    return (await groups.get(chat_id=chat_id)).delservicemsgs


async def toggle_del_service(
    chat_id: int,
    mode: Optional[bool],
):
    await groups.filter(chat_id=chat_id).update(delservicemsgs=mode)


async def get_target_user(
    c: Client,
    m: Message,
    strings=None,
) -> User:
    try:
        if m.reply_to_message:
            target_user = m.reply_to_message.from_user
        else:
            msg_entities = m.entities[1] if m.text.startswith("/") else m.entities[0]
            target_user = await c.get_users(
                msg_entities.user.id
                if msg_entities.type == "text_mention"
                else int(m.command[1])
                if m.command[1].isdecimal()
                else m.command[1]
            )
        return target_user
    except:
        if strings:
            raise target_user_not_found_custom_exception(
                strings("target_user_not_found_err_str", context="admin")
            )
        else:
            raise target_user_not_found_custom_exception("The user is not found.")


async def get_target_user_and_time_and_reason(
    c: Client,
    m: Message,
    strings,
):
    reason = None
    if m.reply_to_message:
        target_user = m.reply_to_message.from_user
        if len(m.text.split()) > 1:
            the_time_string = m.command[1]
        else:
            the_time_string = None
        if len(m.text.split()) > 2:
            reason = m.text.split(None, 2)[2]
        else:
            reason = None
    else:
        try:
            msg_entities = m.entities[1] if m.text.startswith("/") else m.entities[0]
        except:
            return
        target_user = await c.get_users(
            msg_entities.user.id
            if msg_entities.type == "text_mention"
            else int(m.command[1])
            if m.command[1].isdecimal()
            else m.command[1]
        )
        if len(m.text.split()) > 2:
            the_time_string = m.command[2]
        else:
            the_time_string = None
        if len(m.text.split()) > 3:
            reason = m.text.split(None, 3)[3]
        else:
            reason = None
    if not the_time_string:
        return await m.reply_text(
            strings("error_must_specify_time").format(command=m.command[0])
        )
    else:
        try:
            the_time, time_unix_now = await time_extract(m, the_time_string)
        except InvalidTimeUnitStringSpecifiedError as invalidtimeerrmsg:
            await m.reply_text(invalidtimeerrmsg)
            return
    return target_user, the_time, the_time_string, reason, time_unix_now


@Client.on_message(filters.command("echo", prefix))
@require_admin(allow_in_private=True)
async def admin_echo_cmd(c: Client, m: Message):
    if len(m.text.split()) > 1:
        if m.reply_to_message:
            await m.reply_to_message.reply_text(m.text.split(None, 1)[1])
        else:
            await m.reply_text(m.text.split(None, 1)[1], quote=False)


@Client.on_message(filters.command("del", prefix))
@require_admin(
    permissions=["can_delete_messages"],
    allow_in_private=True,
)
@bot_require_admin(
    permissions=["can_delete_messages"],
    allow_in_private=True,
)
async def del_message(c: Client, m: Message):
    try:
        await c.delete_messages(
            m.chat.id,
            m.reply_to_message.message_id,
        )
    except:
        pass
    try:
        await c.delete_messages(m.chat.id, m.message_id)
    except:
        pass


@Client.on_message(filters.command("pin", prefix))
@require_admin(
    permissions=["can_pin_messages"],
    allow_in_private=True,
)
@bot_require_admin(
    permissions=["can_pin_messages"],
    allow_in_private=True,
)
@logging_errors
async def pin(c: Client, m: Message):
    if m.reply_to_message:
        await c.pin_chat_message(
            m.chat.id,
            m.reply_to_message.message_id,
            disable_notification=True,
            both_sides=True,
        )


@Client.on_message(filters.command("pin loud", prefix))
@require_admin(
    permissions=["can_pin_messages"],
    allow_in_private=True,
)
@bot_require_admin(
    permissions=["can_pin_messages"],
    allow_in_private=True,
)
@logging_errors
async def pinloud(c: Client, m: Message):
    if m.reply_to_message:
        await c.pin_chat_message(
            m.chat.id,
            m.reply_to_message.message_id,
            disable_notification=False,
            both_sides=True,
        )


@Client.on_message(filters.command("unpin", prefix))
@require_admin(
    permissions=["can_pin_messages"],
    allow_in_private=True,
)
@bot_require_admin(
    permissions=["can_pin_messages"],
    allow_in_private=True,
)
@logging_errors
async def unpin(c: Client, m: Message):
    if m.reply_to_message:
        await c.unpin_chat_message(m.chat.id, m.reply_to_message.message_id)


@Client.on_message(filters.command(["unpinall", "unpin all"], prefix))
@require_admin(
    permissions=["can_pin_messages"],
    allow_in_private=True,
)
@bot_require_admin(
    permissions=["can_pin_messages"],
    allow_in_private=True,
)
@logging_errors
async def unpinall(c: Client, m: Message):
    await c.unpin_all_chat_messages(m.chat.id)


@Client.on_message(filters.command("ban", prefix))
@use_chat_lang()
@require_admin(permissions=["can_restrict_members"])
@bot_require_admin(permissions=["can_restrict_members"])
@logging_errors
async def ban(c: Client, m: Message, strings):
    try:
        target_user = await get_target_user(c, m, strings)
    except target_user_not_found_custom_exception as e:
        return await m.reply_text(e)
    reason = await get_reason_text(c, m)
    check_admin = await c.get_chat_member(m.chat.id, target_user.id)
    mentionadm = await mention_or_unknowen(m)
    if check_admin.status not in admin_status:
        await c.kick_chat_member(m.chat.id, target_user.id)
        text = strings("ban_success").format(
            user=target_user.mention,
            admin=mentionadm,
        )
        if reason:
            await m.reply_text(
                text + "\n" + strings("reason_string").format(reason_text=reason)
            )
        else:
            await m.reply_text(text)
    else:
        await m.reply_text(strings("i_cant_ban_admins"))


@Client.on_message(filters.command("dban", prefix))
@use_chat_lang()
@require_admin(
    permissions=["can_restrict_members", "can_delete_messages"],
)
@bot_require_admin(
    permissions=["can_restrict_members", "can_delete_messages"],
)
@logging_errors
async def dban(c: Client, m: Message, strings):
    if m.reply_to_message:
        if not m.reply_to_message.from_user:
            return
        check_admin = await c.get_chat_member(
            m.chat.id, m.reply_to_message.from_user.id
        )
        if check_admin.status not in admin_status:
            kick_member_msg = await c.kick_chat_member(
                m.chat.id, m.reply_to_message.from_user.id
            )
            await m.reply_to_message.delete()
            await m.delete()
            await kick_member_msg.delete()
        else:
            await m.reply_text(strings("i_cant_ban_admins"))


@Client.on_message(filters.command("kick", prefix))
@use_chat_lang()
@require_admin(permissions=["can_restrict_members"])
@bot_require_admin(permissions=["can_restrict_members"])
@logging_errors
async def kick(c: Client, m: Message, strings):
    try:
        target_user = await get_target_user(c, m, strings)
    except target_user_not_found_custom_exception as e:
        return await m.reply_text(e)
    reason = await get_reason_text(c, m)
    check_admin = await c.get_chat_member(m.chat.id, target_user.id)
    if check_admin.status not in admin_status:
        mentionadm = await mention_or_unknowen(m)
        await c.kick_chat_member(m.chat.id, target_user.id)
        await m.chat.unban_member(target_user.id)
        text = strings("kick_success").format(
            user=target_user.mention,
            admin=mentionadm,
        )
        if reason:
            await m.reply_text(
                text + "\n" + strings("reason_string").format(reason_text=reason)
            )
        else:
            await m.reply_text(text)
    else:
        await m.reply_text(strings("i_cant_kick_admins"))


@Client.on_message(filters.command("dkick", prefix))
@use_chat_lang()
@require_admin(
    permissions=[
        "can_restrict_members",
        "can_delete_messages",
    ],
)
@bot_require_admin(
    permissions=[
        "can_restrict_members",
        "can_delete_messages",
    ],
)
@logging_errors
async def dkick(c: Client, m: Message, strings):
    if m.reply_to_message:
        if not m.reply_to_message.from_user:
            return
        check_admin = await c.get_chat_member(
            m.chat.id, m.reply_to_message.from_user.id
        )
        if check_admin.status not in admin_status:
            kick_member_msg = await c.kick_chat_member(
                m.chat.id, m.reply_to_message.from_user.id
            )
            await m.chat.unban_member(m.reply_to_message.from_user.id)
            await m.reply_to_message.delete()
            await m.delete()
            await kick_member_msg.delete()
        else:
            await m.reply_text(strings("i_cant_kick_admins"))


@Client.on_message(filters.command("unban", prefix))
@use_chat_lang()
@require_admin(permissions=["can_restrict_members"])
@bot_require_admin(permissions=["can_restrict_members"])
@logging_errors
async def unban(c: Client, m: Message, strings):
    try:
        target_user = await get_target_user(c, m, strings)
    except target_user_not_found_custom_exception as e:
        return await m.reply_text(e)
    reason = await get_reason_text(c, m)
    await m.chat.unban_member(target_user.id)
    mentionadm = await mention_or_unknowen(m)
    text = strings("unban_success").format(
        user=target_user.mention,
        admin=mentionadm,
    )
    if reason:
        await m.reply_text(
            text + "\n" + strings("reason_string").format(reason_text=reason)
        )
    else:
        await m.reply_text(text)


@Client.on_message(filters.command("mute", prefix))
@use_chat_lang()
@require_admin(permissions=["can_restrict_members"])
@bot_require_admin(permissions=["can_restrict_members"])
@logging_errors
async def mute(c: Client, m: Message, strings):
    try:
        target_user = await get_target_user(c, m, strings)
    except target_user_not_found_custom_exception as e:
        return await m.reply_text(e)
    reason = await get_reason_text(c, m)
    check_admin = await c.get_chat_member(m.chat.id, target_user.id)
    if check_admin.status not in admin_status:
        await c.restrict_chat_member(
            m.chat.id,
            target_user.id,
            ChatPermissions(can_send_messages=False),
        )
        mentionadm = await mention_or_unknowen(m)
        text = strings("mute_success").format(
            user=target_user.mention,
            admin=mentionadm,
        )
        if reason:
            await m.reply_text(
                text + "\n" + strings("reason_string").format(reason_text=reason)
            )
        else:
            await m.reply_text(text)
    else:
        await m.reply_text(strings("i_cant_mute_admins"))


@Client.on_message(filters.command("dmute", prefix))
@use_chat_lang()
@require_admin(
    permissions=[
        "can_restrict_members",
        "can_delete_messages",
    ],
)
@bot_require_admin(
    permissions=[
        "can_restrict_members",
        "can_delete_messages",
    ],
)
@logging_errors
async def dmute(c: Client, m: Message, strings):
    if m.reply_to_message:
        if not m.reply_to_message.from_user:
            return
        check_admin = await c.get_chat_member(
            m.chat.id,
            m.reply_to_message.from_user.id,
        )
        if check_admin.status not in admin_status:
            await c.restrict_chat_member(
                m.chat.id,
                m.reply_to_message.from_user.id,
                ChatPermissions(can_send_messages=False),
            )
            await m.reply_to_message.delete()
            await m.delete()

        else:
            await m.reply_text(strings("i_cant_mute_admins"))


@Client.on_message(filters.command("unmute", prefix))
@use_chat_lang()
@require_admin(permissions=["can_restrict_members"])
@bot_require_admin(permissions=["can_restrict_members"])
@logging_errors
async def unmute(c: Client, m: Message, strings):
    try:
        target_user = await get_target_user(c, m, strings)
    except target_user_not_found_custom_exception as e:
        return await m.reply_text(e)
    reason = await get_reason_text(c, m)
    await m.chat.unban_member(target_user.id)
    mentionadm = await mention_or_unknowen(m)
    text = strings("unmute_success").format(
        user=target_user.mention,
        admin=mentionadm,
    )
    if reason:
        await m.reply_text(
            text + "\n" + strings("reason_string").format(reason_text=reason)
        )
    else:
        await m.reply_text(text)


@Client.on_message(filters.command("tmute", prefix))
@use_chat_lang()
@require_admin(permissions=["can_restrict_members"])
@bot_require_admin(permissions=["can_restrict_members"])
@logging_errors
async def tmute(c: Client, m: Message, strings):
    get_tmute_info = await get_target_user_and_time_and_reason(c, m, strings)
    if not get_tmute_info:
        return
    else:
        (
            target_user,
            mute_time,
            mute_time_str,
            the_reason,
            time_unix_now,
        ) = get_tmute_info
        check_if_valid_tmute_range = check_if_ban_time_range(mute_time, time_unix_now)
        if not check_if_valid_tmute_range:
            return await m.reply_text(strings("invalid_punish_time_specified_msg"))
    await c.restrict_chat_member(
        m.chat.id,
        target_user.id,
        ChatPermissions(can_send_messages=False),
        until_date=mute_time,
    )
    mentionadm = await mention_or_unknowen(m)
    the_tmute_message_text = strings("tmute_success").format(
        user=target_user.mention,
        admin=mentionadm,
        time=mute_time_str,
    )
    if the_reason:
        await m.reply_text(
            the_tmute_message_text
            + "\n"
            + strings("reason_string").format(reason_text=the_reason)
        )
    else:
        await m.reply_text(the_tmute_message_text)


@Client.on_message(filters.command("tban", prefix))
@use_chat_lang()
@require_admin(permissions=["can_restrict_members"])
@bot_require_admin(permissions=["can_restrict_members"])
@logging_errors
async def tban(c: Client, m: Message, strings):
    get_tban_info = await get_target_user_and_time_and_reason(c, m, strings)
    if not get_tban_info:
        return
    else:
        target_user, ban_time, ban_time_str, the_reason, time_unix_now = get_tban_info
        check_if_valid_tban_range = check_if_ban_time_range(ban_time, time_unix_now)
        if not check_if_valid_tban_range:
            return await m.reply_text(strings("invalid_punish_time_specified_msg"))
    await c.kick_chat_member(m.chat.id, target_user.id, until_date=ban_time)
    mentionadm = await mention_or_unknowen(m)
    the_tban_message_text = strings("tban_success").format(
        user=target_user.mention,
        admin=mentionadm,
        time=ban_time_str,
    )
    if the_reason:
        await m.reply_text(
            the_tban_message_text
            + "\n"
            + strings("reason_string").format(reason_text=the_reason)
        )
    else:
        await m.reply_text(the_tban_message_text)


@Client.on_message(filters.command("purge", prefix))
@require_admin(
    permissions=["can_delete_messages"],
    allow_in_private=True,
)
@bot_require_admin(
    permissions=["can_delete_messages"],
    allow_in_private=True,
)
@use_chat_lang()
@logging_errors
async def purge(c: Client, m: Message, strings):
    """Purge upto the replied message."""
    status_message = await m.reply_text(strings("purge_in_progress"), quote=True)
    await m.delete()
    message_ids = []
    count_del_etion_s = 0
    if m.reply_to_message:
        for a_s_message_id in range(m.reply_to_message.message_id, m.message_id):
            message_ids.append(a_s_message_id)
            if len(message_ids) == 100:
                await c.delete_messages(
                    chat_id=m.chat.id,
                    message_ids=message_ids,
                    revoke=True,
                )
                count_del_etion_s += len(message_ids)
                message_ids = []
        if len(message_ids) > 0:
            await c.delete_messages(
                chat_id=m.chat.id,
                message_ids=message_ids,
                revoke=True,
            )
            count_del_etion_s += len(message_ids)
    await status_message.edit_text(
        strings("purge_success").format(count=count_del_etion_s)
    )
    await asyncio.sleep(5)
    await status_message.delete()


@Client.on_message(filters.command("antichannelpin", prefix))
@require_admin(permissions=["can_pin_messages"])
@use_chat_lang()
@logging_errors
async def setantichannelpin(c: Client, m: Message, strings):
    if len(m.text.split()) > 1:
        if m.command[1] == "on":
            await toggle_antichannelpin(m.chat.id, True)
            await m.reply_text(strings("antichannelpin_enabled"))
        elif m.command[1] == "off":
            await toggle_antichannelpin(m.chat.id, False)
            await m.reply_text(strings("antichannelpin_disabled"))
        else:
            await m.reply_text(strings("antichannelpin_invalid_arg"))
    else:
        check_acp = await check_if_antichannelpin(m.chat.id)
        if not check_acp:
            await m.reply_text(strings("antichannelpin_status_disabled"))
        else:
            await m.reply_text(strings("antichannelpin_status_enabled"))


@Client.on_message(filters.linked_channel, group=-1)
async def acp_action(c: Client, m: Message):
    try:
        get_acp = await check_if_antichannelpin(m.chat.id)
        getmychatmember = await c.get_chat_member(m.chat.id, "me")
        if (get_acp and getmychatmember.can_pin_messages) is True:
            await m.unpin()
        else:
            pass
    except:
        pass


@Client.on_message(filters.command("cleanservice", prefix))
@require_admin(permissions=["can_delete_messages"])
@use_chat_lang()
@logging_errors
async def delservice(c: Client, m: Message, strings):
    if len(m.text.split()) > 1:
        if m.command[1] == "on":
            await toggle_del_service(m.chat.id, True)
            await m.reply_text(strings("cleanservice_enabled"))
        elif m.command[1] == "off":
            await toggle_del_service(m.chat.id, False)
            await m.reply_text(strings("cleanservice_disabled"))
        else:
            await m.reply_text(strings("cleanservice_invalid_arg"))
    else:
        check_delservice = await check_if_del_service(m.chat.id)
        if check_delservice is None:
            await m.reply_text(strings("cleanservice_status_disabled"))
        elif check_delservice is not None:
            await m.reply_text(strings("cleanservice_status_enabled"))


@Client.on_message(filters.service, group=-1)
async def delservice_action(c: Client, m: Message):
    try:
        get_delservice = await check_if_del_service(m.chat.id)
        getmychatmember = await c.get_chat_member(m.chat.id, "me")
        if (get_delservice and getmychatmember.can_delete_messages) is True:
            await m.delete()
        else:
            pass
    except:
        pass


commands.add_command("antichannelpin", "admin")
commands.add_command("ban", "admin")
commands.add_command("dban", "admin")
commands.add_command("cleanservice", "admin")
commands.add_command("kick", "admin")
commands.add_command("dkick", "admin")
commands.add_command("mute", "admin")
commands.add_command("dmute", "admin")
commands.add_command("pin", "admin")
commands.add_command("purge", "admin")
commands.add_command("tban", "admin")
commands.add_command("tmute", "admin")
commands.add_command("unban", "admin")
commands.add_command("unmute", "admin")
commands.add_command("unpin", "admin")
commands.add_command("unpinall", "admin")
commands.add_command("del", "admin")
