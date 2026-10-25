from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    # Верхняя граница защищает от DoS через огромный «пароль» при хешировании.
    password: str = Field(min_length=8, max_length=128)
    # Необязательный телефон в международном формате E.164, например +79991234567.
    phone: str | None = Field(default=None, pattern=r"^\+[1-9]\d{7,14}$")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    phone: str | None = None
