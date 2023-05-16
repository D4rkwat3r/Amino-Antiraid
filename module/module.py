from abc import ABC
from asyncio import create_task
from aminolib import ApiClient
from model.community import Community
from util import SubscriptionHandler
import log


class Module(ABC):
    def __init__(
        self,
        api_client: ApiClient,
        community: Community,
        source: SubscriptionHandler,
        cfg: dict,
        *args
    ):
        self.name = self.__class__.__name__
        self.full_name = f"{self.name}, {community.name}"
        self.api_client = api_client
        self.community = community
        self.source = source
        self.executing = False

    async def trigger(self, *args) -> None: ...

    async def run(self) -> None: ...

    def run_in_background(self) -> None:
        log.info(self.full_name, "Запуск модуля")
        create_task(self.run())
