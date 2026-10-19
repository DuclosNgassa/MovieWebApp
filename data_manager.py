from datetime import datetime

from models import User, Movie, db
import requests

MOVIE_URL = "http://www.omdbapi.com/"


class DataManager:

    def __init__(self, db):
        self.db = db

    def create_user(self, name):
        new_user = User(name=name)
        self.db.session.add(new_user)
        self.db.session.commit()

    def get_user_by_id(self, user_id):
        user = self.db.session.scalar(
            self.db.select(User).where(User.id == user_id)
        )
        return user

    def get_movie_by_id(self, movie_id):
        movie = self.db.session.scalar(
            self.db.select(Movie).where(Movie.id == movie_id)
        )
        return movie

    def get_user_by_name(self, name):
        user = self.db.session.scalar(
            self.db.select(User).where(User.name == name)
        )
        return user

    def get_users(self):
        statement = self.db.select(User)
        users = self.db.session.scalars(statement).all()
        return users

    def get_movies(self, user_id):
        statement = self.db.select(Movie).where(Movie.user_id == user_id)
        movies = self.db.session.scalars(statement).all()
        return movies

    def add_movie(self, movie):
        self.db.session.add(movie)
        self.db.session.commit()

    def update_movie(self, movie_id, new_title):
        movie = self.db.session.get(Movie, movie_id)

        if not movie:
            print(f"Movie with ID {movie_id} not found.")
            return False

        params = {
            "t": new_title,
            "plot": "full",
            "apikey": "YOUR_API_KEY"  # Replace with your actual OMDb API key
        }

        try:
            response = requests.get(MOVIE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("Response") == "True":
                movie.title = data.get("Title")
                movie.poster = data.get("Poster")

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

    def delete_movie(self, movie_id):
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
