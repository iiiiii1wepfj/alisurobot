from typing import Optional, Tuple

from pyrogram import Client, filters, enums
from pyrogram.errors import BadRequest
from pyrogram.types import InlineKeyboardMarkup, Message

from alisu.config import prefix
from alisu.database import groups
from alisu.utils import (
    button_parser,
    commands,
    get_format_keys,
    require_admin,
)
from alisu.utils.localization import use_chat_lang
from alisu.utils.bot_error_log import logging_errors


async def get_welcome_status(chat_id: int):
    return (await groups.get(chat_id=chat_id)).welcome_enabled


async def get_welcome(chat_id: int) -> Tuple[Optional[str], bool]:
    return (await groups.get(chat_id=chat_id)).welcome


async def set_welcome(chat_id: int, welcome: Optional[str]):
    await groups.filter(chat_id=chat_id).update(welcome=welcome)


async def toggle_welcome(chat_id: int, mode: bool):
    await groups.filter(chat_id=chat_id).update(welcome_enabled=mode)


async def get_del_last_welcome_status(chat_id: int):
    res = (await groups.get(chat_id=chat_id)).del_last_welcome_message
    return True if res is True else False


async def get_last_welcome_message_id(chat_id: int):
    res = (await groups.get(chat_id=chat_id)).last_welcome_message_id
    return res if res else None


async def toggle_del_old_welcome(chat_id: int, mode: bool):
    await groups.filter(chat_id=chat_id).update(del_last_welcome_message=mode)


async def set_last_welcome_message_id(chat_id: int, msg_id: int):
    await groups.filter(chat_id=chat_id).update(last_welcome_message_id=msg_id)


@Client.on_message(
    (
        filters.command("del_old_welcome")
        & ~filters.command(["del_old_welcome on", "del_old_welcome off"])
    )
    & filters.group
)
@require_admin(permissions=["can_change_info"])
@use_chat_lang()
@logging_errors
async def invalid_del_old_welcome_status_arg(c: Client, m: Message, strings):
    await m.reply_text(strings("del_old_welcome_mode_invalid"))


@Client.on_message(filters.command("del_old_welcome on", prefix) & filters.group)
@require_admin(permissions=["can_change_info"])
@use_chat_lang()
@logging_errors
async def enable_del_old_welcome_message(c: Client, m: Message, strings):
    await toggle_del_old_welcome(m.chat.id, True)
    await m.reply_text(
        strings("del_old_welcome_mode_enable").format(chat_title=m.chat.title)
    )


@Client.on_message(filters.command("del_old_welcome off", prefix) & filters.group)
@require_admin(permissions=["can_change_info"])
@use_chat_lang()
@logging_errors
async def disable_del_old_welcome_message(c: Client, m: Message, strings):
    await toggle_del_old_welcome(m.chat.id, False)
    await m.reply_text(
        strings("del_old_welcome_mode_disable").format(chat_title=m.chat.title)
    )


@Client.on_message(
    filters.command(["welcomeformat", "start welcome_format_help"], prefix)
)
@use_chat_lang()
async def welcome_format_message_help(c: Client, m: Message, strings):
    await m.reply_text(strings("welcome_format_help_msg"))

    await m.stop_propagation()


@Client.on_message(filters.command("setwelcome", prefix) & filters.group)
@require_admin(permissions=["can_change_info"])
@use_chat_lang()
@logging_errors
async def set_welcome_message(c: Client, m: Message, strings):
    if len(m.text.split()) > 1:
        message = m.text.html.split(None, 1)[1]
        try:
            # Try to send message with default parameters
            sent = await m.reply_text(
                message.format(
                    id=m.from_user.id,
                    username=m.from_user.username,
                    mention=m.from_user.mention,
                    first_name=m.from_user.first_name,
                    # full_name and name are the same
                    full_name=m.from_user.first_name,
                    name=m.from_user.first_name,
                    # title and chat_title are the same
                    title=m.chat.title,
                    chat_title=m.chat.title,
                    count=(await c.get_chat_members_count(m.chat.id)),
                    dc_id=m.from_user.dc_id or None,
                )
            )
        except AttributeError:
            sent = await m.reply_text(message)
        except (KeyError, BadRequest) as e:
            await m.reply_text(
                strings("welcome_set_error").format(
                    error=e.__class__.__name__ + ": " + str(e)
                )
            )
        else:
            await set_welcome(m.chat.id, message)
            await sent.edit_text(
                strings("welcome_set_success").format(chat_title=m.chat.title)
            )
    else:
        await m.reply_text(
            strings("welcome_set_empty").format(bot_username=c.me.username),
            disable_web_page_preview=True,
        )


