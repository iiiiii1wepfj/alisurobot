from typing import Optional, Tuple

from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    ChatPermissions,
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from alisu.config import prefix
from alisu.database import user_warns, groups
from alisu.utils import (
    commands,
    require_admin,
    bot_require_admin,
)
from alisu.utils.consts import admin_status
from alisu.utils.localization import use_chat_lang
from alisu.utils.bot_error_log import logging_errors
from alisu.utils.bot_custom_exceptions import target_user_not_found_custom_exception

from babel.dates import (
    format_timedelta as babel_format_timedelta,
)
from babel.core import (
    UnknownLocaleError as BabelUnknownLocaleError,
)

from tortoise.exceptions import (
    DoesNotExist as tortoiseormdoesnotexisterr,
)


from alisu.plugins.admin import get_target_user

import time


def check_if_ban_time_range_db(sec):
    if sec in range(30, 31622400):
        return True
    else:
        return False


def get_warn_time_locale_string(
    the_time,
    lang: str,
):
    try:
        return babel_format_timedelta(
            the_time,
            locale=lang,
        )
    except BabelUnknownLocaleError:
        return babel_format_timedelta(
            the_time,
            locale="en",
        )


class InvalidTimeUnitStringSpecifiedDbError(Exception):
    pass


def time_extract_to_db(t: str) -> int:
    if t[-1] in ["m", "h", "d"]:
        unit = t[-1]
        num = t[:-1]
        if not num.isdigit():
            raise InvalidTimeUnitStringSpecifiedError("Invalid Amount specified")

        if unit == "m":
            t_time = int(num) * 60
        elif unit == "h":
            t_time = int(num) * 60 * 60
        elif unit == "d":
            t_time = int(num) * 24 * 60 * 60
        else:
            return 0
        return int(t_time)
    raise InvalidTimeUnitStringSpecifiedError("Invalid time format. Use 'm'/'h'/'d' ")


async def get_warn_reason_text(
    c: Client,
    m: Message,
) -> Message:
    reply = m.reply_to_message
    spilt_text = m.text.split
    if not reply and len(spilt_text()) >= 3:
        warn_reason = spilt_text(None, 2)[2]
    elif reply and len(spilt_text()) >= 2:
        warn_reason = spilt_text(None, 1)[1]
    else:
        warn_reason = None
    return warn_reason


async def get_warn_action(chat_id: int) -> Tuple[Optional[str], bool]:
    res = await groups.get(chat_id=chat_id)
    warn_action_str = "ban" if res.warn_action is None else res.warn_action
    warn_time = 0 if res.warn_time is None else res.warn_time
    return warn_action_str, warn_time


async def set_warn_action(
    chat_id: int,
    action: Optional[str],
    the_time: Optional[str] = None,
):
    await groups.filter(chat_id=chat_id).update(
        warn_action=action,
        warn_time=the_time,
    )


async def get_warns(chat_id: int, user_id: int):
    r = (await user_warns.get(user_id=user_id, chat_id=chat_id)).count
    return r if r else 0


async def add_warns(chat_id: int, user_id: int, number: int):
    check_if_user_warn_already_exists = await user_warns.exists(
        user_id=user_id, chat_id=chat_id
    )
    if check_if_user_warn_already_exists:
        user_warns_number_before_the_warn = (
            await user_warns.get(user_id=user_id, chat_id=chat_id)
        ).count
        user_warns_number_after_the_warn = user_warns_number_before_the_warn + number
        await user_warns.filter(user_id=user_id, chat_id=chat_id).update(
            count=user_warns_number_after_the_warn
        )
    else:
        await user_warns.create(
            user_id=user_id,
            chat_id=chat_id,
            count=number,
        )


async def remove_one_warn_db(chat_id: int, user_id: int, number: int):
    the_number_res = int(number - 1)
    await user_warns.filter(user_id=user_id, chat_id=chat_id).update(
        count=the_number_res
    )


