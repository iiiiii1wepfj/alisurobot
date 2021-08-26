import asyncio
import inspect
import math
import os.path
import re
import time
from functools import partial, wraps
from string import Formatter
from typing import (
    Callable,
    Coroutine,
    List,
    Optional,
    Tuple,
    Union,
)

from pyrogram import Client, emoji, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
)
from pyrogram.errors.exceptions.bad_request_400 import (
    UserNotParticipant as PyroUserNotParticipantError,
)

from alisu.config import sudoers
from alisu.database import groups, users, channels
from alisu.utils.consts import (
    group_types,
    admin_status as pyro_admin_types_chat_member,
)
from alisu.utils.localization import (
    default_language,
    get_lang,
    get_locale_string,
    langdict,
)

BTN_URL_REGEX = re.compile(r"(\[([^\[]+?)\]\(buttonurl:(?:/{0,2})(.+?)(:same)?\))")

SMART_OPEN = "“"
SMART_CLOSE = "”"
START_CHAR = ("'", '"', SMART_OPEN)
_EMOJI_REGEXP = None


class InvalidTimeUnitStringSpecifiedError(Exception):
    pass


def pretty_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def aiowrap(func: Callable) -> Coroutine:
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)

    return run


async def add_chat(chat_id, chat_type):
    if chat_type == "private":
        await users.create(user_id=chat_id)
    elif chat_type in group_types:  # groups and supergroups share the same table
        await groups.create(
            chat_id=chat_id, welcome_enabled=True, del_last_welcome=False
        )
    elif chat_type == "channel":
        await channels.create(chat_id=chat_id)
    else:
        raise TypeError("Unknown chat type '%s'." % chat_type)
    return True


async def chat_exists(chat_id, chat_type):
    if chat_type == "private":
        return await users.exists(user_id=chat_id)
    if chat_type in group_types:  # groups and supergroups share the same table
        return await groups.exists(chat_id=chat_id)
    if chat_type == "channels":
        return await channels.exists(chat_id=chat_id)
    raise TypeError("Unknown chat type '%s'." % chat_type)


async def check_if_is_from_anon_admin(m: Message):
    return bool(m.sender_chat and not m.forward_from_chat and not m.from_user)


async def send_anon_admin_button(m: Message, callbackdatatext: str, strings):
    return await m.reply_text(
        strings("anon_admin_check_msg_txt"),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        strings("click_here_anon_admin_btn"),
                        callback_data=f"{callbackdatatext}",
                    )
                ],
            ]
        ),
    )


async def check_perms(
    client: Client,
    message: Union[CallbackQuery, Message],
    permissions: Optional[Union[list, str]],
    complain_missing_perms: bool,
    strings,
) -> bool:
    if isinstance(message, CallbackQuery):
        sender = partial(message.answer, show_alert=True)
        chat = message.message.chat
    else:
        sender = message.reply_text
        chat = message.chat
    try:
        user = await client.get_chat_member(chat.id, message.from_user.id)
    except PyroUserNotParticipantError:
        return False
    if user.status == "creator":
        return True

    missing_perms = []

    # No permissions specified, accept being an admin.
    if not permissions and user.status == "administrator":
        return True
    if user.status != "administrator":
        if complain_missing_perms:
            await sender(strings("no_admin_error"))
        return False

    if isinstance(permissions, str):
        permissions = [permissions]

    for permission in permissions:
        if not user.__getattribute__(permission):
            missing_perms.append(permission)

    if not missing_perms:
        return True
    if complain_missing_perms:
        await sender(
            strings("no_permission_error").format(permissions=", ".join(missing_perms))
        )
    return False


