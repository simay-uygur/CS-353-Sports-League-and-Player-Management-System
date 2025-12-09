import math
from datetime import datetime, timedelta

import psycopg2

from flask import Blueprint, render_template, request, redirect, url_for, session, abort
from psycopg2.extras import RealDictCursor

from db_helper import * 

from db import get_connection

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")



@admin_bp.before_request
def require_admin_session():
    # Allow both full admins and tournament_admins to access admin routes
    if session.get("user_id") is None or session.get("role") not in ("admin", "tournament_admin"):
        session["next"] = request.path
        return redirect(url_for("login"))


@admin_bp.route("/tournaments")
def view_tournaments():
    admin_id = session.get("user_id")
    if not admin_id:
        return redirect(url_for("login"))

    tournaments = fetch_tournaments(admin_id)
    if not tournaments:
        return render_template(
            "admin_view_tournaments.html",
            tournaments=[],
            selected_tournament=None,
            matches_by_round={},
            create_endpoint="admin.create_tournament_form",
            list_endpoint="admin.view_tournaments",
            allow_create=False,
        )

    requested_tournament_id = request.args.get("tournament_id")
    selected_tournament = _select_tournament(requested_tournament_id, tournaments)
    matches_by_round = fetch_matches_grouped(selected_tournament["tournamentid"])

    return render_template(
        "admin_view_tournaments.html",
        tournaments=tournaments,
        selected_tournament=selected_tournament,
        matches_by_round=matches_by_round,
        create_endpoint="admin.create_tournament_form",
        list_endpoint="admin.view_tournaments",
        delete_endpoint="admin.delete_tournament",
        allow_create=False,
    )


@admin_bp.route("/leagues")
def view_leagues():
    admin_id = session.get("user_id")
    if not admin_id:
        return redirect(url_for("login"))

    leagues = fetch_admin_leagues(admin_id)
    return render_template(
        "admin_view_leagues.html",
        leagues=leagues,
        create_endpoint=None,  # admins don't create leagues
        assign_endpoint=None,
    )


def _select_tournament(requested_id, tournaments):
    if requested_id:
        for tournament in tournaments:
            if str(tournament["tournamentid"]) == requested_id:
                return tournament
    return tournaments[0]


def _to_int(value, label, required=False, min_value=None):
    if value in (None, ""):
        if required:
            raise ValueError(f"{label} is required.")
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a valid number.")
    if min_value is not None and number < min_value:
        raise ValueError(f"{label} must be at least {min_value}.")
    return number


def _normalize_datetime(raw_value):
    if not raw_value:
        return None
    value = raw_value.replace("T", " ")
    if len(value) == 16:
        value += ":00"
    return value


@admin_bp.route("/tournaments/<int:tournament_id>/delete", methods=["POST"])
def delete_tournament(tournament_id):
    admin_id = session.get("user_id")
    if not admin_id:
        return redirect(url_for("login"))

    tournaments = fetch_tournaments(admin_id)
    if not any(t["tournamentid"] == tournament_id for t in tournaments):
        abort(403)

    delete_tournament_and_matches(tournament_id)
    return redirect(url_for("admin.view_tournaments"))


@admin_bp.route("/matches/referees", methods=["GET"])
def view_matches_for_referees():
    """View all tournament and seasonal matches for this admin to assign referees."""
    admin_id = session.get("user_id")
    if not admin_id:
        return redirect(url_for("login"))
    
    matches = fetch_admin_tournament_matches(admin_id)
    return render_template(
        "admin_matches_referees.html",
        matches=matches,
    )


@admin_bp.route("/matches/<int:match_id>/referees", methods=["GET"])
def match_referee_assignment(match_id):
    """View and assign referees to a specific match."""
    admin_id = session.get("user_id")
    if not admin_id:
        return redirect(url_for("login"))
    
    # Verify admin manages this match
    matches = fetch_admin_tournament_matches(admin_id)
    if not any(m["matchid"] == match_id for m in matches):
        abort(403)
    
    match = fetch_match_with_referees(match_id)
    if not match:
        abort(404)
    
    referees = fetch_all_referees()
    assigned_referee_ids = {ref["usersid"] for ref in match.get("referees", [])}
    
    return render_template(
        "admin_match_referee_detail.html",
        match=match,
        referees=referees,
        assigned_referee_ids=assigned_referee_ids,
    )


@admin_bp.route("/matches/<int:match_id>/referees/<int:referee_id>", methods=["POST"])
def assign_match_referee(match_id, referee_id):
    """Assign a referee to a match."""
    admin_id = session.get("user_id")
    if not admin_id:
        return redirect(url_for("login"))
    
    # Verify admin manages this match
    matches = fetch_admin_tournament_matches(admin_id)
    if not any(m["matchid"] == match_id for m in matches):
        abort(403)
    
    try:
        assign_referee_to_match(match_id, referee_id)
    except psycopg2.Error:
        pass  # Silent fail if already assigned
    
    return redirect(url_for("admin.match_referee_assignment", match_id=match_id))


@admin_bp.route("/matches/<int:match_id>/referees/<int:referee_id>/remove", methods=["POST"])
def remove_match_referee(match_id, referee_id):
    """Remove a referee from a match."""
    admin_id = session.get("user_id")
    if not admin_id:
        return redirect(url_for("login"))
    
    # Verify admin manages this match
    matches = fetch_admin_tournament_matches(admin_id)
    if not any(m["matchid"] == match_id for m in matches):
        abort(403)
    
    remove_referee_from_match(match_id, referee_id)
    return redirect(url_for("admin.match_referee_assignment", match_id=match_id))


@admin_bp.route("/matches/seasonal/lock-status")
def view_seasonal_matches_lock():
    """View all seasonal matches with lock/unlock controls."""
    admin_id = session.get("user_id")
    if not admin_id:
        return redirect(url_for("login"))
    
    matches = fetch_seasonal_matches_for_admin(admin_id)
    return render_template(
        "admin_seasonal_matches_lock.html",
        matches=matches,
    )


@admin_bp.route("/matches/<int:match_id>/lock", methods=["POST"])
def lock_match(match_id):
    """Lock a seasonal match."""
    admin_id = session.get("user_id")
    if not admin_id:
        return redirect(url_for("login"))
    
    # Verify admin manages this match
    matches = fetch_seasonal_matches_for_admin(admin_id)
    if not any(m["matchid"] == match_id for m in matches):
        abort(403)
    
    toggle_match_lock(match_id, True)
    return redirect(url_for("admin.view_seasonal_matches_lock"))


@admin_bp.route("/matches/<int:match_id>/unlock", methods=["POST"])
def unlock_match(match_id):
    """Unlock a seasonal match."""
    admin_id = session.get("user_id")
    if not admin_id:
        return redirect(url_for("login"))
    
    # Verify admin manages this match
    matches = fetch_seasonal_matches_for_admin(admin_id)
    if not any(m["matchid"] == match_id for m in matches):
        abort(403)
    
    toggle_match_lock(match_id, False)
    return redirect(url_for("admin.view_seasonal_matches_lock"))
