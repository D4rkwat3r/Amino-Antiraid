from .formatter import Formatter
from .community_formatter import CommunityFormatter
from .user_profile_formatter import UserProfileFormatter
from .chat_formatter import ChatFormatter
from asyncio import create_task
from asyncio import gather


class ChatMessageFormatter(Formatter):
    """
    Available variables: %community.[community variables]%, %author.[user-profile variables]%, %chat.[chat variables]%,
    %content%, %id%, %type%
    """
    def format(self, message_info: dict, parent_object_name: str = "", **kwargs) -> str:
        parent_object = Formatter.parent_object(parent_object_name)
        result = CommunityFormatter(self.string_format).format(
            kwargs["community"],
            f"{parent_object}community"
        )
        if "author" in message_info:
            result = UserProfileFormatter(result).format(
                message_info["author"],
                f"{parent_object}author",
                community=kwargs["community"]
            )
        if "thread" in message_info:
            result = ChatFormatter(result).format(
                message_info["thread"],
                f"{parent_object}chat",
                community=kwargs["community"]
            )
        return result.replace(f"%{parent_object}content%", message_info.get("content") or "-")\
                     .replace(f"%{parent_object}id%", message_info["messageId"])\
                     .replace(f"%{parent_object}type%", str(message_info["type"]))

    async def complete_object_info(self, message: dict, ndc_id: int, api_client) -> None:
        responses = await gather(
            create_task(api_client.get_chat_thread(ndc_id, message["threadId"])),
            create_task(api_client.get_user_profile(ndc_id, message["uid"]))
        )
        message["thread"] = responses[0].data["thread"]
        message["author"] = responses[1].data["userProfile"]
