from aminolib import ApiClient
from aminolib import WSConnection
from model import Community
from util import ChatMessageFormatter
from .event_module import EventModule
import log


class ChatLoggerModule(EventModule):
    def __init__(self, api_client: ApiClient, community: Community, source: WSConnection, cfg: dict):
        super().__init__(api_client, community, source, cfg, [1000])
        self.formatter = ChatMessageFormatter(cfg["format"])
        self.use_api_request = cfg["useApiRequestToGetChatInfo"]

    async def check(self, event_type: int, event: dict) -> bool:
        return True

    async def trigger(self, event_type: int, event: dict) -> None:
        if self.use_api_request or "author" not in event["chatMessage"]:
            await self.formatter.complete_object_info(event["chatMessage"], self.community.ndc_id, self.api_client)
        log.info(self.full_name, self.formatter.format(event["chatMessage"], community=self.community))
