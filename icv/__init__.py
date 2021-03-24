from re import sub, search
from pathlib import Path
from requests_html import HTMLSession
from pickle import dump, load
from atexit import register
from hashlib import sha1
from fuzzywuzzy import process


class ICV:
    def __init__(self, config):
        self._config = config
        Path("session").touch(exist_ok=True)
        with open("session", "rb+") as file:
            try:
                self._s = load(file)
            except EOFError:
                self._s = HTMLSession()
        register(self._save_session)
        if any([cookie.name == "SMFCookie68" and cookie.is_expired() for cookie in self._s.cookies]) \
                or "SMFCookie68" not in self._s.cookies:
            self._login()
        self._threads = {
            "movies": ["45243", "45242", "45240",
                       "45246", "45245", "45244",
                       "45255", "45255", "45255",
                       "12857",
                       "12858",
                       "12874",
                       "12879"],
            "shows": ["45259", "45258", "45257",
                      "45262", "45261", "45260",
                      "73263", "73262", "73261"],
            "anime": ["12877",
                      "12878",
                      "12856"],
            "cartoons": ["29869", "12875",
                         "12876",
                         "12856"],
            "ebooks": ["29871", "12890"],
            "audiobooks": ["12891"],
            "comics": ["96017"],
            "magazines": ["12892"],
            "android": ["12888"],
            "windows": ["104837", "104836", "12880"],
        }

    def _save_session(self):
        with open("session", "wb+") as file:
            dump(self._s, file, 4)

    def _login(self):
        user = self._config.USERNAME
        passwrd = self._config.PASSWORD
        hidden_input = getattr(self._s.get("https://www.icv-crew.com/forum/index.php"), "html")\
            .find("input[name='hash_passwrd'] + input[type='hidden']", first=True)
        session_id = hidden_input.attrs["value"]
        session_name = hidden_input.attrs["name"]
        hash_passwrd = sha1(sha1(user.lower().encode("utf-8") + passwrd.encode("utf-8")).hexdigest().encode("utf-8") +
                            session_id.encode("utf-8")).hexdigest()
        self._s.post("https://www.icv-crew.com/forum/index.php?action=login2", data={"user": user,
                                                                                     "passwrd": "",
                                                                                     "hash_passwrd": hash_passwrd,
                                                                                     session_name: session_id,
                                                                                     "cookieneverexp": "on"})

        if "SMFCookie68" not in self._s.cookies:
            raise Exception("Login error, please check credentials and retry.")
        self._save_session()

    def get_releases(self, categories=None):
        result = {}
        keys = categories if categories else self._threads.keys()
        for key in keys:
            temp = {}
            value = self._threads.get(key, [])
            for link in value:
                r = self._s.get("https://www.icv-crew.com/forum/index.php?topic={}.0".format(link))
                html = getattr(r, "html")
                els = html.find(".tlistcol2 > a")
                for el in els:
                    thread_id = search(r"topic=(\d+)", el.absolute_links.pop()).group(1)
                    temp[thread_id] = el.text
            if temp:
                result[key] = temp
        return result

    def get_magnets(self, thread_id, withdraw=False):
        r = self._s.get("https://www.icv-crew.com/forum/index.php?topic={}".format(thread_id))
        html = getattr(r, "html")
        url = html.find("a.thank_you_button_link", first=True)
        if url:
            url = url.absolute_links.pop()
            r = self._s.get(url)
            html = getattr(r, "html")
        magnets = [m for m in html.find("div.post", first=True).absolute_links if m.startswith("magnet:")]
        if withdraw:
            self._s.get(html.find("a.withdraw_thank_you_button_link", first=True).absolute_links.pop())
        return magnets

    def get_category_list(self):
        return ["all"] + [x for x in self._threads.keys()]

    @staticmethod
    def search(text, releases, limit):
        def processor(a):
            return sub(r" ?\([^)]+\) ?| ?\[[^]]+] ?", "", a)

        results = {}
        for key, value in releases.items():
            results[key] = process.extractBests(text, value, limit=limit, processor=processor)
        return results
