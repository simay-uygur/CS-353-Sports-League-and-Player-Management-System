from artun import artunsPart
import os
import secrets
from datetime import datetime
from decimal import Decimal, InvalidOperation

import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, render_template, request, session, redirect, url_for, g
from werkzeug.security import generate_password_hash, check_password_hash

from db import get_connection
from db_helper import (
    fetch_player_stats_all,
    fetch_player_season_stats,
    fetch_player_tournament_stats,
    fetch_player_available_seasons,
    fetch_player_available_leagues,
    fetch_player_trainings,
    fetch_player_offers,
    update_training_attendance as update_training_attendance_db,
)

from blueprints.admin import admin_bp
from blueprints.superadmin import superadmin_bp
from blueprints.coach import coach_bp
from blueprints.owner import owner_bp
from blueprints.referee import referee_bp


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

app.register_blueprint(admin_bp)
app.register_blueprint(superadmin_bp)
app.register_blueprint(coach_bp)
app.register_blueprint(owner_bp)
app.register_blueprint(referee_bp)

# ============================================================


app.register_blueprint(artunsPart)


@app.route('/ui/match/<int:match_id>')
def view_match_entry(match_id):
    # Corresponds to Figure 9, 10, 11
    return render_template('match_entry.html', match_id=match_id)


@app.route('/ui/admin')
def view_admin_dashboard():
    # Corresponds to Figure 12
    return render_template('admin.html')


@app.route('/ui/stats')
def view_stats():
    # Corresponds to Figure 13
    return render_template('stats.html')

# ========================================================================


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


@app.context_processor
def inject_now():
    """Make datetime.now() available in templates."""
    return {'now': datetime.now()}


@app.before_request
def _set_default_banner():
    role = session.get("role")
    if role == "superadmin":
        g.banner_view_endpoint = "superadmin.view_tournaments"
        g.banner_league_endpoint = "superadmin.view_leagues"
        g.banner_all_matches_endpoint = None
        g.banner_create_league_endpoint = None
        g.banner_owner_endpoint = None
        g.banner_reports_endpoint = None
        g.banner_statistics_endpoint = None
    elif role in ("admin", "tournament_admin"):
        g.banner_view_endpoint = "admin.view_tournaments"
        g.banner_league_endpoint = "admin.view_leagues"
        g.banner_all_matches_endpoint = "admin.view_all_matches_lock"
        g.banner_create_league_endpoint = None
        g.banner_owner_endpoint = None
        g.banner_reports_endpoint = "admin.reports"
        g.banner_statistics_endpoint = None
    elif role == "team_owner":
        g.banner_view_endpoint = None
        g.banner_league_endpoint = None
        g.banner_all_matches_endpoint = None
        g.banner_create_league_endpoint = None
        g.banner_owner_endpoint = "owner.view_teams"
        g.banner_reports_endpoint = None
        g.banner_statistics_endpoint = None
        g.banner_employ_coach_endpoint = "owner.employ_coach"
    elif role == "coach":
        g.banner_view_endpoint = None
        g.banner_league_endpoint = None
        g.banner_all_matches_endpoint = None
        g.banner_create_league_endpoint = None
        g.banner_owner_endpoint = "coach.view_team"
        g.banner_reports_endpoint = None
        g.banner_statistics_endpoint = None
        g.banner_transfer_market_endpoint = "coach.view_transfer_market"
    elif role == "player":
        g.banner_view_endpoint = None
        g.banner_league_endpoint = None
        g.banner_all_matches_endpoint = None
        g.banner_create_league_endpoint = None
        g.banner_owner_endpoint = None
        g.banner_reports_endpoint = None
        g.banner_statistics_endpoint = "home_player"
        g.banner_trainings_endpoint = "view_trainings"
        g.banner_offers_endpoint = "view_offers"
    else:
        g.banner_view_endpoint = None
        g.banner_league_endpoint = None
        g.banner_all_matches_endpoint = None
        g.banner_create_league_endpoint = None
        g.banner_owner_endpoint = None
        g.banner_reports_endpoint = None
        g.banner_statistics_endpoint = None
    g.banner_create_endpoint = None
    g.banner_allow_create = False


