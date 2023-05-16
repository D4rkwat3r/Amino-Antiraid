from .polling_module import PollingModule
from aminolib import ApiClient
from ciso8601 import parse_datetime
from asyncio import create_task
from asyncio import gather
from model.community import Community
from polling_process import NewMembersProcess
import log


class AntiBotnet(PollingModule):
    def __init__(self,
                 api_client: ApiClient,
                 community: Community,
                 source: NewMembersProcess,
                 cfg: dict):
        super().__init__(api_client, community, source, cfg)
        self.count = 0
        self.community_closed = False
        self.count_difference = cfg["maxAllowedCountDifference"]
        self.join_time_difference = cfg["minAllowedJoinTimeDifference"]

    async def check(self, data: tuple[int, list[dict]]) -> bool:
        new_count, profiles = data
        if self.count == 0:
            self.count = new_count
            return False
        old_count = self.count
        self.count = new_count
        if new_count - old_count > self.count_difference:
            return True

    async def trigger(self, _) -> None:
        log.info(self.full_name, f"Замечена атака ботнетом")
        if not self.community_closed: self.community_closed = await self.api_client.change_community_settings(
            self.community.ndc_id,
            joinType=1
        )
        if self.community_closed: log.info(self.full_name, f"Сообщество закрыто "
                                                           f"в рамках защиты от атаки ботнета")
        await self.clear_community()
        log.info(self.full_name, f"Атака ботнета отбита")
        self.community_closed = not await self.api_client.change_community_settings(
            self.community.ndc_id,
            joinType=0
        )

    def filter_profiles(self, all_profiles: list[dict]) -> list[dict]:
        results = []
        for i in range(1, len(all_profiles)):
            difference = parse_datetime(
                all_profiles[i]["createdTime"]
            ).timestamp() - parse_datetime(
                all_profiles[i - 1]["createdTime"]
            ).timestamp()
            if abs(difference) < self.join_time_difference:
                if all_profiles[i] not in results: results.append(all_profiles[i])
                if all_profiles[i - 1] not in results: results.append(all_profiles[i - 1])
        return results

    async def clear_community(self):
        while True:
            response = await self.api_client.get_recent_users(self.community.ndc_id, 0, 100)
            if not response: return log.fatal(self.full_name, f"Во время атаки ботнета на сообщество "
                                                              f"произошёл сбой при отправке запроса на получение"
                                                              f"списка 100 последних участников")
            bot_profiles = self.filter_profiles(response.data["userProfileList"])
            if len(bot_profiles) == 0: return
            bot_profiles = tuple(map(lambda x: x["uid"], bot_profiles))
            ban_results = await gather(
                *[
                    create_task(self.api_client.ban(self.community.ndc_id, 2, "Один из аккаунтов ботнета", uid))
                    for uid in bot_profiles
                ]
            )
            log.info(self.full_name, f"Забанено {ban_results.count(True)} аккаунтов ботнета из {len(ban_results)}")
