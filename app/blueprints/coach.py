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
        amount = request.args.get("amount")
        available_until = request.args.get("availableUntil")
        if not amount or not available_until or not player_id:
            pass

    player = fetch_player_by_id(player_id)
    return render_template("coach_transfer_offer.html", player=player)

@coach_bp.route("/view_transfer_offers")
def view_transfer_offers():
    transfer_offers=[{'offerid': 32}]
    return render_template('coach_view_transfer_offers.html', transfer_offers=transfer_offers)

@coach_bp.route("/evaluate_transfer_offer/<offerid>")
def evaluate_transfer_offer(offerid):
    if request.method == 'POST':
        decision = request.args.get("decision")
        if not decision:
            # no action can be taken, I guess return
            return
        elif decision == 'accept':
            # accept logic
            pass
        elif decision == 'reject':
            # reject logic
            pass
        # either render a page or redirect to the view_transfer_offer page with a message 'you accepted this offer etc. etc.'
    return redirect(url_for('.view_transfer_offers'))