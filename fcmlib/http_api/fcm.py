from oscrypto.asymmetric import generate_pair
from base64 import urlsafe_b64encode
from httpx import AsyncClient
from os import urandom
from ..model.gcm_registration import GcmRegistration
from ..model.fcm_registration import FcmRegistration


class FcmApi:
    def __init__(self):
        self.http_client = AsyncClient(base_url="https://fcm.googleapis.com/", http2=True)

    async def register(self, sender_id: int, gcm_registration: GcmRegistration) -> FcmRegistration:
        public, private = generate_pair("ec", curve="secp256r1")
        keys = {
            "public": urlsafe_b64encode(
                public.asn1.dump()[26:]
            ).replace(b"=", b"").replace(b"\n", b"").decode("ascii"),
            "private": urlsafe_b64encode(
                private.asn1.dump()
            ).replace(b"=", b"").replace(b"\n", b"").decode("ascii"),
            "auth": urlsafe_b64encode(urandom(16)).replace(b"=", b"").replace(b"\n", b"").decode("ascii")
        }
        data = {
            "authorized_entity": sender_id,
            "endpoint": f"https://fcm.googleapis.com/fcm/send/{gcm_registration.token}",
            "encryption_key": keys["public"],
            "encryption_auth": keys["auth"]
        }
        response = (await self.http_client.post(f"fcm/connect/subscribe", headers={
            "Content-Type": "application/x-www-form-urlencoded"
        }, data=data)).json()
        return FcmRegistration(
            FcmRegistration.Encryption(keys["public"], keys["private"], keys["auth"]),
            gcm_registration,
            response["token"],
            response["pushSet"]
        )
