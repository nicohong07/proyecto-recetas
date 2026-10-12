from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base

""""
class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))

    recipes: Mapped[list["Recipes"]] = relationship(back_populates="author")
"""

class Recipes(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    #user_id: Mapped[int] = mapped_column(ForeignKey("users.id")) 
    result_item: Mapped[str] = mapped_column(String(50))
    result_quantity: Mapped[int]
    crafting_station: Mapped[str] = mapped_column(String(50))

    #author: Mapped["Users"] = relationship(back_populates="recipes")
    ingredients: Mapped[list["Ingredients"]] = relationship(
        back_populates="recipe", 
        cascade="all, delete-orphan",
        )

class Ingredients(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"))
    item: Mapped[str] = mapped_column(String(50))
    quantity: Mapped[int] = mapped_column()

    recipe: Mapped["Recipes"] = relationship(back_populates="ingredients")