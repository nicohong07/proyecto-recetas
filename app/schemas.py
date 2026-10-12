from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CraftingStation(str, Enum):
    crafting_table = "crafting_table"
    furnace = "furnace"
    smoker = "smoker"
    blast_furnace = "blast_furnace"


class Ingredient(BaseModel):
    item: str = Field(min_length=2)
    quantity: int = Field(ge=1)


class RecipeCreate(BaseModel):
    name: str = Field(min_length=2)
    result_item: str = Field(min_length=2)
    result_quantity: int = Field(default=1, ge=1)
    crafting_station: CraftingStation
    ingredients: list[Ingredient] = Field(min_length=1)


class Recipe(RecipeCreate):
    id: int

class RecipePage(BaseModel):
    items: list[Any]
    total: int   
    page: int
    page_size: int
    total_pages: int


class UserCreate(BaseModel):
    username: str = Field(min_length=5, max_length=16)
    password: str = Field(min_length = 8, max_length=64)

class User(BaseModel):
    id: int
    username:str
    
class UserInDB(User):
    hashed_password:str


class Token(BaseModel):
    access_token:str
    token_type:str = "bearer"