async def reset_warns(chat_id: int, user_id: int):
    await user_warns.filter(user_id=user_id, chat_id=chat_id).delete()


async def get_warns_limit(chat_id: int):
    res = (await groups.get(chat_id=chat_id)).warns_limit
    return 3 if res is None else res


async def set_warns_limit(chat_id: int, warns_limit: int):
    await groups.filter(chat_id=chat_id).update(warns_limit=warns_limit)


@Client.on_message(filters.command("warn", prefix) & filters.group)
@require_admin(permissions=["can_restrict_members"])
@bot_require_admin(permissions=["can_restrict_members"])
@use_chat_lang()
@logging_errors
async def warn_user(
    c: Client,
    m: Message,
    strings,
):
    try:
        target_user = await get_target_user(c, m, strings)
    except target_user_not_found_custom_exception as e:
        return await m.reply_text(e)
    warns_limit = await get_warns_limit(m.chat.id)
    check_admin = await c.get_chat_member(m.chat.id, target_user.id)
    reason = await get_warn_reason_text(c, m)
    warn_action, warn_time = await get_warn_action(m.chat.id)
    time_parsed = get_warn_time_locale_string(
        the_time=warn_time, lang=strings("warn_time_lang_code_string")
    )
    if check_admin.status not in admin_status:
        await add_warns(m.chat.id, target_user.id, 1)
        user_warns = await get_warns(m.chat.id, target_user.id)
        if user_warns >= warns_limit:
            warn_btns = None
            if warn_action == "ban":
                await c.ban_chat_member(m.chat.id, target_user.id)
                warn_string = strings("warn_banned")
            elif warn_action == "mute":
                await c.restrict_chat_member(
                    m.chat.id,
                    target_user.id,
                    ChatPermissions(can_send_messages=False),
                )
                warn_string = strings("warn_muted")
            elif warn_action == "kick":
                await c.ban_chat_member(m.chat.id, target_user.id)
                await c.unban_chat_member(m.chat.id, target_user.id)
                warn_string = strings("warn_kicked")
            elif warn_action == "tban":
                await c.kick_chat_member(
                    m.chat.id,
                    target_user.id,
                    until_date=(round(time.time()) + warn_time),
                )
                warn_string = strings("warn_tbanned")
            elif warn_action == "tmute":
                await c.restrict_chat_member(
                    m.chat.id,
                    target_user.id,
                    ChatPermissions(can_send_messages=False),
                    until_date=(round(time.time()) + warn_time),
                )
                warn_string = strings("warn_tmuted")
            else:
                return

            warn_text = warn_string.format(
                target_user=target_user.mention,
                warn_count=user_warns,
                the_time=time_parsed,
            )
            await reset_warns(m.chat.id, target_user.id)
        else:
            warn_text = strings("user_warned").format(
                target_user=target_user.mention,
                warn_count=user_warns,
                warn_limit=warns_limit,
            )
            warn_btns = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            strings("rem_warn_btn_str"),
                            callback_data=f"rmwarn.{target_user.id}",
                        )
                    ]
                ]
            )
        if reason:
            await m.reply_text(
                warn_text
                + "\n"
                + strings("warn_reason_text").format(reason_text=reason),
                reply_markup=warn_btns if warn_btns else None,
            )
        else:
            await m.reply_text(
                warn_text,
                reply_markup=warn_btns if warn_btns else None,
            )
    else:
        await m.reply_text(strings("warn_cant_admin"))


