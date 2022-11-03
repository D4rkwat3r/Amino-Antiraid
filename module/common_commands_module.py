from model import Community
from aminolib import WSConnection
from aminolib import ApiClient
from aminolib import ApiRequest
from typing import Optional
from .anti_botnet import AntiBotnet
from .commands_module import CommandsModule
from .commands_module import with_role_filter


class CommonCommandsModule(CommandsModule):
    def __init__(
            self,
            api_client: ApiClient,
            community: Community,
            cfg: dict,
            ws_connection: WSConnection,
            anti_botnet_reference: Optional[AntiBotnet]
    ):
        super().__init__(api_client, community, cfg, ws_connection)
        self.handle("ping", 0, self.cmd_handle_ping)
        self.handle("join", 1, self.cmd_handle_join)
        self.handle("leave", 0, self.cmd_handle_leave)
        self.handle("ban", 2, self.cmd_handle_ban)
        self.handle("unban", 1, self.cmd_handle_unban)
        self.handle("kick", 3, self.cmd_handle_kick)
        self.handle("invite", 1, self.cmd_handle_invite)
        self.handle("clean", 0, self.cmd_handle_clean)
        self.handle("help", 0, self.cmd_handle_help)
        self.anti_botnet_reference = anti_botnet_reference

    async def get_object_id(self, expected_type: int, link: str, thread_id: str, expected_name: str) -> Optional[str]:
        link_info_response = await ApiRequest.get("link-resolution") \
            .global_scope() \
            .param("q", link) \
            .send()
        if not link_info_response:
            await self.api_client.send_message(
                self.community.ndc_id, thread_id, "Не удалось получить информацию о ссылке"
            )
            return
        info_data = link_info_response.data["linkInfoV2"]["extensions"]
        await self.api_client.send_message(self.community.ndc_id, thread_id, "Информация о ссылке получена")
        if info_data.get("linkInfo") is None or info_data["linkInfo"]["objectType"] != expected_type:
            await self.api_client.send_message(self.community.ndc_id, thread_id, f"Это не {expected_name}")
            return
        if info_data["linkInfo"]["ndcId"] != self.community.ndc_id:
            await self.api_client.send_message(
                self.community.ndc_id, thread_id, f"{expected_name.capitalize()} находится не в этом сообществе"
            )
            return
        return info_data["linkInfo"]["objectId"]

    async def cmd_handle_ping(self, message: dict):
        await self.api_client.send_message(self.community.ndc_id, message["threadId"], f"Понг!")

    async def cmd_handle_join(self, message: dict, link: str):
        chat_id = await self.get_object_id(12, link, message["threadId"], "чат")
        if chat_id is None: return
        if await self.api_client.join_chat(self.community.ndc_id, chat_id):
            return await self.api_client.send_message(
                self.community.ndc_id, message["threadId"], "Вошёл в чат"
            )
        else:
            return await self.api_client.send_message(
                self.community.ndc_id, message["threadId"], "При входе в чат возникла ошибка"
            )

    @with_role_filter([100, 101, 102])
    async def cmd_handle_leave(self, message: dict):
        if not await self.api_client.leave_chat(self.community.ndc_id, message["threadId"]):
            await self.api_client.send_message(
                self.community.ndc_id, message["threadId"], "При выходе из чата возника ошибка"
            )

    @with_role_filter([100, 102])
    async def cmd_handle_ban(self, message: dict, *_):
        extensions = message.get("extensions")
        if extensions is None: return
        mentions = extensions.get("mentionedArray")
        if mentions is None: return
        if await self.api_client.ban(
            self.community.ndc_id,
            200,
            f"Команда {self.prefix}ban выполнена пользователем {message['author']['nickname']}",
            mentions[0]["uid"]
        ): await self.api_client.send_message(self.community.ndc_id, message["threadId"], "Пользователь забанен")
        else: await self.api_client.send_message(self.community.ndc_id, message["threadId"], "Возникла ошибка")

    @with_role_filter([100, 102])
    async def cmd_handle_unban(self, message: dict, link: str):
        user_id = await self.get_object_id(0, link, message["threadId"], "пользователь")
        if user_id is None: return
        if await self.api_client.unban(self.community.ndc_id, user_id):
            await self.api_client.send_message(self.community.ndc_id, message["threadId"], "Пользователь разбанен")
        else: await self.api_client.send_message(self.community.ndc_id, message["threadId"], "Возникла ошибка")

    @with_role_filter([100, 101, 102])
    async def cmd_handle_kick(self, message: dict, represented_disallow_rejoin: str, *_):
        extensions = message.get("extensions")
        if extensions is None: return
        mentions = extensions.get("mentionedArray")
        if mentions is None: return
        if await self.api_client.kick(
            self.community.ndc_id,
            message["threadId"],
            mentions[0]["uid"],
            False if represented_disallow_rejoin == "+" else True
        ): await self.api_client.send_message(self.community.ndc_id, message["threadId"], "Пользователь удалён")
        else: await self.api_client.send_message(self.community.ndc_id, message["threadId"], "Возникла ошибка")

    @with_role_filter([100, 101, 102])
    async def cmd_handle_invite(self, message: dict, link: str):
        user_id = await self.get_object_id(0, link, message["threadId"], "пользователь")
        if user_id is None: return
        if await self.api_client.invite(
            self.community.ndc_id,
            message["threadId"],
            (user_id,)
        ): await self.api_client.send_message(self.community.ndc_id, message["threadId"], "Пользователь приглашён")
        else: await self.api_client.send_message(self.community.ndc_id, message["threadId"], "Возникла ошибка")

    @with_role_filter([100, 102])
    async def cmd_handle_clean(self, message: dict):
        if self.anti_botnet_reference is None:
            return await self.api_client.send_message(self.community.ndc_id, message["threadId"], "Извините, этот модуль отключён")
        await self.api_client.send_message(self.community.ndc_id, message["threadId"], "Очистка запущена")
        await self.anti_botnet_reference.clear_community()
        await self.api_client.send_message(self.community.ndc_id, message["threadId"], "Очистка завершена")

    async def cmd_handle_help(self, message: dict):
        await self.api_client.send_message(
            self.community.ndc_id,
            message["threadId"],
            f"{self.prefix}ping - проверка работоспособности\n"
            f"{self.prefix}join [ссылка] - войти в чат по ссылке\n"
            f"{self.prefix}leave - покинуть этот чат (доступно только лидерам и кураторам)\n"
            f"{self.prefix}ban [никнейм через @] - забанить пользователя по ссылке (доступно только лидерам)\n"
            f"{self.prefix}unban [ссылка] - разбанить пользователя по ссылке (доступно только лидерам)\n"
            f"{self.prefix}kick [+: с галочкой, -: без галочки] [никнейм через @] - удалить пользователя из чата (доступно только лидерам и кураторам)\n"
            f"{self.prefix}invite [ссылка] - пригласить пользователя в чат (доступно только лидерам и кураторам)\n"
            f"{self.prefix}clean - принудительно запустить очистку сообщества от одновременно или почти одновременно вошедших аккаунтов (доступно только лидерам)\n"
            f"{self.prefix}help - отправить справку по командам"
        )
