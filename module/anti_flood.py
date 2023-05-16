from model import Community
from aminolib import WSConnection
from aminolib import ApiClient
from asyncio import sleep
from asyncio import create_task
import log
from .event_module import EventModule


class AntiFlood(EventModule):
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
        self.interval = cfg["interval"]
        self.allowed_message_count = cfg["maxAllowedMessageCount"]
        self.delete_when = cfg["deleteWhen"]
        self.kick_when = cfg["kickWhen"]
        self.ban_when = cfg["banWhen"]
        self.allow_rejoin = cfg["kickAllowRejoin"]
        self.received_messages = []
        # предотвращение отправки кучи запросов на бан одного и того же участника
        self.banning = []
        create_task(self.clear_message_list())
        create_task(self.clear_banning_list())

    async def clear_message_list(self):
        while True:
            await sleep(self.interval)
            self.received_messages.clear()

    async def clear_banning_list(self):
        while True:
            await sleep(10)
            self.banning.clear()

    async def check(self, event_type: int, event: dict) -> bool:
        if event["chatMessage"]["uid"] == self.api_client.uid: return False
        if event["chatMessage"]["uid"] in self.banning: return False
        if event["chatMessage"]["type"] == 119: return False
        self.received_messages.append(event["chatMessage"])
        messages_from_user_count = len(tuple(
            filter(
                lambda x: False if "author" not in x or "author" not in event["chatMessage"]
                else x["author"]["uid"] == event["chatMessage"]["author"]["uid"],
                self.received_messages
            )
        ))
        if messages_from_user_count <= self.allowed_message_count:
            return False
        elif self.delete_when <= messages_from_user_count < self.kick_when:
            event["action"] = "delete"
            return True
        elif self.kick_when <= messages_from_user_count < self.ban_when:
            event["action"] = "kick"
            return True
        elif self.ban_when <= messages_from_user_count:
            event["action"] = "ban"
            return True
        else:
            return bool(log.warn(self.full_name, "Пользователь превысил максимально допустимое значение "
                                                 "отправленных сообщений, но из-за неправильно "
                                                 "установленных настроек модуля к нему "
                                                 "нельзя применить никакие действия"))

    async def trigger(self, event_type: int, event: dict) -> None:
        if event["action"] == "delete":
            await self.delete_action(
                event["chatMessage"]["threadId"],
                event["chatMessage"]["messageId"],
                event["chatMessage"]["author"]["nickname"]
            )
        elif event["action"] == "kick":
            await self.kick_action(
                event["chatMessage"]["threadId"],
                event["chatMessage"]["author"]["uid"],
                event["chatMessage"]["author"]["nickname"]
            )
        else:
            await self.ban_action(event["chatMessage"]["author"]["uid"], event["chatMessage"]["author"]["nickname"])

    async def delete_action(self, thread_id: str, message_id: str, author_nickname: str) -> None:
        deleted = await self.api_client.delete_message(self.community.ndc_id, thread_id, message_id, "Флуд сообщениями")
        if deleted: log.info(self.full_name, f"Сообщение от пользователя {author_nickname} удалено из-за флуда")
        else: log.error(self.full_name, f"Сообщение от пользователя {author_nickname} не удалено из-за ошибки (был флуд)")
        try: self.received_messages.remove(next(message for message in self.received_messages if message["messageId"] == message_id))
        except (StopIteration, ValueError): pass

    async def kick_action(self, thread_id: str, author_id: str, author_nickname: str) -> None:
        kicked = await self.api_client.kick(self.community.ndc_id, thread_id, author_id, self.allow_rejoin)
        if kicked: log.info(self.full_name, f"Пользователь {author_nickname} удален из чата за флуд")
        else: log.error(self.full_name, f"Пользователь {author_nickname} не удален из чата за флуд из-за ошибки")

    async def ban_action(self, author_id: str, author_nickname: str) -> None:
        self.banning.append(author_id)
        banned = await self.api_client.ban(self.community.ndc_id, 2, "Флуд сообщениями", author_id)
        if banned: log.info(self.full_name, f"Пользователь {author_nickname} забанен за флуд")
        else: log.error(self.full_name, f"Пользователь {author_nickname} не забанен за флуд из-за ошибки")

