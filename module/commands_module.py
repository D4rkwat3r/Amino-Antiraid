from model import Community
from aminolib import WSConnection
from aminolib import ApiClient
from typing import Callable
from typing import Optional
from typing import Any
from functools import wraps
from .event_module import EventModule


MessageHandler = Callable[[Any, dict, tuple[str]], Any]
MessageFilter = Callable[[dict, tuple[str]], bool]


def with_filter(message_filter: MessageFilter, on_check_failed: Optional[Callable] = None):
    def decorator(handler: MessageHandler):
        @wraps(handler)
        async def wrapper(self, message: dict, *args: str):
            if message_filter(message, args):
                return await handler(self, message, *args)
            if on_check_failed is not None:
                await on_check_failed(self, message)
        return wrapper
    return decorator


def with_role_filter(roles: list[int]):
    return with_filter(
        lambda x, _: x["author"]["role"] in roles,
        lambda x, y: x.api_client.send_message(
            x.community.ndc_id, y["threadId"], "У вас недостаточно прав для выполнения этой команды"
        )
    )


class CommandsModule(EventModule):
    def __init__(
            self,
            api_client: ApiClient,
            community: Community,
            source: WSConnection,
            cfg: dict):
        super().__init__(
            api_client,
            community,
            source,
            cfg,
            [1000]
        )
        self.prefix = cfg["prefix"]
        self.commands = []

    async def check(self, _, event: dict) -> bool:
        if event["chatMessage"].get("content") is None: return False
        if event["chatMessage"]["author"]["uid"] == self.api_client.uid: return False
        if not event["chatMessage"]["content"].startswith(self.prefix): return False
        command_parts = event["chatMessage"]["content"][1:].split()
        command_body, command_args = command_parts[0], command_parts[1:]
        matching_commands = []
        for cmd in [command for command in self.commands if command["text"] == command_body]:
            if len(command_args) >= cmd["arg_count"]:
                matching_commands.append({"args": command_args, "handler": cmd["handler"]})
        if not matching_commands: return False
        event["commands"] = matching_commands
        return True

    async def trigger(self, _, event: dict) -> None:
        for cmd in event["commands"]:
            await cmd["handler"](event["chatMessage"], *cmd["args"])

    def handle(self, text: str, arg_count: int, handler: MessageHandler):
        self.commands.append({"text": text, "arg_count": arg_count, "handler": handler})

