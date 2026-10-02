from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_from_directory,
    flash,
    abort
)

import sqlite3
import os
import uuid
import random
import time

from functools import wraps

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from werkzeug.utils import secure_filename


# =========================================================
# APPLICATION
# =========================================================

app = Flask(__name__)


# =========================================================
# ENVIRONMENT
# =========================================================

ENV = os.environ.get(
    "FLASK_ENV",
    "development"
).lower()

IS_PRODUCTION = ENV == "production"


# =========================================================
# SECRET KEY
# =========================================================

SECRET_KEY = os.environ.get(
    "SECRET_KEY"
)

if not SECRET_KEY:

    if IS_PRODUCTION:

        raise RuntimeError(
            "SECRET_KEY must be set in production."
        )

    SECRET_KEY = (
        "smartplot-development-secret-key"
    )


app.secret_key = SECRET_KEY


# =========================================================
# SESSION SECURITY
# =========================================================

app.config["SESSION_COOKIE_HTTPONLY"] = True

app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

app.config["SESSION_COOKIE_SECURE"] = (
    IS_PRODUCTION
)

app.config["PERMANENT_SESSION_LIFETIME"] = (
    60 * 60 * 8
)


# =========================================================
# REQUEST SIZE
# =========================================================

app.config["MAX_CONTENT_LENGTH"] = (
    10 * 1024 * 1024
)


# =========================================================
# BASE PATHS
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


DATABASE_DIR = os.path.join(
    BASE_DIR,
    "database"
)


DATABASE = os.path.join(
    DATABASE_DIR,
    "smartplot.db"
)


UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads",
    "plots"
)


app.config["UPLOAD_FOLDER"] = (
    UPLOAD_FOLDER
)


# =========================================================
# ALLOWED IMAGE TYPES
# =========================================================

ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp"
}


# =========================================================
# CREATE DIRECTORIES
# =========================================================

