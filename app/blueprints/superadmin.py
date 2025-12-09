import psycopg2
from flask import Blueprint, render_template, request, redirect, url_for, session

from db_helper import (
    create_tournament_with_bracket,
    fetch_all_admins,
    fetch_all_teams,
    fetch_all_tournaments,
    fetch_matches_grouped,
    delete_tournament_and_matches,
    fetch_all_leagues,
    fetch_league_by_id,
    create_league_with_seasons,
    assign_admins_to_season,
    assign_same_admins_to_all_seasons,
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


@superadmin_bp.route("/leagues")
def view_leagues():
    leagues = fetch_all_leagues()
    return render_template(
        "admin_view_leagues.html",
        leagues=leagues,
        create_endpoint="superadmin.create_league_form",
        assign_endpoint="superadmin.assign_admins_form",
    )


@superadmin_bp.route("/leagues/create", methods=["GET", "POST"])
def create_league_form():
    teams = fetch_all_teams()
    admins = fetch_all_admins()
    error_message = None
    form_data = request.form if request.method == "POST" else {}
    selected_team_ids = form_data.getlist("team_ids") if request.method == "POST" else []
    selected_admin_ids = form_data.getlist("global_admin_ids") if request.method == "POST" else []
    
    if request.method == "POST":
        try:
            league_name = form_data.get("league_name", "").strip()
            team_ids = form_data.getlist("team_ids")
            admin_assignment_mode = form_data.get("admin_assignment_mode", "all_seasons")
            
            # Validate teams
            if len(team_ids) < 2:
                raise ValueError("Please select at least 2 teams for the league.")
            
            # Collect seasons from form (season_no is auto-generated)
            season_count = int(form_data.get("season_count", 1))
            seasons_data = []
            seasons_admins = []  # Store admin assignments per season
            
            for i in range(season_count):
                start_date = form_data.get(f"start_date_{i}")
                start_time = form_data.get(f"start_time_{i}", "00:00")
                end_date = form_data.get(f"end_date_{i}")
                end_time = form_data.get(f"end_time_{i}", "23:59")
                prize_pool = form_data.get(f"prize_pool_{i}")
                
                if start_date and end_date:
                    seasons_data.append({
                        "season_year": start_date,  # keep key for downstream, derived from start date
                        "start_date": start_date,
                        "start_time": start_time,
                        "end_date": end_date,
                        "end_time": end_time,
                        "prize_pool": prize_pool or 0,
                    })
                    
                    # Collect admin assignments for this season
                    if admin_assignment_mode == "all_seasons":
                        # Use global admins for all seasons
                        season_admin_ids = form_data.getlist("global_admin_ids")
                    else:
                        # Use per-season admins
                        season_admin_ids = form_data.getlist(f"season_admins_{i}")
                    
                    seasons_admins.append(season_admin_ids)
            
            # Create league with seasons and teams
            result = create_league_with_seasons(league_name, seasons_data, team_ids=team_ids)
            league_id = result["league_id"]
            
            # Assign admins to seasons
            for i, season_admin_ids in enumerate(seasons_admins):
                if season_admin_ids:
                    season_no = i + 1
                    season_year = seasons_data[i]["season_year"]
                    assign_admins_to_season(league_id, season_no, season_year, season_admin_ids)
            
            return redirect(url_for("superadmin.view_leagues"))
        except ValueError as exc:
            error_message = str(exc)
        except psycopg2.Error as exc:
            error_message = getattr(exc.diag, "message_primary", str(exc))
    
    return render_template(
        "admin_create_league.html",
        teams=teams,
        admins=admins,
        error_message=error_message,
        form_data=form_data,
        selected_team_ids=set(selected_team_ids),
        selected_admin_ids=set(selected_admin_ids),
        cancel_endpoint="superadmin.view_leagues",
    )


def _find_league_by_id(leagues, league_id):
    """Find a league in the list by its ID."""
    for league in leagues:
        if league["leagueid"] == league_id:
            return league
    return None


def _process_season_admin_assignment(request_form, league_id):
    """Process per-season admin assignment from form data."""
    season_count = int(request_form.get("season_count", 0))
    for i in range(season_count):
        season_no = request_form.get(f"season_no_{i}")
        season_year = request_form.get(f"season_year_{i}")
        season_admin_ids = request_form.getlist(f"season_admins_{i}")
        
        if season_no and season_year and season_admin_ids:
            assign_admins_to_season(league_id, int(season_no), season_year, season_admin_ids)


def _group_seasons_with_admins(league_data):
    """Group seasons with their admin assignments from query results."""
    seasons_with_admins = {}
    for row in league_data:
        season_key = (row["seasonno"], row["seasonyear"])
        if season_key not in seasons_with_admins:
            seasons_with_admins[season_key] = {
                "season_no": row["seasonno"],
                "season_year": row["seasonyear"],
                "start_date": row["startdate"],
                "end_date": row["enddate"],
                "prize_pool": row["prizepool"],
                "admin_ids": [],
            }
        if row["adminid"]:
            seasons_with_admins[season_key]["admin_ids"].append(row["adminid"])
    
    return list(seasons_with_admins.values())


@superadmin_bp.route("/leagues/<int:league_id>/assign-admins", methods=["GET", "POST"])
def assign_admins_form(league_id):
    admins = fetch_all_admins()
    leagues = fetch_all_leagues()
    
    # Find selected league
    selected_league = _find_league_by_id(leagues, league_id)
    if not selected_league:
        return redirect(url_for("superadmin.view_leagues"))
    
    error_message = None
    
    if request.method == "POST":
        try:
            assignment_type = request.form.get("assignment_type", "all")
            admin_ids = request.form.getlist("admin_ids")
            
            if assignment_type == "all":
                assign_same_admins_to_all_seasons(league_id, admin_ids)
            else:
                _process_season_admin_assignment(request.form, league_id)
            
            return redirect(url_for("superadmin.view_leagues"))
        except ValueError as exc:
            error_message = str(exc)
        except psycopg2.Error as exc:
            error_message = getattr(exc.diag, "message_primary", str(exc))
    
    # Get fresh league data with current admin assignments
    league_data = fetch_league_by_id(league_id)
    seasons_list = _group_seasons_with_admins(league_data)
    # Preselect admins that are assigned to every season (used for "all seasons" mode)
    if seasons_list:
        common_admin_ids = set(seasons_list[0].get("admin_ids", []))
        for season in seasons_list[1:]:
            common_admin_ids &= set(season.get("admin_ids", []))
        global_admin_ids = list(common_admin_ids)
    else:
        global_admin_ids = []
    
    return render_template(
        "admin_assign_admins_to_seasons.html",
        league_id=league_id,
        league_name=selected_league["name"],
        seasons=seasons_list,
        admins=admins,
        global_admin_ids=global_admin_ids,
        error_message=error_message,
        cancel_endpoint="superadmin.view_leagues",
    )
