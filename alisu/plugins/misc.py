import re
from html import escape
from urllib.parse import quote, unquote

from hydrogram import Client, filters, enums
from hydrogram.errors import BadRequest
from hydrogram.types import InlineKeyboardMarkup, Message

from alisu.config import log_chat, prefix
from alisu.utils import button_parser, commands
from alisu.utils.consts import admin_status, http
from alisu.utils.localization import use_chat_lang
from alisu.utils.bot_error_log import logging_errors
from alisu.utils.passindexerr import pass_index_error


@Client.on_message(filters.command("mark", prefix))
@use_chat_lang()
@logging_errors
async def mark(c: Client, m: Message, strings):
    if len(m.command) == 1:
        return await m.reply_text(strings("mark_usage"))
    txt = m.text.split(None, 1)[1]
    msgtxt, buttons = button_parser(txt)
    await m.reply(
        msgtxt,
        parse_mode=enums.ParseMode.MARKDOWN,
        reply_markup=(InlineKeyboardMarkup(buttons) if len(buttons) != 0 else None),
    )


@Client.on_message(filters.command("html", prefix))
@use_chat_lang()
@logging_errors
async def html(c: Client, m: Message, strings):
    if len(m.command) == 1:
        return await m.reply_text(strings("html_usage"))
    txt = m.text.split(None, 1)[1]
    msgtxt, buttons = button_parser(txt)
    await m.reply(
        msgtxt,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=(InlineKeyboardMarkup(buttons) if len(buttons) != 0 else None),
    )


