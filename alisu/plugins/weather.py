from hydrogram import Client, filters
from hydrogram.types import Message

from alisu.config import prefix
from alisu.utils import commands
from alisu.utils.consts import http
from alisu.utils.localization import use_chat_lang
from alisu.utils.bot_error_log import logging_errors

# Api key used in weather.com's mobile app.
weather_apikey: str = "8de2d8b3a93542c9a2d8b3a935a2c909"

get_coords: str = "https://api.weather.com/v3/location/search"
url: str = "https://api.weather.com/v3/aggcommon/v3-wx-observations-current"

headers: dict = {"User-Agent": "curl/7.72.0"}


@Client.on_message(filters.command(["clima", "weather"], prefix))
@use_chat_lang()
@logging_errors
async def weather(c: Client, m: Message, strings):
    if len(m.command) == 1:
        return await m.reply_text(strings("weather_usage"))

    r = await http.get(
        get_coords,
        headers=headers,
        params=dict(
            apiKey=weather_apikey,
            format="json",
            language=strings("weather_language"),
            query=m.text.split(maxsplit=1)[1],
        ),
    )
    loc_json = r.json()
    if not loc_json.get("location"):
        await m.reply_text(strings("location_not_found"))
    else:
        pos = f"{loc_json['location']['latitude'][0]},{loc_json['location']['longitude'][0]}"
        r = await http.get(
            url,
            headers=headers,
            params=dict(
                apiKey=weather_apikey,
                format="json",
                language=strings("weather_language"),
                geocode=pos,
                units=strings("measurement_unit"),
            ),
        )
        res_json = r.json()

        obs_dict = res_json["v3-wx-observations-current"]

        res = strings("details").format(
            location=loc_json["location"]["address"][0],
            temperature=obs_dict["temperature"],
            feels_like=obs_dict["temperatureFeelsLike"],
            air_humidity=obs_dict["relativeHumidity"],
            wind_speed=obs_dict["windSpeed"],
            overview=obs_dict["wxPhraseLong"],
        )

        await m.reply_text(res)


commands.add_command("weather", "tools")
