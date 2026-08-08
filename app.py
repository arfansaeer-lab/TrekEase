from flask import Flask, render_template, request, redirect, url_for, session, flash
from sqlalchemy import or_
from config import Config
from models import db, User, Trek, Booking, Staff
from flask_login import LoginManager
from flask_login import login_user
from flask_login import login_required, current_user
from flask_login import logout_user

app = Flask(__name__)

login_manager = LoginManager()

login_manager.init_app(app)
login_manager.login_message = None
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):

    if session.get("role") == "staff":
        return Staff.query.get(int(user_id))

    return User.query.get(int(user_id))

app.config.from_object(Config)

db.init_app(app)


@app.route("/")
def home():

    if not current_user.is_authenticated:
        return redirect(url_for("login"))

    if session.get("role") == "staff":
        return redirect(url_for("staff_dashboard"))

    if current_user.is_admin:
        return redirect(url_for("dashboard"))


    treks = Trek.query

    search = request.args.get("search", "")
    difficulty = request.args.get("difficulty", "")
    location = request.args.get("location", "")


    if search:
        treks = treks.filter(
            Trek.name.ilike(f"%{search}%")
        )


    if difficulty:
        treks = treks.filter(
            Trek.difficulty == difficulty
        )


    if location:
        treks = treks.filter(
            Trek.location.ilike(f"%{location}%")
        )


    treks = treks.all()


    return render_template(
        "index.html",
        treks=treks,
        search=search,
        difficulty=difficulty,
        location=location
    )

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        admin = User.query.filter_by(
            email=email,
            is_admin=True
        ).first()

        if admin and admin.password == password:
            login_user(admin)
            session["role"] = "admin"
            return redirect(url_for("dashboard"))

        # -----------------------
        # Selected Role
        # -----------------------

        role = request.form.get("role")

        if role == "user":

            user = User.query.filter_by(
                email=email,
                is_admin=False
            ).first()

            if user and user.is_blacklisted:
                flash("Your account has been blacklisted.", "danger")
                return redirect(url_for("login"))

            if user and user.password == password:
                login_user(user)
                session["role"] = "user"
                return redirect(url_for("home"))

        elif role == "staff":

            staff = Staff.query.filter_by(
                email=email
            ).first()

            if staff and staff.is_blacklisted:
                flash("Your staff account has been blacklisted.", "danger")
                return redirect(url_for("login"))

            if staff and staff.password == password:
                login_user(staff)
                session["role"] = "staff"
                return redirect(url_for("staff_dashboard"))

        flash("Invalid Email or Password.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():

    if not current_user.is_admin:
        return redirect(url_for("home"))

    total_users = User.query.filter_by(is_admin=False).count()

    total_staff = Staff.query.count()

    total_treks = Trek.query.count()

    total_bookings = Booking.query.count()

    latest_bookings = Booking.query.order_by(
        Booking.booking_date.desc()
    ).limit(5).all()

    return render_template(
        "dashboard.html",
        total_users=total_users,
        total_staff=total_staff,
        total_treks=total_treks,
        total_bookings=total_bookings,
        bookings=latest_bookings
    )
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        if not name or not email or not password:
            return "Please fill in all the fields."

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            return "Email already registered!"

        new_user = User(
            name=name,
            email=email,
            password=password,
            is_admin=False
)

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("home"))

    return render_template("register.html")

# @app.route("/dashboard/<int:user_id>")
# def dashboard(user_id):

#     user = User.query.get(user_id)

#     return render_template(
#         "dashboard.html",
#         user=user
#     )

@app.route("/logout")
@login_required
def logout():

    logout_user()
    session.pop("role", None)

    return redirect(url_for("home"))

@app.route("/add_trek", methods=["GET", "POST"])
@login_required
def add_trek():

    if not current_user.is_admin:
        return redirect(url_for("home"))

    if request.method == "POST":

        trek = Trek(
            name=request.form["name"],
            location=request.form["location"],
            duration=request.form["duration"],
            price=int(request.form["price"]),
            difficulty=request.form["difficulty"],
            seats=int(request.form["seats"]),
            description=request.form["description"],
            status=request.form["status"]
        )

        db.session.add(trek)
        db.session.commit()

        return redirect(url_for("home"))

    return render_template("add_trek.html")

