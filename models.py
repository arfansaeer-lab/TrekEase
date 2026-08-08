from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(100), unique=True, nullable=False)

    password = db.Column(db.String(100), nullable=False)

    is_admin = db.Column(db.Boolean, default=False)

    is_blacklisted = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return self.name

class Trek(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    location = db.Column(db.String(100), nullable=False)

    duration = db.Column(db.String(50), nullable=False)

    price = db.Column(db.Integer, nullable=False)

    difficulty = db.Column(db.String(50), nullable=False)

    seats = db.Column(db.Integer, nullable=False)

    description = db.Column(db.Text, nullable=False)

    status = db.Column(
        db.String(20),
        default="Open"
    )

    start_date = db.Column(
        db.Date,
        nullable=True
    )

    end_date = db.Column(
        db.Date,
        nullable=True
    )

    staff = db.relationship(
        "Staff",
        backref="trek",
        lazy=True
    )


class Booking(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

    trek_id = db.Column(
        db.Integer,
        db.ForeignKey('trek.id'),
        nullable=False
    )

    booking_date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
    status = db.Column(
        db.String(20),
        default="Booked"
    )

    user = db.relationship(
        'User',
        backref='bookings'
    )

    trek = db.relationship(
        'Trek',
        backref='bookings'
    )
    

class Staff(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(100), unique=True, nullable=False)

    password = db.Column(db.String(100), nullable=False)

    is_blacklisted = db.Column(
        db.Boolean,
        default=False
    )

    assigned_trek_id = db.Column(
        db.Integer,
        db.ForeignKey("trek.id")
    )