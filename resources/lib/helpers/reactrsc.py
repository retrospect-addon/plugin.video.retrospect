from resources.lib.chn_class import PreProcessorResult
import json
from typing import Any, Dict, Optional, Set, List, Union
from typing import Tuple

from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.logger import Logger
from resources.lib.mediaitem import MediaItem


class RSCHelper:
    """
    Helper for converting React Server Components (Next.js RSC wire format)
    into resolved JSON by dereferencing $Lx and $@x references.
    """

    def __init__(self, content: str) -> None:
        self._records: Dict[str, Any] = {}
        self._root: Optional[Any] = None
        self._content: str = content

    def convert_to_json(self) -> Union[List, Dict]:
        """
        Convert RSC wire-format content into resolved JSON.
        """
        self._records.clear()
        self._root = None

        for line in self._content.splitlines():
            self._parse_line(line.strip())

        if self._root is None:
            raise ValueError("No root record (0:) found in RSC content")

        return self._resolve(self._root)

    def _parse_line(self, line: str) -> None:
        if not line or ":" not in line:
            return

        key, raw = line.split(":", 1)
        raw = raw.strip()

        try:
            # Module reference: I[...]
            if raw.startswith("I["):
                self._records[key] = {
                    "__module__": json.loads(raw[1:])
                }
                return

            if raw.startswith("T"):
                # string with length
                hex_length, raw = raw[1:].split(",", 1)
                length = int(hex_length, 16)
                text_value = raw[0:length]
                remainder = raw[length:]
                self._records[key] = text_value
                return self._parse_line(remainder)

            parsed = json.loads(raw)
            self._records[key] = parsed

            if key == "0":
                self._root = parsed

        except json.JSONDecodeError:
            # Ignore non-JSON lines
            pass

    def _normalize(self, value: Any) -> Any:
        if value == "$undefined":
            return None

        if isinstance(value, str) and value.startswith("$S"):
            return {"__symbol__": value[2:]}

        return value

    def _resolve(self, value: Any, seen: Optional[Set[str]] = None) -> Any:
        if seen is None:
            seen = set()

        if isinstance(value, str):
            if value.startswith("$L"):
                key = value[2:]
                if key in seen:
                    return "[Circular]"
                seen.add(key)
                return self._resolve(self._records.get(key), seen)

            if value.startswith("$@"):
                return {
                    "__promise__": self._resolve(value[2:], seen)
                }

            return self._normalize(value)

        if isinstance(value, list):
            return [self._resolve(v, seen.copy()) for v in value]

        if isinstance(value, dict):
            return {k: self._resolve(v, seen.copy()) for k, v in value.items()}

        return value


class NextJsParser:
    def __init__(self, key: str = "", value: str = "", return_parent: bool = False, skip: int = 0) -> None:
        self._key = key
        self._value = value
        self._skip = skip
        self._return_parent = return_parent

    def __call__(self, data: str) -> PreProcessorResult:
        helper = RSCHelper(data)
        result_data = helper.convert_to_json()
        if result_data:
            Logger.debug("Found NextJs data: %s", JsonHelper.dump(result_data, pretty_print=False))

        if self._key and self._value:
            result_data = JsonHelper.find_dict_by_key_value_from(
                result_data, self._key, self._value, skip=[self._skip])
        elif self._key:
            result_data = JsonHelper.find_dict_by_key_from(
                result_data, self._key, self._return_parent, skip=[self._skip])

        if result_data and isinstance(result_data, str):
            return result_data, []
        elif result_data:
            return JsonHelper(result_data), []

        Logger.warning("Could not find NextJs data for key: %s, value: %s", self._key, self._value)
        return "", []

    def __str__(self):
        return f"NextJsParser(key={self._key}, value={self._value})"
