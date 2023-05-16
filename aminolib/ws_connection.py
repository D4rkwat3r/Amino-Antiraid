from typing import Callable
from typing import Optional
from typing import Any
from time import time
from uuid import uuid4
from random import randint
from aiohttp import WSMsgType
from aiohttp import WSMessage
from aiohttp import ClientWebSocketResponse
from json import loads
from json import JSONDecodeError
from asyncio import create_task
from asyncio import sleep
from asyncio import get_running_loop
from inspect import iscoroutinefunction
from util import SubscriptionHandler
from .api_request import ApiRequest
import log


class WSConnection(SubscriptionHandler):
    def __init__(self, sid: str, server: str, ping_interval: int):
        super().__init__()
        self._sid = sid
        self._server = server
        self._ping_interval = ping_interval
        self._loop = get_running_loop()
        self._connection: Optional[ClientWebSocketResponse] = None
        self._on_connect_callbacks = []

    @property
    def active(self) -> bool:
        return self._connection is not None

    async def _create_connection(self) -> ClientWebSocketResponse:
        device = ApiRequest.generate_device_id()
        sign_body = f"{device}|{int(time() * 1000)}"
        connection = await ApiRequest.client_session.ws_connect(
            f"wss://ws{randint(1, 4)}.{self._server}/?signbody={sign_body}",
            headers={
                "NDCDEVICEID": device,
                "NDCAUTH": f"sid={self._sid}",
                "NDC-MSG-SIG": ApiRequest.generate_message_signature(sign_body.encode("utf-8"))
            }
        )
        log.debug("WebSocket", "Соединение установлено")
        return connection

    async def _ping_loop(self):
        # Амино требует регулярную отправку каких-то сообщений и это не обычные пинги,
        # Поэтому приходится отправлять то, что, по крайней мере, ни на что не влияет
        while True:
            await sleep(self._ping_interval)
            await self.send_action(116, {"threadChannelUserInfoList": []})

    async def start(self):
        self._connection = await self._create_connection()
        create_task(self._ping_loop())
        for callback in self._on_connect_callbacks:
            if iscoroutinefunction(callback): await callback()
            else: callback()
        async for raw_message in self._connection:
            raw_message: WSMessage
            if raw_message.type == WSMsgType.ping:
                await self._connection.pong()
                continue
            if raw_message.type != WSMsgType.text:
                log.error("WebSocket", f"Получено сообщение необрабатываемого типа ({raw_message.type})")
                continue
            try:
                message = loads(raw_message.data)
            except JSONDecodeError:
                log.error("WebSocket", "Получено нечитаемое сообщение")
                continue
            log.debug("WebSocket", f"Получено сообщение типа {message['t']}")
            self.broadcast(message)
        log.error("WebSocket", "Соединение разорвано")

    def start_in_background(self) -> "WSConnection":
        create_task(self.start())
        return self

    async def send_action(self, message_type: int, message_body: dict):
        log.debug("WebSocket", f"Отправка сообщения типа {message_type}")
        message_body["id"] = str(randint(1, 1000000))
        await self._connection.send_json(
            {
                "t": message_type,
                "o": message_body,
            }
        )

    def on_connect(self, callback: Callable[[], Any]):
        self._on_connect_callbacks.append(callback)