def require_admin(
    permissions: Union[list, str] = None,
    allow_in_private: bool = False,
    complain_missing_perms: bool = True,
):
    def decorator(func):
        @wraps(func)
        async def wrapper(
            client: Client,
            message: Union[CallbackQuery, Message],
            *args,
            **kwargs,
        ):
            lang = await get_lang(message)
            strings = partial(
                get_locale_string,
                langdict[lang].get("admin", langdict[default_language]["admin"]),
                lang,
                "admin",
            )

            if isinstance(message, CallbackQuery):
                sender = partial(message.answer, show_alert=True)
                msg = message.message
            elif isinstance(message, Message):
                sender = message.reply_text
                msg = message
            else:
                raise NotImplementedError(
                    f"require_admin can't process updates with the type '{message.__name__}' yet."
                )
            msg_to_check_perm = message

            # We don't actually check private and channel chats.
            if msg.chat.type == "private":
                if allow_in_private:
                    return await func(client, message, *args, *kwargs)
                return await sender(strings("private_not_allowed"))
            if msg.chat.type == "channel":
                return await func(client, message, *args, *kwargs)
            anon_admin_check = await check_if_is_from_anon_admin(message)
            check_anon_perms_msg_send = None
            if anon_admin_check:
                get_my_chat_member = await client.get_chat_member(msg.chat.id, "me")
                if get_my_chat_member.status not in pyro_admin_types_chat_member:
                    await message.reply_text(strings("bot_not_admin_error"))
                    return
                the_callback_data = f"{msg.chat.id}|{msg.message_id}"
                check_anon_perms_msg_send = await send_anon_admin_button(
                    msg, the_callback_data, strings
                )
                try:
                    anon_callback_listen = await client.listen.CallbackQuery(
                        id=str(msg.chat.id),
                        filters=(filters.regex(f"^{the_callback_data}$")),
                        timeout=120,
                    )
                    sender = partial(anon_callback_listen.answer, show_alert=True)
                    msg = anon_callback_listen.message
                    msg_to_check_perm = anon_callback_listen
                except asyncio.exceptions.TimeoutError:
                    return
            has_perms = await check_perms(
                client,
                msg_to_check_perm,
                permissions,
                complain_missing_perms,
                strings,
            )
            if has_perms:
                if check_anon_perms_msg_send:
                    await check_anon_perms_msg_send.delete()
                return await func(
                    client,
                    message,
                    *args,
                    *kwargs,
                )

        return wrapper

    return decorator


async def bot_check_perms(
    client: Client,
    message: Union[CallbackQuery, Message],
    permissions: Optional[Union[list, str]],
    complain_missing_perms: bool,
    strings,
) -> bool:
    if isinstance(message, CallbackQuery):
        sender = partial(message.answer, show_alert=True)
        chat = message.message.chat
    else:
        sender = message.reply_text
        chat = message.chat

    user = await client.get_chat_member(chat.id, "me")
    if user.status == "creator":
        return True

    missing_perms = []

    # No permissions specified, accept being an admin.
    if not permissions and user.status == "administrator":
        return True
    if user.status != "administrator":
        if complain_missing_perms:
            await sender(strings("bot_not_admin_error"))
        return False

    if isinstance(permissions, str):
        permissions = [permissions]

    for permission in permissions:
        if not user.__getattribute__(permission):
            missing_perms.append(permission)

    if not missing_perms:
        return True
    if complain_missing_perms:
        await sender(
            strings("bot_no_permission_error").format(
                permissions=", ".join(missing_perms)
            )
        )
    return False


def bot_require_admin(
    permissions: Union[list, str] = None,
    allow_in_private: bool = False,
    complain_missing_perms: bool = True,
):
    def decorator(func):
        @wraps(func)
        async def wrapper(
            client: Client,
            message: Union[CallbackQuery, Message],
            *args,
            **kwargs,
        ):
            lang = await get_lang(message)
            strings = partial(
                get_locale_string,
                langdict[lang].get("admin", langdict[default_language]["admin"]),
                lang,
                "admin",
            )

            if isinstance(message, CallbackQuery):
                sender = partial(message.answer, show_alert=True)
                msg = message.message
            elif isinstance(message, Message):
                sender = message.reply_text
                msg = message
            else:
                raise NotImplementedError(
                    f"bot_require_admin require_admin can't process updates with the type '{message.__name__}' yet."
                )

            # We don't actually check private and channel chats.
            if msg.chat.type == "private":
                if allow_in_private:
                    return await func(client, message, *args, *kwargs)
                return await sender(strings("private_not_allowed"))
            has_perms = await bot_check_perms(
                client,
                message,
                permissions,
                complain_missing_perms,
                strings,
            )
            if has_perms:
                return await func(
                    client,
                    message,
                    *args,
                    *kwargs,
                )

        return wrapper

    return decorator


sudofilter = filters.user(sudoers)


async def time_extract(m: Message, t: str) -> int:
    if t[-1] in ["m", "h", "d"]:
        unit = t[-1]
        num = t[:-1]
        if not num.isdigit():
            return await m.reply_text("Invalid Amount specified")

        if unit == "m":
            t_time = int(num) * 60
        elif unit == "h":
            t_time = int(num) * 60 * 60
        elif unit == "d":
            t_time = int(num) * 24 * 60 * 60
        else:
            return 0
        return int(time.time() + t_time)
    raise InvalidTimeUnitStringSpecifiedError("Invalid time format. Use 'm'/'h'/'d' ")


