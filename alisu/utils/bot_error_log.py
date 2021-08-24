from pyrogram import Client
from pyrogram.types import Message
from pyrogram import StopPropagation
from pyrogram.errors.exceptions.forbidden_403 import ChatWriteForbidden
from pyrogram.errors.exceptions.bad_request_400 import ChatAdminRequired
from alisu.config import nekobin_error_paste_url, log_chat
from alisu.utils.consts import http
from tortoise.exceptions import DoesNotExist
from functools import wraps
import traceback, html


def logging_errors(f):
    @wraps(f)
    async def err_log(
        c: Client,
        m: Message,
        *args,
        **kwargs,
    ):
        try:
            return await f(c, m, *args, **kwargs)
        except ChatWriteForbidden:
            return await m.chat.leave()
        except (DoesNotExist, ChatAdminRequired, StopPropagation):
            pass
        except Exception as e:
            if c.log_chat_errors:
                full_trace = traceback.format_exc()
                try:
                    paste_err = await http.post(
                        f"{nekobin_error_paste_url}/api/documents",
                        json={"content": full_trace},
                    )
                    pastereqjson_one = paste_err.json()
                    pastereqjson = pastereqjson_one["result"]
                    paste_json_key = pastereqjson["key"]
                    paste_url = f"{nekobin_error_paste_url}/{paste_json_key}"
                    thefulltrace = f"{paste_url}"
                except:
                    thefulltrace = "error has occurred in the paste"
                try:
                    await c.send_message(
                        log_chat,
                        f"<b>An error has occurred:</b>\n<code>{type(e).__name__}: {html.escape(str(e))}</code>\n\nFile <code>{f.__module__}</code> in <code>{f.__name__}</code>\n<b>Full traceback:</b> {thefulltrace}",
                        disable_web_page_preview=True,
                    )
                except:
                    pass

    return err_log
