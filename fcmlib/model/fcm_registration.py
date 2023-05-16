from dataclasses import dataclass
from .gcm_registration import GcmRegistration


@dataclass
class FcmRegistration:
    @dataclass
    class Encryption:
        public: str
        private: str
        auth: str
    encryption: Encryption
    gcm: GcmRegistration
    fcm_token: str
    fcm_push_set: str
