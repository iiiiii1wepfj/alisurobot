from pyrogram.types import Message
from pyrogram.file_id import FileId
from pyrogram.scaffold import Scaffold

class PyrogramGetFileFromMessage(Scaffold):
 async def pyrogram_get_file_from_message(self, message: Message):
  media_list_support = ("audio", "document", "photo", "sticker", "animation", "video", "voice", "video_note", "new_chat_photo")
  if isinstance(msg, Message):
   for kind in media_list_support:
    mediatype = getattr(msg, kind, None)
    if mediatype is not None:
     break
   else:
    raise ValueError("can't found the media type")
  else:
   mediatype = msg
  pyro_file_id_obj = FileId.decode(mediatype.file_id)
  r = await self.get_file(file_id=pyro_file_id_obj, file_size=getattr(mediatype, "file_size", 0), progress=None)
  return r
