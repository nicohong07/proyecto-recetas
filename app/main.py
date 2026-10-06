from enum import Enum

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Recipes API")


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


recipes: list[Recipe] = []

next_recipe_id: int = 1


@app.get("/")
def root():
    return {"message": "API de Recetas!"}


@app.get("/stations")
def list_stations():
    return list(CraftingStation)


@app.get("/recipes")
def list_recipes() -> list[Recipe]:
    return recipes

# Create a recipe 
@app.post("/recipes", status_code=201)
def create_recipe(data: RecipeCreate) -> Recipe:
    global next_recipe_id
    recipe = Recipe(
        id=next_recipe_id,
        name=data.name,
        result_item=data.result_item,
        result_quantity=data.result_quantity,
        crafting_station=data.crafting_station,
        ingredients=data.ingredients,
    )
    next_recipe_id += 1
    recipes.append(recipe)
    return recipe
