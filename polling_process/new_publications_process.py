from aminolib import ApiClient
from model import Community
from .polling_process import PollingProcess
import log


class NewPublicationsProcess(PollingProcess):
    def __init__(self, api_client: ApiClient, community: Community, interval: int):
        super().__init__(api_client, community, interval)

    async def request(self):
        response = await self.api_client.get_feed_publications(self.community.ndc_id, 0, 100)
        if not response:
            return log.error(self.full_name, "Не удалось получить список последних постов в сообществе")
        self.broadcast(response.data["blogList"])
