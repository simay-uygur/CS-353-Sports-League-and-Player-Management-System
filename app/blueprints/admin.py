import math
from datetime import datetime, timedelta
from io import BytesIO

import psycopg2
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from flask import Blueprint, render_template, request, redirect, url_for, session, abort, make_response
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
    leagues_with_teams = []
    for league in leagues or []:
        league_entry = dict(league)
        league_entry["teams"] = fetch_league_teams(league["leagueid"])
        league_entry["available_teams"] = fetch_league_available_teams(league["leagueid"])
        league_entry["matches"] = fetch_league_matches(league["leagueid"])
        leagues_with_teams.append(league_entry)

    return render_template(
        "admin_view_leagues.html",
        leagues=leagues_with_teams,
        create_endpoint=None,  # admins don't create leagues
        assign_endpoint=None,
        match_create_endpoint="admin.create_season_match",
        season_delete_endpoint="admin.delete_season_route",
        league_matches_ref_endpoint="admin.league_matches_referees",
    )


@admin_bp.route("/leagues/<int:league_id>/manage-teams", methods=["GET"])
def manage_league_teams(league_id):
    """Manage teams in a league - add/remove teams."""
    admin_id = session.get("user_id")
    if not admin_id:
        return redirect(url_for("login"))

    # Verify admin manages this league
    leagues = fetch_admin_leagues(admin_id)
    if not any(l["leagueid"] == league_id for l in leagues):
        abort(403)

    league = fetch_league_by_id(league_id)
    if not league:
        abort(404)

    league_name = league[0]["name"] if league else "Unknown League"
    league_teams = fetch_league_teams(league_id)
    available_teams = fetch_league_available_teams(league_id)
    error_message = request.args.get("error", None)

    return render_template(
        "admin_manage_league_teams.html",
        league_id=league_id,
        league_name=league_name,
        league_teams=league_teams,
        available_teams=available_teams,
        error_message=error_message,
    )


@admin_bp.route("/leagues/<int:league_id>/teams/<int:team_id>/add", methods=["POST"])
def add_team_to_league(league_id, team_id):
    """Add a team to a league."""
    admin_id = session.get("user_id")
    if not admin_id:
        return redirect(url_for("login"))

    try:
        # Verify admin manages this league
        leagues = fetch_admin_leagues(admin_id)
        if not any(l["leagueid"] == league_id for l in leagues):
            abort(403)

        # Add team to league
        conn = get_connection()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO LeagueTeam (LeagueID, TeamID) VALUES (%s, %s);",
                        (league_id, team_id),
                    )
        finally:
            conn.close()

        return redirect(url_for("admin.manage_league_teams", league_id=league_id))
    except psycopg2.IntegrityError:
        # Team already in league
        return redirect(url_for("admin.manage_league_teams", league_id=league_id))
    except psycopg2.Error as exc:
        error_msg = getattr(exc.diag, "message_primary", str(exc))
        return redirect(
            url_for(
                "admin.manage_league_teams",
                league_id=league_id,
                error=error_msg,
            )
        )


