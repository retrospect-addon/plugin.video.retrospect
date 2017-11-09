import os

from helpers.htmlentityhelper import HtmlEntityHelper
from urihandler import UriHandler
from helpers.jsonhelper import JsonHelper


class LogSender:
    def __init__(self, apiKey, logger=None, proxy=None, mode='gist'):
        """
        @param apiKey: the API key for pastebin or gist
        @param logger: a possible Logger object
        @param proxy:  a possible proxy to use
        @param mode:   either 'gist' or 'pastebin'        
        """

        if not apiKey:
            raise ValueError("API key missing")

        self.__apiKey = apiKey
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

    # def Login(self, username, password):
    #     if not username:
    #         raise ValueError("Username missing")
    #     if not password:
    #         raise ValueError("Password missing")
    #
    #     params = {
    #         'api_user_name': username,
    #         'api_user_password': password,
    #         'api_dev_key': self.__apiKey
    #     }
    #
    #     postParams = reduce(lambda x, y: "%s&%s=%s" % (
    #         x,
    #         y,
    #         HtmlEntityHelper.UrlEncode(str(params[y]))), params.keys(), "").lstrip("&")
    #
    #     data = UriHandler.Open("http://pastebin.com/api/api_login.php", params=postParams,
    #                            proxy=self.__proxy)
    #
    #     if len(data) != 32:
    #         raise IOError(data)
    #
    #     if self.__logger:
    #         self.__logger.Trace("User Key: %s", data)
    #
    #     return data

    def SendFile(self, name, filePath, expire='1M', pasteFormat=None, userKey=None):
        if not filePath:
            raise ValueError("No filename specified")

        if self.__logger:
            self.__logger.Info("Sending log at: %s", filePath)

        if self.__mode == 'gist':
            return self.SendFiles(name, [filePath])

        code = self.__ReadFileBytes(filePath)
        return self.Send(name, code, expire, pasteFormat, userKey)

    def SendFiles(self, name, filePaths):
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

        for filePath in filePaths:
            if not os.path.isfile(filePath):
                continue
            code = self.__ReadFileBytes(filePath)
            fileName = os.path.split(filePath)
            params["files"][fileName[-1]] = {"content": code}

        headers = {
            "Content-Type": "application/json"
        }
        postData = JsonHelper.Dump(params, prettyPrint=False)
        data = UriHandler.Open("https://api.github.com/gists", params=postData,
                               proxy=self.__proxy, additionalHeaders=headers)
        if not data:
            raise IOError("Error posting Gist to GitHub")

        jsonData = JsonHelper(data)
        url = jsonData.GetValue("html_url")
        if self.__logger:
            self.__logger.Info("Gist: %s", url)

        # minify with google
        # POST https://www.googleapis.com/urlshortener/v1/url
        # Content-Type: application/json
        shortener = {"longUrl": url}
        google = "https://www.googleapis.com/urlshortener/v1/url?key=%s" % (self.__apiKey,)
        googleData = UriHandler.Open(google, params=JsonHelper.Dump(shortener, False),
                                     proxy=self.__proxy,
                                     additionalHeaders={"Content-Type": "application/json"})

        googleUrl = JsonHelper(googleData).GetValue("id")
        if self.__logger:
            self.__logger.Info("Goo.gl: %s", googleUrl)
        return googleUrl

    def Send(self, name, code, expire='1M', pasteFormat=None, userKey=None):
        if not name:
            raise ValueError("Name missing")
        if not code:
            raise ValueError("No code data specified")

        if self.__mode == 'pastebin':
            return self.__SendPasteBin(name, code, expire, pasteFormat, userKey)
        else:
            return self.__SendGitHubGist(name, code)

    def __SendGitHubGist(self, name, code):
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
        postData = JsonHelper.Dump(params, prettyPrint=False)
        data = UriHandler.Open("https://api.github.com/gists", params=postData,
                               proxy=self.__proxy, additionalHeaders=headers)
        if not data:
            raise IOError("Error posting Gist to GitHub")

        jsonData = JsonHelper(data)
        url = jsonData.GetValue("html_url")
        if self.__logger:
            self.__logger.Info("Gist: %s", url)

        # minify with google
        # POST https://www.googleapis.com/urlshortener/v1/url
        # Content-Type: application/json
        shortener = {"longUrl": url}
        google = "https://www.googleapis.com/urlshortener/v1/url?key=%s" % (self.__apiKey, )
        googleData = UriHandler.Open(google, params=JsonHelper.Dump(shortener, False),
                                     proxy=self.__proxy,
                                     additionalHeaders={"Content-Type": "application/json"})

        return JsonHelper(googleData).GetValue("id")

    def __SendPasteBin(self, name, code, expire='1M', pasteFormat=None, userKey=None):
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

        if pasteFormat:
            params['api_paste_format'] = pasteFormat
        if userKey:
            params['api_user_key'] = userKey

        postParams = reduce(lambda x, y: "%s&%s=%s" % (
            x,
            y,
            HtmlEntityHelper.UrlEncode(str(params[y]))), params.keys(), "").lstrip("&")

        if self.__logger:
            self.__logger.Debug("Posting %d chars to pastebin.com", len(code))
            # self.__logger.Trace("POST params: %s", postParams)

        data = UriHandler.Open("http://pastebin.com/api/api_post.php", params=postParams,
                               proxy=self.__proxy)

        if "pastebin.com" not in data:
            raise IOError(data)

        if self.__logger:
            self.__logger.Info("PasteBin: %s", data)

        return data

    def __ReadFileBytes(self, filePath):
        code = ""
        with open(filePath) as fp:
            fp.seek(0, os.SEEK_END)
            size = fp.tell()
            fp.seek(0, os.SEEK_SET)
            if size > self.__maxSize:
                if self.__logger:
                    self.__logger.Warning("Filesize too large: %s, posting last %s kB",
                                          size, self.__maxSize / 1024)

                # post the top so wwe have all the required data, and the bottom
                topBytes = 20
                code += fp.read(topBytes * 1024)
                code += "\n%s\n" % ("*" * 100)
                fp.seek(-(self.__maxSize - (topBytes * 1024)), os.SEEK_END)

            code += fp.read()
        return code
