from .api_request import ApiRequest
from .response_wrapper import ResponseWrapper
from time import time
from time import timezone
from typing import Optional


class ApiClient:
    def __init__(self, sid: str, uid: str):
        self.sid = sid
        self.uid = uid

    async def authenticate_and_get_result(self, request: ApiRequest) -> ResponseWrapper:
        return await request.auth(self.sid).send()

    async def authenticate_and_send(self, request: ApiRequest) -> bool:
        return bool(await self.authenticate_and_get_result(request))

    async def get_affiliations(self) -> ResponseWrapper:
        return await self.authenticate_and_get_result(
            ApiRequest.get("account/affiliations")
            .global_scope()
            .param("type", "active")
        )

    async def get_recent_users(self, ndc_id: int, start: int, size: int) -> ResponseWrapper:
        return await self.authenticate_and_get_result(
            ApiRequest.get("user-profile")
            .community_scope(ndc_id)
            .param("type", "recent")
            .param("start", start)
            .param("size", size)
        )

    async def delete_message(self, ndc_id: int, thread_id: str, message_id: str, note: str) -> bool:
        return await self.authenticate_and_send(
            ApiRequest.post(f"chat/thread/{thread_id}/message/{message_id}/admin")
            .community_scope(ndc_id)
            .param("adminOpName", 102)
            .param("adminOpNote", {"content": note})
        )

    async def kick(self, ndc_id: int, thread_id: str, user_id: str, allow_rejoin: bool) -> bool:
        return await self.authenticate_and_send(
            ApiRequest.delete(f"chat/thread/{thread_id}/member/{user_id}")
            .community_scope(ndc_id)
            .param("allowRejoin", int(allow_rejoin))
        )

    async def invite(self, ndc_id: int, thread_id: str, user_id_list: tuple[str]) -> bool:
        return await self.authenticate_and_send(
            ApiRequest.post(f"chat/thread/{thread_id}/member/invite")
            .community_scope(ndc_id)
            .param("uids", user_id_list)
        )

    async def ban(self, ndc_id: int, reason_type: int, note: str, user_id: str) -> bool:
        return await self.authenticate_and_send(
            ApiRequest.post(f"user-profile/{user_id}/ban")
            .community_scope(ndc_id)
            .param("reasonType", reason_type)
            .param("note", {"content": note})
        )

    async def unban(self, ndc_id: int, user_id: str) -> bool:
        return await self.authenticate_and_send(
            ApiRequest.post(f"user-profile/{user_id}/unban").community_scope(ndc_id)
        )

    async def change_community_settings(self, ndc_id: int, **settings) -> bool:
        return await self.authenticate_and_send(
            ApiRequest.post("community/settings")
            .community_scope(ndc_id)
            .params(settings)
        )

    async def send_message(
            self, ndc_id: int, thread_id: str,
            content: Optional[str] = None, message_type: int = 0,
            reply_to: Optional[str] = None,
            link_snippet: Optional[dict] = None,
            file: Optional[dict] = None) -> bool:
        # -- media types --
        # default 0, -
        # jpeg 100, image/jpeg
        # png 100, image/png
        # audio 110, -
        extra_params = {}
        extensions = {}
        if reply_to is not None: extra_params["replyMessageId"] = reply_to
        if link_snippet is not None: extensions["linkSnippetList"] = [link_snippet]
        if file is not None:
            extra_params["mediaType"] = file["type"]
            extra_params["mediaUploadValue"] = file["content"]
            if (mime := file.get("mimeType")) is not None:
                extra_params["mediaUploadValueContentType"] = mime
            if (uhq := file.get("uhq")) is not None:
                extra_params["mediaUhqEnabled"] = uhq
        return await self.authenticate_and_send(
            ApiRequest.post(f"chat/thread/{thread_id}/message")
            .community_scope(ndc_id)
            .param("type", message_type)
            .param("content", content)
            .param("clientRefId", int(time() / 10 % 1000000000))
            .param("attachedObject", None)
            .param("extensions", extensions)
            .params(extra_params)
        )

    async def join_community(self, ndc_id: int) -> bool:
        return await self.authenticate_and_send(
            ApiRequest.post("community/join")
            .community_scope(ndc_id)
            .force_signature()
        )

    async def join_chat(self, ndc_id: int, thread_id: str) -> bool:
        return await self.authenticate_and_send(
            ApiRequest.post(f"chat/thread/{thread_id}/member/{self.uid}").community_scope(ndc_id)
        )

    async def leave_chat(self, ndc_id: int, thread_id: str) -> bool:
        return await self.authenticate_and_send(
            ApiRequest.delete(f"chat/thread/{thread_id}/member/{self.uid}").community_scope(ndc_id)
        )

    async def get_feed_publications(self, ndc_id: int, start: int, size: int) -> ResponseWrapper:
        return await self.authenticate_and_get_result(
            ApiRequest.get("feed/blog-all")
            .community_scope(ndc_id)
            .param("start", start)
            .param("size", size)
        )

    async def hide_publication(self, ndc_id: int, publication_type: int, publication_id: str, note: str) -> bool:
        return await self.authenticate_and_send(
            ApiRequest.post(f"{'item' if publication_type == 1 else 'blog'}/{publication_id}/admin")
            .community_scope(ndc_id)
            .param("adminOpName", 110)
            .param("adminOpValue", 9)
            .param("adminOpNote", {"content": note})
        )

    async def comment(
        self,
        ndc_id: int,
        object_type: int,
        object_id: str,
        content: str,
        reply_to: Optional[str] = None,
        sticker_id: Optional[str] = None
    ) -> bool:
        extra_params = {}
        if reply_to: extra_params["respondTo"] = reply_to
        if sticker_id: extra_params["stickerId"] = sticker_id
        return await self.authenticate_and_send(
            ApiRequest.post(f"{object_type}/{object_id}/comment")
            .community_scope(ndc_id)
            .param("content", content)
            .param("type", 0)
            .params(extra_params)
        )

    async def get_user_profile(self, ndc_id: int, user_id: str) -> ResponseWrapper:
        return await self.authenticate_and_get_result(
            ApiRequest.get(f"user-profile/{user_id}").community_scope(ndc_id)
        )

    async def get_chat_thread(self, ndc_id: int, thread_id: str) -> ResponseWrapper:
        return await self.authenticate_and_get_result(
            ApiRequest.get(f"chat/thread/{thread_id}").community_scope(ndc_id)
        )

    async def start_chat(self, ndc_id: int, users: list[str], content: Optional[str] = None) -> bool:
        return await self.authenticate_and_send(
            ApiRequest.post("chat/thread")
            .community_scope(ndc_id)
            .param("type", 0)
            .param("inviteeUids", users)
            .param("initialMessageContent", content)
        )

    async def get_chat_messages(self, ndc_id: int, thread_id: str, start: int, size: int) -> ResponseWrapper:
        return await self.authenticate_and_get_result(
            ApiRequest.get(f"chat/thread/{thread_id}/message")
            .community_scope(ndc_id)
            .param("start", start)
            .param("size", size)
        )

    async def configure_device(
        self,
        token: str,
        token_type: int,
        device_id: str = ApiRequest.generate_device_id(),
        client_type: int = 100,
        tz: int = -timezone // 1000,
        push_enabled: bool = True
    ) -> bool:
        return await self.authenticate_and_send(
            ApiRequest.post("device")
            .global_scope()
            .param("deviceID", device_id)
            .param("deviceToken", token)
            .param("deviceTokenType", token_type)
            .param("clientType", client_type)
            .param("timezone", tz)
            .param("systemPushEnabled", push_enabled)
        )

    async def get_publication_tipped_users(
        self,
        ndc_id: int,
        publication_id: str,
        start: int,
        size: int,
        publication_type: str = "blog"
    ) -> ResponseWrapper:
        return await self.authenticate_and_get_result(
            ApiRequest.get(f"{publication_type}/{publication_id}/tipping/tipped-users")
            .community_scope(ndc_id)
            .param("start", start)
            .param("size", size)
        )

    async def get_publication_comment(
        self,
        ndc_id: int,
        publication_id: str,
        comment_id: str,
        publication_type: str = "blog"
    ) -> ResponseWrapper:
        return await self.authenticate_and_get_result(
            ApiRequest.get(f"{publication_type}/{publication_id}/comment/{comment_id}")
            .community_scope(ndc_id)
        )

    async def create_custom_title(self, ndc_id: int, user_id: str, title_text: str, color: str) -> bool:
        return await self.authenticate_and_send(
            ApiRequest.post(f"user-profile/{user_id}/admin")
            .community_scope(ndc_id)
            .param("adminOpName", 207)
            .param("adminOpValue", {"titles": [{"title": title_text, "color": color}]})
        )
