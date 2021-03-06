"""Models and database functions for Ratings project."""

from flask_sqlalchemy import SQLAlchemy
from correlation import pearson

# This is the connection to the PostgreSQL database; we're getting this through
# the Flask-SQLAlchemy helper library. On this, we can find the `session`
# object, where we do m st of our interactions (like committing, etc.)

db = SQLAlchemy()


##############################################################################
# Model definitions

class User(db.Model):
    """User of ratings website."""

    __tablename__ = "users"

    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    email = db.Column(db.String(64), nullable=True)
    password = db.Column(db.String(64), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    zipcode = db.Column(db.String(15), nullable=True)

    def __repr__(self):
        """Provide helpful representation when printed."""

        return f"<User user_id={self.user_id} email={self.email}>"

    def similarity(self, other):
        user_ratings = {}
        paired_ratings = []

        # Keys are the movie_id's for all ratings from self
        # Values are the rating

        for rating in self.ratings:
            user_ratings[rating.movie_id] = rating

        # Pair up self's rating of a unique movie with other's rating for it

        for rating in other.ratings:
            has_rated = user_ratings.get(rating.movie_id)
            if has_rated:
                paired_ratings.append((has_rated.score, rating.score))

        if paired_ratings:
            return pearson(paired_ratings)
        else:
            return 0.0

    def predict_rating(self, movie):
        """Predict user's rating of the movie."""

        other_ratings = movie.ratings

        similarities = [(self.similarity(rating.user), rating.score)
                        for rating in other_ratings
                        if self.similarity(rating.user) > 0]

        similarities.sort(key=lambda x: x[0], reverse=True)

        if not similarities:
            return None

        numerator = sum([score * sim for sim, score in similarities])
        denominator = sum([sim for sim, rating in similarities])

        return numerator/denominator


# Put your Movie and Rating model classes here.


class Movie(db.Model):
    """Movie of ratings website."""

    __tablename__ = "movies"

    movie_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    title = db.Column(db.String(100), nullable=True)
    released_at = db.Column(db.DateTime, nullable=True)
    imdb_url = db.Column(db.String, nullable=True)

    def __repr__(self):
        """Provide helpful representation when printed."""

        return f"""<Movie movie_id={self.movie_id}
                   title={self.title}
                   released_at={self.released_at}
                   imdb_url={self.imdb_url}>"""


class Rating(db.Model):
    """Rating of ratings website."""

    __tablename__ = "ratings"

    rating_id = db.Column(db.Integer,
                          autoincrement=True,
                          primary_key=True)
    movie_id = db.Column(db.Integer,
                         db.ForeignKey('movies.movie_id'))
    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.user_id'))
    score = db.Column(db.Integer)

    user = db.relationship("User",
                           backref=db.backref("ratings", order_by=rating_id))

    movie = db.relationship("Movie",
                            backref=db.backref("ratings", order_by=rating_id))

    def __repr__(self):
        """Provide helpful representation when printed."""

        return f"""<Rating rating_id={self.rating_id}
                   movie_id={self.movie_id}
                   user_id={self.user_id}
                   score={self.score}>"""

##############################################################################
# Helper functions


def connect_to_db(app):
    """Connect the database to our Flask app."""

    # Configure to use our PstgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///ratings'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.app = app
    db.init_app(app)


if __name__ == "__main__":
    # As a convenience, if we run this module interactively, it will leave
    # you in a state of being able to work with the database directly.

    from server import app
    connect_to_db(app)
    print("Connected to DB.")