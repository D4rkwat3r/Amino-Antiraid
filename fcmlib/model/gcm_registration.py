from dataclasses import dataclass


@dataclass
class GcmRegistration:
    token: str
    android_id: str
    device_id: str
    secret: str