@app.route("/edit_trek/<int:trek_id>", methods=["GET", "POST"])
@login_required
def edit_trek(trek_id):

    if not current_user.is_admin:
        return redirect(url_for("home"))

    trek = Trek.query.get_or_404(trek_id)

    if request.method == "POST":

        trek.name = request.form["name"]
        trek.location = request.form["location"]
        trek.duration = request.form["duration"]
        trek.price = int(request.form["price"])
        trek.difficulty = request.form["difficulty"]
        trek.seats = int(request.form["seats"])
        trek.description = request.form["description"]
        trek.status = request.form["status"]

        db.session.commit()

        return redirect(url_for("home"))

    return render_template("edit_trek.html", trek=trek)

@app.route("/delete_trek/<int:trek_id>")
@login_required
def delete_trek(trek_id):

    if not current_user.is_admin:
        return redirect(url_for("home"))

    trek = Trek.query.get_or_404(trek_id)

    db.session.delete(trek)
    db.session.commit()

    return redirect(url_for("home"))

@app.route("/manage_treks")
@login_required
def manage_treks():

    if not current_user.is_admin:
        return redirect(url_for("home"))

    treks = Trek.query.all()

    return render_template(
        "manage_treks.html",
        treks=treks
    )

@app.route("/book/<int:trek_id>")
@login_required
def book(trek_id):

    trek = Trek.query.get(trek_id)

    if trek.status != "Open":
        return "This trek is currently not open for booking."

    if trek.seats <= 0:
        return "No seats available!"

    existing_booking = Booking.query.filter_by(
        user_id=current_user.id,
        trek_id=trek.id
    ).first()

    if existing_booking:
        return "You have already booked this trek."

    booking = Booking(
        trek_id=trek.id,
        user_id=current_user.id,
        status="Booked"
    )

    trek.seats -= 1

    db.session.add(booking)
    db.session.commit()

    return redirect(url_for("home"))

@app.route("/add_staff", methods=["GET", "POST"])
@login_required
def add_staff():

    if not current_user.is_admin:
        return redirect(url_for("home"))

    if request.method == "POST":

        staff = Staff(
            name=request.form["name"],
            email=request.form["email"],
            password=request.form["password"]
        )

        db.session.add(staff)
        db.session.commit()

        return redirect(url_for("manage_staff"))

    return render_template("add_staff.html")

@app.route("/manage_staff")
@login_required
def manage_staff():

    if not current_user.is_admin:
        return redirect(url_for("home"))

    staff_members = Staff.query.all()

    return render_template(
        "manage_staff.html",
        staff_members=staff_members
    )

@app.route("/assign_trek/<int:staff_id>", methods=["GET", "POST"])
@login_required
def assign_trek(staff_id):

    if not current_user.is_admin:
        return redirect(url_for("home"))

    staff = Staff.query.get_or_404(staff_id)

    treks = Trek.query.all()

    if request.method == "POST":

        staff.assigned_trek_id = request.form["trek_id"]

        db.session.commit()

        return redirect(url_for("manage_staff"))

    return render_template(
        "assign_trek.html",
        staff=staff,
        treks=treks
    )


@app.route("/delete_staff/<int:staff_id>")
@login_required
def delete_staff(staff_id):

    if not current_user.is_admin:
        return redirect(url_for("home"))

    staff = Staff.query.get_or_404(staff_id)

    db.session.delete(staff)
    db.session.commit()

    return redirect(url_for("manage_staff"))


@app.route("/my_bookings")
@login_required
def my_bookings():

    bookings = Booking.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template(
        "my_bookings.html",
        bookings=bookings
    )

@app.route("/users")
@login_required
def users():

    if not current_user.is_admin:
        return redirect(url_for("home"))

    users = User.query.filter_by(is_admin=False).all()

    return render_template(
        "users.html",
        users=users
    )

