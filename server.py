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
    movie_titles = []
    for rating in ratings:
        movie_titles.append(rating.movie.title)
    return render_template('user_details.html', movie_titles=movie_titles, ratings=ratings)

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
        print(new_user)
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
