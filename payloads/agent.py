from typing import Literal
from pydantic import BaseModel

class Execute(BaseModel):
    task: str

class ResumeRequest(BaseModel):
    input: Literal["yes", "no"]