@Client.on_message(filters.command("admins", prefix) & filters.group)
@use_chat_lang()
@logging_errors
async def mentionadmins(c: Client, m: Message, strings):
    mention: str = ""
    async for i in m.chat.get_members(m.chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
        if not (i.user.is_deleted or i.privileges.is_anonymous):
            mention += f"{i.user.mention}\n"
    await c.send_message(
        m.chat.id,
        strings("admins_list").format(chat_title=m.chat.title, admins_list=mention),
    )


@Client.on_message(
    (filters.command("report", prefix) | filters.regex("^@admin"))
    & filters.group
    & filters.reply
)
@use_chat_lang()
@logging_errors
async def reportadmins(c: Client, m: Message, strings):
    if m.reply_to_message.from_user:
        check_admin = await c.get_chat_member(
            m.chat.id, m.reply_to_message.from_user.id
        )
        if check_admin.status not in admin_status:
            mention = ""
            async for i in m.chat.get_members(filter=enums.ChatMembersFilter.ADMINISTRATORS):
                if not (i.user.is_deleted or i.privileges.is_anonymous or i.user.is_bot):
                    mention += f"<a href='tg://user?id={i.user.id}'>\u2063</a>"
            await m.reply_to_message.reply_text(
                strings("report_admns").format(
                    admins_list=mention,
                    reported_user=m.reply_to_message.from_user.mention(),
                ),
            )


@Client.on_message(filters.command("token"))
@use_chat_lang()
async def getbotinfo(c: Client, m: Message, strings):
    if len(m.command) == 1:
        return await m.reply_text(
            strings("no_bot_token"), reply_to_message_id=m.id
        )
    text = m.text.split(maxsplit=1)[1]
    req = await http.get(f"https://api.telegram.org/bot{text}/getme")
    fullres = req.json()
    if not fullres["ok"]:
        await m.reply(strings("bot_token_invalid"))
    else:
        res = fullres["result"]
        get_bot_info_text = strings("bot_token_info")
    await m.reply(
        get_bot_info_text.format(
            botname=res["first_name"], botusername=res["username"], botid=res["id"]
        ),
        reply_to_message_id=m.id,
    )


@Client.on_message(
    filters.reply
    & filters.group
    & filters.regex(r"(?i)^rt$")
    & filters.text
)
@logging_errors
async def rtcommand(c: Client, m: Message):
    rt_text = None
    if m.reply_to_message.media:
        rt_text = m.reply_to_message.caption
    else:
        rt_text = m.reply_to_message.text

    if rt_text is None:
        return
    if m.from_user:
        from_rt_user = m.from_user.first_name
    elif m.sender_chat:
        from_rt_user = m.sender_chat.title
    else:
        return
    if m.reply_to_message.from_user:
        from_reply_rt_user = m.reply_to_message.from_user.first_name
    elif m.reply_to_message.sender_chat:
        from_reply_rt_user = m.reply_to_message.sender_chat.title
    else:
        return
    if not re.match("🔃 .* retweeted:\n\n👤 .*", rt_text):
        text: str = f"🔃 <b>{escape(from_rt_user)}</b> retweeted:\n\n"
        text += f"👤 <b>{escape(from_reply_rt_user)}</b>:"
        text += f" <i>{escape(rt_text)}</i>"

        await m.reply_to_message.reply_text(
            text,
            disable_web_page_preview=True,
            disable_notification=True,
        )


@Client.on_message(filters.command("urlencode", prefix))
@logging_errors
@pass_index_error
async def urlencodecmd(c: Client, m: Message):
    await m.reply_text(quote(m.text.split(None, 1)[1]))


@Client.on_message(filters.command("urldecode", prefix))
@logging_errors
@pass_index_error
async def urldecodecmd(c: Client, m: Message):
    await m.reply_text(unquote(m.text.split(None, 1)[1]))


@Client.on_message(filters.command("bug", prefix))
@use_chat_lang()
@logging_errors
async def bug_report_cmd(c: Client, m: Message, strings):
    if not m.from_user:
        return
    if len(m.text.split()) > 1:
        try:
            bug_report = (
                "<b>Bug Report</b>\n"
                f"User: {m.from_user.mention}\n"
                f"ID: <code>{m.from_user.id}</code>\n\n"
                "The content of the report:\n"
                f"<code>{escape(m.text.split(None, 1)[1])}</code>"
            )
            await c.send_message(
                chat_id=log_chat,
                text=bug_report,
                disable_web_page_preview=True,
            )
            await m.reply_text(strings("bug_reported_success_to_bot_admins"))
        except BadRequest:
            await m.reply_text(strings("err_cant_send_bug_report_to_bot_admins"))
    else:
        await m.reply(strings("err_no_bug_to_report"))


@Client.on_message(filters.command("request", prefix))
@logging_errors
async def request_cmd(c: Client, m: Message):
    if len(m.text.split()) > 1:
        text = m.text.split(maxsplit=1)[1]
        if re.match(r"^(https?)://", text):
            url = text
        else:
            url = "http://" + text
        req = await http.get(url)
        headers = "<b>{}</b> <code>{} {}</code>\n".format(
            req.extensions.get("http_version").decode(),
            req.status_code,
            req.extensions.get("reason_phrase", b"").decode(),
        )
        headers += "\n".join(
            "<b>{}:</b> <code>{}</code>".format(x.title(), escape(req.headers[x]))
            for x in req.headers
        )
        await m.reply_text(f"<b>Headers:</b>\n{headers}", parse_mode=enums.ParseMode.HTML)
    else:
        await m.reply_text(
            "You must specify the url, E.g.: <code>/request https://example.com</code>"
        )


@Client.on_message(filters.command("parsebutton"))
@use_chat_lang()
@logging_errors
async def button_parse_helper(c: Client, m: Message, strings):
    if len(m.text.split()) > 2:
        await m.reply_text(
            f"[{m.text.split(None, 2)[2]}](buttonurl:{m.command[1]})", parse_mode=enums.ParseMode.DISABLED
        )
    else:
        await m.reply_text(strings("parsebtn_err"))


@Client.on_message(filters.command("donate"))
@logging_errors
async def donate_to_owner_cmd(c: Client, m: Message):
    await m.reply_text("https://paypal.me/itayki")


commands.add_command("mark", "general")
commands.add_command("html", "general")
commands.add_command("admins", "general")
commands.add_command("token", "general")
commands.add_command("urlencode", "general")
commands.add_command("urldecode", "general")
commands.add_command("parsebutton", "general")
commands.add_command("donate", "general")
