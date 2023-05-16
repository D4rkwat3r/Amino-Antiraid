from .formatter import Formatter
from model import Community


class CommunityFormatter(Formatter):
    """
    Available variables: %name%, %id%
    """
    def format(self, obj: Community, parent_object_name: str = "", **kwargs) -> str:
        parent_object = Formatter.parent_object(parent_object_name)
        return self.string_format.replace(f"%{parent_object}name%", str(obj.name))\
                                 .replace(f"%{parent_object}id%", str(obj.ndc_id))

    async def complete_object_info(self, community: Community, ndc_id: int, api_client) -> None:
        raise NotImplementedError
