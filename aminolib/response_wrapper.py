from dataclasses import dataclass


@dataclass
class ResponseWrapper:
    data: dict

    def __bool__(self):
        return self.data.get("api:statuscode") == 0
