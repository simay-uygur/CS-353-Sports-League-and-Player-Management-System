from flask import Blueprint, render_template, request, redirect, url_for, session

from db_helper import * 

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