# SPDX-License-Identifier: GPL-3.0-or-later

import io
import xbmc

from resources.lib.logger import Logger
from resources.lib.retroconfig import Config
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.helpers.languagehelper import LanguageHelper


class WebDialogue(object):
    def __init__(self):
        self.__value = None
        return

    # noinspection PyCompatibility
    def input(self, heading, text, time_out=0):
        """ Show an input dialog.

        :param str|int heading:             Dialog heading.
        :param str|int text:                Default value
        :param int time_out:            Seconds to autoclose dialog (default=do not autoclose)

        :return: Returns the entered data as a string. Returns an empty string if dialog was canceled.
        :rtype: str

        """

        if isinstance(heading, int):
            heading = LanguageHelper.get_localized_string(heading)
        if isinstance(text, int):
            text = LanguageHelper.get_localized_string(text)

        port = 3145
        server_address = ('', port)
        try:
            # noinspection PyUnresolvedReferences
            from http.server import HTTPServer
            # noinspection PyUnresolvedReferences
            from http.server import BaseHTTPRequestHandler
        except:
            # noinspection PyUnresolvedReferences
            from SocketServer import TCPServer as HTTPServer
            # noinspection PyUnresolvedReferences
            from BaseHTTPServer import BaseHTTPRequestHandler

        # Create simple handler class
        class RetroHandler(BaseHTTPRequestHandler):
            def __init__(self, request, client_address, server):
                BaseHTTPRequestHandler.__init__(self, request, client_address, server)
                self.server = server

            artwork = {
                "fanart": (Config.fanart, "image/jpeg"),
                "poster": (Config.poster, "image/jpeg"),
                "icon": (Config.icon, "image/png")
            }

            ok = xbmc.getLocalizedString(222)
            cancel = xbmc.getLocalizedString(186)

            # noinspection PyPep8Naming
            def do_GET(self):
                if self.path.startswith("/image/"):
                    path, mime = RetroHandler.artwork.get(self.path.rsplit("/", 1)[-1], (None, None))
                    if not path:
                        self.send_error(404, "NOT FOUND")
                        return

                    self.send_response(200)
                    self.send_header("Content-Type", mime)
                    self.end_headers()
                    self.wfile.write(io.open(path, mode='br').read())
                    return

                elif self.path != "/":
                    self.send_error(404, "NOT FOUND")
                    return

                self.send_response(200)
                self.end_headers()
                self.wfile.write(self.__get_html(
                    Config.appName, heading, text, RetroHandler.ok, RetroHandler.cancel).encode("utf-8"))
                self.wfile.write(b'\n')
                return

            # noinspection PyPep8Naming
            def do_POST(self):
                if self.path != "/":
                    self.send_error(404, "NOT FOUND")
                    return
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                data = {}
                for kv in post_data.split("&"):
                    key, value = kv.split("=", 1)
                    data[key] = HtmlEntityHelper.url_decode(value)

                self.send_response(200)
                self.end_headers()
                self.wfile.write(self.__close_html().encode("utf-8"))
                self.server._BaseServer__shutdown_request = True

                if "cancel" in data:
                    self.server.cancelled = True
                self.server.value = data["value"]
                return

            # noinspection PyShadowingBuiltins
            def log_message(self, format, *args):
                Logger.debug(format, *args)

            def __close_html(self):
                return """<html>
                    <head>
                    <body style="background-color: black; 
                                 font-family: sans-serif;
                                 color: white">
                    </body>
                    </html>
                    """""

            def __get_html(self, title, setting_name, setting_value, ok="Ok", cancel="Cancel"):
                return """<!DOCTYPE html>
                    <html>
                    <head>
                    <body style="background-color: black; 
                                 background-image: url('image/fanart'); 
                                 background-position: center top;
                                 font-family: sans-serif;
                                 color: white;">
    
                    <h1>{}</h2> 
                    <form action="/" method="post">
                      <label for="value">{}:</label><br />
                      <input type="text" id="value" name="value" value="{}" style="margin: 10px 0px; min-width: 450px;" />
                      <br /><br />
                      <input type="submit" name="ok" value="{}" />
                      <input type="submit" name="cancel" value="{}" />
                    </form>
                    </body>
                    </html>
                    """.format(title, setting_name, setting_value, ok, cancel)

        class RetroHTTPServer(HTTPServer):
            # noinspection PyPep8Naming
            def __init__(self, server_address, RequestHandlerClass):  # NOSONAR
                HTTPServer.__init__(self, server_address, RequestHandlerClass)
                self.value = None
                self.cancelled = False

            def handle_error(self, request, client_address):
                """Handle an error gracefully. May be overridden.

                The default is to print a traceback and continue.

                """
                import traceback
                Logger.error("RetroHTTP: %s", traceback.format_exc())

        try:
            httpd = RetroHTTPServer(server_address, RetroHandler)
            print("Servering on ", port)
            httpd.serve_forever()
            return httpd.value, httpd.cancelled
        except:
            Logger.critical("Error with WebDialogue", exc_info=True)
            return None, False


if __name__ == '__main__':
    Logger.create_logger(None, "WebDialogue", min_log_level=0)
    d = WebDialogue()
    print(d.input("Cookie value for site", "test"))
