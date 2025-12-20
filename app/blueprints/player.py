from flask import Blueprint, render_template, request, redirect, url_for, session
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
)

player_bp = Blueprint("player", __name__, url_prefix="/player")

@player_bp.before_request
def require_player_session():
    if session.get("user_id") is None or session.get("role") != "player":
        session["next"] = request.path
        return redirect(url_for("login"))

@player_bp.route("/home")
def home():
    player_id = session.get("user_id")
    
    # Fetch overall statistics from PlayerStatsAll view
    overall_stats = fetch_player_stats_all(player_id)
    
    # Fetch all season stats from PlayerSeasonStats view
    season_stats = fetch_player_season_stats(player_id)
    
    # Fetch tournament stats from PlayerTournamentStats view
    tournament_stats = fetch_player_tournament_stats(player_id)
    
    # Get player info for display (including Overall)
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT FirstName, LastName, IsEligible, Overall
                FROM Users u
                JOIN Player p ON u.UsersID = p.UsersID
                WHERE u.UsersID = %s;
                """,
                (player_id,),
            )
            player_info = cur.fetchone()
    finally:
        conn.close()
    
    # Fetch all season stats (no filtering)
    all_season_stats = fetch_player_season_stats(player_id)
    
    return render_template(
        "home_player.html",
        player_info=player_info,
        overall_stats=overall_stats,
        season_stats=all_season_stats,
        tournament_stats=tournament_stats,
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
    
    try:
        update_training_attendance_db(player_id, session_id, int(status))
    except ValueError as exc:
        # Could add flash message here if needed
        pass
    
    return redirect(url_for("player.view_trainings"))

@player_bp.route("/offers")
def view_offers():
    player_id = session.get("user_id")
    pending_offers, past_offers = fetch_player_offers(player_id)
    now = datetime.now()
    
    return render_template("player_offers.html", pending_offers=pending_offers, past_offers=past_offers, now=now)

@player_bp.route("/offers/<int:offer_id>/evaluate", methods=["POST"])
def evaluate_offer(offer_id):
    player_id = session.get("user_id")
    
    # Verify the offer belongs to this player
    pending_offers, past_offers = fetch_player_offers(player_id)
    all_offers = pending_offers + past_offers
    if not any(offer["offerid"] == offer_id for offer in all_offers):
        return redirect(url_for("player.view_offers"))
    
    decision = request.form.get("decision")
    if decision in ("accept", "reject"):
        final_decision = decision == 'accept'
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

