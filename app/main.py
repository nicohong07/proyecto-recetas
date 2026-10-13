import math

from fastapi import Depends, FastAPI, Form, HTTPException, Query

from app import models
from app.core import security
from app.database import crud
from app.database.database import Base, engine
from app.schemas import *

tags_metadata = [
    {"name": "Auth", "description": "Registration and Login"},
    {"name": "Saved Recipes", "description": "Look for all recipes in the Database"},
    {"name": "Recipes", "description": "Create, update and delete recipes"},
    {"name": "Users", "description": "Check your data"},
    {"name": "Stations", "description": "Available stations for crafting"},
]

app = FastAPI(title="Recipes API", openapi_tags=tags_metadata)

Base.metadata.create_all(bind=engine)


# ---------- Auth ----------

# Create a user endpoint
@app.post("/auth/register", status_code=201, tags=["Auth"])
def create_user(data: UserCreate) -> User:
    hashed_password = security.get_password_hash(data.password)

    user = crud.create_user(data.username, hashed_password)

    if user is None:
        raise HTTPException(status_code=409, detail="Username already exists")
    return user


# Login endpoint
@app.post("/auth/login", tags=["Auth"])
def login(username: str = Form(), password: str = Form()) -> Token:
    user = crud.get_user_by_username(username)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Incorrect Username or Password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    is_correct = security.verify_password(password, user.hashed_password)

    if not is_correct:
        raise HTTPException(
            status_code=401,
            detail="Incorrect Username or Password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = security.create_access_token(user.id)

    return Token(access_token=token)


# ---------- Saved Recipes (public) ----------

# List recipes, filtered with name, ingredients or both. Page system
@app.get("/recipes", tags=["Saved Recipes"])
def list_recipes(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    name: str | None = None,
    item: str | None = None,
) -> RecipePage:
    items, total = crud.list_recipes(page, page_size, name, item)

    return RecipePage(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size),
    )


# Get recipe by id endpoint
@app.get("/recipes/{recipe_id}", tags=["Saved Recipes"])
def get_recipe_by_id(recipe_id: int) -> Recipe:
    recipe = crud.get_recipe_by_id(recipe_id)

    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe Not Found")

    return recipe


# ---------- Recipes (authenticated) ----------

# Create a recipe endpoint
@app.post("/recipes", status_code=201, tags=["Recipes"])
def create_recipe(data: RecipeCreate, user_id: int = Depends(security.get_current_user)) -> Recipe:
    recipe = crud.create_recipe(data, user_id)

    return recipe


# Edit a recipe
@app.put("/recipes/{recipe_id}", tags=["Recipes"])
def update_recipe(recipe_id: int, data: RecipeCreate, user_id: int = Depends(security.get_current_user)) -> Recipe:
    recipe = crud.get_recipe_by_id(recipe_id)

    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe Not Found")

    if recipe["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="You can't edit other users' recipes")

    recipe = crud.update_recipe(recipe_id, data, user_id)

    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe Not Found")

    return recipe


# Delete a recipe
@app.delete("/recipes/{recipe_id}", tags=["Recipes"])
def delete_recipe(recipe_id: int, user_id: int = Depends(security.get_current_user)):
    recipe = crud.get_recipe_by_id(recipe_id)

    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe Not Found")

    if recipe["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="You can't delete other users' recipes")

    row_name = crud.delete_recipe(recipe_id)

    if row_name is None:
        raise HTTPException(status_code=404, detail="Recipe Not Found")

    return f"The recipe {row_name} of ID {recipe_id} deleted successfully"


# ---------- Users ----------

# Get my recipes endpoint
@app.get("/users/me/recipes", tags=["Users"])
def get_my_recipes(user_id: int = Depends(security.get_current_user)) -> list[Recipe]:
    return crud.get_my_recipes(user_id)


# ---------- Stations ----------

# Getter stations
@app.get("/stations", tags=["Stations"])
def list_stations():
    return list(CraftingStation)