import math
from enum import Enum

from fastapi import FastAPI, HTTPException, Query
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

class RecipePage(BaseModel):
    items: list[Recipe]
    total: int   
    page: int
    page_size: int
    total_pages: int
    
def has_ingredient(ingredient_name: str, recipe: Recipe):
    for ingredient in recipe.ingredients:
        if ingredient_name.lower() in ingredient.item.lower():
            return True
    return False


recipes: list[Recipe] = []

next_recipe_id: int = 1


@app.get("/")
def root():
    return {"message": "API de Recetas!"}


# Getter stations
@app.get("/stations")
def list_stations():
    return list(CraftingStation)


# List recipes, filtered with name, ingredients or both. Page system
@app.get("/recipes")
def list_recipes(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    name: str | None = None,
    item: str | None = None,
) -> RecipePage:
    result = []
    for recipe in recipes:
        matches_name = name is None or name.lower() in recipe.name.lower()
        matches_ingredients = item is None or has_ingredient(item, recipe)
        if matches_ingredients and matches_name:
            result.append(recipe)
    total = len(result)
    total_pages = math.ceil(total / page_size)
    start: int = (page - 1) * page_size
    end: int = page * page_size

    return RecipePage(
        items = result[start:end],
        total = total,
        page = page,
        page_size = page_size,
        total_pages = total_pages
    )


# Search for a recipe with the id
@app.get("/recipes/{recipe_id}")
def get_recipe_by_ID(recipe_id: int) -> Recipe:
    for recipe in recipes:
        if recipe.id == recipe_id:
            return recipe
    # If recipe not found in recipes. Error 404
    raise HTTPException(status_code=404, detail="Recipe Not Found")


# # Create a recipe
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


# Edit a recipe
@app.put("/recipes/{recipe_id}")
def update_recipe(data: RecipeCreate, recipe_id: int) -> Recipe:
    for pos, recipe in enumerate(recipes):
        if recipe.id == recipe_id:
            recipes[pos] = Recipe(
                id=recipe_id,
                name=data.name,
                result_item=data.result_item,
                result_quantity=data.result_quantity,
                crafting_station=data.crafting_station,
                ingredients=data.ingredients,
            )
            return recipes[pos]
    raise HTTPException(status_code=404, detail="Recipe not found")


# Delete a recipe
@app.delete("/recipes/{recipe_id}")
def delete_recipe(recipe_id: int):
    for pos, recipe in enumerate(recipes):
        if recipe.id == recipe_id:
            msg = f"The recipe {recipe.name} of ID {recipe.id} deleted successfully"
            del recipes[pos]
            return msg
    raise HTTPException(status_code=404, detail="Recipe not found")
