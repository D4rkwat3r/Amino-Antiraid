from model.community import Community
from aminolib import ApiClient
from polling_process import PollingProcess
from typing import Union
from .module import Module


class PollingModule(Module):
    def __init__(
        self,
        api_client: ApiClient,
        community: Community,
        source: PollingProcess,
        cfg: dict,
        *args
    ):
        super().__init__(api_client, community, source, cfg)
        self.subscription_id = None

    def __del__(self):
        self.source.unsubscribe(self.subscription_id)

    async def receive(self, data: Union[dict, list]):
        if await self.check(data): await self.trigger(data)

    async def check(self, data: Union[dict, list]) -> bool: ...

    async def trigger(self, data: Union[dict, list]) -> None: ...

    async def run(self) -> None:
        self.subscription_id = self.source.subscribe(self.receive)
