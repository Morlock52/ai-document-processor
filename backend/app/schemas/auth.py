from pydantic import BaseModel, Field


class AuthStatus(BaseModel):
    require_login: bool = Field(default=False, description="Whether login is required for API access")
    login_configured: bool = Field(default=False, description="Whether a passcode has been set")


class LoginRequest(BaseModel):
    passcode: str = Field(..., min_length=6, description="Passcode set in settings to unlock the app")


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginSettingsUpdate(BaseModel):
    require_login: bool
    passcode: str | None = Field(default=None, description="New passcode when enabling login")
