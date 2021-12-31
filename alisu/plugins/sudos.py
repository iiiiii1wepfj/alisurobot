import asyncio
import html
import io
import os
import re
import sys
import traceback
import humanfriendly
import time
from contextlib import redirect_stdout
from typing import Union

import speedtest
from meval import meval
from pyrogram import (
    Client,
    filters,
    __version__ as pyrogram_version,
)
from pyrogram.errors import RPCError
from pyrogram.raw.all import (
    layer as pyrogram_layer,
)
from pyrogram.types import Message

from alisu import (
    __version__ as alisu_version,
)
from alisu.database import (
    groups,
    users,
    notes,
    filters as dbfilters,
)
from alisu.utils import sudofilter
from alisu.utils.localization import use_chat_lang

from threading import Thread

prefix: Union[list, str] = "!"


def restartbot(c: Client):
    c.stop_sync()
    args = [sys.executable, "-m", "alisu"]
    os.execv(sys.executable, args)


@Client.on_message(filters.command("sudos", prefix) & sudofilter)
async def sudos(c: Client, m: Message):
    await m.reply_text("Test")


@Client.on_message(filters.command("cmd", prefix) & sudofilter)
@use_chat_lang()
async def run_cmd(c: Client, m: Message, strings):
    cmd = m.text.split(maxsplit=1)[1]
    if re.match("(?i)poweroff|halt|shutdown|reboot", cmd):
        res = strings("forbidden_command")
    else:
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        res = (
            "<b>Output:</b>\n<code>{}</code>".format(
                html.escape(stdout.decode().strip())
            )
            if stdout
            else ""
        ) + (
            "\n<b>Errors:</b>\n<code>{}</code>".format(
                html.escape(stderr.decode().strip())
            )
            if stderr
            else ""
        )
    await m.reply_text(res)


