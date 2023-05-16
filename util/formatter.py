from abc import ABC
from typing import Any


class Formatter(ABC):
    def __init__(self, string_format: str):
        self.string_format = string_format

    def format(self, obj: Any, parent_object_name: str = "", **kwargs) -> str: ...

    @staticmethod
    def parent_object(name: str) -> str: return f"{name}." if name else ""

    async def complete_object_info(self, obj: Any, ndc_id: int, api_client) -> None:
        ...
