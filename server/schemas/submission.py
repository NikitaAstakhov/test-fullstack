import datetime
from typing import List, Dict, Any
from pydantic import BaseModel, field_validator


class SubmitPayload(BaseModel):
    date: datetime.date
    first_name: str
    last_name: str

    @field_validator("first_name")
    def no_whitespace_in_first(cls, v: str) -> str:
        if " " in v:
            raise ValueError("No whitespace in first name is allowed")
        return v

    @field_validator("last_name")
    def no_whitespace_in_last(cls, v: str) -> str:
        if " " in v:
            raise ValueError("No whitespace in last name is allowed")
        return v


class ErrorResponse(BaseModel):
    success: bool = False
    error: Dict[str, List[str]]


class HistoryItem(BaseModel):
    date: str
    first_name: str
    last_name: str
    count: int


class SuccessResponse(BaseModel):
    success: bool = True
    data: List[Dict[str, Any]]
