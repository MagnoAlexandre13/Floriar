from typing import Literal

from pydantic import BaseModel, ConfigDict

Size = Literal["petite", "classic", "abundant"]
Color = Literal["original", "yellow", "pink", "white", "red", "lilac"]


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