def remove_escapes(text: str) -> str:
    counter = 0
    res = ""
    is_escaped = False
    while counter < len(text):
        if is_escaped:
            res += text[counter]
            is_escaped = False
        elif text[counter] == "\\":
            is_escaped = True
        else:
            res += text[counter]
        counter += 1
    return res


def split_quotes(text: str) -> List:
    if any(text.startswith(char) for char in START_CHAR):
        counter = 1  # ignore first char -> is some kind of quote
        while counter < len(text):
            if text[counter] == "\\":
                counter += 1
            elif text[counter] == text[0] or (
                text[0] == SMART_OPEN and text[counter] == SMART_CLOSE
            ):
                break
            counter += 1
        else:
            return text.split(None, 1)

        key = remove_escapes(text[1:counter].strip())
        rest = text[counter + 1 :].strip()
        if not key:
            key = text[0] + text[0]
        return list(filter(None, [key, rest]))
    return text.split(None, 1)


def button_parser(markdown_note):
    note_data = ""
    buttons = []
    if markdown_note is None:
        return note_data, buttons
    if markdown_note.startswith("/") or markdown_note.startswith("!"):
        args = markdown_note.split(None, 2)
        markdown_note = args[2]
    prev = 0
    for match in BTN_URL_REGEX.finditer(markdown_note):
        n_escapes = 0
        to_check = match.start(1) - 1
        while to_check > 0 and markdown_note[to_check] == "\\":
            n_escapes += 1
            to_check -= 1

        if n_escapes % 2 == 0:
            if bool(match.group(4)) and buttons:
                buttons[-1].append(
                    InlineKeyboardButton(text=match.group(2), url=match.group(3))
                )
            else:
                buttons.append(
                    [InlineKeyboardButton(text=match.group(2), url=match.group(3))]
                )
            note_data += markdown_note[prev : match.start(1)]
            prev = match.end(1)

        else:
            note_data += markdown_note[prev:to_check]
            prev = match.start(1) - 1

    note_data += markdown_note[prev:]

    return note_data, buttons


class BotCommands:
    def __init__(self):
        self.commands = {}

    def add_command(
        self,
        command: str,
        category: str,
        description_key: str = None,
        context_location: str = None,
    ):
        if context_location is None:
            # If context_location is not defined, get context from file name who added the command
            frame = inspect.stack()[1]
            context_location = (
                frame[0].f_code.co_filename.split(os.path.sep)[-1].split(".")[0]
            )
        if description_key is None:
            description_key = command + "_description"
        if self.commands.get(category) is None:
            self.commands[category] = []
        self.commands[category].append(
            dict(
                command=command,
                description_key=description_key,
                context=context_location,
            )
        )

    def get_commands_message(self, strings_manager, category: str = None):
        # TODO: Add pagination support.
        if category is None:
            cmds_list = []
            for category in self.commands:
                cmds_list += self.commands[category]
        else:
            cmds_list = self.commands[category]

        res = (
            strings_manager("command_category_title").format(
                category=strings_manager(category)
            )
            + "\n\n"
        )

        cmds_list.sort(key=lambda k: k["command"])

        for cmd in cmds_list:
            res += f"<b>/{cmd['command']}</b> - <i>{strings_manager(cmd['description_key'], context=cmd['context'])}</i>\n"

        return res


commands = BotCommands()


def get_emoji_regex():
    global _EMOJI_REGEXP
    if not _EMOJI_REGEXP:
        e_list = [
            getattr(emoji, e).encode("unicode-escape").decode("ASCII")
            for e in dir(emoji)
            if not e.startswith("_")
        ]
        # to avoid re.error excluding char that start with '*'
        e_sort = sorted([x for x in e_list if not x.startswith("*")], reverse=True)
        # Sort emojis by length to make sure multi-character emojis are
        # matched first
        pattern_ = f"({'|'.join(e_sort)})"
        _EMOJI_REGEXP = re.compile(pattern_)
    return _EMOJI_REGEXP


EMOJI_PATTERN = get_emoji_regex()


def deEmojify(text: str) -> str:
    """Remove emojis and other non-safe characters from string."""
    return EMOJI_PATTERN.sub("", text)


# Thank github.com/usernein for shell_exec
async def shell_exec(code, treat=True):
    process = await asyncio.create_subprocess_shell(
        code, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )

    stdout = (await process.communicate())[0]
    if treat:
        stdout = stdout.decode().strip()
    return stdout, process


def get_format_keys(string: str) -> List[str]:
    """Return a list of formatting keys present in string."""
    return [i[1] for i in Formatter().parse(string) if i[1] is not None]
