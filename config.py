from dataclasses_json import dataclass_json
from dataclasses_json import LetterCase
from dataclasses import dataclass
from dataclasses import field
from typing import Optional


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Config:
    @dataclass_json(letter_case=LetterCase.CAMEL)
    @dataclass
    class GeneralConfig:
        communities: list[int]

    @dataclass_json(letter_case=LetterCase.CAMEL)
    @dataclass
    class ApiClientConfig:
        @dataclass_json(letter_case=LetterCase.CAMEL)
        @dataclass
        class ProxyConfig:
            @dataclass_json
            @dataclass
            class Proxy:
                @dataclass_json
                @dataclass
                class Auth:
                    username: str
                    password: str

                scheme: str
                host: str
                port: str
                auth: Optional[Auth]

                @property
                def proxy_string(self) -> str:
                    result = f"{self.scheme}://"
                    if self.auth is not None:
                        result += f"{self.auth.username}:{self.auth.password}@"
                    result += f"{self.host}:{self.port}"
                    return result
            proxies: list[Proxy]

        base_api_url: str
        connect_timeout: int
        read_timeout: int
        proxy_enabled: bool
        proxy_config: Optional[ProxyConfig]

    @dataclass_json(letter_case=LetterCase.CAMEL)
    @dataclass
    class WebSocketConfig:
        server: str
        ping_interval: int

    @dataclass_json
    @dataclass
    class PollingProcess:
        name: str
        enabled: bool
        interval: int

    @dataclass_json(letter_case=LetterCase.CAMEL)
    @dataclass
    class Module:
        name: str
        config: dict
        enabled_globally: bool = field(default_factory=bool)
        enabled_in: list[int] = field(default_factory=list)
        dependencies: list[str] = field(default_factory=list)

    @dataclass_json
    @dataclass
    class Account:
        email: str
        password: str

    logging_level: str
    general_config: GeneralConfig
    api_client_config: ApiClientConfig
    web_socket_config: WebSocketConfig
    polling_processes: list[PollingProcess]
    modules: list[Module]
    accounts: list[Account]

    def module(self, name: str) -> Optional[Module]:
        try:
            return [x for x in self.modules if x.name == name][0]
        except IndexError:
            return None

    def enabled_module(self, name: str) -> Optional[Module]:
        module = self.module(name)
        if module is None: return module
        if not module.enabled: return None
        return module
