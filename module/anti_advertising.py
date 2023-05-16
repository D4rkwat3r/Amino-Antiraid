import log
from aminolib import ApiClient
from aminolib import WSConnection
from model import Community
from asyncio import sleep
from asyncio import create_task
from re import compile
from .event_module import EventModule


class AntiAdvertising(EventModule):
    def __init__(
            self,
            api_client: ApiClient,
            community: Community,
            source: WSConnection,
            cfg: dict,
    ):
        super().__init__(
            api_client,
            community,
            source,
            cfg,
            [1000],
            [lambda: create_task(self.update_online_status_loop())]
        )
        self.domain_pattern = compile(r"(?:https?://)?([A-zА-я0-9]+\.[A-zА-я0-9]{2,10})/.+")
        self.disallowed_domains = cfg["disallowedDomains"]
        self.reaction = cfg["reaction"]
        self.ignore_staff = cfg["ignoreStaff"]
        self.interval = cfg["updateOnlineStatusInterval"]

    async def check(self, event_type: int, event: dict) -> bool:
        if event["chatMessage"].get("content") is None: return False
        if event["chatMessage"]["author"]["role"] != 0 and self.ignore_staff: return False
        search_result = self.domain_pattern.search(event["chatMessage"]["content"])
        if search_result is None: return False
        matches = tuple(map(lambda x: x.replace(" ", ""), search_result.groups()))
        for match in matches:
            if match in self.disallowed_domains:
                event["domain"] = match
                return True
        return False

    async def trigger(self, event_type: int, event: dict) -> None:
        if self.reaction == "delete":
            await self.delete_reaction(
                event["chatMessage"]["threadId"],
                event["chatMessage"]["messageId"],
                event["chatMessage"]["author"]["nickname"],
                event["domain"]
            )
        elif self.reaction == "ban":
            await self.ban_reaction(
                event["chatMessage"]["author"]["uid"],
                event["chatMessage"]["author"]["nickname"],
                event["domain"]
            )
        else:
            log.warn(
                self.full_name,
                f"{self.reaction} не является допустимым типом реакции. Допустимые типы: delete, ban"
            )

    async def delete_reaction(self, thread_id: str, message_id: str, author_nickname: str, domain: str):
        deleted = await self.api_client.delete_message(
            self.community.ndc_id, thread_id,
            message_id, f"В этом сообществе запрещено отправлять ссылки с доменом {domain}"
        )
        if deleted: log.info(
            self.full_name,
            f"Сообщение от пользователя {author_nickname} удалено из-за присутствия в нём ссылки с доменом {domain}"
        )
        else: log.error(
            self.full_name,
            f"Сообщение от пользователя {author_nickname} не удалено из-за ошибки (домен: {domain})"
        )

    async def ban_reaction(self, author_id: str, author_nickname: str, domain: str):
        banned = await self.api_client.ban(
            self.community.ndc_id,
            200,
            f"В этом сообществе запрещено отправлять ссылки с доменом {domain}",
            author_id
        )
        if banned: log.info(
            self.full_name,
            f"Пользователь {author_nickname} забанен из-за присутствия в его сообщении ссылки с доменом {domain}"
        )
        else: log.error(
            self.full_name,
            f"Пользователь не забанен из-за ошибки (домен: {domain})"
        )

    async def update_online_status_loop(self):
        while True:
            await self.source.send_action(
                304,
                {
                    "actions": ["Browsing"],
                    "target": f"ndc://x{self.community.ndc_id}/",
                    "ndcId": self.community.ndc_id
                }
            )
            await sleep(self.interval)