@Client.on_callback_query(filters.regex("^rmwarn."))
@use_chat_lang()
@require_admin(permissions=["can_restrict_members"])
async def remwarncallbackfunc(c: Client, m: CallbackQuery, strings):
    chatid = m.message.chat.id
    the_msg_obj = m.message
    try:
        just_unused_callback_one, unwarn_user_id_one = m.data.split(".")
        unwarn_user_id = int(unwarn_user_id_one)
        warns_limit = await get_warns_limit(chatid)
        user_warns = await get_warns(chatid, unwarn_user_id)
        if user_warns >= warns_limit:
            return await the_msg_obj.edit("¯\\_(ツ)_/¯")
        elif user_warns == 0:
            return await the_msg_obj.edit("¯\\_(ツ)_/¯")
        else:
            await remove_one_warn_db(
                chat_id=chatid, user_id=unwarn_user_id, number=user_warns
            )
            return await the_msg_obj.edit(strings("warn_one_removed_edit_str"))
    except tortoiseormdoesnotexisterr:
        return await the_msg_obj.edit("¯\\_(ツ)_/¯")


@Client.on_message(filters.command("setwarnslimit", prefix) & filters.group)
@require_admin(permissions=["can_restrict_members"])
@use_chat_lang()
@logging_errors
async def on_set_warns_limit(
    c: Client,
    m: Message,
    strings,
):
    if len(m.command) == 1:
        return await m.reply_text(strings("warn_limit_help"))
    try:
        warns_limit = int(m.command[1])
    except ValueError:
        await m.reply_text(strings("warn_limit_invalid"))
    else:
        await set_warns_limit(m.chat.id, warns_limit)
        await m.reply(strings("warn_limit_changed").format(warn_limit=warns_limit))


@Client.on_message(filters.command(["resetwarns", "unwarn"], prefix) & filters.group)
@require_admin(permissions=["can_restrict_members"])
@use_chat_lang()
@logging_errors
async def unwarn_user(
    c: Client,
    m: Message,
    strings,
):
    try:
        target_user = await get_target_user(c, m, strings)
    except target_user_not_found_custom_exception as e:
        return await m.reply_text(e)
    await reset_warns(m.chat.id, target_user.id)
    await m.reply_text(strings("warn_reset").format(target_user=target_user.mention))


@Client.on_message(filters.command("warns", prefix) & filters.group)
@require_admin()
@use_chat_lang()
@logging_errors
async def get_user_warns_cmd(
    c: Client,
    m: Message,
    strings,
):
    try:
        target_user = await get_target_user(c, m, strings)
    except target_user_not_found_custom_exception as e:
        return await m.reply_text(e)
    user_warns = await get_warns(m.chat.id, target_user.id)
    await m.reply_text(
        strings("warns_count_string").format(
            target_user=target_user.mention, warns_count=user_warns
        )
    )


@Client.on_message(
    filters.command(["setwarnsaction", "warnsaction"], prefix) & filters.group
)
@require_admin(permissions=["can_restrict_members"])
@use_chat_lang()
@logging_errors
async def set_warns_action_cmd(
    c: Client,
    m: Message,
    strings,
):
    if len(m.text.split()) > 1:
        if not m.command[1] in ("ban", "mute", "kick", "tban", "tmute"):
            return await m.reply_text(strings("warns_action_set_invalid"))
        if m.command[1] in ("tban", "tmute"):
            if len(m.text.split()) > 2:
                try:
                    the_time = time_extract_to_db(m.command[2])
                    check_if_valid_time_range = check_if_ban_time_range_db(the_time)
                    if not check_if_valid_time_range:
                        return await m.reply_text(
                            strings("invalid_punish_time_specified_msg")
                        )
                except Exception as e:
                    return await m.reply_text(f"{e}")
            else:
                return await m.reply_text(strings("warn_no_time_error_str"))
        else:
            the_time = None

        warn_action_txt = m.command[1]

        await set_warn_action(m.chat.id, warn_action_txt, the_time=the_time)
        await m.reply_text(
            strings("warns_action_set_string").format(action=warn_action_txt)
        )
    else:
        the_warn_action, the_warn_time = await get_warn_action(m.chat.id)
        await m.reply_text(strings("warn_action_status").format(action=the_warn_action))


commands.add_command("warn", "admin")
commands.add_command("setwarnslimit", "admin")
commands.add_command("resetwarns", "admin")
commands.add_command("warns", "admin")
commands.add_command("setwarnsaction", "admin")
