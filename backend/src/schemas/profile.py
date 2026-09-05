from pydantic import BaseModel


class ProfileUpdate(BaseModel):
    name: str
    business: str
    category: str = "other"
    description: str = ""


class ProfileRead(ProfileUpdate):
    id: str