@app.route("/unblacklist/<int:user_id>")
@login_required
def unblacklist_user(user_id):

    if not current_user.is_admin:
        return redirect(url_for("home"))

    user = User.query.get_or_404(user_id)

    user.is_blacklisted = False

    db.session.commit()

    return redirect(url_for("users"))

@app.route("/blacklist/<int:user_id>")
@login_required
def blacklist_user(user_id):

    if not current_user.is_admin:
        return redirect(url_for("home"))

    user = User.query.get_or_404(user_id)

    user.is_blacklisted = True

    db.session.commit()

    return redirect(url_for("users"))

@app.route("/blacklist_staff/<int:staff_id>")
@login_required
def blacklist_staff(staff_id):

    if not current_user.is_admin:
        return redirect(url_for("home"))

    staff = Staff.query.get_or_404(staff_id)

    staff.is_blacklisted = True

    db.session.commit()

    return redirect(url_for("manage_staff"))


@app.route("/unblacklist_staff/<int:staff_id>")
@login_required
def unblacklist_staff(staff_id):

    if not current_user.is_admin:
        return redirect(url_for("home"))

    staff = Staff.query.get_or_404(staff_id)

    staff.is_blacklisted = False

    db.session.commit()

    return redirect(url_for("manage_staff"))

@app.route("/staff_dashboard")
@login_required
def staff_dashboard():

    assigned_trek = Trek.query.get(
        current_user.assigned_trek_id
    )

    participants = []

    if assigned_trek:

        participants = Booking.query.filter_by(
            trek_id=assigned_trek.id
        ).all()

    return render_template(
        "staff_dashboard.html",
        staff=current_user,
        trek=assigned_trek,
        participants=participants
    )

@app.route("/staff_treks")
@login_required
def staff_treks():

    if session.get("role") != "staff":
        return redirect(url_for("home"))

    treks = Trek.query.all()

    return render_template(
        "staff_treks.html",
        treks=treks
    )


@app.route("/update_trek_status", methods=["POST"])
@login_required
def update_trek_status():

    if session.get("role") != "staff":
        return redirect(url_for("home"))

    trek = Trek.query.get(current_user.assigned_trek_id)

    trek.status = request.form["status"]

    db.session.commit()

    return redirect(url_for("staff_dashboard"))

@app.route("/update_slots", methods=["POST"])
@login_required
def update_slots():

    if session.get("role") != "staff":
        return redirect(url_for("home"))

    trek = Trek.query.get(current_user.assigned_trek_id)

    trek.seats = int(request.form["seats"])

    db.session.commit()

    return redirect(url_for("staff_dashboard"))

@app.route("/search", methods=["GET"])
@login_required
def search():

    if not current_user.is_admin:
        return redirect(url_for("home"))

    query = request.args.get("query", "").strip()

    users = []
    staff = []
    treks = []

    if query:

        users = User.query.filter(
            or_(
                User.name.ilike(f"%{query}%"),
                User.id == int(query) if query.isdigit() else False
            ),
            User.is_admin == False
        ).all()

        staff = Staff.query.filter(
            or_(
                Staff.name.ilike(f"%{query}%"),
                Staff.id == int(query) if query.isdigit() else False
            )
        ).all()

        treks = Trek.query.filter(
            or_(
                Trek.name.ilike(f"%{query}%"),
                Trek.id == int(query) if query.isdigit() else False
            )
        ).all()

    return render_template(
        "search.html",
        query=query,
        users=users,
        staff=staff,
        treks=treks
    )

@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():

    if current_user.is_admin:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        current_user.name = request.form["name"]
        current_user.email = request.form["email"]
        current_user.password = request.form["password"]

        db.session.commit()

        return redirect(url_for("home"))

    return render_template("edit_profile.html")


if __name__ == "__main__":

    with app.app_context():

        db.create_all()

        admin = User.query.filter_by(
            email="admin@gmail.com"
        ).first()

        if admin is None:

            admin = User(
                name="Admin",
                email="admin@gmail.com",
                password="admin123",
                is_admin=True
            )

            db.session.add(admin)
            db.session.commit()

    app.run(host="0.0.0.0", port=5000, debug=True)