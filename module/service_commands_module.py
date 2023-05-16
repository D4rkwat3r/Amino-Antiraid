from model import Community
from aminolib import WSConnection
from aminolib import ApiClient
from aminolib import ApiRequest
from typing import Optional
from asyncio import create_task
from asyncio import gather
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from io import BytesIO
from base64 import b64encode
from .anti_botnet import AntiBotnet
from .commands_module import CommandsModule
from .commands_module import with_role_filter


class ServiceCommandsModule(CommandsModule):
    def __init__(
            self,
            api_client: ApiClient,
            community: Community,
            ws_connection: WSConnection,
            cfg: dict,
            anti_botnet_reference: Optional[AntiBotnet]
    ):
        super().__init__(api_client, community, ws_connection, cfg)
        self.handle("ping", 0, self.cmd_handle_ping)
        self.handle("join", 1, self.cmd_handle_join)
        self.handle("leave", 0, self.cmd_handle_leave)
        self.handle("ban", 1, self.cmd_handle_ban)
        self.handle("unban", 1, self.cmd_handle_unban)
        self.handle("kick", 2, self.cmd_handle_kick)
        self.handle("invite", 1, self.cmd_handle_invite)
        self.handle("clean", 0, self.cmd_handle_clean)
        self.handle("open", 0, self.cmd_handle_open)
        self.handle("close", 0, self.cmd_handle_close)
        self.handle("clean_history", 1, self.cmd_handle_clean_history)
        self.handle("snippet", 2, self.cmd_handle_snippet)
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

    async def delete_messages(self, message: dict, messages: list[dict]) -> int:
        return (await gather(*[
            create_task(
                self.api_client.delete_message(
                    self.community.ndc_id,
                    message["threadId"],
                    msg["messageId"],
                    f"Команда /clean_history выполнена пользователем {message['author']['nickname']}"
                )
            ) for msg in messages
        ])).count(True)

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
        ):
            await self.api_client.send_message(self.community.ndc_id, message["threadId"], "Пользователь забанен")
        else:
            await self.api_client.send_message(self.community.ndc_id, message["threadId"], "Возникла ошибка")

    @with_role_filter([100, 102])
    async def cmd_handle_unban(self, message: dict, link: str):
        user_id = await self.get_object_id(0, link, message["threadId"], "пользователь")
        if user_id is None: return
        if await self.api_client.unban(self.community.ndc_id, user_id):
            await self.api_client.send_message(self.community.ndc_id, message["threadId"], "Пользователь разбанен")
        else:
            await self.api_client.send_message(self.community.ndc_id, message["threadId"], "Возникла ошибка")

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
        ):
            await self.api_client.send_message(self.community.ndc_id, message["threadId"], "Пользователь удалён")
        else:
            await self.api_client.send_message(self.community.ndc_id, message["threadId"], "Возникла ошибка")

    @with_role_filter([100, 101, 102])
    async def cmd_handle_invite(self, message: dict, link: str):
        user_id = await self.get_object_id(0, link, message["threadId"], "пользователь")
        if user_id is None: return
        if await self.api_client.invite(
                self.community.ndc_id,
                message["threadId"],
                (user_id,)
        ):
            await self.api_client.send_message(self.community.ndc_id, message["threadId"], "Пользователь приглашён")
        else:
            await self.api_client.send_message(self.community.ndc_id, message["threadId"], "Возникла ошибка")

    @with_role_filter([100, 102])
    async def cmd_handle_clean(self, message: dict):
        if self.anti_botnet_reference is None:
            return await self.api_client.send_message(self.community.ndc_id, message["threadId"],
                                                      "Извините, этот модуль отключён")
        await self.api_client.send_message(self.community.ndc_id, message["threadId"], "Очистка запущена")
        await self.anti_botnet_reference.clear_community()
        await self.api_client.send_message(self.community.ndc_id, message["threadId"], "Очистка завершена")

    @with_role_filter([100, 102])
    async def cmd_handle_open(self, message: dict):
        opened = await self.api_client.change_community_settings(self.community.ndc_id, joinType=0)
        if opened:
            await self.api_client.send_message(self.community.ndc_id, message["threadId"], "Сообщество открыто")
        else:
            await self.api_client.send_message(self.community.ndc_id, message["threadId"], "Возникла ошибка")

    @with_role_filter([100, 102])
    async def cmd_handle_close(self, message: dict):
        closed = await self.api_client.change_community_settings(self.community.ndc_id, joinType=1)
        if closed:
            await self.api_client.send_message(self.community.ndc_id, message["threadId"], "Сообщество закрыто")
        else:
            await self.api_client.send_message(self.community.ndc_id, message["threadId"], "Возникла ошибка")

    @with_role_filter([100, 101, 102])
    async def cmd_handle_clean_history(self, message: dict, count: str):
        if not count.isdigit():
            return
        count = int(count)
        deleted = 0
        for portion in range(count // 100):
            messages = await self.api_client.get_chat_messages(self.community.ndc_id, message["threadId"], 0, 100)
            deleted += await self.delete_messages(message, messages.data["messageList"])
            count -= 100
        if count > 0:
            messages = await self.api_client.get_chat_messages(self.community.ndc_id, message["threadId"], 0, count)
            deleted += await self.delete_messages(message, messages.data["messageList"])
        await self.api_client.send_message(self.community.ndc_id, message["threadId"], f"Удалено сообщений: {deleted}")

    def generate_snippet(
        self,
        snippet_size: tuple[int, int],
        container_size: tuple[int, int],
        snippet_fill_color: tuple[int, int, int],
        container_fill_color: tuple[int, int, int],
        container_radius: int,
        text: str,
        text_size: int,
        text_color: tuple[int, int, int]
    ) -> bytes:
        snippet = Image.new("RGBA", snippet_size, color=snippet_fill_color)
        draw = ImageDraw.Draw(snippet)
        container_start_position = (
            (snippet_size[0] - container_size[0]) // 2,
            (snippet_size[1] - container_size[1]) // 2
        )
        container_end_position = (
            container_start_position[0] + container_size[0],
            container_start_position[1] + container_size[1]
        )
        draw.rounded_rectangle(
            (container_start_position, container_end_position),
            container_radius,
            container_fill_color
        )
        font = ImageFont.truetype("font.ttf", text_size)
        _, _, text_width, text_height = draw.textbbox((0, 0), text, font)
        text_position = (
            (snippet_size[0] - text_width) // 2,
            (snippet_size[1] - text_height) // 2
        )
        draw.text(
            text_position,
            text,
            text_color,
            font,
            align="center"
        )
        buffer = BytesIO()
        snippet.save(buffer, "PNG")
        return buffer.getvalue()

    async def cmd_handle_snippet(self, message: dict, size: str, text: str):
        x, y = tuple([int(x) for x in size.split("x")])
        snippet = self.generate_snippet(
            (x, y),
            (x // 1.3, y // 1.3),
            (255, 255, 255),
            (0, 0, 0),
            30,
            text,
            70,
            (255, 255, 255)
        )
        await self.api_client.send_message(
            self.community.ndc_id,
            message["threadId"],
            "Сниппет сгенерирован",
            link_snippet={
                "link": "https://aminoapps.com",
                "mediaType": 100,
                "mediaUploadValueContentType": "image/png",
                "mediaUploadValue": b64encode(snippet).decode("utf-8")
            }
        )

    async def cmd_handle_help(self, message: dict):
        await self.api_client.send_message(
            self.community.ndc_id,
            message["threadId"],
            f"[BC]- - - СЛУЖЕБНЫЕ КОМАНДЫ - - -\n\n"
            f"{self.prefix}ping - проверка работоспособности\n"
            f"{self.prefix}join [ссылка] - войти в чат по ссылке\n"
            f"{self.prefix}leave - покинуть этот чат (доступно только лидерам и кураторам)\n"
            f"{self.prefix}ban [никнейм через @] - забанить пользователя по никнейму (доступно только лидерам)\n"
            f"{self.prefix}unban [ссылка] - разбанить пользователя по ссылке (доступно только лидерам)\n"
            f"{self.prefix}kick [+: с галочкой, -: без галочки] [никнейм через @] - удалить пользователя из чата (доступно только лидерам и кураторам)\n"
            f"{self.prefix}invite [ссылка] - пригласить пользователя в чат (доступно только лидерам и кураторам)\n"
            f"{self.prefix}clean - принудительно запустить очистку сообщества от одновременно или почти одновременно вошедших аккаунтов (доступно только лидерам)\n"
            f"{self.prefix}open - открыть сообщество (доступно только лидерам)\n"
            f"{self.prefix}close - закрыть сообщество (доступно только лидерам)\n"
            f"{self.prefix}clean_history [кол-во сообщений, не рекомендуется ставить больше 100] - удалить указанное количество сообщений (доступно только лидерам и кураторам\n"
            f"{self.prefix}snippet [WxH] [TEXT] - ???\n"
            f"{self.prefix}help - отправить справку по командам"
        )