@admin_bp.route("/leagues/<int:league_id>/teams/<int:team_id>/remove", methods=["POST"])
def remove_team_from_league(league_id, team_id):
    """Remove a team from a league."""
    admin_id = session.get("user_id")
    if not admin_id:
        return redirect(url_for("login"))

    try:
        # Verify admin manages this league
        leagues = fetch_admin_leagues(admin_id)
        if not any(l["leagueid"] == league_id for l in leagues):
            abort(403)

        # Remove team from league
        conn = get_connection()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM LeagueTeam WHERE LeagueID = %s AND TeamID = %s;",
                        (league_id, team_id),
                    )
        finally:
            conn.close()

        return redirect(url_for("admin.manage_league_teams", league_id=league_id))
    except psycopg2.Error as exc:
        error_msg = getattr(exc.diag, "message_primary", str(exc))
        return redirect(
            url_for(
                "admin.manage_league_teams",
                league_id=league_id,
                error=error_msg,
            )
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
    
    # Get league_id from query parameter if coming from league view
    league_id = request.args.get("league_id", type=int)
    
    return render_template(
        "admin_match_referee_detail.html",
        match=match,
        referees=referees,
        assigned_referee_ids=assigned_referee_ids,
        league_id=league_id,
    )


@admin_bp.route("/leagues/<int:league_id>/matches/referees")
def league_matches_referees(league_id):
    admin_id = session.get("user_id")
    if not admin_id:
        return redirect(url_for("login"))

    allowed_leagues = {l["leagueid"] for l in fetch_admin_leagues(admin_id)}
    if league_id not in allowed_leagues:
        abort(403)

    matches = [m for m in fetch_league_matches(league_id)]
    referees = fetch_all_referees()
    return render_template(
        "admin_league_matches_referees.html",
        league_id=league_id,
        matches=matches,
        referees=referees,
    )


@admin_bp.route("/matches/<int:match_id>/referees", methods=["POST"])
@admin_bp.route("/matches/<int:match_id>/referees/<int:referee_id>", methods=["POST"])
def assign_match_referee(match_id, referee_id=None):
    """Assign a referee to a match."""
    admin_id = session.get("user_id")
    if not admin_id:
        return redirect(url_for("login"))
    
    # Verify admin manages this match
    matches = fetch_admin_tournament_matches(admin_id)
    if not any(m["matchid"] == match_id for m in matches):
        abort(403)
    
    ref_id = referee_id or request.form.get("referee_id")
    try:
        assign_referee_to_match(match_id, int(ref_id))
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


@admin_bp.route("/leagues/<int:league_id>/teams/add", methods=["GET", "POST"])
def add_team_to_league_route(league_id):
    admin_id = session.get("user_id")
    if not admin_id:
        return redirect(url_for("login"))
    allowed_leagues = {l["leagueid"] for l in fetch_admin_leagues(admin_id)}
    if league_id not in allowed_leagues:
        abort(403)
    
    if request.method == "GET":
        # Redirect to leagues view if accessed via GET
        return redirect(url_for("admin.view_leagues"))
    
    # POST: Add team to league
    team_id = request.form.get("team_id")
    if not team_id:
        abort(400)
    add_team_to_league(league_id, int(team_id))
    return redirect(url_for("admin.view_leagues"))


@admin_bp.route("/leagues/<int:league_id>/seasons/<int:season_no>/<season_year>/delete", methods=["POST"])
def delete_season_route(league_id, season_no, season_year):
    admin_id = session.get("user_id")
    if not admin_id:
        return redirect(url_for("login"))
    allowed_leagues = {l["leagueid"] for l in fetch_admin_leagues(admin_id)}
    if league_id not in allowed_leagues:
        abort(403)
    delete_season(league_id, season_no, season_year)
    return redirect(url_for("admin.view_leagues"))


@admin_bp.route("/leagues/<int:league_id>/seasons/<int:season_no>/<season_year>/matches/create", methods=["GET", "POST"])
def create_season_match_form(league_id, season_no, season_year):
    admin_id = session.get("user_id")
    if not admin_id:
        return redirect(url_for("login"))
    
    allowed_leagues = {l["leagueid"] for l in fetch_admin_leagues(admin_id)}
    if league_id not in allowed_leagues:
        abort(403)

    def _render_form(error_message=None):
        league = fetch_league_by_id(league_id)
        if not league:
            abort(404)
        league_name = league[0]["name"] if league else "Unknown League"
        teams = fetch_league_teams(league_id)
        return render_template(
            "admin_create_season_match.html",
            league_id=league_id,
            league_name=league_name,
            season_no=season_no,
            season_year=season_year,
            teams=teams,
            error_message=error_message,
            form_data=request.form,
        )

    if request.method == "GET":
        # Display the form
        return _render_form()
    
    # Handle POST
    home_team_id = request.form.get("home_team_id")
    away_team_id = request.form.get("away_team_id")
    start_dt_raw = request.form.get("start_datetime")
    venue = request.form.get("venue") or None

    missing_bits = []
    if not home_team_id:
        missing_bits.append("home team")
    if not away_team_id:
        missing_bits.append("away team")
    if not start_dt_raw:
        missing_bits.append("start date/time")
    if missing_bits:
        return _render_form(f"Please provide: {', '.join(missing_bits)}.")

    if home_team_id == away_team_id:
        return _render_form("Home and away team must be different.")

    normalized_start = _normalize_datetime(start_dt_raw)
    match_date = normalized_start.split(" ")[0] if normalized_start else None

    if match_date:
        conflicts = []
        if team_has_match_on_date(int(home_team_id), match_date):
            conflicts.append("home team")
        if team_has_match_on_date(int(away_team_id), match_date):
            conflicts.append("away team")
        if conflicts:
            return _render_form(
                f"Cannot create match: the {', '.join(conflicts)} already has a match on {match_date}."
            )

    try:
        create_season_match(
            league_id,
            season_no,
            season_year,
            int(home_team_id),
            int(away_team_id),
            normalized_start,
            venue,
        )
    except ValueError as exc:
        return _render_form(str(exc))

    return redirect(url_for("admin.view_leagues"))


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


@admin_bp.route("/matches/all/lock-status")
def view_all_matches_lock():
    """View all matches (league and tournament) with filters and lock/unlock controls for league matches only."""
    admin_id = session.get("user_id")
    if not admin_id:
        return redirect(url_for("login"))
    
    # Get filter parameters - handle both single and multiple values
    season_year_params = request.args.getlist("season_year")
    season_year = int(season_year_params[0]) if season_year_params and season_year_params[0] else None
    league_id_params = request.args.getlist("league_id")
    league_id = league_id_params[0] if league_id_params and league_id_params[0] else None
    tournament_id_params = request.args.getlist("tournament_id")
    tournament_id = tournament_id_params[0] if tournament_id_params and tournament_id_params[0] else None
    
    # Fetch dropdown data
    seasons = fetch_seasons_for_dropdown()
    leagues = fetch_leagues_for_dropdown()
    tournaments = fetch_tournaments_for_dropdown()
    
    # Fetch filtered matches
    matches = fetch_all_matches_with_filters(admin_id, season_year, league_id, tournament_id)
    
    return render_template(
        "admin_all_matches_lock.html",
        matches=matches,
        seasons=seasons,
        leagues=leagues,
        tournaments=tournaments,
        selected_season_year=season_year_params[0] if season_year_params and season_year_params[0] else None,
        selected_league_id=league_id_params[0] if league_id_params and league_id_params[0] else None,
        selected_tournament_id=tournament_id_params[0] if tournament_id_params and tournament_id_params[0] else None,
    )


@admin_bp.route("/matches/<int:match_id>/toggle-lock", methods=["POST"])
def toggle_match_lock_route(match_id):
    """Toggle lock/unlock for a league match only (with permission check)."""
    admin_id = session.get("user_id")
    if not admin_id:
        return redirect(url_for("login"))
    
    # Try to toggle the lock (only works for league matches with permission)
    rows_affected = toggle_league_match_lock_by_admin(match_id, admin_id)
    
    if rows_affected == 0:
        # No permission or not a league match
        abort(403)
    
    # Preserve filters in redirect
    season_year = request.args.get("season_year")
    league_id = request.args.get("league_id")
    tournament_id = request.args.get("tournament_id")
    
    return redirect(url_for("admin.view_all_matches_lock", 
                           season_year=season_year, 
                           league_id=league_id, 
                           tournament_id=tournament_id))


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


@admin_bp.route("/reports", methods=["GET", "POST"])
def reports():
    admin_id = session.get("user_id")
    if not admin_id:
        return redirect(url_for("login"))

    players_report = None
    standings_report = None
    attendance_report = None
    error_message = request.args.get("error")

    if request.method == "POST":
        report_type = request.form.get("report_type")
        try:
            if report_type == "players":
                players_report = report_players({
                    "player_id": _to_int(request.form.get("player_id"), "Player ID") if request.form.get("player_id") else None,
                    "currently_employed": bool(request.form.get("currently_employed")),
                    "employed_before": request.form.get("employed_before"),
                    "employed_after": request.form.get("employed_after"),
                    "ended_before": request.form.get("ended_before"),
                    "ended_after": request.form.get("ended_after"),
                })
            elif report_type == "standings":
                league_id = _to_int(request.form.get("league_id"), "League ID", required=True)
                season_no = _to_int(request.form.get("season_no"), "Season No", required=True)
                season_year = request.form.get("season_year")
                if not season_year:
                    raise ValueError("Season year is required.")
                standings_report = report_league_standings(league_id, season_no, season_year)
            elif report_type == "attendance":
                date_from = request.form.get("date_from") or None
                date_to = request.form.get("date_to") or None
                player_id = _to_int(request.form.get("player_id"), "Player ID") if request.form.get("player_id") else None
                team_id = _to_int(request.form.get("team_id"), "Team ID") if request.form.get("team_id") else None
                all_teams = bool(request.form.get("all_teams"))
                attendance_report = report_player_attendance(date_from, date_to, player_id, team_id, all_teams)
        except ValueError as exc:
            error_message = str(exc)

    leagues = fetch_all_leagues()
    teams = fetch_all_teams()
    return render_template(
        "admin_reports.html",
        error_message=error_message,
        players_report=players_report,
        standings_report=standings_report,
        attendance_report=attendance_report,
        leagues=leagues,
        teams=teams,
    )


@admin_bp.route("/reports/download", methods=["POST"])
def download_report_pdf():
    admin_id = session.get("user_id")
    if not admin_id:
        return redirect(url_for("login"))

    report_type = request.form.get("report_type")
    filter_info = []
    
    try:
        if report_type == "players":
            player_id = request.form.get("player_id")
            currently_employed = request.form.get("currently_employed")
            employed_before = request.form.get("employed_before")
            employed_after = request.form.get("employed_after")
            ended_before = request.form.get("ended_before")
            ended_after = request.form.get("ended_after")
            
            if player_id:
                filter_info.append(f"Player ID: {player_id}")
            if currently_employed:
                filter_info.append("Currently Employed: Yes")
            if employed_before:
                filter_info.append(f"Employed Before: {employed_before}")
            if employed_after:
                filter_info.append(f"Employed After: {employed_after}")
            if ended_before:
                filter_info.append(f"Ended Before: {ended_before}")
            if ended_after:
                filter_info.append(f"Ended After: {ended_after}")
            
            data = report_players({
                "player_id": _to_int(player_id, "Player ID") if player_id else None,
                "currently_employed": bool(currently_employed),
                "employed_before": employed_before,
                "employed_after": employed_after,
                "ended_before": ended_before,
                "ended_after": ended_after,
            })
            title = "Player Report"
            headers = ["Name", "Email", "Position", "Team", "Start", "End"]
            rows = [
                [
                    f"{row['firstname']} {row['lastname']}",
                    row["email"],
                    row["position"],
                    row["teamname"] or "Unassigned",
                    row["startdate"].strftime("%Y-%m-%d") if row["startdate"] else "",
                    row["enddate"].strftime("%Y-%m-%d") if row["enddate"] else "",
                ]
                for row in data
            ]
            filename = "player-report.pdf"
        elif report_type == "standings":
            league_id = _to_int(request.form.get("league_id"), "League ID", required=True)
            season_no = _to_int(request.form.get("season_no"), "Season No", required=True)
            season_year = request.form.get("season_year")
            if not season_year:
                raise ValueError("Season year is required.")
            
            filter_info.append(f"League ID: {league_id}")
            filter_info.append(f"Season No: {season_no}")
            filter_info.append(f"Season Year: {season_year}")
            
            data = report_league_standings(league_id, season_no, season_year)
            title = f"League Standings"
            headers = ["Team", "Pts", "W", "D", "L", "GF", "GA", "GD"]
            rows = [
                [
                    row["teamname"],
                    row["points"],
                    row["wins"],
                    row["draws"],
                    row["losses"],
                    row["gf"],
                    row["ga"],
                    row["gf"] - row["ga"],
                ]
                for row in data
            ]
            filename = "standings-report.pdf"
        elif report_type == "attendance":
            date_from = request.form.get("date_from") or None
            date_to = request.form.get("date_to") or None
            player_id = request.form.get("player_id")
            team_id = request.form.get("team_id")
            all_teams = request.form.get("all_teams")
            
            if date_from:
                filter_info.append(f"Date From: {date_from}")
            if date_to:
                filter_info.append(f"Date To: {date_to}")
            if player_id:
                filter_info.append(f"Player ID: {player_id}")
            if team_id:
                filter_info.append(f"Team ID: {team_id}")
            if all_teams:
                filter_info.append("All Teams: Yes")
            if not filter_info:
                filter_info.append("All Trainings")
            
            data = report_player_attendance(
                date_from,
                date_to,
                _to_int(player_id, "Player ID") if player_id else None,
                _to_int(team_id, "Team ID") if team_id else None,
                bool(all_teams)
            )
            title = "Training Attendance Report"
            headers = ["Player", "Appearances"]
            rows = [
                [
                    f"{row['firstname']} {row['lastname']}",
                    row["appearances"],
                ]
                for row in data
            ]
            filename = "attendance-report.pdf"
        else:
            raise ValueError("Invalid report type.")
    except ValueError as exc:
        return redirect(url_for("admin.reports", error=str(exc)))

    pdf_bytes = _build_pdf_document(title, headers, rows, filter_info)

    response = make_response(pdf_bytes)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def _build_pdf_document(title, headers, rows, filter_info=None):
    """
    Generate PDF document with Excel-like table formatting using reportlab.
    Uses landscape orientation if table is too wide, otherwise portrait.
    """
    buffer = BytesIO()
    
    # Determine page orientation based on number of columns
    # Use landscape if more than 6 columns
    num_cols = len(headers)
    use_landscape = num_cols > 6
    
    # Calculate minimum column width needed
    min_col_width = 1.0 * inch
    estimated_total_width = num_cols * min_col_width
    
    # Check if we need landscape based on width
    portrait_width = letter[0] - (0.5 * inch * 2)  # minus margins
    if estimated_total_width > portrait_width:
        use_landscape = True
    
    if use_landscape:
        pagesize = landscape(letter)
    else:
        pagesize = letter
    
    page_width, page_height = pagesize
    
    # Create PDF document
    doc = SimpleDocTemplate(buffer, pagesize=pagesize,
                            rightMargin=0.5*inch, leftMargin=0.5*inch,
                            topMargin=0.75*inch, bottomMargin=0.5*inch)
    
    # Container for PDF elements
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        spaceAfter=20,
        alignment=TA_LEFT
    )
    
    # Add title
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Add filter information if provided
    if filter_info:
        filter_text = "Filters: " + " | ".join(filter_info)
        elements.append(Paragraph(filter_text, subtitle_style))
        elements.append(Spacer(1, 0.1*inch))
    
    # Prepare table data
    table_data = [headers] + rows
    
    # Calculate column widths - distribute evenly
    available_width = page_width - doc.leftMargin - doc.rightMargin
    col_widths = [available_width / num_cols] * num_cols
    
    # Create table
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    # Table style - Excel-like appearance
    table_style = TableStyle([
        # Header row styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        
        # Data rows styling
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D0D0D0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        
        # Alternating row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F2F2')]),
    ])
    
    table.setStyle(table_style)
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    
    # Get PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes
