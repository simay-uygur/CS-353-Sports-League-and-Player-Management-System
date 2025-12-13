from flask import Blueprint, render_template, request, redirect, url_for, session
from datetime import datetime

from db_helper import (
    fetch_transferable_players,
    fetch_all_nationalities,
    fetch_all_positions,
    fetch_all_teams,
    fetch_player_by_id,
    make_transfer_offer,
    fetch_team_transfer_offers,
    fetch_sent_transfer_offers,
    finalize_transfer_offer,
    fetch_team_by_coach,
    fetch_team_players,
    fetch_team_coaches,
)

coach_bp = Blueprint("coach", __name__, url_prefix="/coach")

@coach_bp.before_request
def require_coach_session():
    # Allow both full admins and tournament_admins to access admin routes
    if session.get("user_id") is None or session.get("role") not in ("coach", "superadmin"):
        session["next"] = request.path
        return redirect(url_for("login"))

@coach_bp.route("/transfer_market", methods=["GET"])
def view_transfer_market():
    coachid = session['user_id']
    name = request.args.get("name")
    nationality = request.args.get("nationality")
    position = request.args.get("pos")
    min_age = request.args.get("minAge")
    max_age = request.args.get("maxAge")
    current_team = request.args.get("team")
    contact_expiration_date = request.args.get("contactExpirationDate")

    # nationality, position, min_age, and max_age
    # do not have sanitation because I didn't care

    if name is not None:
        name = name.strip()

    filters = {
        'name': name,
        'nationality': nationality,
        'min_age': min_age,
        'max_age': max_age,
        'team': current_team,
        'position': position,
        'contact_expiration_date': contact_expiration_date
    }

    players = fetch_transferable_players(filters, coachid)
    nationalities = fetch_all_nationalities()
    positions = fetch_all_positions()
    teams = fetch_all_teams()

    return render_template("coach_transfer_market.html", players=players, nationalities=nationalities, positions=positions, teams=teams)
    
    
@coach_bp.route("/transfer_offer/<player_id>", methods=["GET", "POST"])
def transfer_offer(player_id):
    if not player_id:
        return redirect(url_for('.view_transfer_market'))
    if request.method == "POST":
        amount = request.form.get("amount")
        available_until = request.form.get("availableUntil")
        offered_end_date = request.form.get("offeredEndDate")
        
        coach_id = session['user_id']
        make_transfer_offer(player_id, coach_id, amount, available_until, offered_end_date)
        return redirect(url_for('.view_transfer_market', message="Transfer offer made successfully."))

    player = fetch_player_by_id(player_id)
    return render_template("coach_transfer_offer.html", player=player)

@coach_bp.route("/view_transfer_offers")
def view_transfer_offers():
    coachid = session['user_id']
    transfer_offers = fetch_team_transfer_offers(coachid)
    return render_template('coach_view_transfer_offers.html', transfer_offers=transfer_offers)

@coach_bp.route("/evaluate_transfer_offer/<offerid>", methods=["GET", "POST"])
def evaluate_transfer_offer(offerid):
    if request.method == 'POST':
        decision = request.form.get("decision")
        if not decision:
            return redirect(url_for('.view_transfer_offers'))
        
        final_decision = decision == 'accept'
        finalize_transfer_offer(offerid, final_decision)
    return redirect(url_for('.view_transfer_offers'))

@coach_bp.route("/team")
def view_team():
    coach_id = session.get("user_id")
    team = fetch_team_by_coach(coach_id)
    
    if not team:
        # Coach doesn't have a team assigned
        return render_template("coach_team.html", team=None, players=[], coaches=[])
    
    # Fetch players and coaches for this team
    players = fetch_team_players(team["teamid"])
    coaches = fetch_team_coaches(team["teamid"])
    
    return render_template(
        "coach_team.html",
        team=team,
        players=players,
        coaches=coaches,
    )

@coach_bp.route("/offers")
def view_team_offers():
    coach_id = session.get("user_id")
    pending_offers, past_offers = fetch_team_transfer_offers(coach_id)
    sent_offers = fetch_sent_transfer_offers(coach_id)
    now = datetime.now()
    return render_template("coach_view_team_offers.html", pending_offers=pending_offers, past_offers=past_offers, sent_offers=sent_offers, now=now)

@coach_bp.route("/offers/<int:offer_id>/evaluate", methods=["POST"])
def evaluate_team_offer(offer_id):
    coach_id = session.get("user_id")
    
    # Verify the offer is for a player on this coach's team
    pending_offers, past_offers = fetch_team_transfer_offers(coach_id)
    all_offers = pending_offers + past_offers
    if not any(offer["offerid"] == offer_id for offer in all_offers):
        return redirect(url_for("coach.view_team_offers"))
    
    decision = request.form.get("decision")
    if decision in ("accept", "reject"):
        final_decision = decision == 'accept'
        finalize_transfer_offer(offer_id, final_decision)
    
    return redirect(url_for("coach.view_team_offers"))

@coach_bp.route("/trainings/assign")
def assign_training():
    """Placeholder page for training assignment functionality."""
    return render_template("coach_assign_training.html")