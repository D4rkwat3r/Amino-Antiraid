from .polling_module import PollingModule
from aminolib import ApiClient
from model import Community
from collections import Counter
from datetime import datetime
from ciso8601 import parse_datetime
from typing import Any
from polling_process import NewPublicationsProcess
from typing import Optional
import log


class FeedAntiFlood(PollingModule):
    def __init__(self,
                 api_client: ApiClient,
                 community: Community,
                 source: NewPublicationsProcess,
                 cfg: dict):
        super().__init__(api_client, community, source, cfg)
        self.allowed_publication_count = cfg["maxAllowedPublicationCount"]
        self.hide_when = cfg["hideWhen"]
        self.ban_when = cfg["banWhen"]
        self.hide_published_by_banned_users = cfg["hidePublishedByBannedUsers"]
        self.last_check_time = datetime.now().timestamp()

    def update_last_check_time(self):
        self.last_check_time = datetime.now().timestamp()

    async def delete_published_before_last_check(self, blogs: list[dict]) -> Optional[tuple[Any, ...]]:
        blogs = tuple(filter(lambda x: x["status"] == 0, blogs))
        recent = tuple(
            filter(
                lambda x: parse_datetime(x["createdTime"]).timestamp() > self.last_check_time,
                blogs
            )
        )
        return recent

    async def hide_publication(self, publication: dict, note: str) -> str:
        publication_id = publication["refObjectId"] if publication["type"] == 1 else publication["blogId"]
        succeed = await self.api_client.hide_publication(
            self.community.ndc_id,
            publication["type"],
            publication_id,
            note
        )
        return publication_id if succeed else ""

    async def check(self, data: list[dict]) -> bool:
        publications = await self.delete_published_before_last_check(data)
        if len(publications) == 0: return False
        author_ids = tuple(map(lambda x: x["author"]["uid"], publications))
        must_trigger = not (Counter(author_ids).most_common()[0][1] <= self.allowed_publication_count)
        if not must_trigger: self.update_last_check_time()
        return must_trigger

    async def trigger(self, data: list[dict]) -> None:
        publications = await self.delete_published_before_last_check(data)
        author_ids = tuple(map(lambda x: x["author"]["uid"], publications))
        for user, publication_count in Counter(author_ids).most_common():
            if publication_count <= self.allowed_publication_count:
                break
            elif self.hide_when <= publication_count < self.ban_when:
                await self.hide_action(user, publications)
            elif self.ban_when <= publication_count:
                await self.ban_action(user)
            else:
                log.warn(self.full_name, "Пользователь превысил максимально допустимое значение "
                                         "созданных постов, но из-за неправильно "
                                         "установленных настроек модуля к нему "
                                         "нельзя применить никакие действия")
        self.update_last_check_time()

    async def hide_action(self, user_id: str, blog_list: tuple[Any]):
        last_publication = next(publication for publication in blog_list if publication["author"]["uid"] == user_id)
        if pid := await self.hide_publication(last_publication, "Флуд постами"):
            await self.api_client.comment(
                self.community.ndc_id,
                "item" if last_publication["type"] == 1 else "blog",
                pid,
                f"Пост отключён за флуд. В этом сообществе нельзя создавать более "
                f"{self.allowed_publication_count} постов за {self.source.interval} секунд"
            )
            log.info(self.full_name, "Пост отлючён за флуд")
        else:
            log.error(self.full_name, "Не удалось отключить пост из-за ошибки (был флуд)")

    async def ban_action(self, user_id: str):
        if await self.api_client.ban(self.community.ndc_id, 2, "Флуд постами", user_id):
            log.info(self.full_name, "Пользователь забанен за флуд")
        else:
            log.fatal(self.full_name, "Пользователь не забанен из-за ошибки (был флуд)")
