from ..protopy import Checkin
from ..protopy import CheckinRequest
from ..protopy import CheckinResponse
from httpx import AsyncClient
from google.protobuf.json_format import MessageToDict as messageToDict
from uuid import uuid4
from ..model.gcm_registration import GcmRegistration

# Available device types
#    DEVICE_ANDROID_OS;
#    DEVICE_IOS_OS;
#    DEVICE_CHROME_BROWSER;
#    DEVICE_CHROME_OS;

# Should be dynamic?
SERVER_KEY_B64 = "BDOU99-h67HcA6JeFXHbSNMu7e2yNNu3RzoMj8TM4W88jITfq7ZmPvIM1Iv-4_l2LxQcYwhqby2xGpWwzjfAnG4"


class GcmApi:
    def __init__(self, app_name: str, device_type: str):
        self.app_name = app_name
        self.device_type = device_type
        self.android_id = None
        self.security_token = None
        self.http_client = AsyncClient(base_url="https://android.clients.google.com/", http2=True)

    async def checkin(self) -> CheckinResponse:
        response = await self.http_client.post("checkin", headers={
            "Content-Type": "application/x-protobuf"
        }, data=CheckinRequest(
            checkin=Checkin(type="DEVICE_ANDROID_OS"),
            version=3
        ).SerializeToString())
        data = CheckinResponse()
        data.ParseFromString(response.read())
        return messageToDict(data)

    async def register(self, android_id: str, security_token: str) -> GcmRegistration:
        response = await self.http_client.post("c2dm/register3", headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"AidLogin {android_id}:{security_token}"
        }, data={
            "app": self.app_name,
            "X-subtype": f"wp:receiver.push.com#{uuid4()}",
            "device": android_id,
            "sender": SERVER_KEY_B64
        })
        return GcmRegistration(response.text.split("token=")[1], android_id,
                               "android-%x" % int(android_id), security_token)

