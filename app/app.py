import os
import secrets
from datetime import datetime
from decimal import Decimal, InvalidOperation

import psycopg2
from flask import Flask, jsonify, render_template, request, session, redirect, url_for, g
from werkzeug.security import generate_password_hash, check_password_hash

from db import get_connection

from blueprints.admin import admin_bp
from blueprints.superadmin import superadmin_bp

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

app.register_blueprint(admin_bp)
app.register_blueprint(superadmin_bp)

@app.template_filter('strftime')
def strftime_filter(value, format_string='%Y-%m-%d %H:%M:%S'):
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace(' ', 'T'))
        except (ValueError, TypeError, AttributeError):
            return value
    if hasattr(value, 'strftime'):
        return value.strftime(format_string)
    return value

@app.before_request
def _set_default_banner():
    role = session.get("role")
    if role == "superadmin":
        g.banner_view_endpoint = "superadmin.view_tournaments"
        g.banner_league_endpoint = "superadmin.view_leagues"
        g.banner_create_league_endpoint = None
    elif role in ("admin", "tournament_admin"):
        g.banner_view_endpoint = "admin.view_tournaments"
        g.banner_league_endpoint = "admin.view_leagues"
        g.banner_create_league_endpoint = None
    else:
        g.banner_view_endpoint = None
        g.banner_league_endpoint = None
        g.banner_create_league_endpoint = None
    g.banner_create_endpoint = None
    g.banner_allow_create = False

# Role to home endpoint mapping - tournamnet-admin is now also league admin 
ROLE_HOME_ENDPOINTS = {
    "player": "home_player",
    "coach": "home_coach",
    "referee": "home_referee",
    "team_owner": "home_team_owner",
    "admin": "admin.view_tournaments", 
    "superadmin": "superadmin.view_tournaments",
}

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/home/player")
def home_player():
    return render_template("home_player.html")


@app.route("/home/coach")
def home_coach():
    return render_template("home_coach.html")


@app.route("/home/referee")
def home_referee():
    return render_template("home_referee.html")


@app.route("/home/team-owner")
def home_team_owner():
    return render_template("home_team_owner.html")


@app.route("/home/tournament-admin")
def home_tournament_admin():
    return render_template("home_tournament_admin.html")


