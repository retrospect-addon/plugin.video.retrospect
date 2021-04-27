# SPDX-License-Identifier: GPL-3.0-or-later

__all__ = ["test_version", "test_urihandler", "test_datehelper", "test_jsonhelper", "test_logger",
           "test_cloaker", "test_templatehelper", "test_youtube", "test_kodilibs", "test_logsender",
           "test_localsettings", "test_subtitlehelper", "test_channelimporter",
           "test_htmlentityhelper"]
import os
os.environ["KODI_STUB_RPC_RESPONSES"] = os.path.join(os.path.dirname(__file__), "data", "jsonrcpcommands")
