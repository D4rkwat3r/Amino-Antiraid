from hmac import new
from base64 import b64encode
from os import urandom
from hashlib import sha1
from ujson import dumps
from typing import Optional
from aiohttp import ClientSession
from dataclasses_json import DataClassJsonMixin
from json import dumps
from json import loads
from json import JSONDecodeError
from time import time
from config import Config
from random import choice
from .response_wrapper import ResponseWrapper
import log


class ApiRequest:
    device: Optional[str] = None
    client_session: ClientSession
    proxies: list[Config.ApiClientConfig.ProxyConfig.Proxy]
    url: str = "https://service.aminoapps.com/api/v1"

    def __init__(self):
        self._method = None
        self._path = None
        self._force_signature = False
        self._auth = None
        self._params = {}

    def __call__(self, *args, **kwargs):
        return self.send()

    def __repr__(self):
        return f"{self._method} /{self._path}"

    def __str__(self):
        return self.__repr__()

    @staticmethod
    def generate_message_signature(data: bytes) -> str:
        return b64encode(
            bytes.fromhex("19") + new(bytes.fromhex("DFA5ED192DDA6E88A12FE12130DC6206B1251E44"), data, sha1).digest()
        ).decode("utf-8")

    @staticmethod
    def generate_device_id() -> str:
        identifier = urandom(20)
        return f"19{identifier.hex()}" \
               f"{new(bytes.fromhex('E7309ECC0953C6FA60005B2765F99DBBC965C8E9'), bytes.fromhex('19') + identifier, sha1).hexdigest()}".upper()

    @classmethod
    def method(cls, method: str):
        instance = cls()
        instance._method = method
        return instance

    @classmethod
    def get(cls, path: str):
        return cls.method("GET").path(path)

    @classmethod
    def delete(cls, path: str):
        return cls.method("DELETE").path(path)

    @classmethod
    def post(cls, path: str):
        return cls.method("POST").path(path)

    def path(self, path: str):
        self._path = path
        if self._path.startswith("/"): self._path = self._path[1:]
        return self

    def unconfined_scope(self):
        return self.path(f"xx/s/{self._path}")

    def global_scope(self):
        return self.path(f"g/s/{self._path}")

    def guest_scope(self, ndc_id: int):
        return self.path(f"g/s-x{ndc_id}/{self._path}")

    def community_scope(self, ndc_id: int):
        return self.path(f"x{ndc_id}/s/{self._path}")

    def param(self, key: str, value: object):
        if type(value) in [str, int, float, bool, type(None), dict, tuple, list, set]: self._params[key] = value
        elif isinstance(value, DataClassJsonMixin): self._params[key] = value.to_dict()
        else: raise ValueError(f"Invalid param type ({type(value)})")
        self._params[key] = value
        return self

    def params(self, params: dict):
        for key, value in zip(params.keys(), params.values()): self.param(key, value)
        return self

    def force_signature(self):
        self._force_signature = True
        return self

    def auth(self, sid: str):
        self._auth = f"sid={sid}"
        return self

    async def send(self) -> ResponseWrapper:
        if self.device is None: self.device = self.generate_device_id()
        h = {
            "NDCDEVICEID": self.device,
            "NDCLANG": "ru",
            "Accept-Language": "ru-RU",
            "User-Agent": "Apple iPhone14,2 iOS v16.2 Main/3.13.1"
        }
        if self._auth is not None: h["NDCAUTH"] = self._auth
        data = ""
        if self._method == "POST":
            if len(self._params) == 0 and not self._force_signature:
                h["Content-Type"] = "application/x-www-form-urlencoded"
            else:
                self.param("timestamp", int(time() * 1000))
                data = dumps(self._params).encode("utf-8")
                h["Content-Type"] = "application/json; charset=utf-8"
                h["NDC-MSG-SIG"] = self.generate_message_signature(data)
        else:
            keys = tuple(self._params.keys())
            values = tuple(self._params.values())
            for key, value in zip(keys, values):
                if key == keys[0]: self._path += "?"
                self._path += f"{key}={value}"
                if key != keys[-1]: self._path += "&"
        response = await self.client_session.request(
            self._method,
            f"{self.url}/{self._path}",
            headers=h,
            data=data,
            proxy=None if not self.proxies else choice(self.proxies).proxy_string
        )
        log.debug("API", f"Отправлен запрос к API: [{self}], статус: {'УСПЕХ' if response.status == 200 else 'НЕУДАЧА'}")
        try: response_json = loads(await response.text())
        except JSONDecodeError: return ResponseWrapper({})
        return ResponseWrapper(response_json)
