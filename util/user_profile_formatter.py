from .formatter import Formatter
from .community_formatter import CommunityFormatter


class UserProfileFormatter(Formatter):
    """
    Available variables: %community.[community variables]%, %nickname%, %id%, %level_name%, %level%, %avatar%
    """

    def format(self, user_info: dict, parent_object_name: str = "", **kwargs) -> str:
        parent_object = Formatter.parent_object(parent_object_name)
        result = CommunityFormatter(self.string_format).format(
            kwargs["community"],
            f"{parent_object}community"
        )
        return result.replace(f"%{parent_object}nickname%", user_info["nickname"])\
                     .replace(f"%{parent_object}id%", user_info["uid"])\
                     .replace(f"%{parent_object}level_name%", user_info.get("rankingTitle") or "-")\
                     .replace(f"%{parent_object}level%", str(user_info.get("level") or "-"))\
                     .replace(f"%{parent_object}avatar%", user_info.get("icon") or "-")

    async def complete_object_info(self, user: dict, ndc_id: int, api_client) -> None:
        response = await api_client.get_user_profile(ndc_id, user["uid"])
        user.update(response.data["userProfile"])
