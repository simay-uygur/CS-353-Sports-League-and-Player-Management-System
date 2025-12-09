from flask import Blueprint, render_template, request, redirect, url_for, session, abort

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
    name = request.args.get("name")
    nationality = request.args.get("nationality")
    position = request.args.get("pos")
    min_age = request.args.get("minAge")
    max_age = request.args.get("maxAge")
    current_team = request.args.get("team")

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
        'position': position
    }

    players = fetch_filtered_players(filters)
    nationalities = fetch_all_nationalities()

    return render_template("coach_transfer_market.html", players=players, nationalities=nationalities)
    
    
@coach_bp.route("/transfer_offer/<player_id>", methods=["GET", "POST"])
def transfer_offer(player_id):
    if not player_id:
        # return an error and redirect to view_transfer_offer
        pass
    if request.method == "POST":
        amount = request.args.get("amount")
        available_until = request.args.get("availableUntil")
        if not amount or not available_until or player_id:
            # return an error and rerender transfer_offer
            pass