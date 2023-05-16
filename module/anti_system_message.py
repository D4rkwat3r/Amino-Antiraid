from .event_module import EventModule
from aminolib import ApiClient
from aminolib import WSConnection
from model import Community


class AntiSystemMessage(EventModule):
    def __init__(
            self,
            api_client: ApiClient,
            community: Community,
            source: WSConnection,
            cfg: dict
    ):
        super().__init__(api_client, community, source, cfg, [1000])

    async def check(self, event_type: int, event: dict) -> bool:
        return event["chatMessage"]["type"] not in [0, 103] \
               and event["chatMessage"].get("content") is not None

    async def trigger(self, event_type: int, event: dict) -> None:
        await self.api_client.delete_message(
            self.community.ndc_id,
            event["chatMessage"]["threadId"],
            event["chatMessage"]["messageId"],
            "Сообщение нестандартного типа"
        )
