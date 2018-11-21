import os

from helpers.htmlentityhelper import HtmlEntityHelper
from urihandler import UriHandler
from helpers.jsonhelper import JsonHelper


class LogSender:
    def __init__(self, api_key, logger=None, proxy=None, mode='gist'):
        """
        @param api_key: the API key for pastebin or gist
        @param logger: a possible Logger object
        @param proxy:  a possible proxy to use
        @param mode:   either 'gist' or 'pastebin'        
        """

        if not api_key:
            raise ValueError("API key missing")

        self.__apiKey = api_key
        self.__logger = logger
        self.__proxy = proxy

        self.__mode = mode
        if mode == 'pastebin':
            self.__maxSize = 475 * 1024  # max is 500 kB but we play it safe
        elif mode == 'gist':
            self.__maxSize = 25 * 1024 * 1024  # max is 1000 kB for displaying, none for raw
        else:
            raise ValueError("Invalid mode: %s" % (mode, ))
        return

    def send_file(self, name, file_path, expire='1M', paste_format=None, user_key=None):
        if not file_path:
            raise ValueError("No filename specified")

        if self.__logger:
            self.__logger.info("Sending log at: %s", file_path)

        if self.__mode == 'gist':
            return self.send_files(name, [file_path])

        code = self.__read_file_bytes(file_path)
        return self.send(name, code, expire, paste_format, user_key)

    def send_files(self, name, file_paths):
        if self.__mode != "gist":
            raise ValueError("Invalid mode for multiple files")

        params = {
            "description": name,
            "public": False,
            "files": {
                # name: {
                #     "content": code
                # }
            }
        }

        for file_path in file_paths:
            if not os.path.isfile(file_path):
                continue
            code = self.__read_file_bytes(file_path)
            file_name = os.path.split(file_path)
            params["files"][file_name[-1]] = {"content": code}

        headers = {
            "Content-Type": "application/json"
        }
        post_data = JsonHelper.dump(params, pretty_print=False)
        data = UriHandler.open("https://api.github.com/gists", params=post_data,
                               proxy=self.__proxy, additional_headers=headers)
        if not data:
            raise IOError("Error posting Gist to GitHub")

        json_data = JsonHelper(data)
        url = json_data.get_value("html_url")
        if self.__logger:
            self.__logger.info("Gist: %s", url)

        # minify with google
        # POST https://www.googleapis.com/urlshortener/v1/url
        # Content-Type: application/json
        shortener = {"longUrl": url}
        google = "https://www.googleapis.com/urlshortener/v1/url?key=%s" % (self.__apiKey,)
        google_data = UriHandler.open(google, params=JsonHelper.dump(shortener, False),
                                      proxy=self.__proxy,
                                      additional_headers={"Content-Type": "application/json"})

        google_url = JsonHelper(google_data).get_value("id")
        if self.__logger:
            self.__logger.info("Goo.gl: %s", google_url)
        return google_url

    def send(self, name, code, expire='1M', paste_format=None, user_key=None):
        if not name:
            raise ValueError("Name missing")
        if not code:
            raise ValueError("No code data specified")

        if self.__mode == 'pastebin':
            return self.__send_paste_bin(name, code, expire, paste_format, user_key)
        else:
            return self.__send_git_hub_gist(name, code)

    def __send_git_hub_gist(self, name, code):
        params = {
            "description": name,
            "public": False,
            "files": {
                name: {
                    "content": code
                }
            }
        }
        headers = {
            "Content-Type": "application/json"
        }
        post_data = JsonHelper.dump(params, pretty_print=False)
        data = UriHandler.open("https://api.github.com/gists", params=post_data,
                               proxy=self.__proxy, additional_headers=headers)
        if not data:
            raise IOError("Error posting Gist to GitHub")

        json_data = JsonHelper(data)
        url = json_data.get_value("html_url")
        if self.__logger:
            self.__logger.info("Gist: %s", url)

        # minify with google
        # POST https://www.googleapis.com/urlshortener/v1/url
        # Content-Type: application/json
        shortener = {"longUrl": url}
        google = "https://www.googleapis.com/urlshortener/v1/url?key=%s" % (self.__apiKey, )
        google_data = UriHandler.open(google, params=JsonHelper.dump(shortener, False),
                                      proxy=self.__proxy,
                                      additional_headers={"Content-Type": "application/json"})

        return JsonHelper(google_data).get_value("id")

    def __send_paste_bin(self, name, code, expire='1M', paste_format=None, user_key=None):
        if not name:
            raise ValueError("Name missing")
        if not code:
            raise ValueError("No code data specified")

        params = {
            'api_option': 'paste',
            'api_paste_private': 1,  # 0=public 1=unlisted 2=private
            'api_paste_name': name,
            'api_paste_expire_date': expire,
            'api_dev_key': self.__apiKey,
            'api_paste_code': code,
        }

        if paste_format:
            params['api_paste_format'] = paste_format
        if user_key:
            params['api_user_key'] = user_key

        post_params = reduce(lambda x, y: "%s&%s=%s" % (
            x,
            y,
            HtmlEntityHelper.url_encode(str(params[y]))), params.keys(), "").lstrip("&")

        if self.__logger:
            self.__logger.debug("Posting %d chars to pastebin.com", len(code))
            # self.__logger.Trace("POST params: %s", post_params)

        data = UriHandler.open("http://pastebin.com/api/api_post.php", params=post_params,
                               proxy=self.__proxy)

        if "pastebin.com" not in data:
            raise IOError(data)

        if self.__logger:
            self.__logger.info("PasteBin: %s", data)

        return data

    def __read_file_bytes(self, file_path):
        code = ""
        with open(file_path) as fp:
            fp.seek(0, os.SEEK_END)
            size = fp.tell()
            fp.seek(0, os.SEEK_SET)
            if size > self.__maxSize:
                if self.__logger:
                    self.__logger.warning("Filesize too large: %s, posting last %s kB",
                                          size, self.__maxSize / 1024)

                # post the top so wwe have all the required data, and the bottom
                top_bytes = 20
                code += fp.read(top_bytes * 1024)
                code += "\n%s\n" % ("*" * 100)
                fp.seek(-(self.__maxSize - (top_bytes * 1024)), os.SEEK_END)

            code += fp.read()
        return code
