from __future__ import annotations  # <-- Crucial fix for forward referencing Movie inside User

from datetime import date
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

db = SQLAlchemy()


class User(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), unique=False, nullable=False)
    movies: Mapped[list[Movie]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.id}: {self.name!r}>"

    def __str__(self):
        return f"User: ID: {self.id}, Name: {self.name}"


class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(80), unique=False, nullable=False)
    director: Mapped[str] = mapped_column(String(80), unique=False, nullable=False)
    poster: Mapped[str] = mapped_column(String(500), unique=True, nullable=True)
    year: Mapped[date] = mapped_column(Date, unique=False, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), nullable=False)
    user: Mapped["User"] = relationship(back_populates="movies")

    def __repr__(self):
        return f"<Movie {self.id}: {self.title!r}>"

    def __str__(self):
        return f"User: ID: {self.id}, Title: {self.title}, Poster: {self.poster}, Year: {self.year}, user_id: {self.user_id}"