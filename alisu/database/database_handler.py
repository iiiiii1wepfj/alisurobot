from tortoise import Tortoise, fields
from tortoise.models import Model


class groups(Model):
    chat_id = fields.BigIntField(pk=True)
    welcome = fields.TextField(null=True)
    welcome_enabled = fields.BooleanField(null=True)
    last_welcome_message_id = fields.BigIntField(null=True)
    del_last_welcome_message = fields.BooleanField(null=True)
    rules = fields.TextField(null=True)
    warns_limit = fields.IntField(null=True)
    chat_lang = fields.TextField(null=True)
    cached_admins = fields.TextField(null=True)
    antichannelpin = fields.BooleanField(null=True)
    delservicemsgs = fields.BooleanField(null=True)
    warn_action = fields.TextField(null=True)
    warn_time = fields.BigIntField(null=True)
    private_rules = fields.BooleanField(null=True)


class users(Model):
    user_id = fields.BigIntField(pk=True)
    chat_lang = fields.TextField(null=True)


class filters(Model):
    chat_id = fields.BigIntField()
    filter_name = fields.TextField()
    raw_data = fields.TextField(null=True)
    file_id = fields.TextField(null=True)
    filter_type = fields.TextField()


class notes(Model):
    chat_id = fields.BigIntField()
    note_name = fields.TextField()
    raw_data = fields.TextField(null=True)
    file_id = fields.TextField(null=True)
    note_type = fields.TextField()


class channels(Model):
    chat_id = fields.BigIntField(pk=True)
    chat_lang = fields.TextField(null=True)


class user_warns(Model):
    user_id = fields.BigIntField(null=True)
    chat_id = fields.BigIntField(null=True)
    count = fields.IntField(null=True)


async def init_database():
    await Tortoise.init(
        db_url="sqlite://alisu/database/alisudb.db", modules={"models": [__name__]}
    )
    await Tortoise.generate_schemas()
