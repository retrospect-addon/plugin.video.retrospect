# SPDX-License-Identifier: GPL-3.0-or-later

import io


from resources.lib.retroconfig import Config
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper


class WebDialogue(object):
    def __init__(self):
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

        port = 8181
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
                self.wfile.write(b"message")
                self.wfile.write(b'\n')
                return

            # noinspection PyPep8Naming
            def do_POST(self):
                if self.path != "/":
                    self.send_error(404, "NOT FOUND")
                    return
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                key, value = post_data.split("=", 1)
                value = HtmlEntityHelper.url_decode(value)

                self.send_response(200)
                self.end_headers()
                self.wfile.write("POST request for {}: {}".format(self.path, value).encode('utf-8'))

        httpd = HTTPServer(server_address, RetroHandler)
        print("Servering on ", port)
        httpd.serve_forever()
        return None


if __name__ == '__main__':
    d = WebDialogue()
    d.input("test", "test")
