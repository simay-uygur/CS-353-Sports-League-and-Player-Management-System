from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from psycopg2.extras import RealDictCursor
from datetime import datetime

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
    finalize_transfer_offer,
    fetch_team_by_player,
    fetch_team_players,
    fetch_team_coaches,
    is_player_eligible,
    get_player_injury_status,
    fetch_session_date,
    update_expired_injuries,
)

player_bp = Blueprint("player", __name__, url_prefix="/player")


@player_bp.before_request
def require_player_session():
    if session.get("user_id") is None or session.get("role") != "player":
        session["next"] = request.path
        return redirect(url_for("login"))
    update_expired_injuries()


@player_bp.route("/home")
def home():
    player_id = session.get("user_id")

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
            player_id, league_id, season_no, season_year
        )

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


@player_bp.route("/trainings")
def view_trainings():
    player_id = session.get("user_id")
    trainings = fetch_player_trainings(player_id)
    now = datetime.now()

    return render_template("player_trainings.html", trainings=trainings, now=now)


@player_bp.route("/trainings/<int:session_id>/attendance", methods=["POST"])
def update_training_attendance(session_id):
    player_id = session.get("user_id")
    status = request.form.get("status")

    if status not in ("0", "1"):
        return redirect(url_for("player.view_trainings"))

    # SADECE JOIN (1) DURUMUNDA KONTROL YAP
    if status == "1":
        # 1. Verileri çek
        is_currently_eligible, recovery_date = get_player_injury_status(player_id)
        session_date = fetch_session_date(session_id)

        # 2. Eğer şu an eligible DEĞİLSE detaylı kontrol et
        if not is_currently_eligible:
            can_join = False

            # Eğer iyileşme tarihi varsa ve antrenman tarihi iyileşme tarihinden sonraysa izin ver
            if recovery_date and session_date:
                # session_date datetime objesidir, recovery_date date veya datetime olabilir.
                # Karşılaştırma için ikisini de date'e çevirmek en güvenlisidir.
                sess_d = (
                    session_date.date()
                    if isinstance(session_date, datetime)
                    else session_date
                )
                rec_d = (
                    recovery_date.date()
                    if isinstance(recovery_date, datetime)
                    else recovery_date
                )

                if sess_d > rec_d:
                    can_join = True

            if not can_join:
                flash(
                    "You are currently injured and cannot join this training session.",
                    "error",
                )
                if recovery_date:
                    flash(f"Your recovery date is: {recovery_date}", "info")
                return redirect(url_for("player.view_trainings"))

    try:
        update_training_attendance_db(player_id, session_id, int(status))

        if status == "1":
            flash("Successfully joined the training session!", "success")
        else:
            flash("You have marked yourself as absent/skipped.", "info")

    except ValueError as e:
        flash(f"Error: {str(e)}", "error")
    except Exception as e:
        flash("An unexpected error occurred.", "error")
        print(f"Error: {e}")

    return redirect(url_for("player.view_trainings"))


@player_bp.route("/offers")
def view_offers():
    player_id = session.get("user_id")
    offers = fetch_player_offers(player_id)

    return render_template("player_offers.html", offers=offers)


@player_bp.route("/offers/<int:offer_id>/evaluate", methods=["POST"])
def evaluate_offer(offer_id):
    player_id = session.get("user_id")

    # Verify the offer belongs to this player
    offers = fetch_player_offers(player_id)
    if not any(offer["offerid"] == offer_id for offer in offers):
        return redirect(url_for("player.view_offers"))

    decision = request.form.get("decision")
    if decision in ("accept", "reject"):
        final_decision = decision == "accept"
        finalize_transfer_offer(offer_id, final_decision)

    return redirect(url_for("player.view_offers"))


@player_bp.route("/team")
def view_team():
    player_id = session.get("user_id")
    team = fetch_team_by_player(player_id)

    if not team:
        # Player doesn't have a team assigned
        return render_template("player_team.html", team=None, players=[], coaches=[])

    # Fetch players and coaches for this team
    players = fetch_team_players(team["teamid"])
    coaches = fetch_team_coaches(team["teamid"])

    return render_template(
        "player_team.html",
        team=team,
        players=players,
        coaches=coaches,
    )
