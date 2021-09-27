# pip3 install pytio
from pytio import Tio

tio = Tio()

tiolangslist_one = tio.query_languages()

langslist = sorted(tiolangslist_one)

langs_html_string_one: str = """
<html>

<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />

    <title>tio.run languages list</title>
</head>

<body>

    <ul>
"""

langs_html_string_two: str = """
    </ul>
</body>

</html>
"""

with open("langs.html", "w") as langsfile:
    langsfile.write(langs_html_string_one)

with open("langs.html", "a") as langsfile_writelangs:
    for lang in langslist:
        langsfile_writelangs.write(f"        <li>{lang}</li>\n")

with open("langs.html", "a") as langsfile_two_write:
    langsfile_two_write.write(langs_html_string_two)
