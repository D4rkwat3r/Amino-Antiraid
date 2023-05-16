from ssl import create_default_context
from asyncio import open_connection
from struct import unpack
from typing import Optional
from ..model.mcs_packet import MCSPacket


def varint32(number: int) -> bytes:
    res = bytearray()
    while number != 0:
        b = (number & 0x7F)
        number >>= 7
        if number != 0:
            b |= 0x80
        res.append(b)
    return bytes(res)


class MCSProtocol:
    def __init__(self, version: int):
        self.version = version
        self.server_protocol_version = 0
        self.reader = None
        self.writer = None

    async def connect(self):
        self.reader, self.writer = await open_connection(
            host="mtalk.google.com",
            port=5228,
            ssl=create_default_context()
        )

    async def receive_one_byte(self) -> int:
        return unpack("B", await self.reader.read(1))[0]

    async def receive_payload_size(self) -> int:
        result = 0
        shift = 0
        while True:
            b, = unpack("B", await self.reader.read(1))
            result |= (b & 0x7F) << shift
            if (b & 0x80) == 0:
                break
            shift += 7
        return result

    async def receive_packet(self, expected_tag: int, payload_proto) -> Optional[MCSPacket]:
        if self.server_protocol_version == 0:
            self.server_protocol_version = await self.receive_one_byte()
        tag = await self.receive_one_byte()
        size = await self.receive_payload_size()
        if tag != expected_tag:
            return None
        payload_data = payload_proto()
        payload_data.ParseFromString(await self.reader.read(size))
        return MCSPacket(self.server_protocol_version, tag, size, payload_data)

    async def send(self, proto, tag: int):
        packet_payload = proto.SerializeToString()
        self.writer.write(bytes([self.version, tag]) + varint32(len(packet_payload)) + packet_payload)
        await self.writer.drain()
