from .module import Module
from aminolib import ApiClient
from fcmlib import FcmListener
from model import Community
from asyncio import create_task
from re import compile
from typing import Optional
from re import Pattern


class PushModule(Module):

    MATCHER_FORMAT = r"ndc://x(\d+)/({}).+".format
    MATCHER_NDC_BLOG = compile(MATCHER_FORMAT("blog"))
    MATCHER_NDC_ITEM = compile(MATCHER_FORMAT("item"))
    MATCHER_NDC_CHAT = compile(MATCHER_FORMAT("chat"))
    MATCHER_NDC_USER = compile(MATCHER_FORMAT("user-profile"))
    MATCHER_NDC_COMMENT = compile(MATCHER_FORMAT("comment"))
    MATCHER_NDC_SHARED_FOLDER = compile(MATCHER_FORMAT("shared-folder"))

    def __init__(
        self,
        api_client: ApiClient,
        community: Community,
        source: FcmListener,
        cfg: dict,
        matchers: Optional[list[Pattern]] = None,
        *args
    ):
        super().__init__(api_client, community, source, cfg, *args)
        self.matchers = matchers or []
        self.subscription_id = None

    def __del__(self):
        self.source.unsubscribe(self.subscription_id)

    async def receive(self, push: dict) -> None:
        if await self.check(push): create_task(self.trigger(push))

    async def check(self, push: dict) -> bool: ...

    async def trigger(self, push: dict) -> None: ...

    async def run(self) -> None:
        self.subscription_id = self.source.subscribe(
            self.receive,
            lambda x: x["ndcId"] == self.community.ndc_id and all(
                [matcher.match(x["link"]) for matcher in self.matchers]
            ),
            lambda x: {
                "ndcId": x["ndcId"],
                "link": x.get("u") or "",
                "text": x["aps"]["alert"]["body"],
                "type": x["notifType"]
            }
        )
