from .event_module import EventModule
from aminolib import ApiClient
from aminolib import WSConnection
from model import Community
from asyncio import sleep
from asyncio import create_task


class ChatJoinLeaveHandler(EventModule):
    def __init__(
            self,
            api_client: ApiClient,
            community: Community,
            cfg: dict,
            ws_connection: WSConnection
    ):
        super().__init__(
            api_client,
            community,
            cfg,
            ws_connection,
            [1000]
        )
        self.on_join_message = cfg["onJoinMessage"]
        self.on_leave_message = cfg["onLeaveMessage"]
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
        profile = (await self.api_client.get_user_profile(self.community.ndc_id, event["chatMessage"]["uid"])).data
        if event["chatMessage"]["type"] == 101:
            await self.api_client.send_message(
                self.community.ndc_id,
                event["chatMessage"]["threadId"],
                self.on_join_message.replace("%nickname%", profile["userProfile"]["nickname"])
            )
        else:
            await self.api_client.send_message(
                self.community.ndc_id,
                event["chatMessage"]["threadId"],
                self.on_leave_message.replace("%nickname%", profile["userProfile"]["nickname"])
            )
        self.cooldown_list.append(event["chatMessage"]["uid"])
