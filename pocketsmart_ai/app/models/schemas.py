from typing import Literal
from pydantic import BaseModel, Field, EmailStr, field_validator

PlannerType = Literal["home", "party", "jewelry"]

class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr

class HomeItem(BaseModel):
    category: str
    quantity: int = Field(ge=1, le=50)
    notes: str = ""

class HomeRequest(BaseModel):
    budget: float = Field(gt=0, le=10_000_000)
    room: str = Field(min_length=2, max_length=80)
    style: str = Field(default="modern", max_length=80)
    items: list[HomeItem] = Field(min_length=1, max_length=20)

class PartyRequest(BaseModel):
    budget: float = Field(gt=0, le=10_000_000)
    guests: int = Field(ge=1, le=5000)
    event_type: str = Field(min_length=2, max_length=80)
    venue: str = Field(default="indoor", max_length=100)
    city: str = Field(default="", max_length=100)
    food_preference: str = Field(default="mixed", max_length=100)

class JewelryRequest(BaseModel):
    budget: float = Field(gt=0, le=10_000_000)
    occasion: str = Field(min_length=2, max_length=80)
    style: str = Field(default="elegant", max_length=80)
    outfit_color: str = Field(default="", max_length=80)
    material: str = Field(default="any", max_length=80)

class RecommendationItem(BaseModel):
    name: str
    category: str
    platform: str
    price: float = Field(ge=0)
    reason: str
    url: str
    budget_fit: str = "within budget"

class RecommendationResponse(BaseModel):
    planner: PlannerType
    budget: float
    summary: str
    allocations: dict[str, float] = {}
    recommendations: list[RecommendationItem] = []
    tips: list[str] = []
    source: str = "fallback"