# Role to home endpoint mapping - tournamnet-admin is now also league admin
ROLE_HOME_ENDPOINTS = {
    "player": "home_player",
    "coach": "home_coach",
    "referee": "home_referee",
    "team_owner": "home_team_owner",
    "admin": "admin.view_tournaments",
    "tournament_admin": "admin.view_tournaments",
    "superadmin": "superadmin.view_tournaments",
}


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/home/player")
def home_player():
    player_id = session.get("user_id")
    if not player_id or session.get("role") != "player":
        return redirect(url_for("login"))

    # Fetch overall statistics for summary cards
    overall_stats = fetch_player_stats_all(player_id)

    # Fetch available seasons and leagues for filters
    available_seasons = fetch_player_available_seasons(player_id)
    available_leagues = fetch_player_available_leagues(player_id)

    # Get filter parameters
    league_id = request.args.get("league_id", type=int)
    season_no = request.args.get("season_no", type=int)
    season_year = request.args.get("season_year")

    # Fetch season-specific stats if filters are provided
    season_stats = None
    if league_id is not None and season_no is not None and season_year:
        season_stats = fetch_player_season_stats(
            player_id, league_id, season_no, season_year)

    # Fetch tournament stats
    tournament_stats = fetch_player_tournament_stats(player_id)

    # Get player info for display
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT FirstName, LastName, IsEligible
                FROM Users u
                JOIN Player p ON u.UsersID = p.UsersID
                WHERE u.UsersID = %s;
                """,
                (player_id,),
            )
            player_info = cur.fetchone()
    finally:
        conn.close()

    return render_template(
        "home_player.html",
        player_info=player_info,
        overall_stats=overall_stats,
        season_stats=season_stats,
        tournament_stats=tournament_stats,
        available_seasons=available_seasons,
        available_leagues=available_leagues,
        selected_league_id=league_id,
        selected_season_no=season_no,
        selected_season_year=season_year,
    )


@app.route("/player/trainings")
def view_trainings():
    player_id = session.get("user_id")
    if not player_id or session.get("role") != "player":
        return redirect(url_for("login"))

    trainings = fetch_player_trainings(player_id)
    from datetime import datetime
    now = datetime.now()

    return render_template("player_trainings.html", trainings=trainings, now=now)


@app.route("/player/trainings/<int:session_id>/attendance", methods=["POST"])
def update_training_attendance(session_id):
    player_id = session.get("user_id")
    if not player_id or session.get("role") != "player":
        return redirect(url_for("login"))

    status = request.form.get("status")
    if status not in ("0", "1"):
        return redirect(url_for("view_trainings"))

    try:
        update_training_attendance_db(player_id, session_id, int(status))
    except ValueError as exc:
        # Could add flash message here if needed
        pass

    return redirect(url_for("view_trainings"))


@app.route("/player/offers")
def view_offers():
    player_id = session.get("user_id")
    if not player_id or session.get("role") != "player":
        return redirect(url_for("login"))

    offers = fetch_player_offers(player_id)

    return render_template("player_offers.html", offers=offers)


@app.route("/home/coach")
def home_coach():
    return render_template("home_coach.html")


@app.route("/home/referee")
def home_referee():
    return render_template("home_referee.html")


@app.route("/home/team-owner")
def home_team_owner():
    return redirect(url_for("owner.view_teams"))


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
    certification = form.get(
        "certification", "").strip() or "Pending certification"

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
    net_worth = _parse_decimal(
        form.get("net_worth"), "Net worth", minimum=0, allow_empty=True)

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
    hashed_password = generate_password_hash(
        password + salt, method="pbkdf2:sha256")

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
    hashed_password = hashed_password.strip() if isinstance(
        hashed_password, str) else hashed_password
    salt = salt.strip() if isinstance(salt, str) else salt

    if not check_password_hash(hashed_password, password + salt):
        raise ValueError("Invalid email or password.")

    return {"id": user_id, "role": role}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
