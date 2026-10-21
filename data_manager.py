from datetime import datetime
from typing import Any

from requests import Response

from models import User, Movie
import requests
import os
from dotenv import load_dotenv

load_dotenv()

OMDB_API_KEY = os.getenv('OMDB_API_KEY')

MOVIE_URL = "http://www.omdbapi.com/"


def call_omdb_api(params: dict[str, str | None | Any]) -> Response:
    """
    Helper function for calling OMDB API.
    """
    params["apikey"] = OMDB_API_KEY
    return requests.get(MOVIE_URL, params=params)


class DataManager:

    def __init__(self, db):
        self.db = db

    def create_user(self, name) -> None:
        """
        Creates a user with given name.
        :param name:
        :return: None
        """
        new_user = User(name=name)
        self.db.session.add(new_user)
        self.db.session.commit()

    def get_user_by_id(self, user_id) -> User | None:
        """
        Gets a user with given ID.
        :param user_id:
        :return: User found or None
        """
        user = self.db.session.scalar(
            self.db.select(User).where(User.id == user_id)
        )
        return user

    def get_user_by_name(self, name) -> User | None:
        """
        Gets a user with given name.
        :param name:
        :return: User found or None
        """
        user = self.db.session.scalar(
            self.db.select(User).where(User.name == name)
        )
        return user

    def get_all_users(self) -> list[User]:
        """
        Gets all users.
        :return: list of users
        """
        statement = self.db.select(User)
        users = self.db.session.scalars(statement).all()
        return users

    def get_movie_by_id(self, movie_id) -> Movie | None:
        """
        Gets a movie with given ID.
        :param movie_id:
        :return: Movie found or None
        """
        movie = self.db.session.scalar(
            self.db.select(Movie).where(Movie.id == movie_id)
        )
        return movie

    def get_all_user_movies(self, user_id) -> list[Movie]:
        """
        Gets all movies of a user.
        :param user_id:
        :return: all movies of the given user by user_id
        """
        statement = self.db.select(Movie).where(Movie.user_id == user_id)
        movies = self.db.session.scalars(statement).all()
        return movies

    def add_movie(self, movie) -> None:
        """
        Adds a movie to the database.
        :param movie:
        :return: None
        """
        self.db.session.add(movie)
        self.db.session.commit()

    def update_movie(self, movie_id, new_title) -> bool:
        """
        Updates a movie with the given ID.
        :param movie_id:
        :param new_title:
        :return: True if the movie was updated successfully, False otherwise
        """
        movie = self.db.session.get(Movie, movie_id)

        if not movie:
            print(f"Movie with ID {movie_id} not found.")
            return False

        params = {
            "t": new_title,
            "plot": "full",
        }

        try:
            response = call_omdb_api(params)
            response.raise_for_status()
            data = response.json()

            if data.get("Response") == "True":
                movie.title = data.get("Title")
                movie.poster = data.get("Poster")
                movie.director = data.get("Director")

                year_str = data.get("Year", "").split("–")[0].strip()
                if year_str.isdigit():
                    movie.year = datetime.strptime(year_str, "%Y").date()

                self.db.session.commit()
                print(f"Movie ID {movie_id} successfully updated to '{movie.title}'.")
                return True
            else:
                print(f"Error from OMDb API: {data.get('Error', 'Movie not found')}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"An error occurred during the API request: {e}")
            movie.title = new_title
            self.db.session.commit()

            return True

    def delete_movie(self, movie_id) -> bool:
        """
        Deletes a movie from the database.
        :param movie_id:
        :return: True if the movie was deleted successfully, False otherwise
        """
        movie = self.db.session.get(Movie, movie_id)

        if not movie:
            print(f"Movie with ID {movie_id} not found.")
            return False

        try:
            self.db.session.delete(movie)

            self.db.session.commit()
            print(f"Movie ID {movie_id} successfully deleted from favorites.")
            return True

        except Exception as e:
            # Rollback the session in case of unexpected database errors
            self.db.session.rollback()
            print(f"An error occurred while deleting the movie: {e}")
            return False
