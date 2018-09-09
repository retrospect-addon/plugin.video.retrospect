from typing import Any, Optional, Union, Dict, List
from logger import Logger

# make_stub_files: Sun 09 Sep 2018 at 13:18:57
class JsonHelper:
    logger = ...  # type: Logger
    data = ...  # type: str
    json = ...  # type: Union[Dict, List]

    def __init__(self, data: str, logger: Logger=None) -> None: ...

    @staticmethod
    def convert_special_chars(text: str, do_quotes: bool=True) -> str: ...

    @staticmethod
    def __convert_quotes(text: str) -> str: ...

    @staticmethod
    def __special_chars_handler(match: Any) -> str: ...

    def get_value(self, *args, **kwargs) -> Optional[Any]: ...

    @staticmethod
    def dump(dictionary: Union[Dict, List], pretty_print: bool=True) -> str: ...

    @staticmethod
    def loads(json_data: str) -> Union[Dict, List]: ...

    def __str__(self) -> str: ...
