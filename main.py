from asyncio import get_event_loop
from config import Config
from aiohttp.client import ClientTimeout
from aminolib import ApiRequest
from aminolib import ApiClient
from aminolib import WSConnection
from aiohttp import ClientSession
from model import Community
from model import Account
from asyncio import create_task
from asyncio import gather
from inspect import signature
import module as module_classes
import polling_process as polling_process_classes
import log


async def run_polling_processes(config: Config, api_client: ApiClient, community: Community):
    created_polling_process_objects = {}
    for polling_process in config.polling_processes:
        if not polling_process.enabled: continue
        polling_process_class = getattr(polling_process_classes, polling_process.name, None)
        if polling_process_class is None:
            log.error(__name__, f"Опрашивающий процесс {polling_process.name} "
                                f"зарегистрирован в JSON-файле конфигурации, "
                                f"но не имеет собственного класса (или класс не импортирован в __init__.py)")
            continue
        polling_process_object = polling_process_class(api_client, community, polling_process.interval)
        polling_process_object.run_in_background()
        created_polling_process_objects[polling_process.name] = polling_process_object
    return created_polling_process_objects


async def run_modules(
    config: Config,
    api_client: ApiClient,
    connection: WSConnection,
    community: Community
) -> dict:
    created_module_objects = {}
    polling_processes = await run_polling_processes(config, api_client, community)
    for module in config.modules:
        if not module.enabled_globally and community.ndc_id not in module.enabled_in:
            continue
        module_class = getattr(module_classes, module.name, None)
        if module_class is None:
            log.error(__name__, f"Модуль {module.name} зарегистрирован в JSON-файле конфигурации, "
                                f"но не имеет собственного класса (или класс не импортирован в __init__.py)")
            continue
        dependencies = [created_module_objects.get(name) for name in module.dependencies]
        if issubclass(module_class, module_classes.PollingModule):
            try:
                polling_process_class = signature(module_class.__init__).parameters["source"].annotation
            except KeyError:
                log.error(__name__, f"Модуль {module.name} не имеет в методе __init__ параметра source")
                continue
            if not issubclass(polling_process_class, polling_process_classes.PollingProcess):
                log.error(__name__, f"Модуль {module.name} имеет неверную (или не имеет "
                                    f"вообще) аннотацию типа у параметра source. "
                                    f"Класс аннотации должен расширять класс PollingProcess")
                continue
            try:
                module_object = module_class(
                    api_client, community,
                    polling_processes[polling_process_class.__name__], module.config,
                    *dependencies
                )
            except KeyError:
                log.error(__name__, f"Опрашивающий процесс {polling_process_class.__name__} используется "
                                    f"модулен {module.name}, но не зарегистрирован или отключён")
                continue
        elif issubclass(module_class, module_classes.EventModule):
            module_object = module_class(api_client, community, connection, module.config, *dependencies)
        else:
            log.error(__name__, f"Класс модуля должен расширять класс PollingModule или EventModule")
            continue
        module_object.run_in_background()
        created_module_objects[module.name] = module_object
    return created_module_objects


async def run(config: Config, account: Account, communities: tuple[Community, ...]):
    connection = WSConnection(
        account.sid,
        config.web_socket_config.server,
        config.web_socket_config.ping_interval
    ).start_in_background()
    api_client = ApiClient(account.sid, account.uid)
    affiliations = (await api_client.get_affiliations()).data.get("affiliations") or []
    for community in communities:
        if community.ndc_id not in affiliations:
            joined = await api_client.join_community(community.ndc_id)
            if joined:
                log.info(__name__, f"Вошли в сооющество {community.name} с аккаунта {account.uid}")
            else:
                log.error(__name__, f"Не смогли войти в сообщество {community.name} с аккаунта {account.uid}")
                continue
        await run_modules(config, api_client, connection, community)


async def main():
    with open("config.json", "r", encoding="utf-8") as file:
        config: Config = Config.from_json(file.read())
        log.set_level(log.logging_levels.get(config.logging_level) or 6)
        ApiRequest.url = config.api_client_config.base_api_url
        ApiRequest.proxies = [] if not config.api_client_config.proxy_enabled \
            else config.api_client_config.proxy_config.proxies
        timeout = ClientTimeout(
            sock_connect=config.api_client_config.connect_timeout,
            sock_read=config.api_client_config.read_timeout
        )
        ApiRequest.client_session = ClientSession(timeout=timeout)
        communities = await gather(
            *[
                create_task(ApiRequest.get("community/info").guest_scope(community).send())
                for community in config.general_config.communities
            ]
        )
        communities = tuple(filter(lambda x: bool(x), communities))
        communities = tuple(map(lambda x: Community.from_dict(x.data["community"]), communities))
        log.info(__name__, f"Получили информацию о "
                           f"{len(communities)} сообществах "
                           f"из общего числа в {len(config.general_config.communities)}")
        for account in config.accounts:
            login_response = await ApiRequest.post("auth/login") \
                .global_scope() \
                .param("email", account.email) \
                .param("secret", f"0 {account.password}") \
                .param("clientType", 300) \
                .send()
            if not login_response:
                log.fatal(__name__, f"Не удалось войти в аккаунт {account.email}")
                continue
            log.info(__name__, f"Успешно вошли в аккаунт {account.email}")
            await run(
                config,
                Account(login_response.data["userProfile"]["uid"], login_response.data["sid"]),
                communities
            )


if __name__ == "__main__":
    loop = get_event_loop()
    loop.create_task(main())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("Получено клавиатурное прерывание, работа завершается")
        exit(0)
