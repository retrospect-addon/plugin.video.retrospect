# SPDX-License-Identifier: CC-BY-NC-SA-4.0

__all__ = ["test_version", "test_updater", "test_urihandler", "test_datehelper", "test_jsonhelper"]

import os
os.environ["KODI_STUB_RPC_RESPONSES"] = os.path.join(os.path.dirname(__file__), "data", "jsonrcpcommands")
