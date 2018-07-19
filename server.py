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

##############################################################################
# Home Page


@app.route('/')
def index():
    """Homepage."""

    return render_template("homepage.html")


##############################################################################
# User Pages


@app.route('/users')
def user_list():
    """Show list of users"""

    users = User.query.all()
    return render_template("user_list.html", users=users)


@app.route('/users/<user_id>')
def user_detail(user_id):
    """Show a user's individual ratings and information"""

    ratings = Rating.query.filter_by(user_id=user_id)
    user = User.query.filter_by(user_id=user_id).one()

    movie_data = [(rating.movie.title, rating.score) for rating in ratings]

    return render_template('user_details.html',
                           movie_data=movie_data,
                           user=user)


##############################################################################
# Movie Pages


@app.route('/movies')
def movie_list():
    """Show list of movies"""

    movies = Movie.query.order_by(Movie.title)
    return render_template('movie_list.html', movies=movies)


@app.route('/movies/<movie_id>')
def movie_detail(movie_id):
    """Show's individual movie's rating and Eye's opinion"""

    # Get movie information and set average rating
    movie = Movie.query.get(movie_id)
    ratings = Rating.query.filter_by(movie_id=movie_id).all()

    rating_scores = [rating.score for rating in ratings]
    avg_rating = round(sum(rating_scores) / len(rating_scores), 2)

    # Check if user is logged in, and if so displays user's rating
    # or predicts user's rating
    prediction = None
    user_rating = None
    effective_rating = None

    user_id = session.get("user_id")

    if user_id:
        user = User.query.get(user_id)
        user_rating = Rating.query.filter_by(
            movie_id=movie_id, user_id=user_id).first()
        effective_rating = user_rating

        if not user_rating:
            prediction = round(user.predict_rating(movie))
            effective_rating = prediction

    # Gets a beratement from the Eye  
    beratement = get_beratement(effective_rating, movie)

    return render_template('movie_details.html',
                           movie=movie,
                           ratings=ratings,
                           user_id=user_id,
                           user_rating=user_rating,
                           avg_rating=avg_rating,
                           prediction=prediction,
                           beratement=beratement)


def get_beratement(effective_rating, movie):
    """Generates a beratement for the user based on their lack of taste"""

    # Obtain the Eye's user information
    the_eye = User.query.get('946')
    eye_rating = Rating.query.filter_by(user_id=the_eye.user_id,
                                        movie_id=movie.movie_id).first()

    # If eye has never made a rating, he will predict his opinion
    # Otherwise, he will use his previous rating
    if eye_rating is None:
        eye_rating = the_eye.predict_rating(movie)

    else:
        eye_rating = eye_rating.score

    # The eye generates a beratement based on the difference between the
    # current user's effective_rating and his own rating.
    if eye_rating and effective_rating:
        difference = abs(eye_rating - effective_rating)

    else:
        # We couldn't get an eye rating, so we'll skip difference
        difference = None

    BERATEMENT_MESSAGES = [
        "I suppose you don't have such bad taste after all.",
        "I regret every decision that I've ever made that has " +
        "brought me to listen to your opinion.",
        "Words fail me, as your taste in movies has clearly " +
        "failed you.",
        "That movie is great. For a clown to watch. Idiot.",
        "Words cannot express the awfulness of your taste."
    ]

    # Generate beratement based on difference between ratings
    # Otherwise, return None if not enough information
    if difference is not None:
        beratement = BERATEMENT_MESSAGES[int(difference)]

    else:
        beratement = None

    return beratement


@app.route('/rate-movie', methods=["POST"])
def rate_movie():
    """Send user's movie rating to database"""

    score = request.form.get("rating")
    user = request.form.get("user_id")
    movie = request.form.get("movie_id")

    # Checks to see if rating exists. If rating exists, then updates row info
    # otherwise the rating is added to the database
    try:
        rating = Rating.query.filter(
            Rating.movie_id == movie,
            Rating.user_id == user).one()

        rating.score = score
        flash("Your rating has been updated!")

    except NoResultFound:
        rating = Rating(user_id=user, movie_id=movie, score=score)

        db.session.add(rating)
        flash("Your rating has been added!")

    db.session.commit()
    return redirect('/movies/' + movie)


##############################################################################
# Registration and Login Pages


@app.route('/register', methods=["GET"])
def register_form():
    """Registration page for new users"""

    return render_template('register_form.html')


@app.route('/register', methods=["POST"])
def register_process():
    """Processes registration. Checks if user exists, if not adds to db """

    email = request.form.get("email")
    password = request.form.get("password")

    # Check to see if user exists before registering a new user
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
    """Show page to login as user"""

    return render_template('login_form.html')


@app.route('/login', methods=['POST'])
def login_process():
    """Process login request"""

    # Obtain form information
    email = request.form.get("email")
    password = request.form.get("password")

    # Make sure user actually exists
    try:
        user = User.query.filter(User.email == email).one()
    except NoResultFound:
        flash("Email not registered!")
        return redirect('/')

    # Check to make sure password is correct
    if user.password == password:
        session['user_id'] = user.user_id
        flash("User logged in!")
        return redirect('/users/' + str(user.user_id))
    else:
        flash("Incorrect password!")
        return redirect('/')


@app.route('/logout')
def logout():
    """Log out of user session"""
    
    del session['user_id']
    flash("Logged out successfully")

    return redirect('/')


##############################################################################
# Main Function


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
