from aminolib import ApiClient
from model import Community
from util import SubscriptionHandler
from asyncio import create_task
from asyncio import sleep


class PollingProcess(SubscriptionHandler):
    def __init__(self, api_client: ApiClient, community: Community, interval: int):
        super().__init__()
        self.api_client = api_client
        self.community = community
        self.interval = interval
        self.full_name = f"{self.__class__.__name__}({community.name})"

    async def request(self):
        ...

    async def run(self):
        while True:
            await sleep(self.interval)
            await self.request()

    def run_in_background(self) -> "PollingProcess":
        create_task(self.run())
        return self
