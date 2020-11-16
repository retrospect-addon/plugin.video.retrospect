# SPDX-License-Identifier: GPL-3.0-or-later

__all__ = ["test_version", "test_updater", "test_urihandler", "test_datehelper", "test_jsonhelper"]

import os
os.environ["KODI_STUB_RPC_RESPONSES"] = os.path.join(os.path.dirname(__file__), "data", "jsonrcpcommands")
