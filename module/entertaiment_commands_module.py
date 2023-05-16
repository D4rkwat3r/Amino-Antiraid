from aminolib import ApiClient
from aminolib import WSConnection
from model import Community
from aiohttp import ClientSession
from aiohttp import FormData
from bs4 import BeautifulSoup
from random import choice
from random import randint
from urllib.parse import quote
from typing import Optional
from typing import Union
from base64 import b64encode
from io import BytesIO
from pydub import AudioSegment
from googletrans import Translator
from string import ascii_lowercase
from asyncio import get_running_loop
from .commands_module import CommandsModule


class EntertainmentCommandsModule(CommandsModule):
    def __init__(self, api_client: ApiClient, community: Community, ws_connection: WSConnection, cfg: dict):
        super().__init__(api_client, community, ws_connection, cfg)
        self.client_session = ClientSession()
        self.translator = Translator()
        self.ai_enabled = cfg["openAIEnabled"]
        self.handle("анекдот", 0, self.cmd_handle_anecdote)
        self.handle("гс", 1, self.cmd_handle_speech)
        self.handle("число", 2, self.cmd_handle_number)
        self.handle("картинка", 1, self.cmd_handle_image)
        self.handle("помощь", 0, self.cmd_handle_help)
        if self.ai_enabled:
            self.token = cfg["openAIConfig"]["token"]
            self.hint = cfg["openAIConfig"]["replyHint"]
            if self.hint.startswith(".file"):
                with open(self.hint.split(".file")[1].strip(), "r", encoding="utf-8") as file:
                    self.hint = file.read()
            self.handle("распознать", 0, self.cmd_handle_recognize)
            self.handle("бот", 1, self.cmd_handle_talk)

    async def send_oai_request(self, path: str, data: Union[dict, FormData]) -> Optional[dict]:
        response = await self.client_session.post(
            f"https://api.openai.com/v1/{path}",
            headers={"Authorization": f"Bearer {self.token}"},
            json=data if isinstance(data, dict) else None,
            data=data if isinstance(data, FormData) else None
        )
        return await response.json() if response.status == 200 else None

    async def get_speech_file_from_task(self, task: dict) -> Optional[str]:
        if task["voiceUrl"]: return task["voiceUrl"]
        if not task["taskId"]: return None
        while True:
            task_status = await (await self.client_session.get(
                f"https://voxworker.com/ru/ajax/status?id={task['taskId']}"
            )).json()
            if task_status["code"]: return None
            if not task_status["voiceUrl"]: continue
            return task_status["voiceUrl"]

    async def recognize_speech_file(self, url: str) -> str:
        media = await self.client_session.get(url)
        buffer = BytesIO()
        AudioSegment.from_file(BytesIO(await media.read()), "aac").export(buffer, format="mp3")
        data = FormData()
        data.add_field("file", buffer, filename="file.mp3")
        data.add_field("model", "whisper-1")
        return (await self.send_oai_request("audio/transcriptions", data))["text"]

    async def create_stablediff_image(self, prompt: str) -> Optional[tuple[str, str]]:
        ws = await self.client_session.ws_connect("wss://runwayml-stable-diffusion-v1-5.hf.space/queue/join")
        session_hash = "".join([choice(ascii_lowercase + "0123456789") for _ in range(11)])
        if (await ws.receive_json())["msg"] == "send_hash":
            await ws.send_json({
                "session_hash": session_hash,
                "fn_index": 2
            })
        while (await ws.receive_json())["msg"] != "send_data":
            continue
        await ws.send_json({
            "data": [prompt],
            "session_hash": session_hash,
            "fn_index": 2,
        })
        if (await ws.receive_json())["msg"] == "process_starts":
            data = (await ws.receive_json())["output"]["data"][0][0]
            return data, data.replace("data:image/jpeg;base64,", "", 1)
        return None

    async def cmd_handle_anecdote(self, message: dict):
        page = await self.client_session.get("https://anekdoty.ru")
        soup = BeautifulSoup(await page.text(), "lxml")
        text = choice(soup.find_all("div", attrs={"class": "holder-body"})).find("p").texz
        await self.api_client.send_message(self.community.ndc_id, message["threadId"], text)

    async def cmd_handle_speech(self, message: dict, *text):
        task = await self.client_session.post(
            "https://voxworker.com/ru/ajax/convert",
            data=f"voice=rh-oleg&speed=1.0&pitch=1.0&text={quote(' '.join(text))}",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        file = await self.get_speech_file_from_task(await task.json())
        if not file: return await self.api_client.send_message(
            self.community.ndc_id,
            message["threadId"],
            "Извините, возникла ошибка",
            reply_to=message["messageId"]
        )
        content = await self.client_session.get(file)
        await self.api_client.send_message(
            self.community.ndc_id,
            message["threadId"],
            message_type=2,
            file={
                "type": 110,
                "content": b64encode(await content.read()).decode("utf-8")
            }
        )

    async def cmd_handle_recognize(self, message: dict):
        if (reply_message := message.get("extensions", {}).get("replyMessage")) is None:
            return await self.api_client.send_message(self.community.ndc_id, message["threadId"],
                                                      "Для испольозования этой команды ответьте"
                                                      "на голосовое сообщение")
        if reply_message["mediaType"] != 110:
            return await self.api_client.send_message(self.community.ndc_id, message["threadId"],
                                                      "Сообщение не содержит аудиофайл")
        try: result = await self.recognize_speech_file(message["extensions"]["replyMessage"]["mediaValue"])
        except: return await self.api_client.send_message(
            self.community.ndc_id,
            message["threadId"],
            "Извините, возникла ошибка",
            reply_to=message["messageId"]
        )
        await self.api_client.send_message(
            self.community.ndc_id,
            message["threadId"],
            result.capitalize(),
            reply_to=message["extensions"]["replyMessage"]["messageId"]
        )

    async def cmd_handle_number(self, message: dict, n_from: str, n_to: str):
        if not n_from.isdigit() or not n_to.isdigit():
            return await self.api_client.send_message(
                self.community.ndc_id,
                message["threadId"],
                "Неверный ввод.\n",
                reply_to=message["messageId"]
            )
        if int(n_from) > int(n_to):
            return await self.api_client.send_message(
                self.community.ndc_id,
                message["threadId"],
                "Начало диапазона не может превышать конец диапазона.\n",
                reply_to=message["messageId"]
            )
        await self.api_client.send_message(
            self.community.ndc_id,
            message["threadId"],
            f"Случайное число: {randint(int(n_from), int(n_to))}",
            reply_to=message["messageId"]
        )

    async def cmd_handle_image(self, message: dict, *prompt):
        actual_prompt = " ".join(prompt)
        need_translate = prompt[0] != "-"
        translated_prompt = (await get_running_loop().run_in_executor(
            None,
            lambda: self.translator.translate(actual_prompt, dest="en")
        )).text if need_translate else "ОТСУТСТВУЕТ"
        await self.api_client.send_message(
            self.community.ndc_id,
            message["threadId"],
            f"Используется следующий перевод запроса: \"{translated_prompt}\".\n\nСоздаю картинку.",
            reply_to=message["messageId"]
        )
        link, data = await self.create_stablediff_image(translated_prompt if need_translate else actual_prompt)
        await self.api_client.send_message(
            self.community.ndc_id,
            message["threadId"],
            "Картинка создана",
            reply_to=message["messageId"]
        )
        await self.api_client.send_message(
            self.community.ndc_id,
            message["threadId"],
            file={
                "type": 100,
                "content": data,
                "mimeType": "image/jpeg",
                "uhq": True
            }
        )

    async def cmd_handle_talk(self, message: dict, *prompt):
        response = await self.send_oai_request("chat/completions", {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": self.hint},
                {"role": "user", "content": " ".join(prompt)}
            ],
            "n": 1
        })
        await self.api_client.send_message(
            self.community.ndc_id,
            message["threadId"],
            response["choices"][0]["message"]["content"],
            reply_to=message["messageId"]
        )

    async def cmd_handle_help(self, message: dict):
        help_text = f"[BC]- - - РАЗВЛЕКАТЕЛЬНЫЕ КОМАНДЫ - - -\n\n" \
                    f"{self.prefix}анекдот - случайный анекдот с сайта anekdoty.ru\n" \
                    f"{self.prefix}гс - преобразовать текст в голосовое сообщение\n" \
                    f"{self.prefix}число [от] [до] - создать случайное число в указанном диапазоне\n" \
                    f"{self.prefix}картинка [-, если не требуется перевод] [текст] - создать картинку по запросу\n"
        if self.ai_enabled:
            help_text += f"{self.prefix}распознать - распознать текст голосового сообщения\n"
            help_text += f"{self.prefix}бот [текст] - задать боту вопрос\n"
        help_text += f"{self.prefix}помощь - вывести список команд"
        await self.api_client.send_message(
            self.community.ndc_id,
            message["threadId"],
            help_text
        )