os.makedirs(
    DATABASE_DIR,
    exist_ok=True
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():

    connection = sqlite3.connect(
        DATABASE,
        timeout=10
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def create_database():

    conn = get_db_connection()

    cursor = conn.cursor()


    # =====================================================
    # USERS
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT NOT NULL UNIQUE,

            phone TEXT NOT NULL,

            password TEXT NOT NULL,

            role TEXT NOT NULL
                CHECK (
                    role IN (
                        'buyer',
                        'seller'
                    )
                )

        )
    """)


    # =====================================================
    # PLOTS
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plots (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            title TEXT NOT NULL,

            location TEXT NOT NULL,

            area REAL NOT NULL,

            price REAL NOT NULL,

            road_width REAL,

            property_type TEXT,

            facing TEXT,

            landmark TEXT,

            description TEXT,

            status TEXT DEFAULT 'available'
                CHECK (
                    status IN (
                        'available',
                        'reserved',
                        'sold'
                    )
                ),

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE

        )
    """)


    # =====================================================
    # MIGRATION FOR OLD DATABASES
    # =====================================================

    columns = cursor.execute(
        "PRAGMA table_info(plots)"
    ).fetchall()


    column_names = {
        column["name"]
        for column in columns
    }


    if "landmark" not in column_names:

        cursor.execute("""
            ALTER TABLE plots
            ADD COLUMN landmark TEXT
        """)


    # =====================================================
    # PLOT IMAGES
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plot_images (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            plot_id INTEGER NOT NULL,

            filename TEXT NOT NULL,

            FOREIGN KEY (plot_id)
                REFERENCES plots(id)
                ON DELETE CASCADE

        )
    """)


    # =====================================================
    # FAVORITES
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorites (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            plot_id INTEGER NOT NULL,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            UNIQUE (
                user_id,
                plot_id
            ),

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY (plot_id)
                REFERENCES plots(id)
                ON DELETE CASCADE

        )
    """)


    # =====================================================
    # INQUIRIES
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inquiries (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            buyer_id INTEGER NOT NULL,

            seller_id INTEGER NOT NULL,

            plot_id INTEGER NOT NULL,

            message TEXT NOT NULL,

            status TEXT DEFAULT 'new'
                CHECK (
                    status IN (
                        'new',
                        'read'
                    )
                ),

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (buyer_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY (seller_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY (plot_id)
                REFERENCES plots(id)
                ON DELETE CASCADE

        )
    """)


    conn.commit()

    conn.close()


# =========================================================
# SECURITY HEADERS
# =========================================================

@app.after_request
def add_security_headers(response):

    response.headers[
        "X-Content-Type-Options"
    ] = "nosniff"


    response.headers[
        "X-Frame-Options"
    ] = "SAMEORIGIN"


    response.headers[
        "Referrer-Policy"
    ] = (
        "strict-origin-when-cross-origin"
    )


    response.headers[
        "Permissions-Policy"
    ] = (
        "geolocation=(self), "
        "microphone=(), "
        "camera=()"
    )


    response.headers[
        "Content-Security-Policy"
    ] = (
        "default-src 'self'; "
        "img-src 'self' data: https:; "
        "style-src 'self' 'unsafe-inline' https:; "
        "script-src 'self' 'unsafe-inline'; "
        "font-src 'self' https:; "
        "connect-src 'self'; "
        "frame-ancestors 'self';"
    )


    if IS_PRODUCTION:

        response.headers[
            "Strict-Transport-Security"
        ] = (
            "max-age=31536000; "
            "includeSubDomains"
        )


    return response


# =========================================================
# LOGIN DECORATOR
# =========================================================

def login_required(view):

    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if "user_id" not in session:

            return redirect(
                url_for("login")
            )

        return view(
            *args,
            **kwargs
        )

    return wrapped_view


# =========================================================
# ROLE DECORATOR
# =========================================================

def role_required(role):

    def decorator(view):

        @wraps(view)
        def wrapped_view(
            *args,
            **kwargs
        ):

            if "user_id" not in session:

                return redirect(
                    url_for("login")
                )


            if session.get(
                "user_role"
            ) != role:

                return redirect(
                    url_for("dashboard")
                )


            return view(
                *args,
                **kwargs
            )

        return wrapped_view

    return decorator


# =========================================================
# IMAGE VALIDATION
# =========================================================

def allowed_file(filename):

    if not filename:

        return False


    if "." not in filename:

        return False


    extension = (
        filename
        .rsplit(".", 1)[1]
        .lower()
    )


    return extension in ALLOWED_EXTENSIONS


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# =========================================================
# SIGNUP
# =========================================================

@app.route(
    "/signup",
    methods=["GET", "POST"]
)
def signup():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()


        email = request.form.get(
            "email",
            ""
        ).strip().lower()


        phone = request.form.get(
            "phone",
            ""
        ).strip()


        password = request.form.get(
            "password",
            ""
        )


        role = request.form.get(
            "role",
            ""
        ).strip().lower()


        if (
            not name
            or not email
            or not phone
            or not password
            or not role
        ):

            return render_template(
                "signup.html",
                error=(
                    "Please fill all fields."
                )
            )


        if role not in (
            "buyer",
            "seller"
        ):

            return render_template(
                "signup.html",
                error=(
                    "Invalid account type."
                )
            )


        if len(password) < 6:

            return render_template(
                "signup.html",
                error=(
                    "Password must contain "
                    "at least 6 characters."
                )
            )


        hashed_password = (
            generate_password_hash(
                password
            )
        )


        conn = get_db_connection()


        try:

            conn.execute("""
                INSERT INTO users
                (
                    name,
                    email,
                    phone,
                    password,
                    role
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                name,
                email,
                phone,
                hashed_password,
                role
            ))


            conn.commit()


        except sqlite3.IntegrityError:

            conn.close()


            return render_template(
                "signup.html",
                error=(
                    "Email already exists."
                )
            )


        conn.close()


        flash(
            "Account created successfully. "
            "Please login.",
            "success"
        )


        return redirect(
            url_for("login")
        )


    return render_template(
        "signup.html"
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()


        password = request.form.get(
            "password",
            ""
        )


        conn = get_db_connection()


        user = conn.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (
            email,
        )).fetchone()


        conn.close()


        if user and check_password_hash(
            user["password"],
            password
        ):

            session.clear()


            session["user_id"] = (
                user["id"]
            )


            session["user_name"] = (
                user["name"]
            )


            session["user_role"] = (
                user["role"]
            )


            session.permanent = True


            return redirect(
                url_for("dashboard")
            )


        return render_template(
            "login.html",
            error=(
                "Invalid email or password."
            )
        )


    return render_template(
        "login.html"
    )


# =========================================================
# FORGOT PASSWORD
# =========================================================

@app.route(
    "/forgot-password",
    methods=["GET", "POST"]
)
def forgot_password():

    if request.method == "POST":

        action = request.form.get(
            "action",
            ""
        )


        # -------------------------------------------------
        # SEND OTP
        # -------------------------------------------------

        if action == "send_otp":

            email = request.form.get(
                "email",
                ""
            ).strip().lower()


            phone = request.form.get(
                "phone",
                ""
            ).strip()


            if not email or not phone:

                return render_template(
                    "forgot_password.html",
                    step="details",
                    error=(
                        "Please enter email "
                        "and phone number."
                    ),
                    email=email,
                    phone=phone
                )


            conn = get_db_connection()


            user = conn.execute("""
                SELECT *
                FROM users
                WHERE email = ?
                AND phone = ?
            """, (
                email,
                phone
            )).fetchone()


            conn.close()


            if not user:

                return render_template(
                    "forgot_password.html",
                    step="details",
                    error=(
                        "Email and phone number "
                        "do not match our records."
                    ),
                    email=email,
                    phone=phone
                )


            otp = str(
                random.randint(
                    100000,
                    999999
                )
            )


            session["reset_user_id"] = (
                user["id"]
            )


            session["reset_otp"] = otp


            session["reset_otp_time"] = (
                time.time()
            )


            print()
            print("=" * 55)
            print(
                "SMARTPLOT PASSWORD RESET OTP"
            )
            print("=" * 55)
            print(
                "Email:",
                user["email"]
            )
            print(
                "OTP:",
                otp
            )
            print(
                "Valid for: 5 minutes"
            )
            print("=" * 55)
            print()


            return render_template(
                "forgot_password.html",
                step="otp",
                email=email
            )


        # -------------------------------------------------
        # VERIFY OTP
        # -------------------------------------------------

        if action == "verify_otp":

            entered_otp = request.form.get(
                "otp",
                ""
            ).strip()


            saved_otp = session.get(
                "reset_otp"
            )


            otp_time = session.get(
                "reset_otp_time"
            )


            email = request.form.get(
                "email",
                ""
            ).strip().lower()


            if (
                not saved_otp
                or not otp_time
            ):

                return render_template(
                    "forgot_password.html",
                    step="details",
                    error=(
                        "OTP session expired. "
                        "Please request a new OTP."
                    )
                )


            if (
                time.time()
                - otp_time
                > 300
            ):

                session.pop(
                    "reset_otp",
                    None
                )


                session.pop(
                    "reset_otp_time",
                    None
                )


                return render_template(
                    "forgot_password.html",
                    step="details",
                    error=(
                        "OTP expired. "
                        "Please request a new OTP."
                    )
                )


            if entered_otp != saved_otp:

                return render_template(
                    "forgot_password.html",
                    step="otp",
                    error=(
                        "Invalid OTP. "
                        "Please try again."
                    ),
                    email=email
                )


            session["otp_verified"] = True


            return render_template(
                "forgot_password.html",
                step="password",
                email=email
            )


        # -------------------------------------------------
        # RESET PASSWORD
        # -------------------------------------------------

        if action == "reset_password":

            if not session.get(
                "otp_verified"
            ):

                return render_template(
                    "forgot_password.html",
                    step="details",
                    error=(
                        "Please verify OTP first."
                    )
                )


            new_password = request.form.get(
                "new_password",
                ""
            )


            confirm_password = request.form.get(
                "confirm_password",
                ""
            )


            if (
                not new_password
                or not confirm_password
            ):

                return render_template(
                    "forgot_password.html",
                    step="password",
                    error=(
                        "Please fill both "
                        "password fields."
                    )
                )


            if new_password != confirm_password:

                return render_template(
                    "forgot_password.html",
                    step="password",
                    error=(
                        "Passwords do not match."
                    )
                )


            if len(new_password) < 6:

                return render_template(
                    "forgot_password.html",
                    step="password",
                    error=(
                        "Password must contain "
                        "at least 6 characters."
                    )
                )


            user_id = session.get(
                "reset_user_id"
            )


            if not user_id:

                return render_template(
                    "forgot_password.html",
                    step="details",
                    error=(
                        "Password reset session "
                        "expired."
                    )
                )


            hashed_password = (
                generate_password_hash(
                    new_password
                )
            )


            conn = get_db_connection()


            conn.execute("""
                UPDATE users
                SET password = ?
                WHERE id = ?
            """, (
                hashed_password,
                user_id
            ))


            conn.commit()

            conn.close()


            session.clear()


            return render_template(
                "login.html",
                success=(
                    "Password reset successfully. "
                    "Please login."
                )
            )


    return render_template(
        "forgot_password.html",
        step="details"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()


    return redirect(
        url_for("login")
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    conn = get_db_connection()


    user = conn.execute("""
        SELECT
            id,
            name,
            email,
            phone,
            role
        FROM users
        WHERE id = ?
    """, (
        session["user_id"],
    )).fetchone()


    if not user:

        conn.close()

        session.clear()

        return redirect(
            url_for("login")
        )


    statistics = {
        "total_listings": 0,
        "available_listings": 0,
        "reserved_listings": 0,
        "sold_listings": 0,
        "total_inquiries": 0,
        "total_favorites": 0
    }


    # =====================================================
    # SELLER STATISTICS
    # =====================================================

    if user["role"] == "seller":

        user_id = user["id"]


        statistics[
            "total_listings"
        ] = conn.execute("""
            SELECT COUNT(*)
            FROM plots
            WHERE user_id = ?
        """, (
            user_id,
        )).fetchone()[0]


        statistics[
            "available_listings"
        ] = conn.execute("""
            SELECT COUNT(*)
            FROM plots
            WHERE user_id = ?
            AND status = 'available'
        """, (
            user_id,
        )).fetchone()[0]


        statistics[
            "reserved_listings"
        ] = conn.execute("""
            SELECT COUNT(*)
            FROM plots
            WHERE user_id = ?
            AND status = 'reserved'
        """, (
            user_id,
        )).fetchone()[0]


        statistics[
            "sold_listings"
        ] = conn.execute("""
            SELECT COUNT(*)
            FROM plots
            WHERE user_id = ?
            AND status = 'sold'
        """, (
            user_id,
        )).fetchone()[0]


        statistics[
            "total_inquiries"
        ] = conn.execute("""
            SELECT COUNT(*)
            FROM inquiries
            WHERE seller_id = ?
        """, (
            user_id,
        )).fetchone()[0]


        statistics[
            "total_favorites"
        ] = conn.execute("""
            SELECT COUNT(*)
            FROM favorites
            JOIN plots
                ON favorites.plot_id = plots.id
            WHERE plots.user_id = ?
        """, (
            user_id,
        )).fetchone()[0]


    session["user_name"] = (
        user["name"]
    )


    session["user_role"] = (
        user["role"]
    )


    user_data = {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "phone": user["phone"],
        "account_type": user["role"]
    }


    conn.close()


    return render_template(
        "dashboard.html",
        user=user_data,
        statistics=statistics
    )


# =========================================================
# SELLER STATISTICS
#
# THIS ROUTE MATCHES:
#
# url_for('seller_statistics')
# =========================================================

@app.route(
    "/seller-statistics"
)
@login_required
@role_required("seller")
def seller_statistics():

    conn = get_db_connection()


    user_id = session["user_id"]


    # -----------------------------------------------------
    # TOTAL LISTINGS
    # -----------------------------------------------------

    total_listings = conn.execute("""
        SELECT COUNT(*)
        FROM plots
        WHERE user_id = ?
    """, (
        user_id,
    )).fetchone()[0]


    # -----------------------------------------------------
    # AVAILABLE
    # -----------------------------------------------------

    available_listings = conn.execute("""
        SELECT COUNT(*)
        FROM plots
        WHERE user_id = ?
        AND status = 'available'
    """, (
        user_id,
    )).fetchone()[0]


    # -----------------------------------------------------
    # RESERVED
    # -----------------------------------------------------

    reserved_listings = conn.execute("""
        SELECT COUNT(*)
        FROM plots
        WHERE user_id = ?
        AND status = 'reserved'
    """, (
        user_id,
    )).fetchone()[0]


    # -----------------------------------------------------
    # SOLD
    # -----------------------------------------------------

    sold_listings = conn.execute("""
        SELECT COUNT(*)
        FROM plots
        WHERE user_id = ?
        AND status = 'sold'
    """, (
        user_id,
    )).fetchone()[0]


    # -----------------------------------------------------
    # INQUIRIES
    # -----------------------------------------------------

    total_inquiries = conn.execute("""
        SELECT COUNT(*)
        FROM inquiries
        WHERE seller_id = ?
    """, (
        user_id,
    )).fetchone()[0]


    # -----------------------------------------------------
    # NEW INQUIRIES
    # -----------------------------------------------------

    new_inquiries = conn.execute("""
        SELECT COUNT(*)
        FROM inquiries
        WHERE seller_id = ?
        AND status = 'new'
    """, (
        user_id,
    )).fetchone()[0]


    # -----------------------------------------------------
    # READ INQUIRIES
    # -----------------------------------------------------

    read_inquiries = conn.execute("""
        SELECT COUNT(*)
        FROM inquiries
        WHERE seller_id = ?
        AND status = 'read'
    """, (
        user_id,
    )).fetchone()[0]


    # -----------------------------------------------------
    # FAVORITES
    # -----------------------------------------------------

    total_favorites = conn.execute("""
        SELECT COUNT(*)
        FROM favorites
        JOIN plots
            ON favorites.plot_id = plots.id
        WHERE plots.user_id = ?
    """, (
        user_id,
    )).fetchone()[0]


    # -----------------------------------------------------
    # TOTAL PROPERTY VALUE
    # -----------------------------------------------------

    total_property_value = conn.execute("""
        SELECT COALESCE(
            SUM(price),
            0
        )
        FROM plots
        WHERE user_id = ?
        AND status = 'available'
    """, (
        user_id,
    )).fetchone()[0]


    # -----------------------------------------------------
    # AVERAGE PRICE
    # -----------------------------------------------------

    average_price = conn.execute("""
        SELECT COALESCE(
            AVG(price),
            0
        )
        FROM plots
        WHERE user_id = ?
    """, (
        user_id,
    )).fetchone()[0]


    # -----------------------------------------------------
    # RECENT LISTINGS
    # -----------------------------------------------------

    recent_listings = conn.execute("""
        SELECT
            id,
            title,
            location,
            area,
            price,
            status,
            created_at
        FROM plots
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 5
    """, (
        user_id,
    )).fetchall()


    conn.close()


    statistics = {

        "total_listings":
            total_listings,

        "available_listings":
            available_listings,

        "reserved_listings":
            reserved_listings,

        "sold_listings":
            sold_listings,

        "total_inquiries":
            total_inquiries,

        "new_inquiries":
            new_inquiries,

        "read_inquiries":
            read_inquiries,

        "total_favorites":
            total_favorites,

        "total_property_value":
            total_property_value,

        "average_price":
            average_price

    }


    return render_template(
        "seller_statistics.html",
        statistics=statistics,
        recent_listings=recent_listings
    )


# =========================================================
# MODIFY ACCOUNT
# =========================================================

@app.route(
    "/modify-account",
    methods=["GET", "POST"]
)
@login_required
def modify_account():

    conn = get_db_connection()


    user = conn.execute("""
        SELECT
            id,
            name,
            email,
            phone,
            role
        FROM users
        WHERE id = ?
    """, (
        session["user_id"],
    )).fetchone()


    if not user:

        conn.close()

        session.clear()

        return redirect(
            url_for("login")
        )


    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()


        email = request.form.get(
            "email",
            ""
        ).strip().lower()


        phone = request.form.get(
            "phone",
            ""
        ).strip()


        if (
            not name
            or not email
            or not phone
        ):

            conn.close()

            return render_template(
                "modify_account.html",
                user=user,
                error=(
                    "Please fill all fields."
                )
            )


        try:

            conn.execute("""
                UPDATE users
                SET
                    name = ?,
                    email = ?,
                    phone = ?
                WHERE id = ?
            """, (
                name,
                email,
                phone,
                session["user_id"]
            ))


            conn.commit()


        except sqlite3.IntegrityError:

            conn.close()

            return render_template(
                "modify_account.html",
                user=user,
                error=(
                    "Email already exists."
                )
            )


        conn.close()


        session["user_name"] = name


        flash(
            "Account information updated successfully.",
            "success"
        )


        return redirect(
            url_for("dashboard")
        )


    conn.close()


    return render_template(
        "modify_account.html",
        user=user
    )


# =========================================================
# ADD PLOT
# =========================================================

@app.route(
    "/add-plot",
    methods=["GET", "POST"]
)
@login_required
@role_required("seller")
def add_plot():

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()


        location = request.form.get(
            "location",
            ""
        ).strip()


        area = request.form.get(
            "area",
            ""
        ).strip()


        price = request.form.get(
            "price",
            ""
        ).strip()


        road_width = request.form.get(
            "road_width",
            ""
        ).strip()


        property_type = request.form.get(
            "property_type",
            ""
        ).strip()


        facing = request.form.get(
            "facing",
            ""
        ).strip()


        landmark = request.form.get(
            "landmark",
            ""
        ).strip()


        description = request.form.get(
            "description",
            ""
        ).strip()


        confirm = request.form.get(
            "confirm"
        )


        if (
            not title
            or not location
            or not area
            or not price
            or not property_type
            or not confirm
        ):

            return render_template(
                "add_plot.html",
                error=(
                    "Please fill all required "
                    "fields and confirm the "
                    "information."
                )
            )


        try:

            area_value = float(area)

            price_value = float(price)


            if (
                area_value <= 0
                or price_value <= 0
            ):

                raise ValueError


        except ValueError:

            return render_template(
                "add_plot.html",
                error=(
                    "Area and price must "
                    "be valid positive numbers."
                )
            )


        road_width_value = None


        if road_width:

            try:

                road_width_value = float(
                    road_width
                )


                if road_width_value < 0:

                    raise ValueError


            except ValueError:

                return render_template(
                    "add_plot.html",
                    error=(
                        "Please enter a valid "
                        "road width."
                    )
                )


        conn = get_db_connection()


        cursor = conn.execute("""
            INSERT INTO plots
            (
                user_id,
                title,
                location,
                area,
                price,
                road_width,
                property_type,
                facing,
                landmark,
                description,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            title,
            location,
            area_value,
            price_value,
            road_width_value,
            property_type,
            facing,
            landmark,
            description,
            "available"
        ))


        plot_id = cursor.lastrowid


        images = request.files.getlist(
            "images"
        )


        image_count = 0


        for image in images:

            if (
                not image
                or not image.filename
            ):

                continue


            if image_count >= 5:

                break


            safe_name = secure_filename(
                image.filename
            )


            if not safe_name:

                continue


            if not allowed_file(
                safe_name
            ):

                continue


            extension = (
                safe_name
                .rsplit(".", 1)[1]
                .lower()
            )


            unique_filename = (
                uuid.uuid4().hex
                + "."
                + extension
            )


            file_path = os.path.join(
                UPLOAD_FOLDER,
                unique_filename
            )


            image.save(
                file_path
            )


            conn.execute("""
                INSERT INTO plot_images
                (
                    plot_id,
                    filename
                )
                VALUES (?, ?)
            """, (
                plot_id,
                unique_filename
            ))


            image_count += 1


        conn.commit()

        conn.close()


        flash(
            "Plot published successfully!",
            "success"
        )


        return redirect(
            url_for("my_listings")
        )


    return render_template(
        "add_plot.html"
    )


# =========================================================
# MY LISTINGS
# =========================================================

@app.route("/my-listings")
@login_required
@role_required("seller")
def my_listings():

    conn = get_db_connection()


    plots_data = conn.execute("""
        SELECT *
        FROM plots
        WHERE user_id = ?
        ORDER BY id DESC
    """, (
        session["user_id"],
    )).fetchall()


    conn.close()


    return render_template(
        "my_listings.html",
        plots=plots_data
    )


# =========================================================
# UPDATE PLOT STATUS
# =========================================================

@app.route(
    "/update-status/<int:plot_id>/<status>",
    methods=["POST"]
)
@login_required
@role_required("seller")
def update_status(
    plot_id,
    status
):

    allowed_statuses = {
        "available",
        "reserved",
        "sold"
    }


    if status not in allowed_statuses:

        return redirect(
            url_for("my_listings")
        )


    conn = get_db_connection()


    conn.execute("""
        UPDATE plots
        SET status = ?
        WHERE id = ?
        AND user_id = ?
    """, (
        status,
        plot_id,
        session["user_id"]
    ))


    conn.commit()

    conn.close()


    return redirect(
        url_for("my_listings")
    )


# =========================================================
# DELETE PLOT
# =========================================================

@app.route(
    "/delete-plot/<int:plot_id>",
    methods=["POST"]
)
@login_required
@role_required("seller")
def delete_plot(plot_id):

    conn = get_db_connection()


    images = conn.execute("""
        SELECT filename
        FROM plot_images
        WHERE plot_id = ?
    """, (
        plot_id,
    )).fetchall()


    conn.execute("""
        DELETE FROM plots
        WHERE id = ?
        AND user_id = ?
    """, (
        plot_id,
        session["user_id"]
    ))


    conn.commit()

    conn.close()


    for image in images:

        image_path = os.path.join(
            UPLOAD_FOLDER,
            image["filename"]
        )


        if os.path.exists(
            image_path
        ):

            try:

                os.remove(
                    image_path
                )

            except OSError:

                app.logger.warning(
                    "Could not remove image: %s",
                    image_path
                )


    return redirect(
        url_for("my_listings")
    )


# =========================================================
# BUYER - FIND PLOTS
# =========================================================

@app.route("/plots")
@login_required
@role_required("buyer")
def plots():

    location = request.args.get(
        "location",
        ""
    ).strip()


    min_area = request.args.get(
        "min_area",
        ""
    ).strip()


    max_area = request.args.get(
        "max_area",
        ""
    ).strip()


    min_price = request.args.get(
        "min_price",
        ""
    ).strip()


    max_price = request.args.get(
        "max_price",
        ""
    ).strip()


    property_type = request.args.get(
        "property_type",
        ""
    ).strip()


    sort = request.args.get(
        "sort",
        "newest"
    ).strip()


    allowed_sorts = {
        "newest",
        "price_low",
        "price_high",
        "area_low",
        "area_high"
    }


    if sort not in allowed_sorts:

        sort = "newest"


    query = """
        SELECT *
        FROM plots
        WHERE status = 'available'
    """


    params = []


    if location:

        query += """
            AND location LIKE ?
        """


        params.append(
            f"%{location}%"
        )


    if min_area:

        try:

            value = float(
                min_area
            )


            if value >= 0:

                query += """
                    AND area >= ?
                """


                params.append(
                    value
                )


        except ValueError:

            pass


    if max_area:

        try:

            value = float(
                max_area
            )


            if value >= 0:

                query += """
                    AND area <= ?
                """


                params.append(
                    value
                )


        except ValueError:

            pass


    if min_price:

        try:

            value = float(
                min_price
            )


            if value >= 0:

                query += """
                    AND price >= ?
                """


                params.append(
                    value
                )


        except ValueError:

            pass


    if max_price:

        try:

            value = float(
                max_price
            )


            if value >= 0:

                query += """
                    AND price <= ?
                """


                params.append(
                    value
                )


        except ValueError:

            pass


    allowed_property_types = {
        "Residential",
        "Commercial",
        "Agricultural",
        "Industrial"
    }


    if property_type in allowed_property_types:

        query += """
            AND property_type = ?
        """


        params.append(
            property_type
        )


    else:

        property_type = ""


    if sort == "price_low":

        query += """
            ORDER BY price ASC
        """


    elif sort == "price_high":

        query += """
            ORDER BY price DESC
        """


    elif sort == "area_low":

        query += """
            ORDER BY area ASC
        """


    elif sort == "area_high":

        query += """
            ORDER BY area DESC
        """


    else:

        query += """
            ORDER BY id DESC
        """


        sort = "newest"


    conn = get_db_connection()


    plots_data = conn.execute(
        query,
        params
    ).fetchall()


    favorite_rows = conn.execute("""
        SELECT plot_id
        FROM favorites
        WHERE user_id = ?
    """, (
        session["user_id"],
    )).fetchall()


    favorite_ids = {
        row["plot_id"]
        for row in favorite_rows
    }


    image_rows = conn.execute("""
        SELECT
            plot_id,
            filename
        FROM plot_images
        ORDER BY id ASC
    """).fetchall()


    conn.close()


    plot_images = {}


    for image in image_rows:

        plot_id = image["plot_id"]


        if plot_id not in plot_images:

            plot_images[plot_id] = []


        plot_images[plot_id].append(
            image["filename"]
        )


    return render_template(
        "plots.html",
        plots=plots_data,
        favorite_ids=favorite_ids,
        plot_images=plot_images,
        location=location,
        min_area=min_area,
        max_area=max_area,
        min_price=min_price,
        max_price=max_price,
        property_type=property_type,
        sort=sort
    )


# =========================================================
# FAVORITES
# =========================================================

@app.route("/favorites")
@login_required
@role_required("buyer")
def favorites():

    conn = get_db_connection()


    favorites_data = conn.execute("""
        SELECT
            plots.*,
            favorites.created_at AS favorited_at

        FROM favorites

        JOIN plots
            ON favorites.plot_id = plots.id

        WHERE favorites.user_id = ?

        ORDER BY favorites.id DESC
    """, (
        session["user_id"],
    )).fetchall()


    favorites_list = []


    for plot in favorites_data:

        image = conn.execute("""
            SELECT filename
            FROM plot_images
            WHERE plot_id = ?
            ORDER BY id ASC
            LIMIT 1
        """, (
            plot["id"],
        )).fetchone()


        plot_dict = dict(
            plot
        )


        plot_dict["image"] = (
            image["filename"]
            if image
            else None
        )


        favorites_list.append(
            plot_dict
        )


    conn.close()


    return render_template(
        "favorites.html",
        favorites=favorites_list
    )


# =========================================================
# TOGGLE FAVORITE
# =========================================================

@app.route(
    "/toggle-favorite/<int:plot_id>",
    methods=["POST"]
)
@login_required
@role_required("buyer")
def toggle_favorite(plot_id):

    conn = get_db_connection()


    plot = conn.execute("""
        SELECT id
        FROM plots
        WHERE id = ?
        AND status = 'available'
    """, (
        plot_id,
    )).fetchone()


    if not plot:

        conn.close()

        return redirect(
            url_for("plots")
        )


    existing = conn.execute("""
        SELECT id
        FROM favorites
        WHERE user_id = ?
        AND plot_id = ?
    """, (
        session["user_id"],
        plot_id
    )).fetchone()


    if existing:

        conn.execute("""
            DELETE FROM favorites
            WHERE user_id = ?
            AND plot_id = ?
        """, (
            session["user_id"],
            plot_id
        ))


    else:

        conn.execute("""
            INSERT OR IGNORE INTO favorites
            (
                user_id,
                plot_id
            )
            VALUES (?, ?)
        """, (
            session["user_id"],
            plot_id
        ))


    conn.commit()

    conn.close()


    return redirect(
        request.referrer
        or url_for("plots")
    )


# =========================================================
# PLOT DETAILS
# =========================================================

@app.route(
    "/plot/<int:plot_id>"
)
@login_required
def plot_details(plot_id):

    conn = get_db_connection()


    plot = conn.execute("""
        SELECT

            plots.*,

            users.name AS owner_name,

            users.phone AS owner_phone,

            users.email AS owner_email

        FROM plots

        JOIN users
            ON plots.user_id = users.id

        WHERE plots.id = ?
    """, (
        plot_id,
    )).fetchone()


    if not plot:

        conn.close()

        abort(404)


    images = conn.execute("""
        SELECT *
        FROM plot_images
        WHERE plot_id = ?
        ORDER BY id ASC
    """, (
        plot_id,
    )).fetchall()


    is_favorite = False


    if session.get(
        "user_role"
    ) == "buyer":

        favorite = conn.execute("""
            SELECT id
            FROM favorites
            WHERE user_id = ?
            AND plot_id = ?
        """, (
            session["user_id"],
            plot_id
        )).fetchone()


        is_favorite = (
            favorite is not None
        )


    conn.close()


    price_per_sqft = 0


    if (
        plot["area"]
        and plot["area"] > 0
    ):

        price_per_sqft = (
            plot["price"]
            / plot["area"]
        )


    return render_template(
        "plot_details.html",
        plot=plot,
        images=images,
        price_per_sqft=price_per_sqft,
        is_favorite=is_favorite
    )


# =========================================================
# SEND INQUIRY
# =========================================================

@app.route(
    "/send-inquiry/<int:plot_id>",
    methods=["POST"]
)
@login_required
@role_required("buyer")
def send_inquiry(plot_id):

    message = request.form.get(
        "message",
        ""
    ).strip()


    if not message:

        flash(
            "Please enter a message.",
            "error"
        )


        return redirect(
            url_for(
                "plot_details",
                plot_id=plot_id
            )
        )


    if len(message) > 2000:

        flash(
            "Message is too long.",
            "error"
        )


        return redirect(
            url_for(
                "plot_details",
                plot_id=plot_id
            )
        )


    conn = get_db_connection()


    plot = conn.execute("""
        SELECT
            id,
            user_id,
            status
        FROM plots
        WHERE id = ?
    """, (
        plot_id,
    )).fetchone()


    if not plot:

        conn.close()

        abort(404)


    if plot["status"] != "available":

        conn.close()


        flash(
            "This plot is no longer available.",
            "error"
        )


        return redirect(
            url_for(
                "plot_details",
                plot_id=plot_id
            )
        )


    if plot["user_id"] == session["user_id"]:

        conn.close()

        return redirect(
            url_for(
                "plot_details",
                plot_id=plot_id
            )
        )


    conn.execute("""
        INSERT INTO inquiries
        (
            buyer_id,
            seller_id,
            plot_id,
            message,
            status
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        session["user_id"],
        plot["user_id"],
        plot_id,
        message,
        "new"
    ))


    conn.commit()

    conn.close()


    flash(
        "Your inquiry has been sent to the owner.",
        "success"
    )


    return redirect(
        url_for(
            "plot_details",
            plot_id=plot_id
        )
    )


# =========================================================
# SELLER INQUIRIES
# =========================================================

@app.route("/inquiries")
@login_required
@role_required("seller")
def inquiries():

    conn = get_db_connection()


    inquiries_data = conn.execute("""
        SELECT

            inquiries.id,

            inquiries.message,

            inquiries.status,

            inquiries.created_at,

            plots.id AS plot_id,

            plots.title AS plot_title,

            plots.location AS plot_location,

            users.name AS buyer_name,

            users.email AS buyer_email,

            users.phone AS buyer_phone

        FROM inquiries

        JOIN plots
            ON inquiries.plot_id = plots.id

        JOIN users
            ON inquiries.buyer_id = users.id

        WHERE inquiries.seller_id = ?

        ORDER BY inquiries.id DESC
    """, (
        session["user_id"],
    )).fetchall()


    conn.close()


    return render_template(
        "inquiries.html",
        inquiries=inquiries_data
    )


# =========================================================
# MARK INQUIRY READ
# =========================================================

@app.route(
    "/inquiry-read/<int:inquiry_id>",
    methods=["POST"]
)
@login_required
@role_required("seller")
def inquiry_read(inquiry_id):

    conn = get_db_connection()


    conn.execute("""
        UPDATE inquiries

        SET status = 'read'

        WHERE id = ?

        AND seller_id = ?
    """, (
        inquiry_id,
        session["user_id"]
    ))


    conn.commit()

    conn.close()


    return redirect(
        url_for("inquiries")
    )


# =========================================================
# SERVE PLOT IMAGES
# =========================================================

@app.route(
    "/uploads/plots/<path:filename>"
)
@login_required
def uploaded_plot_image(filename):

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "404.html"
    ), 404


@app.errorhandler(413)
def request_too_large(error):

    return (
        "Uploaded file or request is too large.",
        413
    )


@app.errorhandler(500)
def internal_server_error(error):

    app.logger.exception(
        "Internal server error"
    )


    return (
        "An internal server error occurred.",
        500
    )


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

create_database()


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )