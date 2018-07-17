"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import (Flask, render_template, redirect, request, flash, session)
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.orm.exc import NoResultFound

from model import connect_to_db, db, User, Rating, Movie


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""
    return render_template("homepage.html")


@app.route('/users')
def user_list():
    """Show list of users"""

    users = User.query.all()
    return render_template("user_list.html", users=users)


@app.route('/users/<user_id>')
def user_detail(user_id):
    ratings = Rating.query.filter_by(user_id=user_id).all()
    user = User.query.filter_by(user_id=user_id).one()
    movie_data = []
    for rating in ratings:
        movie_data.append((rating.movie.title, rating.score))
    return render_template('user_details.html',
                           movie_data=movie_data,
                           user=user)


@app.route('/movies')
def movie_list():
    movies = Movie.query.order_by(Movie.title).all()
    return render_template('movie_list.html', movies=movies)


@app.route('/movies/<movie_id>')
def movie_detail(movie_id):
    movie = Movie.query.filter_by(movie_id=movie_id).one()
    ratings = Rating.query.filter_by(movie_id=movie_id).all()
    return render_template('movie_details.html', movie=movie, ratings=ratings)


@app.route('/rate-movie', methods=["POST"])
def rate_movie():
    score = request.form.get("rating")
    user = request.form.get("user_id")
    movie = request.form.get("movie_id")

    try:
        rating = Rating.query.filter(Rating.movie_id == movie, Rating.user_id == user).one()
        rating.score = score
        flash("Your rating has been updated!")
    except NoResultFound:
        rating = Rating(user_id=user, movie_id=movie, score=score)
        print(rating)
        db.session.add(rating)
        flash("Your rating has been added!")
    db.session.commit()

    return redirect('/movies')


@app.route('/register', methods=["GET"])
def register_form():
    """Registration page for new users"""
    return render_template('register_form.html')


@app.route('/register', methods=["POST"])
def register_process():
    """Processes registration. Checks if user exists, if not adds to db """
    email = request.form.get("email")
    password = request.form.get("password")

    if (User.query.filter(User.email == email).all()):
        flash("A user with that email already exists!")

    else:
        # Make a new user
        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        flash("You have successfully registered!")

    return redirect('/')


@app.route('/login')
def login_form():
    return render_template('login_form.html')


@app.route('/login', methods=['POST'])
def login_process():
    email = request.form.get("email")
    password = request.form.get("password")

    try:
        user = User.query.filter(User.email == email).one()
    except NoResultFound:
        flash("Email not registered!")
        return redirect('/')

    if user.password == password:
        session['user_id'] = user.user_id
        flash("User logged in!")
        return redirect('/users/' + str(user.user_id))
    else:
        flash("Incorrect password!")
        return redirect('/')


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully")

    return redirect('/')


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    # make sure templates, etc. are not cached in debug mode
    app.jinja_env.auto_reload = app.debug

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
