from enum import Enum

from fastapi import FastAPI, HTTPException
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

#Getter stations
@app.get("/stations")
def list_stations():
    return list(CraftingStation)

#Getter recipes
@app.get("/recipes")
def list_recipes() -> list[Recipe]:
    return recipes

# Search recipe for id
@app.get("/recipes/{recipe_id}")
def get_recipe(recipe_id: int) -> Recipe:
    for recipe in recipes:
        if recipe.id == recipe_id:
            return recipe
    #If recipe not found in recipes. Error 404
    raise HTTPException(status_code=404, detail="Recipe Not Found")
   
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

# Edit a recipe
@app.put("/recipes/{recipe_id}")
def update_recipe(data : RecipeCreate, recipe_id : int) -> Recipe:
    for pos, recipe in enumerate(recipes):
        if recipe.id == recipe_id:
            recipes[pos] = Recipe(
                id = recipe_id,
                name = data.name,
                result_item = data.result_item,
                result_quantity = data.result_quantity,
                crafting_station = data.crafting_station,
                ingredients = data.ingredients,
            )   
            return recipes[pos]
    raise HTTPException (status_code=404, detail="Recipe not found")

# Delete a recipe
@app.delete("/recipes/{recipe_id}")
def delete_recipe(recipe_id: int):
    for pos, recipe in enumerate(recipes):
        if recipe.id == recipe_id:
            msg = f"The recipe {recipe.name} of ID {recipe.id} deleted successfully"
            del recipes[pos]
            return msg
    raise HTTPException (status_code = 404, detail = "Recipe not found")