from pydantic import BaseModel


class UserQueryRequest(BaseModel):
    query: str
    model: str 