@Client.on_message(
    (filters.command("welcome") & ~filters.command(["welcome on", "welcome off"]))
    & filters.group
)
@require_admin(permissions=["can_change_info"])
@use_chat_lang()
@logging_errors
async def invalid_welcome_status_arg(c: Client, m: Message, strings):
    await m.reply_text(strings("welcome_mode_invalid"))


@Client.on_message(filters.command("getwelcome", prefix) & filters.group)
@require_admin(permissions=["can_change_info"])
@use_chat_lang()
@logging_errors
async def getwelcomemsg(c: Client, m: Message, strings):
    welcome_enabled = await get_welcome_status(m.chat.id)
    if welcome_enabled:
        welcome = await get_welcome(m.chat.id)
        await m.reply_text(
            strings("welcome_default") if welcome is None else welcome, parse_mode=enums.ParseMode.DISABLED
        )
    else:
        await m.reply_text("None")


@Client.on_message(filters.command("welcome on", prefix) & filters.group)
@require_admin(permissions=["can_change_info"])
@use_chat_lang()
@logging_errors
async def enable_welcome_message(c: Client, m: Message, strings):
    await toggle_welcome(m.chat.id, True)
    await m.reply_text(strings("welcome_mode_enable").format(chat_title=m.chat.title))


@Client.on_message(filters.command("welcome off", prefix) & filters.group)
@require_admin(permissions=["can_change_info"])
@use_chat_lang()
@logging_errors
async def disable_welcome_message(c: Client, m: Message, strings):
    await toggle_welcome(m.chat.id, False)
    await m.reply_text(strings("welcome_mode_disable").format(chat_title=m.chat.title))


@Client.on_message(
    filters.command(["resetwelcome", "clearwelcome"], prefix) & filters.group
)
@require_admin(permissions=["can_change_info"])
@use_chat_lang()
@logging_errors
async def reset_welcome_message(c: Client, m: Message, strings):
    await set_welcome(m.chat.id, None)
    await m.reply_text(strings("welcome_reset").format(chat_title=m.chat.title))


@Client.on_message(filters.new_chat_members & filters.group)
@use_chat_lang()
async def greet_new_members(c: Client, m: Message, strings):
    members = m.new_chat_members
    chat_title = m.chat.title
    first_name = ", ".join(map(lambda a: a.first_name, members))
    full_name = ", ".join(
        map(lambda a: a.first_name + " " + (a.last_name or ""), members)
    )
    user_id = ", ".join(map(lambda a: str(a.id), members))
    username = ", ".join(
        map(lambda a: "@" + a.username if a.username else a.mention, members)
    )
    mention = ", ".join(map(lambda a: a.mention, members))
    if not m.from_user.is_bot:
        welcome_enabled = await get_welcome_status(m.chat.id)
        if welcome_enabled:
            welcome = await get_welcome(m.chat.id)
            if welcome is None:
                welcome = strings("welcome_default")
            if "count" in get_format_keys(welcome):
                count = await c.get_chat_members_count(m.chat.id)
            else:
                count = 0
            if "preview" in get_format_keys(welcome):
                check_if_disable_preview = False
            else:
                check_if_disable_preview = True
            welcome = welcome.format(
                id=user_id,
                username=username,
                mention=mention,
                first_name=first_name,
                # full_name and name are the same
                full_name=full_name,
                name=full_name,
                # title and chat_title are the same
                title=chat_title,
                chat_title=chat_title,
                count=count,
                dc_id=m.from_user.dc_id or None,
                preview="",
            )
            welcome, welcome_buttons = button_parser(welcome)
            the_last_welcome_msg = await m.reply_text(
                welcome,
                disable_web_page_preview=check_if_disable_preview,
                reply_markup=(
                    InlineKeyboardMarkup(welcome_buttons)
                    if len(welcome_buttons) != 0
                    else None
                ),
            )
            check_if_delete_old_welcome_message = await get_del_last_welcome_status(
                m.chat.id
            )
            if check_if_delete_old_welcome_message is True:
                get_last_welcome_msg_id = await get_last_welcome_message_id(m.chat.id)
                if get_last_welcome_msg_id:
                    try:
                        await c.delete_messages(
                            chat_id=m.chat.id,
                            message_ids=get_last_welcome_msg_id,
                            revoke=True,
                        )
                    except:
                        pass
            await set_last_welcome_message_id(
                m.chat.id, the_last_welcome_msg.id
            )


commands.add_command("del_old_welcome", "admin")
commands.add_command("resetwelcome", "admin")
commands.add_command("setwelcome", "admin")
commands.add_command("welcome", "admin")
commands.add_command("welcomeformat", "admin")
