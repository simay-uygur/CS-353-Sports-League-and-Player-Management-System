from flask import Blueprint, render_template, session, redirect, url_for, request, abort

from db_helper import (
    fetch_teams_by_owner,
    fetch_other_team_owners,
    transfer_team_owner,
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
    return render_template(
        "owner_teams.html",
        teams=teams,
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
    except ValueError:
        abort(400)
    return redirect(url_for("owner.view_teams"))

