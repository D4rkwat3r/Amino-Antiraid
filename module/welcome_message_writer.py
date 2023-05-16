import log
from .polling_module import PollingModule
from polling_process import NewMembersProcess
from aminolib import ApiClient
from model import Community
from util import UserProfileFormatter


class WelcomeMessageWriter(PollingModule):
    def __init__(self,
                 api_client: ApiClient,
                 community: Community,
                 source: NewMembersProcess,
                 cfg: dict):
        super().__init__(api_client, community, source, cfg)
        self.send_method = cfg["sendMethod"]
        self.formatter = UserProfileFormatter(cfg["text"])
        self.members = []

    async def extract_new_members(self, members_list: list[dict]) -> tuple[list[str], list[str]]:
        members = [user["uid"] for user in members_list]
        return members, list(filter(lambda x: x not in self.members, members))

    async def check(self, data: tuple[int, list[dict]]) -> bool:
        if not self.members:
            self.members = [user["uid"] for user in data[1]]
            return False
        members, new_members = await self.extract_new_members(data[1])
        if not new_members:
            self.members = members
            return False
        return True

    async def trigger(self, data: list[dict]) -> None:
        members, new_members = await self.extract_new_members(data[1])
        for uid in new_members:
            profile = (await self.api_client.get_user_profile(self.community.ndc_id, uid)).data["userProfile"]
            text = self.formatter.format(profile, community=self.community)
            if self.send_method == "chat":
                sent = await self.api_client.start_chat(self.community.ndc_id, [uid], text)
            elif self.send_method == "comment":
                sent = await self.api_client.comment(self.community.ndc_id, "user-profile", uid, text)
            else:
                sent = log.warn(self.full_name, f"{self.send_method} не является допустимым методом отправки "
                                                f"приветственных сообщений. Допустимые методы: chat, comment")
            if sent:
                log.info(self.full_name, f"Написали приветственное сообщение участнику {profile['nickname']}")
            else:
                log.error(self.full_name, f"Не смогли написать приветственное сообщение "
                                          f"участнику {profile['nickname']} из-за ошибки")
        self.members = members
