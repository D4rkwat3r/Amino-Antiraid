from .formatter import Formatter
from .community_formatter import CommunityFormatter
from .user_profile_formatter import UserProfileFormatter


class ChatFormatter(Formatter):
    """
    Available variables: %community.[community variables], %host.[user-profile variables]%, %title%, %id%,
    %members_count%, %members_quota%
    """
    def format(self, chat_info: dict, parent_object_name: str = "", **kwargs) -> str:
        parent_object = Formatter.parent_object(parent_object_name)
        result = CommunityFormatter(self.string_format).format(
            kwargs["community"],
            f"{parent_object}community"
        )
        result = UserProfileFormatter(result).format(
            chat_info["author"],
            f"{parent_object}host",
            community=kwargs["community"]
        )
        return result.replace(f"%{parent_object}title%", chat_info.get("title") or "-")\
                     .replace(f"%{parent_object}id%", chat_info["threadId"])\
                     .replace(f"%{parent_object}members_count", str(chat_info.get("membersCount")) or "-")\
                     .replace(f"%{parent_object}members_quota%", str(chat_info.get("membersQuota") or "-"))

    async def complete_object_info(self, chat: dict, ndc_id: int, api_client) -> None:
        response = await api_client.get_chat_thread(ndc_id, chat["threadId"])
        chat.update(response.data["thread"])