@Client.on_message(filters.command("upgrade", prefix) & sudofilter)
@use_chat_lang()
async def upgrade(c: Client, m: Message, strings):
    sm = await m.reply_text("Upgrading sources...")
    proc = await asyncio.create_subprocess_shell(
        "git pull --no-edit",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout = (await proc.communicate())[0]
    if proc.returncode == 0:
        if "Already up to date." in stdout.decode():
            await sm.edit_text("There's nothing to upgrade.")
        else:
            await sm.edit_text(strings("restarting"))
            Thread(target=asyncio.run, args=(restartbot(c),)).start()
            await sm.edit_text("done")
    else:
        await sm.edit_text(
            f"Upgrade failed (process exited with {proc.returncode}):\n{stdout.decode()}"
        )
        proc = await asyncio.create_subprocess_shell("git merge --abort")
        await proc.communicate()


@Client.on_message(filters.command("eval", prefix) & sudofilter)
async def evals(c: Client, m: Message):
    text = m.text.split(maxsplit=1)[1]
    try:
        res = await meval(text, globals(), **locals())
    except:  # skipcq
        ev = traceback.format_exc()
        output_eval_one = f"<code>{html.escape(ev)}</code>"
        if len(output_eval_one) > c.tg_max_text_msg_len:
            bio = io.BytesIO(str(ev).encode())
            bio.name: str = "eval.txt"
            await m.reply_document(bio)
        else:
            await m.reply_text(output_eval_one)
    else:
        try:
            output_eval_msg_two_txt = f"<code>{html.escape(str(res))}</code>"
            if len(output_eval_msg_two_txt) > c.tg_max_text_msg_len:
                bio = io.BytesIO(str(res).encode())
                bio.name: str = "eval.txt"
                await m.reply_document(bio)
            else:
                await m.reply_text(output_eval_msg_two_txt)
        except Exception as e:  # skipcq
            output_eval_e = str(e)
            if len(output_eval_e) > c.tg_max_text_msg_len:
                bio = io.BytesIO(str(output_eval_e).encode())
                bio.name: str = "eval.txt"
                await m.reply_document(bio)
            else:
                await m.reply_text(output_eval_e)


@Client.on_message(filters.command("exec", prefix) & sudofilter)
async def execs(c: Client, m: Message):
    strio = io.StringIO()
    code = m.text.split(maxsplit=1)[1]
    exec(
        "async def __ex(c, m): " + " ".join("\n " + l for l in code.split("\n"))
    )  # skipcq: PYL-W0122
    with redirect_stdout(strio):
        try:
            await locals()["__ex"](c, m)
        except:  # skipcq
            trace_format_exc_exec_cmd = traceback.format_exc()
            msg_out_one = html.escape(trace_format_exc_exec_cmd)
            if len(msg_out_one) > c.tg_max_text_msg_len:
                bio = io.BytesIO(str(trace_format_exc_exec_cmd).encode())
                bio.name: str = "exec.txt"
                return await m.reply_document(bio)
            else:
                return await m.reply_text(msg_out_one)

    if strio.getvalue().strip():
        out_one = strio.getvalue()
        out = f"<code>{html.escape(out_one)}</code>"
    else:
        out_one = "Command executed."
        out = "Command executed."
    if len(out) > c.tg_max_text_msg_len:
        bio = io.BytesIO(str(out_one).encode())
        bio.name: str = "exec.txt"
        await m.reply_document(bio)
    else:
        await m.reply_text(out)


@Client.on_message(filters.command("speedtest", prefix) & sudofilter)
@use_chat_lang()
async def test_speed(c: Client, m: Message, strings):
    string = strings("speedtest")
    sent = await m.reply_text(string.format(host="", ping="", download="", upload=""))
    s = speedtest.Speedtest()
    bs = s.get_best_server()
    await sent.edit_text(
        string.format(
            host=bs["sponsor"], ping=int(bs["latency"]), download="", upload=""
        )
    )
    dl = round(s.download() / 1024 / 1024, 2)
    await sent.edit_text(
        string.format(
            host=bs["sponsor"], ping=int(bs["latency"]), download=dl, upload=""
        )
    )
    ul = round(s.upload() / 1024 / 1024, 2)
    await sent.edit_text(
        string.format(
            host=bs["sponsor"], ping=int(bs["latency"]), download=dl, upload=ul
        )
    )


@Client.on_message(filters.command("restart", prefix) & sudofilter)
@use_chat_lang()
async def restart(c: Client, m: Message, strings):
    sent = await m.reply_text(strings("restarting"))
    Thread(target=restartbot, args=(c,)).start()
    await sent.edit_text("done")


@Client.on_message(filters.command("leave", prefix) & sudofilter)
async def leave_chat(c: Client, m: Message):
    if len(m.command) == 1:
        try:
            await c.leave_chat(m.chat.id)
        except RPCError as e:
            print(e)
    else:
        chat_id = m.text.split(maxsplit=1)[1]
        try:
            await c.leave_chat(int(chat_id))
        except RPCError as e:
            print(e)


@Client.on_message(filters.command(["bot_stats", "stats"], prefix) & sudofilter)
async def getbotstats(c: Client, m: Message):
    users_count = await users.all().count()
    groups_count = await groups.all().count()
    filters_count = await dbfilters.all().count()
    notes_count = await notes.all().count()
    bot_uptime = round(time.time() - c.start_time)
    bot_uptime = humanfriendly.format_timespan(bot_uptime)

    await m.reply_text(
        "<b>Bot statistics:</b>\n\n"
        f"<b>Users:</b> {users_count}\n"
        f"<b>Groups:</b> {groups_count}\n"
        f"<b>Filters:</b> {filters_count}\n"
        f"<b>Notes:</b> {notes_count}\n"
        f"<b>Pyrogram Version:</b> {pyrogram_version} (Layer {pyrogram_layer})\n"
        f"<b>Bot Version:</b> {alisu_version} ({c.version_code})\n"
        f"<b>Uptime:</b> {bot_uptime}"
    )


@Client.on_message(filters.command("chat", prefix) & sudofilter)
async def getchatcmd(c: Client, m: Message):
    if len(m.text.split()) > 1:
        targetchat = await c.get_chat(m.command[1])
        if targetchat.type != "private":
            await m.reply_text(
                f"<b>Title:</b> {targetchat.title}\n<b>Username:</b> {targetchat.username}\n<b>Link:</b> {targetchat.invite_link}\n<b>Members:</b> {targetchat.members_count}"
            )
        else:
            await m.reply_text("This is a private Chat.")
    else:
        await m.reply_text("You must specify the Chat.")
