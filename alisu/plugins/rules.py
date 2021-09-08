from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from alisu.config import prefix
from alisu.database import groups
from alisu.utils import button_parser, commands, require_admin
from alisu.utils.localization import use_chat_lang
from alisu.utils.bot_error_log import logging_errors


async def get_rules(chat_id: int):
    try:
        return (await groups.get(chat_id=chat_id)).rules
    except IndexError:
        return None


async def set_rules(chat_id: int, rules):
    await groups.filter(chat_id=chat_id).update(rules=rules)


async def toggle_private_rules(chat_id: int, mode: bool):
    await groups.filter(chat_id=chat_id).update(private_rules=mode)


async def check_private_rules_status(chat_id: int):
    res = (await groups.get(chat_id=chat_id)).private_rules
    return True if res is True else False


@Client.on_message(filters.command("setrules", prefix) & filters.group)
@require_admin(permissions=["can_change_info"])
@use_chat_lang()
@logging_errors
async def settherules(c: Client, m: Message, strings):
    if len(m.text.split()) > 1:
        await set_rules(m.chat.id, m.text.split(None, 1)[1])
        await m.reply_text(strings("rules_set_success").format(chat_title=m.chat.title))
    else:
        await m.reply_text(strings("rules_set_empty"))


@Client.on_message(filters.command("set_pvt_rules", prefix) & filters.group)
@require_admin(permissions=["can_change_info"])
@use_chat_lang()
@logging_errors
async def set_pvt_rules_cmd(c: Client, m: Message, strings):
    if len(m.text.split()) > 1:
        if m.command[1] in ("on", "off"):
            if m.command[1] == "on":
                await toggle_private_rules(m.chat.id, True)
                return await m.reply_text(strings("pvt_rules_set_msg_enabled"))
            else:
                await toggle_private_rules(m.chat.id, False)
                return await m.reply_text(strings("pvt_rules_set_msg_disabled"))
        else:
            await m.reply_text(strings("set_pvt_rules_invalid_arg"))
    else:
        await m.reply_text(strings("set_pvt_rules_invalid_arg"))


@Client.on_message(filters.command("check_pvt_rules", prefix) & filters.group)
@require_admin()
@use_chat_lang()
@logging_errors
async def check_pvt_rules_cmd(c: Client, m: Message, strings):
    get_pvt_rules_mode = await check_private_rules_status(m.chat.id)
    if get_pvt_rules_mode:
        await m.reply_text(strings("check_pvt_rules_mode_enabled"))
    else:
        await m.reply_text(strings("check_pvt_rules_mode_disabled"))


@Client.on_message(filters.command("resetrules", prefix) & filters.group)
@require_admin(permissions=["can_change_info"])
@use_chat_lang()
@logging_errors
async def delete_rules(c: Client, m: Message, strings):
    await set_rules(m.chat.id, None)
    await m.reply_text(strings("rules_deleted"))


@Client.on_message(filters.command("rules", prefix) & filters.group)
@use_chat_lang()
@logging_errors
async def show_rules(c: Client, m: Message, strings):
    check_if_pvt_rules_db = await check_private_rules_status(m.chat.id)
    if check_if_pvt_rules_db:
        return await m.reply_text(
            strings("rules_pvt_message_group_text"),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            strings("rules_pvt_message_group_button"),
                            url=f"https://t.me/{c.me.username}?start=rules_{m.chat.id}",
                        )
                    ],
                ]
            ),
        )
    else:
        gettherules = await get_rules(m.chat.id)
        rulestxt, rules_buttons = button_parser(gettherules)
        if rulestxt:
            await m.reply_text(
                strings("rules_message").format(
                    chat_title=m.chat.title, rules=rulestxt
                ),
                reply_markup=(
                    InlineKeyboardMarkup(rules_buttons)
                    if len(rules_buttons) != 0
                    else None
                ),
            )
        else:
            await m.reply_text(strings("rules_empty"))


@Client.on_message(filters.regex("^/start rules_") & filters.private)
@use_chat_lang()
@logging_errors
async def show_rules_pvt(c: Client, m: Message, strings):
    cid_one = m.text.split("_")[1]
    gettherules = await get_rules(cid_one if cid_one.startswith("-") else f"-{cid_one}")
    rulestxt, rules_buttons = button_parser(gettherules)
    if rulestxt:
        await m.reply_text(
            rulestxt,
            reply_markup=(
                InlineKeyboardMarkup(rules_buttons) if len(rules_buttons) != 0 else None
            ),
        )
    else:
        await m.reply_text(strings("rules_empty"))

    await m.stop_propagation()


commands.add_command("setrules", "admin")
commands.add_command("resetrules", "admin")
commands.add_command("rules", "admin")
commands.add_command("set_pvt_rules", "admin")
commands.add_command("check_pvt_rules", "admin")
