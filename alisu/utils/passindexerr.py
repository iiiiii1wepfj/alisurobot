def pass_index_error(f):
    @wraps(f)
    async def pass_index_err(
        c: Client,
        m: Message,
        *args,
        **kwargs,
    ):
        try:
            return await f(c, m, *args, **kwargs)
        except IndexError:
            pass
    return pass_index_err