@app.route("/home/superadmin")
def home_superadmin():
    return redirect(url_for("superadmin.view_tournaments"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        try:
            user = _authenticate_user(email, password)
            session["user_id"] = user["id"]
            session["role"] = user["role"]

            next_path = session.pop("next", None)
            safe_next = _safe_next_path(user, next_path)
            if safe_next:
                return redirect(safe_next)
            
            # Use ROLE_HOME_ENDPOINTS to redirect based on role
            endpoint = ROLE_HOME_ENDPOINTS.get(user["role"])
            if endpoint:
                return redirect(url_for(endpoint))
            return redirect(url_for("home"))
        except (ValueError, psycopg2.Error) as exc:
            message = _friendly_db_error(exc)
        return render_template("login.html", message=message)

    return render_template("login.html")

@app.route("/register/player", methods=["GET", "POST"])
def register_player():
    message = None
    if request.method == "POST":
        try:
            _register_player(request.form)
            message = "Player registered successfully! You can now log in."
        except (ValueError, psycopg2.Error) as exc:
            message = _friendly_db_error(exc)
    return render_template("register_player.html", message=message)

@app.route("/register/coach", methods=["GET", "POST"])
def register_coach():
    message = None
    if request.method == "POST":
        try:
            _register_coach(request.form)
            message = "Coach registered successfully! You can now log in."
        except (ValueError, psycopg2.Error) as exc:
            message = _friendly_db_error(exc)
    return render_template("register_coach.html", message=message)

@app.route("/register/referee", methods=["GET", "POST"])
def register_referee():
    message = None
    if request.method == "POST":
        try:
            _register_referee(request.form)
            message = "Referee registered successfully! You can now log in."
        except (ValueError, psycopg2.Error) as exc:
            message = _friendly_db_error(exc)
    return render_template("register_referee.html", message=message)

@app.route("/register/team-owner", methods=["GET", "POST"])
def register_team_owner():
    message = None
    if request.method == "POST":
        try:
            _register_team_owner(request.form)
            message = "Team owner registered successfully! You can now log in."
        except (ValueError, psycopg2.Error) as exc:
            message = _friendly_db_error(exc)
    return render_template("register_team_owner.html", message=message)

@app.route("/register/tournament-admin", methods=["GET", "POST"])
def register_tournament_admin():
    message = None
    if request.method == "POST":
        try:
            _register_tournament_admin(request.form)
            message = "Tournament admin registered successfully! You can now log in."
        except (ValueError, psycopg2.Error) as exc:
            message = _friendly_db_error(exc)
    return render_template("register_tournament_admin.html", message=message)

@app.route("/register", methods=["GET"])
def register_select():
    return render_template("register_select.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/users")
def users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM users;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    data = [{"id": r[0], "name": r[1]} for r in rows]
    return jsonify(data)


def _register_player(form):
    user_data = _extract_user_fields(form, role="player")
    height = _parse_decimal(form.get("height"), "Height", minimum=0)
    weight = _parse_decimal(form.get("weight"), "Weight", minimum=0)
    position = form.get("position", "").strip()
    if not position:
        raise ValueError("Position is required.")

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                user_id = _insert_user(cur, user_data)
                _insert_employee(cur, user_id)
                _insert_player(cur, user_id, height, weight, position)
    finally:
        conn.close()


def _register_coach(form):
    user_data = _extract_user_fields(form, role="coach")
    certification = form.get("certification", "").strip() or "Pending certification"

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                user_id = _insert_user(cur, user_data)
                _insert_employee(cur, user_id)
                _insert_coach(cur, user_id, certification)
    finally:
        conn.close()


def _register_referee(form):
    user_data = _extract_user_fields(form, role="referee")
    # Certification is auto-filled; form does not request it.
    certification = "Auto-certified"

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                user_id = _insert_user(cur, user_data)
                _insert_referee(cur, user_id, certification)
    finally:
        conn.close()


def _register_team_owner(form):
    user_data = _extract_user_fields(form, role="team_owner")
    net_worth = _parse_decimal(form.get("net_worth"), "Net worth", minimum=0, allow_empty=True)

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                user_id = _insert_user(cur, user_data)
                _insert_team_owner(cur, user_id, net_worth)
    finally:
        conn.close()


def _register_tournament_admin(form):
    user_data = _extract_user_fields(form, role="admin")

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                user_id = _insert_user(cur, user_data)
                _insert_admin(cur, user_id)
                _assign_league_moderation(cur, user_id)
    finally:
        conn.close()


def _extract_user_fields(form, role):
    first_name = form.get("first_name", "").strip()
    last_name = form.get("last_name", "").strip()
    email = form.get("email", "").strip().lower()
    nationality = form.get("nationality", "").strip()
    phone = form.get("phone", "").strip() or None
    birth_date_raw = form.get("birth_date", "").strip()
    password = form.get("password", "")
    confirm_password = form.get("confirm_password", "")

    if not first_name or not last_name:
        raise ValueError("First and last name are required.")
    if not email:
        raise ValueError("Email is required.")
    if not nationality:
        raise ValueError("Nationality is required.")

    if not birth_date_raw:
        raise ValueError("Birth date is required.")
    try:
        birth_date = datetime.strptime(birth_date_raw, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Birth date must be in YYYY-MM-DD format.")

    if not password:
        raise ValueError("Password is required.")
    if password != confirm_password:
        raise ValueError("Passwords do not match.")

    salt = secrets.token_hex(16)
    hashed_password = generate_password_hash(password + salt, method="pbkdf2:sha256")

    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "hashed_password": hashed_password,
        "salt": salt,
        "password_date": datetime.utcnow(),
        "phone": phone,
        "birth_date": birth_date,
        "role": role,
        "nationality": nationality,
    }


def _insert_user(cur, data):
    cur.execute(
        """
        INSERT INTO Users (
          FirstName,
          LastName,
          Email,
          HashedPassword,
          Salt,
          PasswordDate,
          PhoneNumber,
          BirthDate,
          Role,
          Nationality
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING UsersID;
        """,
        (
            data["first_name"],
            data["last_name"],
            data["email"],
            data["hashed_password"],
            data["salt"],
            data["password_date"],
            data["phone"],
            data["birth_date"],
            data["role"],
            data["nationality"],
        ),
    )
    return cur.fetchone()[0]


def _insert_employee(cur, user_id, team_id=None):
    cur.execute(
        "INSERT INTO Employee (UsersID, TeamID) VALUES (%s, %s);",
        (user_id, team_id),
    )


def _insert_player(cur, user_id, height, weight, position):
    cur.execute(
        """
        INSERT INTO Player (UsersID, Height, Weight, Overall, Position, IsEligible)
        VALUES (%s, %s, %s, %s, %s, %s);
        """,
        (user_id, height, weight, None, position, "eligible"),
    )


def _insert_coach(cur, user_id, certification):
    cur.execute(
        "INSERT INTO Coach (UsersID, Certification) VALUES (%s, %s);",
        (user_id, certification),
    )


def _insert_referee(cur, user_id, certification):
    cur.execute(
        "INSERT INTO Referee (UsersID, Certification) VALUES (%s, %s);",
        (user_id, certification),
    )


def _insert_team_owner(cur, user_id, net_worth):
    cur.execute(
        "INSERT INTO TeamOwner (UsersID, NetWorth) VALUES (%s, %s);",
        (user_id, net_worth),
    )


def _insert_admin(cur, user_id):
    cur.execute(
        "INSERT INTO Admin (UsersID) VALUES (%s);",
        (user_id,),
    )


def _assign_league_moderation(cur, admin_id):
    cur.execute(
        "SELECT LeagueID, SeasonNo, SeasonYear FROM Season;"
    )
    seasons = cur.fetchall()
    for league_id, season_no, season_year in seasons:
        cur.execute(
            """
            INSERT INTO SeasonModeration (LeagueID, SeasonNo, SeasonYear, AdminID)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT DO NOTHING;
            """,
            (league_id, season_no, season_year, admin_id),
        )


def _parse_decimal(raw_value, label, minimum=None, allow_empty=False):
    if raw_value in (None, ""):
        if allow_empty:
            return None
        raise ValueError(f"{label} is required.")
    try:
        value = Decimal(str(raw_value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{label} must be a valid number.")
    if minimum is not None and value < Decimal(str(minimum)):
        raise ValueError(f"{label} must be at least {minimum}.")
    return value


def _friendly_db_error(exc):
    if isinstance(exc, psycopg2.Error):
        diag = getattr(exc, "diag", None)
        constraint = getattr(diag, "constraint_name", "") or ""
        sqlstate = getattr(exc, "pgcode", "") or ""

        if constraint in _CONSTRAINT_MESSAGES:
            return _CONSTRAINT_MESSAGES[constraint]

        message = getattr(diag, "message_primary", "") or str(exc)
        lowered = message.lower()

        # Fallbacks based on SQLSTATE/message content when constraint names differ
        if sqlstate == "23505" and "email" in lowered:
            return _CONSTRAINT_MESSAGES["users_email_key"]
        if sqlstate == "23514":
            if "age_validation" in lowered:
                return _CONSTRAINT_MESSAGES["age_validation"]
            if "net_worth_check" in lowered:
                return _CONSTRAINT_MESSAGES["net_worth_check"]

        return message
    return str(exc)


_CONSTRAINT_MESSAGES = {
    "users_email_key": "An account with this email already exists.",
    "age_validation": "You must be at least 16 years old to register.",
    "net_worth_check": "Net worth must be greater than 100000.",
}

def _safe_next_path(user, next_path):
    if not next_path:
        return None
    # Block admin pages for non-admins to avoid redirect loops
    if next_path.startswith("/admin") and user.get("role") != "admin":
        return None
    if next_path.startswith("/superadmin") and user.get("role") != "superadmin":
        return None
    return next_path

def _authenticate_user(email, password):
    if not email or not password:
        raise ValueError("Email and password are required.")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT UsersID, Role, HashedPassword, Salt
                FROM Users
                WHERE Email = %s;
                """,
                (email,),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        raise ValueError("Invalid email or password.")

    user_id, role, hashed_password, salt = row
    hashed_password = hashed_password.strip() if isinstance(hashed_password, str) else hashed_password
    salt = salt.strip() if isinstance(salt, str) else salt

    if not check_password_hash(hashed_password, password + salt):
        raise ValueError("Invalid email or password.")

    return {"id": user_id, "role": role}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
