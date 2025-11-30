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
        allow_create=False,
    )


@admin_bp.route("/tournaments/create", methods=["GET", "POST"])
def create_tournament_form():
    if session.get("role") != "superadmin":
        return abort(403)

    teams = fetch_all_teams()
    error_message = None
    form_data = request.form if request.method == "POST" else {}
    selected_team_ids = form_data.getlist("team_ids") if request.method == "POST" else []

    if request.method == "POST":
        try:
            result = create_tournament_with_bracket(form_data, session.get("user_id"))
            return redirect(url_for("admin.view_tournaments", tournament_id=result["tournament_id"]))
        except ValueError as exc:
            error_message = str(exc)
        except psycopg2.Error as exc:
            error_message = getattr(exc.diag, "message_primary", str(exc))

    return render_template(
        "admin_create_tournament.html",
        teams=teams,
        admins=None,
        error_message=error_message,
        form_data=form_data,
        selected_team_ids=set(selected_team_ids),
        selected_admin_ids=set(),
        cancel_endpoint="admin.view_tournaments",
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
