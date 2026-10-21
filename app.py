import os
import requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, abort
from werkzeug.exceptions import HTTPException

from data_manager import DataManager, call_omdb_api
from models import db, Movie

app = Flask(__name__)

# Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'data/movies.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions and DB context
db.init_app(app)
#with app.app_context():
#   db.create_all()

data_manager = DataManager(db=db)


# ==================== ROUTES ====================

@app.route('/')
def index():
    """
    Home page
    """
    users = data_manager.get_all_users()
    return render_template('index.html', users=users)


@app.route('/users', methods=['POST'])
def add_user():
    """
    Endpoint for adding a user to the database
    :return: redirect to home page
    """
    name = request.form.get('name', '').strip()

    if not name:
        abort(400, description="User name cannot be empty.")

    # Check if a user with this name already exists
    existing_user = data_manager.get_user_by_name(name)

    if existing_user:
        abort(400, description=f"A user with the name '{name}' already exists.")

    try:
        data_manager.create_user(name)
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Database error while adding user: {e}")
        abort(500, description="An error occurred while saving the user to the database.")

    return redirect(url_for('index'))


@app.route('/users/<int:user_id>/movies', methods=['GET'])
def get_user_movies(user_id):
    """
    Endpoint for getting all movies associated with a user
    :param user_id:
    :return: redirect to movie page
    """
    user = data_manager.get_user_by_id(user_id)
    if not user:
        abort(404, description=f"User with ID {user_id} not found.")

    return render_template('movies.html', user=user, movies=user.movies)


@app.route('/users/<int:user_id>/movies', methods=['POST'])
def add_movie_to_user(user_id):
    """
    Endpoint for adding a movie to the database
    :param user_id: user id associated with the movie to add
    :return: redirect to movie page
    """
    user = data_manager.get_user_by_id(user_id)
    if not user:
        abort(404, description=f"User with ID {user_id} not found.")

    title = request.form.get('title', '').strip()
    if not title:
        abort(400, description="Movie title cannot be empty.")

    params = {
        "t": title,
        "plot": "full",
    }

    try:
        response = call_omdb_api(params)
        response.raise_for_status()
        data = response.json()

        if data.get("Response") == "True":
            movie_title = data.get("Title")
            director = data.get("Director")
            poster = data.get("Poster")

            # Extract year string and convert to date object
            year_str = data.get("Year", "").split("–")[0].strip()
            movie_year = datetime.strptime(year_str, "%Y").date() if year_str.isdigit() else datetime.now().date()

            new_movie = Movie(
                title=movie_title,
                poster=poster,
                year=movie_year,
                director=director,
                user_id=user_id
            )

            data_manager.add_movie(new_movie)
        else:
            error_msg = data.get('Error', 'Movie not found')
            abort(404, description=f"OMDb API Error: {error_msg}")

    except requests.exceptions.RequestException as e:
        app.logger.error(f"API request error: {e}")
        new_movie = Movie(
            title=title,
            year=datetime.now().date(),
            director="John Doe",
            user_id=user_id
        )
        data_manager.add_movie(new_movie)
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Database error while adding movie: {e}")
        abort(500, description="An error occurred while saving the movie to the database.")

    return redirect(url_for('get_user_movies', user_id=user_id))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/update', methods=['POST'])
def update_movie_title(user_id, movie_id):
    """
    Endpoint for updating a movie title. Title is passed as request parameter
    :param user_id: user associated with the movie to update
    :param movie_id: id of the movie to update
    :return: redirect to movie page
    """
    user = data_manager.get_user_by_id(user_id)
    if not user:
        abort(404, description=f"User with ID {user_id} not found.")

    movie = data_manager.get_movie_by_id(movie_id)
    if not movie or movie.user_id != user_id:
        abort(404, description=f"Movie with ID {movie_id} not found for this user.")

    new_title = request.form.get('title', '').strip()
    if not new_title:
        abort(400, description="Movie title cannot be empty.")

    try:
        movie.title = new_title
        data_manager.update_movie(movie_id, new_title)
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Database error while updating movie: {e}")
        abort(500, description="An error occurred while updating the movie title.")

    return redirect(url_for('get_user_movies', user_id=user_id))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/delete', methods=['POST'])
def delete_user_movie(user_id, movie_id):
    """
    Endpoint for deleting a movie
    :param user_id: user_id associated with the movie to delete
    :param movie_id: id of the movie to delete
    :return: redirect to movie page
    """
    user = data_manager.get_user_by_id(user_id)
    if not user:
        abort(404, description=f"User with ID {user_id} not found.")

    movie = data_manager.get_movie_by_id(movie_id)
    if not movie or movie.user_id != user_id:
        abort(404, description=f"Movie with ID {movie_id} not found for this user.")

    try:
        data_manager.delete_movie(movie_id)
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Database error while deleting movie: {e}")
        abort(500, description="An error occurred while deleting the movie.")

    return redirect(url_for('get_user_movies', user_id=user_id))


# ==================== ERROR HANDLERS ====================

@app.errorhandler(HTTPException)
def handle_http_exception(e):
    """Catches all standard HTTP exceptions (400, 404, 403, 500, etc.) and renders error.html"""
    return render_template(
        'error.html',
        error_code=e.code,
        error_title=e.name,
        error_message=e.description
    ), e.code


@app.errorhandler(Exception)
def handle_unexpected_error(e):
    """Catches unhandled Python exceptions and presents a clean 500 error page"""
    app.logger.error(f"Unexpected error: {e}", exc_info=True)
    return render_template(
        'error.html',
        error_code=500,
        error_title="Internal Server Error",
        error_message="Something unexpected went wrong on our end. Please try again later."
    ), 500


if __name__ == '__main__':
    app.run(debug=True)