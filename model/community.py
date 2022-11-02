from dataclasses_json import dataclass_json
from dataclasses_json import LetterCase
from dataclasses import dataclass


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Community:
    name: str
    ndc_id: int
