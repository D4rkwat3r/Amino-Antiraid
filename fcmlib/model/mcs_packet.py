from dataclasses import dataclass
from typing import Any


@dataclass
class MCSPacket:
    protocol_version: int
    payload_tag: int
    payload_size: int
    payload: Any
