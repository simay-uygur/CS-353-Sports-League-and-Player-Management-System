import psycopg2
from flask import Blueprint, render_template, request, redirect, url_for, session

from db_helper import (
    create_tournament_with_bracket,
    fetch_all_admins,
    fetch_all_teams,
    fetch_all_tournaments,
    fetch_matches_grouped,
    delete_tournament_and_matches,
)

superadmin_bp = Blueprint("superadmin", __name__, url_prefix="/superadmin")


@superadmin_bp.before_request
def require_superadmin_session():
    if session.get("user_id") is None or session.get("role") != "superadmin":
        session["next"] = request.path
        return redirect(url_for("login"))


@superadmin_bp.route("/tournaments")
def view_tournaments():
    tournaments = fetch_all_tournaments()
    if not tournaments:
        return render_template(
            "admin_view_tournaments.html",
            tournaments=[],
            selected_tournament=None,
            matches_by_round={},
            create_endpoint="superadmin.create_tournament_form",
            list_endpoint="superadmin.view_tournaments",
            delete_endpoint="superadmin.delete_tournament",
            allow_create=True,
        )

    requested_tournament_id = request.args.get("tournament_id")
    selected_tournament = _select_tournament(requested_tournament_id, tournaments)
    matches_by_round = fetch_matches_grouped(selected_tournament["tournamentid"])

    return render_template(
        "admin_view_tournaments.html",
        tournaments=tournaments,
        selected_tournament=selected_tournament,
        matches_by_round=matches_by_round,
        create_endpoint="superadmin.create_tournament_form",
        list_endpoint="superadmin.view_tournaments",
        delete_endpoint="superadmin.delete_tournament",
        allow_create=True,
    )


@superadmin_bp.route("/tournaments/create", methods=["GET", "POST"])
def create_tournament_form():
    teams = fetch_all_teams()
    admins = fetch_all_admins()
    error_message = None
    form_data = request.form if request.method == "POST" else {}
    selected_team_ids = form_data.getlist("team_ids") if request.method == "POST" else []
    selected_admin_ids = form_data.getlist("moderator_ids") if request.method == "POST" else []

    if request.method == "POST":
        try:
            result = create_tournament_with_bracket(
                form_data,
                session.get("user_id"),
                moderator_ids=selected_admin_ids,
            )
            return redirect(url_for("superadmin.view_tournaments", tournament_id=result["tournament_id"]))
        except ValueError as exc:
            error_message = str(exc)
        except psycopg2.Error as exc:
            error_message = getattr(exc.diag, "message_primary", str(exc))

    return render_template(
        "admin_create_tournament.html",
        teams=teams,
        admins=admins,
        error_message=error_message,
        form_data=form_data,
        selected_team_ids=set(selected_team_ids),
        selected_admin_ids=set(selected_admin_ids),
        cancel_endpoint="superadmin.view_tournaments",
    )


def _select_tournament(requested_id, tournaments):
    if requested_id:
        for tournament in tournaments:
            if str(tournament["tournamentid"]) == requested_id:
                return tournament
    return tournaments[0]


@superadmin_bp.route("/tournaments/<int:tournament_id>/delete", methods=["POST"])
def delete_tournament(tournament_id):
    delete_tournament_and_matches(tournament_id)
    return redirect(url_for("superadmin.view_tournaments"))
