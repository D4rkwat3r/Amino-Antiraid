from .http_api import GcmApi
from .http_api import FcmApi
from .model import FcmRegistration
from .mcs import MCSProtocol
from .protopy import LoginRequest
from .protopy import LoginResponse
from .protopy import DataMessage
from base64 import urlsafe_b64decode
from cryptography.hazmat.primitives.serialization import load_der_private_key
from http_ece import decrypt
from ujson import loads
from util import SubscriptionHandler
from asyncio import create_task
import log


class FcmListener(SubscriptionHandler):
    def __init__(self, device_identifier: str = "android-10",
                 device_type: str = "DEVICE_ANDROID_OS"):
        super().__init__()
        self.device_identifier = device_identifier
        self.device_type = device_type
        self.gcm = GcmApi("com.narvii.amino.master", device_type)
        self.fcm = FcmApi()
        self.mcs = MCSProtocol(41)

    async def _listen_loop(self, registration: FcmRegistration):
        log.debug("PushListener", "Соединение установлено")
        while True:
            packet = await self.mcs.receive_packet(8, DataMessage)
            if packet is None:
                continue
            message_json = loads(decrypt(
                content=packet.payload.raw_data,
                salt=urlsafe_b64decode(
                    next(part.value for part in packet.payload.app_data if part.key == "encryption")[5:]
                ),
                private_key=load_der_private_key(
                    urlsafe_b64decode(registration.encryption.private + "========"),
                    password=None
                ),
                dh=urlsafe_b64decode(
                    next(part.value for part in packet.payload.app_data if part.key == "crypto-key")[3:]
                ),
                version="aesgcm",
                auth_secret=urlsafe_b64decode(registration.encryption.auth + "========")
            ))
            payload = loads(message_json["data"]["payload"])
            log.debug("PushListener", f"Получено уведомление типа {payload['notifType']}")
            self.broadcast(payload)

    async def start(
        self,
        registration: FcmRegistration = None
    ):
        await self.mcs.connect()
        packet = LoginRequest(
            id="android-10",
            domain="mcs.android.com",
            user=registration.gcm.android_id,
            resource=registration.gcm.android_id,
            auth_token=registration.gcm.secret,
            device_id=registration.gcm.device_id,
            received_persistent_id=[],
            adaptive_heartbeat=False,
            auth_service=2
        )
        await self.mcs.send(packet, 2)
        await self.mcs.receive_packet(3, LoginResponse)
        await self._listen_loop(registration)

    async def start_in_background(self) -> tuple["FcmListener", FcmRegistration]:
        credentials = await self.gcm.checkin()
        gcm_registration = await self.gcm.register(credentials["androidId"], credentials["securityToken"])
        registration = await self.fcm.register(
            641940763521,
            gcm_registration
        )
        create_task(self.start(registration))
        return self, registration
