from .event_module import EventModule
from aminolib import ApiClient
from aminolib import WSConnection
from model import Community
from asyncio import sleep
from asyncio import create_task
from util import ChatMessageFormatter


class ChatJoinLeaveHandler(EventModule):
    def __init__(
            self,
            api_client: ApiClient,
            community: Community,
            source: WSConnection,
            cfg: dict
    ):
        super().__init__(
            api_client,
            community,
            source,
            cfg,
            [1000]
        )
        self.on_join_formatter = ChatMessageFormatter(cfg["onJoinMessage"])
        self.on_leave_formatter = ChatMessageFormatter(cfg["onLeaveMessage"])
        self.cooldown_time = cfg["cooldownTime"]
        self.cooldown_list = []
        create_task(self.clear_cooldown_list())

    async def clear_cooldown_list(self):
        while True:
            await sleep(self.cooldown_time)
            self.cooldown_list.clear()

    async def check(self, event_type: int, event: dict) -> bool:
        if event["chatMessage"]["uid"] in self.cooldown_list: return False
        return True if event["chatMessage"]["type"] in [101, 102] else False

    async def trigger(self, event_type: int, event: dict) -> None:
        fmt = self.on_join_formatter if event["chatMessage"]["type"] == 101 else self.on_leave_formatter
        await fmt.complete_object_info(
            event["chatMessage"], self.community.ndc_id, self.api_client
        )
        await self.api_client.send_message(
            self.community.ndc_id,
            event["chatMessage"]["threadId"],
            fmt.format(event["chatMessage"], community=self.community),
            reply_to=event["chatMessage"]["messageId"]
        )
        self.cooldown_list.append(event["chatMessage"]["uid"])
