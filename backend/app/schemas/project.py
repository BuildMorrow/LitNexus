import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProjectCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    domain: str | None = None
    research_question: str = Field(min_length=5)
    pico_framework: dict = Field(default_factory=dict)
    inclusion_criteria: list[str] = Field(default_factory=list)
    exclusion_criteria: list[str] = Field(default_factory=list)


class ProjectOut(BaseModel):
    id: uuid.UUID
    title: str
    domain: str | None
    research_question: str
    pico_framework: dict
    inclusion_criteria: list[str]
    exclusion_criteria: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}
