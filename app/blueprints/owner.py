from flask import Blueprint, render_template, session, redirect, url_for, request, abort, flash

from db_helper import (
    fetch_teams_by_owner,
    fetch_other_team_owners,
    transfer_team_owner,
    fetch_available_coaches,
    fetch_all_coaches,
    employ_coach_to_team,
    fetch_team_players,
)

owner_bp = Blueprint("owner", __name__, url_prefix="/owner")


@owner_bp.before_request
def require_owner():
    if session.get("role") != "team_owner":
        return redirect(url_for("login"))


@owner_bp.route("/teams")
def view_teams():
    owner_id = session.get("user_id")
    teams = fetch_teams_by_owner(owner_id)
    other_owners = fetch_other_team_owners(owner_id)
    all_coaches = fetch_all_coaches()
    
    # Get current coach and players for each team
    teams_with_details = []
    for team in teams:
        team_dict = dict(team)
        # Find coach assigned to this team
        current_coach = next((c for c in all_coaches if c.get("teamid") == team["teamid"]), None)
        team_dict["current_coach"] = current_coach
        # Fetch players for this team
        team_dict["players"] = fetch_team_players(team["teamid"])
        teams_with_details.append(team_dict)
    
    return render_template(
        "owner_teams.html",
        teams=teams_with_details,
        other_owners=other_owners,
    )


@owner_bp.route("/teams/<int:team_id>/transfer", methods=["POST"])
def transfer_team(team_id):
    owner_id = session.get("user_id")
    new_owner_id = request.form.get("new_owner_id")
    if not new_owner_id:
        abort(400)
    try:
        transfer_team_owner(team_id, owner_id, int(new_owner_id))
        flash("Team transferred successfully.", "success")
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("owner.view_teams"))
    return redirect(url_for("owner.view_teams"))


@owner_bp.route("/coaches/employ", methods=["GET", "POST"])
def employ_coach():
    owner_id = session.get("user_id")
    error_message = None
    
    if request.method == "POST":
        team_id = request.form.get("team_id")
        coach_id = request.form.get("coach_id")
        
        if not team_id or not coach_id:
            error_message = "Please select both a team and a coach."
        else:
            try:
                employ_coach_to_team(int(coach_id), int(team_id), owner_id)
                return redirect(url_for("owner.employ_coach"))
            except ValueError as exc:
                error_message = str(exc)
    
    teams = fetch_teams_by_owner(owner_id)
    available_coaches = fetch_available_coaches()
    all_coaches = fetch_all_coaches()
    
    # Get current coach for each team
    teams_with_coaches = []
    for team in teams:
        team_dict = dict(team)
        # Find coach assigned to this team
        current_coach = next((c for c in all_coaches if c.get("teamid") == team["teamid"]), None)
        team_dict["current_coach"] = current_coach
        teams_with_coaches.append(team_dict)
    
    return render_template(
        "owner_employ_coach.html",
        teams=teams_with_coaches,
        available_coaches=available_coaches,
        error_message=error_message,
    )


@owner_bp.route("/teams/<int:team_id>/employ-coach", methods=["POST"])
def assign_coach(team_id):
    owner_id = session.get("user_id")
    coach_id = request.form.get("coach_id")
    
    if not coach_id:
        abort(400)
    
    try:
        employ_coach_to_team(int(coach_id), team_id, owner_id)
    except ValueError:
        abort(400)
    
    return redirect(url_for("owner.employ_coach"))

