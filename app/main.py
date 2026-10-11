import math

from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import text

from app import models
from app.database import Base, engine
from app.schemas import *

app = FastAPI(title="Recipes API")

Base.metadata.create_all(bind=engine)


def has_ingredient(ingredient_name: str, recipe: Recipe):
    for ingredient in recipe.ingredients:
        if ingredient_name.lower() in ingredient.item.lower():
            return True
    return False

@app.get("/")
def root():
    return {"message": "API de Recetas!"}


# Health
@app.get("/health")
def health():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


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
    item: str | None = None ,
) -> RecipePage:
    
    offset = (page-1)* page_size
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT * FROM recipes
            WHERE (CAST(:name AS TEXT) IS NULL or name ILIKE :name)
            AND (CAST(:item AS TEXT) IS NULL or EXISTS(
                SELECT 1 FROM ingredients
                WHERE recipe_id = recipes.id
                AND item ILIKE :item
            ))
            ORDER BY id ASC
            LIMIT :page_size OFFSET :offset     
                          """
        ), {"name": f"%{name}%" if name else None,
            "item": f"%{item}%" if item else None,
            "page_size": page_size,
            "offset": offset
            }
        ).mappings().all()

        total = conn.execute(text("""
            SELECT COUNT(*) FROM recipes
            WHERE (CAST(:name AS TEXT) IS NULL OR name ILIKE :name)
              AND (CAST(:item AS TEXT) IS NULL OR EXISTS (
                    SELECT 1 FROM ingredients
                    WHERE recipe_id = recipes.id
                    AND item ILIKE :item
              ))
        """), {
            "name": f"%{name}%" if name else None,
            "item": f"%{item}%" if item else None,
        }).scalar()

        

        items = []
        for row in rows:
            recipe = dict(row)

            ingredients = conn.execute(text("""
                SELECT item, quantity FROM ingredients
                WHERE recipe_id = :recipe_id
            """), {"recipe_id": recipe["id"]}
            ).mappings().all()

            list_ingredients = []
            for i in ingredients:
                list_ingredients.append(dict(i))
            recipe["ingredients"] = list_ingredients
            items.append(recipe)

             
    total_pages = math.ceil(total / page_size)

    return RecipePage(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )

@app.get("/recipes/{recipe_id}")
def get_recipe_by_id(recipe_id: int) -> Recipe:
    with engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT id, name, result_item, result_quantity, crafting_station
                FROM recipes
                WHERE id = :id
            """),
            {"id": recipe_id},
        ).mappings().first()

        if row is None:
            raise HTTPException(status_code=404, detail="Recipe Not Found")

        ingredients = conn.execute(
            text("""
                SELECT item, quantity
                FROM ingredients
                WHERE recipe_id = :id
            """),
            {"id": recipe_id},
        ).mappings().all()

    ingredients_list = []
    for i in ingredients:
        ingredients_list.append(dict(i))
    recipe = dict(row)

    recipe["ingredients"] = ingredients_list
    return recipe

@app.post("/recipes", status_code=201)
def create_recipe(data: RecipeCreate):
    with engine.begin() as conn:
        row = conn.execute(
            text("""
            INSERT INTO recipes(name, result_item, result_quantity, crafting_station)
            VALUES (:name, :result_item, :result_quantity, :crafting_station)
            RETURNING id
        """),
            {
                "name": data.name,
                "result_item": data.result_item,
                "result_quantity": data.result_quantity,
                "crafting_station": data.crafting_station.value,
            },
        )
        row_id = row.scalar()
        for ing in data.ingredients:
            conn.execute(
                text("""
                INSERT INTO ingredients(recipe_id, item, quantity)
                VALUES (:recipe_id, :item, :quantity)
            """),
                {"recipe_id": row_id, "item": ing.item, "quantity": ing.quantity},
            )
    return Recipe(
        id=row_id,
        name=data.name,
        result_item=data.result_item,
        result_quantity=data.result_quantity,
        crafting_station=data.crafting_station,
        ingredients=data.ingredients,
    )

# Edit a recipe
@app.put("/recipes/{recipe_id}")
def update_recipe(data: RecipeCreate, recipe_id:int):
    with engine.begin() as conn:
        row = conn.execute(text("""
            UPDATE recipes
            SET name = :name,
                result_item = :result_item, 
                result_quantity = :result_quantity, 
                crafting_station = :crafting_station
            WHERE id = :id
            RETURNING id
        """), { 
                "id": recipe_id,
                "name": data.name,
                "result_item": data.result_item,
                "result_quantity": data.result_quantity,
                "crafting_station": data.crafting_station.value
               }
        )
        row_id = row.scalar_one_or_none()

        if row_id is None:
            raise HTTPException(status_code = 404, detail="Recipe Not Found")
        conn.execute(text("""
            DELETE FROM ingredients
            WHERE recipe_id = :recipe_id
        """), {
                "recipe_id": row_id
              }
        )
        for ing in data.ingredients:
            conn.execute(text("""
                INSERT INTO ingredients(recipe_id, item, quantity)
                VALUES (:recipe_id, :item, :quantity)
                """), 
                {   
                    "recipe_id": row_id,
                    "item": ing.item,
                    "quantity": ing.quantity,
                }
        )
    return Recipe(
            id=row_id,
            name=data.name,
            result_item=data.result_item,
            result_quantity=data.result_quantity,
            crafting_station=data.crafting_station,
            ingredients=data.ingredients,
        )

@app.delete("/recipes/{recipe_id}")
def delete_recipe(recipe_id: int):
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM ingredients WHERE recipe_id = :id"),
            {"id": recipe_id},
        )
        row = conn.execute(
            text("DELETE FROM recipes WHERE id = :id RETURNING name"),
            {"id": recipe_id},
        )
        row_name = row.scalar_one_or_none()
        if row_name is None:
            raise HTTPException(status_code=404, detail="Recipe not found")

    return f"The recipe {row_name} of ID {recipe_id} deleted successfully"  