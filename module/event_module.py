from model import Community
from aminolib import WSConnection
from aminolib import ApiClient
from asyncio import create_task
from typing import Optional
from typing import Callable
from typing import Any
from .module import Module


class EventModule(Module):
    def __init__(
        self,
        api_client: ApiClient,
        community: Community,
        source: WSConnection,
        cfg: dict,
        supported_event_types: list[int],
        on_connect_callbacks: Optional[list[Callable[[], Any]]] = None,
        *args
    ):
        super().__init__(api_client, community, source, cfg)
        self.supported_event_types = supported_event_types
        self.subscription_id = None
        if on_connect_callbacks is not None:
            for callback in on_connect_callbacks: self.source.on_connect(callback)

    def __del__(self):
        self.source.unsubscribe(self.subscription_id)

    async def receive(self, event: dict) -> None:
        if await self.check(event["t"], event["o"]): create_task(self.trigger(event["t"], event["o"]))

    async def check(self, event_type: int, event: dict) -> bool: ...

    async def trigger(self, event_type: int, event: dict) -> None: ...

    async def run(self) -> None:
        self.subscription_id = self.source.subscribe(
            self.receive,
            lambda x: x["t"] in self.supported_event_types and x["o"]["ndcId"] == self.community.ndc_id
        )
