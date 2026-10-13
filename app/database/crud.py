from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.database.database import engine
from app.schemas import Recipe, RecipeCreate, User, UserInDB


def get_ingredients(conn, recipe_id) -> list[dict]:
    rows = conn.execute(text("""
        SELECT item, quantity FROM ingredients
        WHERE recipe_id = :recipe_id
    """), {"recipe_id": recipe_id}
    ).mappings().all()

    list_ingredients = []

    for ing in rows:
        list_ingredients.append(dict(ing))
    return list_ingredients

def insert_ingredients(conn, recipe_id, data:RecipeCreate):
    for ing in data.ingredients:
           conn.execute(text("""
                INSERT INTO ingredients(recipe_id, item, quantity)
                VALUES (:recipe_id, :item, :quantity)
        """), {
            "recipe_id": recipe_id,
            "item": ing.item,
            "quantity": ing.quantity
            }
        )

def get_recipe_by_id(recipe_id: int):
    with engine.connect() as conn:
        row = conn.execute(text("""
                SELECT id, name, result_item, user_id, result_quantity, crafting_station
                FROM recipes
                WHERE id = :id
         """), {
             "id": recipe_id,
             }
         ).mappings().first()
        if row is None:
            return None

        recipe = dict(row)
        recipe["ingredients"] = get_ingredients(conn, recipe_id)
    return recipe

def get_my_recipes(user_id:int) -> list[dict]:
    with engine.connect() as conn:
        rows = conn.execute(text("""
        SELECT * FROM recipes
        WHERE user_id = :user_id
        ORDER BY id
    """), {"user_id": user_id}
    ).mappings().all()

        list_my_recipes = []
        for row in rows:
            recipe = dict(row)
            recipe["ingredients"] = get_ingredients(conn, recipe["id"])
            list_my_recipes.append(recipe)
    return list_my_recipes
        
        
def list_recipes(page: int, page_size: int, name: str | None, item: str | None):
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
            recipe["ingredients"] = get_ingredients(conn, recipe["id"])


def create_recipe(data: RecipeCreate, user_id: int):
    with engine.begin() as conn:
        new_id = conn.execute(text("""
                INSERT INTO recipes(name, result_item, user_id, result_quantity, crafting_station)
                VALUES (:name, :result_item, :user_id, :result_quantity, :crafting_station)
                RETURNING id
            """), 
                {
                "name": data.name,
                "result_item": data.result_item,
                "user_id": user_id,
                "result_quantity": data.result_quantity,
                "crafting_station": data.crafting_station.value,
                }
            
            ).scalar_one()
        insert_ingredients(conn, new_id, data)
    return Recipe(
         name = data.name,
         result_item = data.result_item,
         result_quantity = data.result_quantity,
         crafting_station = data.crafting_station,
         ingredients = data.ingredients,
         id = new_id,
         user_id = user_id
    )

def update_recipe(recipe_id: int , data: RecipeCreate, user_id: int):
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
            return None
        
        conn.execute(text("""
            DELETE FROM ingredients
            WHERE recipe_id = :recipe_id
            """), {
                    "recipe_id": row_id
                    }
            )
        insert_ingredients(conn, row_id, data)

    return Recipe(
        id=row_id,
        name=data.name,
        result_item=data.result_item,
        result_quantity=data.result_quantity,
        crafting_station=data.crafting_station,
        ingredients=data.ingredients,
        user_id=user_id
    )

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

    return row_name

# USER NAME CRUD FUNCTIONS

def create_user(username: str, hashed_password: str):
    try:
        with engine.begin() as conn:
            row = conn.execute(text("""
                INSERT INTO users(username, hashed_password)
                VALUES(:username, :hashed_password)
                RETURNING id, username
                    """),       
            {
            "username": username,
           "hashed_password": hashed_password
            }
    ).mappings().one()
            row_id = row["id"]
            row_username = row["username"]
        
    except IntegrityError:
        return None
    
    return User(
                id = row_id,
                username = row_username
            )
def get_user_by_username(username: str) -> UserInDB | None:
    with engine.connect() as conn:
        row = conn.execute(text("""
                SELECT id, username, hashed_password FROM users
                WHERE username = :username
                
            """), {"username": username}
            ).mappings().one_or_none()
        
        if row is None:
            return None
        
    return UserInDB(
        id=row["id"],
        username=row["username"],
        hashed_password=row["hashed_password"]
        )
        

