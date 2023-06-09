from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


metadata = Base.metadata

users_products = Table(
    "users_products",
    metadata,
    Column("users_id", ForeignKey("users.id"), primary_key=True),
    Column("products_id", ForeignKey("products.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True, nullable=True)
    chat_id: Mapped[int] = mapped_column(unique=True, nullable=True)
    is_admin: Mapped[bool] = mapped_column(default=False)

    # Relations
    token: Mapped[SessionToken] = relationship(
        "SessionToken", uselist=False, back_populates="user"
    )
    products: Mapped[List[Product]] = relationship(
        secondary=users_products, back_populates="users"
    )

    def __str__(self):
        return f"User '{self.username}'"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_link: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str] = mapped_column(nullable=True)
    current_price: Mapped[float] = mapped_column(default=0)
    previous_price: Mapped[float] = mapped_column(default=0)
    updated_at: Mapped[datetime] = mapped_column(nullable=True)

    # Relations
    users: Mapped[List[User]] = relationship(
        secondary=users_products, back_populates="products"
    )

    def __str__(self):
        return f"Product '{self.name}'"


class SessionToken(Base):
    __tablename__ = "session_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Relations
    user: Mapped[User] = relationship("User", back_populates="token")

    def __str__(self):
        return f"Token '{self.id}'"


class UnregisteredUser(Base):
    __tablename__ = "unregistered_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True, nullable=True)
    chat_id: Mapped[int] = mapped_column(unique=True, nullable=True)

    def __str__(self):
        return f"JoinUser '{self.username}'"
