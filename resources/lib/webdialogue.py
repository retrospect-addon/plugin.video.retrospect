# SPDX-License-Identifier: GPL-3.0-or-later

import io

import xbmc
import xbmcgui

from resources.lib.logger import Logger
from resources.lib.retroconfig import Config
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.urihandler import UriHandler


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
            artwork = {
                "fanart": (Config.fanart, "image/jpeg"),
                "poster": (Config.poster, "image/jpeg"),
                "icon": (Config.icon, "image/png")
            }

            cancel = xbmc.getLocalizedString(222)
            ok = xbmc.getLocalizedString(186)

            def __init__(self, request, client_address, server):
                # Set the handler timeout so connections from browsers get killed faster.
                self.timeout = 1
                # We need the server to be accessible.
                self.server = server
                BaseHTTPRequestHandler.__init__(self, request, client_address, server)

            # noinspection PyPep8Naming
            def do_GET(self):
                if self.path.startswith("/image/"):
                    path, mime = RetroHandler.artwork.get(self.path.rsplit("/", 1)[-1], (None, None))
                    if not path:
                        self.send_error(404, "NOT FOUND")
                        self.__fill_and_end_headers()
                        return

                    self.send_response(200)
                    self.send_header("Content-Type", mime)
                    with io.open(path, mode='br') as fp:
                        data = fp.read()
                        self.send_header('Content-Length', str(len(data)))
                        self.__fill_and_end_headers()
                        self.wfile.write(data)
                    return

                elif self.path != "/":
                    self.send_error(404, "NOT FOUND")
                    self.__fill_and_end_headers()
                    return

                self.send_response(200)
                html = self.__get_html(
                    Config.appName, heading, text, RetroHandler.ok, RetroHandler.cancel).encode("utf-8")

                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(html)))
                self.__fill_and_end_headers()
                self.wfile.write(html)
                self.server.active = True
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
                    Logger.trace("RetroServer: Received a 'Cancel' POST request")
                    self.server.cancelled = True
                else:
                    Logger.trace("RetroServer: Received a 'Ok' POST request")
                    self.server.completed = True
                self.server.value = data["value"]
                return

            # noinspection PyShadowingBuiltins
            def log_message(self, format, *args):
                text = format % args
                Logger.trace("RetroServer: %s", text)

            def __fill_and_end_headers(self):
                self.send_header("Keep-Alive", "max=0")
                self.send_header('Connection', 'close')
                self.end_headers()

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

        class RetroHTTPServer(HTTPServer, xbmc.Monitor):
            # noinspection PyPep8Naming
            def __init__(self, server_address, RequestHandlerClass):  # NOSONAR
                HTTPServer.__init__(self, server_address, RequestHandlerClass)
                xbmc.Monitor.__init__(self)
                self.value = None
                self.cancelled = False
                self.completed = False
                self.active = False

            def handle_error(self, request, client_address):
                """Handle an error gracefully. May be overridden.

                The default is to print a traceback and continue.

                """
                import traceback
                Logger.error("RetroServer: %s", traceback.format_exc())

            def force_stop(self):
                Logger.debug("RetroServer: Forcing a shutdown.")
                self.shutdown()
                self.socket.close()

        try:
            httpd = RetroHTTPServer(server_address, RetroHandler)

            import threading
            th = threading.Thread(target=httpd.serve_forever)
            th.daemon = True
            th.start()

            Logger.info("RetroServer: Serving on %s", port)

            d = xbmcgui.DialogProgress()
            d.create("Stop Web Dialog", "Open browser on http://localhost:3145.")

            for i in range(0, 33):
                if d.iscanceled():
                    Logger.debug("RetroServer: User aborted the dialogue.")
                    break

                percentage = 100 - i * 3
                stop = False
                if httpd.completed:
                    Logger.debug("RetroServer: Browser input received.")
                    d.update(percentage, "Browser input received.")
                    stop = True
                elif httpd.cancelled:
                    Logger.debug("RetroServer: Browser input cancelled.")
                    d.update(percentage, "Browser input cancelled.")
                    stop = True
                elif httpd.abortRequested():
                    Logger.debug("RetroServer: Kodi requested a stop.")
                    break
                elif httpd.active:
                    d.update(percentage, "Waiting for browser response.")
                else:
                    d.update(percentage)

                # We sleep here to make sure we can read the response.
                httpd.waitForAbort(1)
                if stop:
                    Logger.trace("RetroServer: Aborting loop.")
                    break
            d.close()

            httpd.force_stop()
            if th.is_alive():
                th.join()
            th = None
            return httpd.value, httpd.cancelled
        except:
            Logger.critical("RetroServer: Error with WebDialogue", exc_info=True)
            return None, False


if __name__ == '__main__':
    Logger.create_logger(None, "WebDialogue", min_log_level=0)
    UriHandler.create_uri_handler()
    d = WebDialogue()
    print(d.input("Cookie value for site", "test"))
